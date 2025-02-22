import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import logging
import os
import re

# إعدادات تسجيل الأخطاء
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self):
        """ تهيئة المصادر والمحددات الخاصة بها لاستخراج الأخبار """
        self.news_sources = {
            'Youm7': {
                'name': 'Youm7',
                'url': 'https://www.youm7.com',
                'article_selector': '.news-box, .col-xs-12.bigOneSec, .secList',
                'title_selector': 'h3 a, h2 a, .newsTitle a',
                'link_selector': 'h3 a, h2 a, .newsTitle a',
                'summary_selector': '.newsStory, .bigNewsStory',
                'content_selector': '.articleBody, .article-text, #articleBody, .article-content',
                'base_url': 'https://www.youm7.com'
            }
        }

        self.json_filename = "news_data.json"
        self.article_limit = 15  # الحد الأقصى للمقالات المستخرجة

    def get_full_article_content(self, article_url, source_name):
        """ استخراج محتوى المقال كاملاً من صفحته """
        if not article_url.startswith('http'):
            article_url = f"{self.news_sources[source_name]['base_url']}{article_url}"

        logger.debug(f"Fetching article content from: {article_url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
            }

            time.sleep(1.5)  # تأخير بسيط لتجنب الحظر
            response = requests.get(article_url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to access article page. Status code: {response.status_code}")
                return ""

            soup = BeautifulSoup(response.content, 'html.parser')
            source_config = self.news_sources[source_name]

            content_element = soup.select_one(source_config['content_selector'])
            if content_element:
                paragraphs = content_element.find_all('p')
                return ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
            
            return ""

        except Exception as e:
            logger.error(f"Error extracting article content: {str(e)}")
            return ""

    def get_articles(self, source_name):
        """ استخراج عناوين الأخبار وروابطها ومحتواها من الصفحة الرئيسية للموقع """
        source_config = self.news_sources[source_name]
        articles = []

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            logger.debug(f"Connecting to {source_config['url']}")
            response = requests.get(source_config['url'], headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to connect to {source_name}. Status code: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = soup.select(source_config['article_selector'])
            logger.debug(f"Found {len(article_elements)} articles using main selector")

            processed_count = 0

            for element in article_elements:
                if processed_count >= self.article_limit:
                    break

                try:
                    # استخراج الرابط
                    link_element = element.select_one(source_config['link_selector'])
                    if not link_element or not link_element.get('href'):
                        continue
                    article_url = link_element['href']

                    if source_name == 'Youm7' and not re.search(r'/story/', article_url) and not re.search(r'/news/', article_url):
                        continue

                    # استخراج العنوان
                    title_element = link_element if link_element.text.strip() else element.select_one(source_config['title_selector'])
                    if not title_element or not title_element.text.strip():
                        continue
                    article_title = title_element.text.strip()

                    # استخراج الملخص
                    summary_element = element.select_one(source_config['summary_selector'])
                    summary = summary_element.text.strip() if summary_element else ""

                    # تعديل الرابط ليصبح كاملاً
                    if not article_url.startswith('http'):
                        article_url = f"{source_config['base_url']}{article_url}"

                    # استخراج المحتوى الكامل
                    full_content = self.get_full_article_content(article_url, source_name)

                    if full_content:
                        article_data = {
                            'source': source_name,
                            'title': article_title,
                            'url': article_url,
                            'summary': summary,
                            'content': full_content,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                        articles.append(article_data)
                        processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing article from {source_name}: {str(e)}")
                    continue

            logger.info(f"Collected {len(articles)} articles from {source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching articles from {source_name}: {str(e)}")
            return []

    def save_articles(self, articles):
        """ حفظ البيانات إلى ملف JSON """
        try:
            existing_data = []
            if os.path.exists(self.json_filename):
                with open(self.json_filename, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("JSON file was empty or corrupt. Starting fresh.")

            existing_data.extend(articles)

            with open(self.json_filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)

            logger.info(f"Saved {len(articles)} articles to {self.json_filename}")

        except Exception as e:
            logger.error(f"Error saving articles: {str(e)}")

    def run(self):
        """ تشغيل البرنامج لجلب الأخبار وحفظها """
        all_articles = []
        for source in self.news_sources.keys():
            articles = self.get_articles(source)
            if articles:
                all_articles.extend(articles)

        if all_articles:
            self.save_articles(all_articles)


# تنفيذ البرنامج
if __name__ == "__main__":
    analyzer = NewsAnalyzer()
    analyzer.run()
