import requests
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_currency_rates():
    """
    يقوم بجلب أسعار العملات من موقع يدعم API أو يقدم البيانات بشكل أسهل
    """
    # نستخدم API مجاني لأسعار العملات كمثال
    url = "https://api.exchangerate-api.com/v4/latest/EGP"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            
            # نقوم بحساب العكس لأن API يعطينا النسبة مقابل الجنيه المصري
            currencies = {
                'USD': round(1 / rates.get('USD', 0), 2),
                'EUR': round(1 / rates.get('EUR', 0), 2),
                'GBP': round(1 / rates.get('GBP', 0), 2),
                'SAR': round(1 / rates.get('SAR', 0), 2)
            }
            
            logger.info(f"تم جلب الأسعار بنجاح: {currencies}")
            return currencies
        else:
            logger.error(f"خطأ في الاتصال: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"خطأ في جلب البيانات: {str(e)}")
        return None

def save_to_json(data):
    """
    حفظ البيانات في ملف JSON
    """
    try:
        filename = 'currency_rates.json'
        # قراءة البيانات الموجودة
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
        
        # إضافة البيانات الجديدة
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "timestamp": timestamp,
            "rates": data
        }
        existing_data.append(new_entry)
        
        # حفظ البيانات
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"تم حفظ البيانات بنجاح في {timestamp}")
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات: {str(e)}")

def main():
    """
    الدالة الرئيسية للبرنامج
    """
    update_interval = 300  # تحديث كل 5 دقائق
    
    logger.info("بدء متابعة أسعار العملات...")
    while True:
        try:
            rates = get_currency_rates()
            if rates:
                save_to_json(rates)
            time.sleep(update_interval)
        except KeyboardInterrupt:
            logger.info("تم إيقاف البرنامج")
            break
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            time.sleep(60)  # انتظر دقيقة قبل المحاولة مرة أخرى

if __name__ == "__main__":
    main()