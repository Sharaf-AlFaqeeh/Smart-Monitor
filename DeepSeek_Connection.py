import requests
import base64
import requests
import configparser

# Load account details from config.inf
config = configparser.ConfigParser()
config.read("config.inf")
# initialize Gemini API 
DEEPSEEK_API_KEY = config["DeepSeek"]["DEEPSEEK_API_KEY"]


def analyze_image_with_deepseek(image_path, prompt, api_key):
    """
    دالة لإرسال صورة وطلب إلى Deepseek API وتحليل النتيجة.
    
    المَعلمات:
        image_path (str): مسار ملف الصورة
        prompt (str): الطلب أو السؤال عن الصورة
        api_key (str): مفتاح API الخاص بـ Deepseek
    
    الإرجاع:
        str: نتيجة التحليل
    """
    
    # 1. قراءة الصورة وتشفيرها بـ base64
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # 2. تحضير البيانات للإرسال
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "image": encoded_image,
        "prompt": prompt,
        # يمكن إضافة معاملات إضافية حسب متطلبات API
    }
    
    # 3. إرسال الطلب إلى API
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/vision",  # افتراضي - قد يختلف URL الفعلي
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()  # التحقق من الأخطاء
        
        # 4. معالجة الاستجابة
        result = response.json().get("analysis_result", "No result found")
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# مثال استخدام الدالة
try:
    analysis_result = analyze_image_with_deepseek(
        image_path="captured_image.jpg",
        prompt="ما هو الوصف المناسب لهذه الصورة؟",
        api_key=DEEPSEEK_API_KEY
    )
    print(analysis_result)
except Exception as e:
    print(f"Error: {e}")