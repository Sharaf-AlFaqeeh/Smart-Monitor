import cv2
import base64
import requests
import json
import google.generativeai as genai
import configparser
import sys

# تحميل إعدادات الحساب من ملف config.inf والتحقق من وجود قسم Gemini والمفتاح المطلوب
config = configparser.ConfigParser()
config.read("config.inf")
if "Gemini" not in config or "GEMINI_API_KEY" not in config["Gemini"]:
    print("خطأ: ملف الإعدادات لا يحتوي على تفاصيل Gemini API.")
    sys.exit(1)

# تهيئة Gemini API باستخدام المفتاح المحمل من ملف الإعدادات
GOOGLE_API_KEY = config["Gemini"]["GEMINI_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

def send_gemini_vision_request_from_frame(frame, prompt):
    """
    ترسل صورة (كائن صورة من الكاميرا) ونص الطلب (prompt) إلى Gemini Vision API وترجع النتيجة.

    المعاملات:
      - frame: كائن الصورة الملتقطة (numpy array) من الكاميرا.
      - prompt: نص الطلب لتحليل الصورة.
    
    تعيد الدالة استجابة JSON في حالة نجاح الطلب أو None مع طباعة رسالة خطأ.
    """
    try:
        # التحقق من صحة الإطار
        if frame is None:
            print("خطأ: الصورة الملتقطة فارغة.")
            return None

        # تحويل الصورة إلى JPEG وترميزها إلى base64
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("فشل ترميز الصورة إلى JPEG.")
            return None

        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # رابط الـ endpoint الخاص بنموذج Gemini Vision
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GOOGLE_API_KEY}"

        # إعداد بيانات الطلب وفق البنية المتوقعة
        payload = {
            "prompt": {
                "text": prompt
            },
            "image": {
                "content": image_base64,
                "mimeType": "image/jpeg"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            response_data = response.json()
            # يمكن تعديل هذا الفحص حسب بنية الاستجابة المتوقعة من Gemini Vision API
            if response_data.get("result"):
                return response_data
            else:
                print("الاستجابة لا تحتوي على البيانات المتوقعة:", response_data)
                return None
        else:
            print(f"خطأ: رمز الحالة {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print("فشل إرسال الطلب:", e)
        return None

# مثال على الاستخدام:
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("خطأ: لا يمكن فتح الكاميرا.")
    else:
        ret, frame = cap.read()
        if ret:
            PROMPT = "قم بتحليل الصورة ووصف محتوياتها."
            result = send_gemini_vision_request_from_frame(frame, PROMPT)
            if result:
                print("الاستجابة من Gemini Vision API:")
                print(json.dumps(result, indent=4, ensure_ascii=False))
            else:
                print("لم يتم استلام استجابة صحيحة من Gemini Vision API.")
        else:
            print("فشل التقاط الصورة من الكاميرا.")
    cap.release()
    cv2.destroyAllWindows()