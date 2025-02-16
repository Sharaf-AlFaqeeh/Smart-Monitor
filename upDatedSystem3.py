import requests
import configparser
import cv2
import time
import threading
import logging
import numpy as np
import json
from ultralytics import YOLO
import google.generativeai as genai

from GeminiConection import send_gemini_vision_request_from_frame
from alert_system import (
    execute_command_and_alert,
    send_telegram_message__alert,
    send_telegram_alert,
    send_sms,
    TELEGRAM_CHAT_ID,
    TELEGRAM_BOT_TOKEN
)
from command_section import (
    camera_on, camera_off,
    camera_left, camera_right,
    camera_up, camera_down,
    buzzer_on, buzzer_off, buzzer_beep
)
from flask import Flask, Response

# إعداد سجل الأحداث (logging)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# قراءة الإعدادات من ملف config.inf
def load_config():
    config = configparser.ConfigParser()
    config.read("config.inf", encoding="utf-8")
    return config

config = load_config()
API_KEY = config["Gemini"]["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# إعداد المتغيرات المشتركة بين الخيوط
frame_lock = threading.Lock()
latest_raw_frame = None       # آخر إطار خام (للتحليل والتقاط الصور)
latest_encoded_frame = None   # آخر إطار مشفر (لبث الفيديو عبر الويب)

# إعداد مصفوفات التحكم الافتراضية
def initialize_control_array():
    pre_control_camera_and_buzzer = np.array([1, 0, 0, 0, 1], dtype="int8")
    pre_control_camera_position = np.array([0, 0, 0, 0], dtype="int8")
    pre_merged_array = np.concatenate((pre_control_camera_and_buzzer, pre_control_camera_position))
    return pre_control_camera_and_buzzer, pre_control_camera_position, pre_merged_array

pre_control_camera_and_buzzer, pre_control_camera_position, pre_merged_array = initialize_control_array()

model = YOLO('yolo11n.pt')

CAPTURE_URL = "http://192.168.8.197:81/stream"
cap = cv2.VideoCapture(1)

# تعريف الكائنات التي يتم اكتشافها (يمكن تعديلها حسب الحاجة)
crime_objects = {
    1: 'Pistol',
    2: 'Rifle',
    3: 'knife',
    4: 'fire'
}

# معلمات التنبيه
last_sent_time = 0
ALERT_INTERVAL = 10  # ثواني

# دالة لإرجاع آخر إطار خام بشكل آمن
def get_latest_raw_frame():
    with frame_lock:
        return latest_raw_frame.copy() if latest_raw_frame is not None else None

# دالة لالتقاط صورة وإرسالها عبر Telegram
def capture_and_send():
    frame = get_latest_raw_frame()
    if frame is not None:
        image_path = "captured_image.jpg"
        cv2.imwrite(image_path, frame)
        send_telegram_alert("الصورة الملتقطة", image_path)
        logging.info("تم التقاط الصورة وإرسالها.")
    else:
        logging.warning("لا يوجد إطار متاح للالتقاط.")

# دالة لتسجيل فيديو لفترة محددة وإرساله عبر Telegram
def record_and_send(duration):
    video_path = "recorded_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))
    
    # استخدام كائن VideoCapture جديد للتسجيل لتفادي التعارض مع العملية الرئيسية
    cap_rec = cv2.VideoCapture(CAPTURE_URL)
    start_time = time.time()
    while time.time() - start_time < duration:
        ret_rec, frame_rec = cap_rec.read()
        if not ret_rec:
            logging.error("فشل في قراءة الإطار أثناء التسجيل.")
            break
        out.write(frame_rec)
    out.release()
    cap_rec.release()
    
    video_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            response = requests.post(video_url, data=data, files=files)
            if response.ok:
                logging.info("تم تسجيل الفيديو وإرساله.")
            else:
                logging.error("فشل إرسال الفيديو عبر Telegram.")
    except Exception as e:
        logging.error(f"حدث خطأ أثناء إرسال الفيديو: {e}")

# دالة للاستماع للأوامر الواردة من Telegram وتنفيذها
def listen_for_commands():
    global pre_merged_array
    try:
        with open("lastUp.json", "r") as f:
            last_update_data = json.load(f)
        last_update_id = int(last_update_data.get("last_update_id", 0))
    except Exception:
        logging.warning("لم يتم العثور على ملف lastUp.json، سيتم البدء من البداية.")
        last_update_id = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            # استخدام معامل offset لتجنب قراءة التحديثات القديمة واستخدام timeout لتقليل عدد الطلبات
            params = {"offset": last_update_id + 1, "timeout": 10}
            response = requests.get(url, params=params, timeout=15).json()
            if not response.get("ok", False):
                logging.error("استجابة غير صحيحة من Telegram API")
                time.sleep(2)
                continue

            updates = response.get("result", [])
            for update in updates:
                update_id = int(update["update_id"])
                last_update_id = update_id
                # تحديث ملف lastUp.json
                with open("lastUp.json", "w") as f:
                    json.dump({"last_update_id": last_update_id}, f)

                if "message" in update and "text" in update["message"]:
                    command = update["message"]["text"].strip().lower()
                    logging.info(f"استقبل أمر: {command}")

                    if command == "capture":
                        capture_and_send()
                    elif command.startswith("record"):
                        try:
                            parts = command.split()
                            duration = int(parts[1]) if len(parts) > 1 else 5
                            threading.Thread(target=record_and_send, args=(duration,), daemon=True).start()
                        except Exception as e:
                            logging.error("خطأ في إدخال مدة الفيديو: " + str(e))
                    elif command == "default":
                        send_telegram_message__alert("تم استعادة إعدادات الكاميرا والصوت الافتراضية")
                        pre_control_camera_and_buzzer, pre_control_camera_position, pre_merged_array = initialize_control_array()
                    else:
                        control_camera_and_buzzer = np.array([
                            1 if command == "camera on" else 0,
                            1 if command == "camera off" else 0,
                            1 if command == "buzzer on" else 0,
                            1 if command == "buzzer beep" else 0,
                            1 if command == "buzzer off" else 0
                        ], dtype="int8")
                        control_camera_position = np.array([
                            1 if command == "camera right" else 0,
                            1 if command == "camera left" else 0,
                            1 if command == "camera up" else 0,
                            1 if command == "camera down" else 0
                        ], dtype="int8")
                        merged_array = np.concatenate((control_camera_and_buzzer, control_camera_position))
                        if not np.array_equal(pre_merged_array, merged_array):
                            execute_command_and_alert(merged_array, command)
                            pre_merged_array = merged_array
                        else:
                            try:
                                send_telegram_message__alert("Gemini chat analysis")
                                frame_for_analysis = get_latest_raw_frame()
                                if frame_for_analysis is not None:
                                    result = send_gemini_vision_request_from_frame(
                                        frame=frame_for_analysis,
                                        prompt=command,
                                        api_key=API_KEY
                                    )
                                    send_telegram_message__alert(result)
                                else:
                                    send_telegram_message__alert("لا يوجد إطار متاح لتحليل Gemini")
                            except Exception as e:
                                send_telegram_message__alert("حدث خطأ في تحليل Gemini: " + str(e))
            time.sleep(1)
        except Exception as e:
            logging.error(f"حدث خطأ في listen_for_commands: {e}")
            time.sleep(2)

# دالة لمعالجة الإطارات القادمة من الكاميرا
def process_frames():
    global latest_raw_frame, latest_encoded_frame, last_sent_time
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logging.error("فشل في قراءة الإطار من الكاميرا.")
            time.sleep(0.1)
            continue

        with frame_lock:
            latest_raw_frame = frame.copy()

        # إجراء الكشف باستخدام نموذج YOLO
        results = model.predict(frame, conf=0.5)
        detected = set()
        if results and results[0].boxes is not None:
            for box in results[0].boxes.data:
                class_id = int(box[5])
                if class_id in crime_objects:
                    detected.add(crime_objects[class_id])
        
        annotated_frame = results[0].plot() if results else frame
        cv2.imshow('Crime Object Detection', annotated_frame)

        if cv2.waitKey(500) & 0xFF == ord('q'):
            break

process_frames()