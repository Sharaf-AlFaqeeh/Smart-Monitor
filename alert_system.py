
import requests
import configparser
from twilio.rest import Client
import google.generativeai as genai

# Load account details from config.inf
config = configparser.ConfigParser()
config.read("config.inf", encoding="utf-8")
# telegram to send photo
TELEGRAM_BOT_TOKEN = config["TELEGRAM"]["BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM"]["CHAT_ID"]
# toillo to send sms
TWILIO_SID = config["SMS"]["TWILIO_SID"]
TWILIO_AUTH_TOKEN = config["SMS"]["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = config["SMS"]["TWILIO_PHONE_NUMBER"]
RECEIVER_PHONE_NUMBER = config["SMS"]["RECEIVER_PHONE_NUMBER"]
# initialize Gemini API
GOOGLE_API_KEY = config["Gemini"]["GEMINI_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)


# for sending sms 
def send_sms(detected_object):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"🚨 تنبيه: تم اكتشاف {detected_object} في الفيديو المباشر! انتقل إلى البوت: t.me/SmartCamCrimeAlertBot",
            from_=TWILIO_PHONE_NUMBER,
            to=RECEIVER_PHONE_NUMBER
        )
        print(f"[+] تم إرسال رسالة SMS: {message.sid}")
    except Exception as e:
        print(f"[!] فشل إرسال الرسالة: {e}")
    
# send message
def send_telegram_message__alert(message):
    try:
        text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text_payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(text_url, data=text_payload)
    except Exception as e:
        print(f"[!] فشل في ارسال الرسالة: {e}")
    
# function to send alerts to telegram
def send_telegram_alert(detected_object, image_path=None):
    try:
        message = f"🚨 تنبيه: تم اكتشاف {detected_object} في الفيديو المباشر!"
        text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text_payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(text_url, data=text_payload)
        # photo to send
        photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        try:
            with open(image_path, "rb") as photo:
                files = {"photo": photo}
                data = {"chat_id": TELEGRAM_CHAT_ID}
                requests.post(photo_url, data=data, files=files)
        except FileNotFoundError:
            print(f"File not found: {image_path}")
    except Exception as e:
        print(f"[!] فشل في ارسال الرسالة: {e}")


# for sending alerts
def execute_command_and_alert(merged_array, command):
    
    commands = [ "camera on", "camera off", "buzzer on", "buzzer beep", "buzzer off",
                 "camera right", "camera left", "camera up", "camera down"  ]
    # search for executed commands
    executed_commands = [commands[i] for i in range(len(merged_array)) if merged_array[i] == 1]
    # if there are executed commands, send an alert
    if executed_commands:
        message = f"تم تنفيذ الأمر التالي: {', '.join(executed_commands)}"
        send_telegram_message__alert(message)
    else: 
        message = f"  الأمر التالي ليس في قائمة الأوامر {', '.join(command)}"
        send_telegram_message__alert(message)