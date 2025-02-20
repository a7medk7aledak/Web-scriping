import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import logging
import os
import re

# إعداد التسجيل
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self):
        self.news_sources = {
            'youm7': {
                'url': 'https://www.youm7.com',
                # استخدام محددات أكثر عمومية
                'article_selector': 'div.news-box',  # البحث عن أي عنصر div بفئة news-box
                'title_selector': 'h3, h2, div.news-title',  # دعم أكثر من تاج للعنوان
                'link_selector': 'a[href*="/story/"]',  # البحث عن روابط تحتوي على "story"
                'summary_selector': 'div.news-lead-txt, div.briefs-lead, div.brief-tit'  # محاولة للعثور على ملخص
            }
        }
        
    def _find_relative_element(self, parent, selector):
        """البحث عن عنصر داخل عنصر أبوي أو في أقرب عنصر شقيق"""
        # البحث داخل العنصر الأبوي أولاً
        element = parent.select_one(selector)
        if element:
            return element
            
        # البحث في الأشقاء إذا لم يتم العثور داخل الأب
        siblings = list(parent.next_siblings)
        for sibling in siblings[:3]:  # فحص أول 3 أشقاء فقط
            if hasattr(sibling, 'select_one'):
                element = sibling.select_one(selector)
                if element:
                    return element
        return None

    def get_full_article_content(self, article_url, source_name):
        """استخراج محتوى المقال الكامل من صفحة المقال نفسها"""
        if not article_url.startswith('http'):
            article_url = f"{self.news_sources[source_name]['url']}{article_url}"
            
        logger.debug(f"جاري استخراج محتوى المقال من: {article_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            }
            
            response = requests.get(article_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"فشل في الوصول إلى صفحة المقال. كود الاستجابة: {response.status_code}")
                return ""
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # محاولة العثور على محتوى المقال باستخدام عدة محددات شائعة
            content_selectors = [
                'div.articlecontent', 
                'div.article-content',
                'div.article-body',
                'div.entry-content',
                'div.content-area',
                'article'
            ]
            
            article_content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # استخراج جميع الفقرات
                    paragraphs = content_element.find_all('p')
                    if paragraphs:
                        article_content = ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
                        logger.debug(f"تم العثور على محتوى المقال ({len(article_content)} حرف) باستخدام المحدد: {selector}")
                        break
            
            if not article_content:
                logger.warning(f"لم يتم العثور على محتوى المقال باستخدام المحددات المعروفة في: {article_url}")
                # خطة احتياطية: البحث عن أي فقرات داخل العناصر الرئيسية
                main_elements = soup.select('main, article, div.content, div.main-content')
                for element in main_elements:
                    paragraphs = element.find_all('p')
                    if paragraphs and len(paragraphs) > 2:  # على الأقل 3 فقرات لتجنب التقاط العناصر غير المتعلقة
                        article_content = ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
                        logger.debug(f"تم العثور على محتوى محتمل للمقال ({len(article_content)} حرف) من خلال البحث عن الفقرات")
                        break
            
            return article_content
                
        except Exception as e:
            logger.error(f"خطأ في استخراج محتوى المقال: {str(e)}")
            return ""

    def get_articles(self, source_name):
        """جلب المقالات من مصدر محدد مع استخدام محددات أكثر مرونة"""
        source_config = self.news_sources[source_name]
        articles = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
            }
            
            logger.debug(f"محاولة الاتصال بـ {source_config['url']}")
            response = requests.get(source_config['url'], headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"فشل الاتصال بـ {source_name}. كود الحالة: {response.status_code}")
                return []
                
            logger.debug(f"تم الاتصال بنجاح بـ {source_name}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # محاولة العثور على المقالات باستخدام عدة محددات
            article_elements = soup.select(source_config['article_selector'])
            logger.debug(f"تم العثور على {len(article_elements)} عنصر باستخدام محدد المقالات الرئيسي")
            
            # إذا لم يتم العثور على أي مقالات، جرب محددات أخرى
            if not article_elements:
                alternative_selectors = [
                    'div.col-xs-12', 
                    'div.news-item',
                    'div.item',
                    'article',
                    '.news-card',
                    'div.newsbox'
                ]
                
                for selector in alternative_selectors:
                    article_elements = soup.select(selector)
                    if article_elements:
                        logger.debug(f"تم العثور على {len(article_elements)} عنصر باستخدام محدد بديل: {selector}")
                        break
            
            # حفظ صفحة HTML للتصحيح
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            logger.debug("تم حفظ صفحة HTML للتصحيح في debug_page.html")
            
            # الحد من عدد المقالات للاختبار
            article_limit = 5
            processed_count = 0
            
            for element in article_elements:
                if processed_count >= article_limit:
                    break

                try:
                    # البحث عن الروابط أولاً (أكثر موثوقية)
                    link_element = element.select_one(source_config['link_selector'])
                    
                    # تخطي العناصر التي لا تحتوي على روابط صالحة
                    if not link_element or not link_element.get('href'):
                        continue
                    
                    article_url = link_element['href']
                    
                    # التأكد من أن الرابط هو رابط مقال فعلي
                    if not (re.search(r'/story/', article_url) or re.search(r'/news/', article_url)):
                        continue
                    
                    # البحث عن العنوان
                    title_element = None
                    
                    # 1. البحث عن العنوان داخل الرابط
                    if link_element.text.strip():
                        title_element = link_element
                    
                    # 2. البحث عن العنوان في العنصر الأبوي باستخدام المحدد
                    if not title_element or not title_element.text.strip():
                        title_element = element.select_one(source_config['title_selector'])
                    
                    # 3. البحث عن أي عنصر h2 أو h3 داخل العنصر
                    if not title_element or not title_element.text.strip():
                        title_element = element.select_one('h2, h3, h4')
                    
                    # تخطي المقال إذا لم نتمكن من العثور على عنوان
                    if not title_element or not title_element.text.strip():
                        continue
                    
                    article_title = title_element.text.strip()
                    
                    # البحث عن الملخص
                    summary = ""
                    summary_element = None
                    
                    if 'summary_selector' in source_config:
                        summary_element = element.select_one(source_config['summary_selector'])
                    
                    if summary_element and summary_element.text.strip():
                        summary = summary_element.text.strip()
                    
                    # قبل استخراج المحتوى الكامل، تأكد من أن لدينا عنوان ورابط صالحين
                    if article_title and article_url:
                        logger.debug(f"جاري استخراج محتوى المقال الكامل لـ: {article_title[:30]}...")
                        
                        # استخراج المحتوى الكامل
                        full_content = self.get_full_article_content(article_url, source_name)
                        
                        article_data = {
                            'source': source_name,
                            'title': article_title,
                            'url': article_url if article_url.startswith('http') else f"{source_config['url']}{article_url}",
                            'summary': summary,
                            'content': full_content,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        articles.append(article_data)
                        logger.debug(f"تمت إضافة مقال: {article_data['title'][:30]}... (محتوى: {len(full_content)} حرف)")
                        processed_count += 1
                
                except Exception as e:
                    logger.error(f"خطأ في معالجة مقال من {source_name}: {str(e)}")
                    continue
            
            logger.info(f"تم جلب {len(articles)} مقال من {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"خطأ في الاتصال بـ {source_name}: {str(e)}")
            return []

    def save_articles(self, articles, filename='news_data.json'):
        """حفظ المقالات في ملف JSON مع التحقق من وجود المجلد"""
        try:
            # التأكد من أن الملف موجود
            if not os.path.exists(filename):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                logger.debug(f"تم إنشاء ملف جديد: {filename}")
            
            # قراءة البيانات الموجودة
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.debug(f"تم قراءة {len(existing_data)} مقال من الملف الموجود")
            except json.JSONDecodeError:
                logger.warning("الملف الموجود غير صالح. سيتم إنشاء بيانات جديدة.")
                existing_data = []
            
            # إضافة المقالات الجديدة
            existing_data.extend(articles)
            
            # حفظ البيانات
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"تم حفظ {len(articles)} مقال جديد. إجمالي المقالات: {len(existing_data)}")
            
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {str(e)}")
            logger.error(f"مسار الملف: {os.path.abspath(filename)}")

    def run(self):
        """تشغيل التحليل مرة واحدة للاختبار"""
        logger.info("بدء تحليل الأخبار...")
        all_articles = []
        
        for source_name in self.news_sources:
            logger.info(f"جاري تحليل الأخبار من {source_name}")
            articles = self.get_articles(source_name)
            all_articles.extend(articles)
            
            # طباعة معلومات عن المقالات التي تم جمعها
            if articles:
                logger.info(f"تم جمع {len(articles)} مقال من {source_name}:")
                for idx, article in enumerate(articles[:3]):  # عرض أول 3 مقالات فقط
                    content_preview = article['content'][:100] + "..." if article['content'] else "لا يوجد محتوى"
                    logger.info(f"{idx+1}. {article['title'][:50]}... | المحتوى: {content_preview}")
            else:
                logger.warning(f"لم يتم جمع أي مقالات من {source_name}!")
            
            time.sleep(3)  # انتظار قصير بين المصادر
        
        if all_articles:
            self.save_articles(all_articles)
            logger.info(f"تم الانتهاء من التحليل. تم جمع {len(all_articles)} مقال في المجموع.")
        else:
            logger.warning("لم يتم جمع أي مقالات!")

if __name__ == "__main__":
    analyzer = NewsAnalyzer()
    analyzer.run()