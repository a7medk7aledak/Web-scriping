import requests # to send GET requests
from bs4 import BeautifulSoup # to parse HTML
import json 
import time
import random
from fake_useragent import UserAgent
ua = UserAgent()

def get_headers():
    """توليد هيدر عشوائي لكل طلب"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

def get_amazon_laptops(pages=3, retry_limit=3, use_proxies=False):
    """
    استخراج بيانات اللابتوبات من أمازون.
    :param pages: عدد الصفحات اللي عايزين نجلب منها البيانات
    :param retry_limit: عدد المحاولات لو تم الحظر
    :param use_proxies: استخدام بروكسي إذا كان مفعل
    :return: قائمة بالبيانات المستخرجة
    """

    all_laptops = []
    for page in range(1, pages + 1):
        retry_count = 0
        success = False
        url = f"https://www.amazon.com/s?k=laptop&page={page}"
        while retry_count < retry_limit and not success:
            try:
                current_headers = get_headers()
                
                # Use proxy if required
                proxies = None
                if use_proxies:
                    proxies = {"http": "http://your-proxy", "https": "https://your-proxy"}

                session = requests.Session()
                session.headers.update(current_headers)
                
                # Visit Amazon homepage first to set cookies
                session.get("https://www.amazon.com/", proxies=proxies, timeout=15)
                time.sleep(random.uniform(5, 10))  # Random delay to avoid blocking
                # Request the product page
                response = session.get(url, proxies=proxies, timeout=20)
                if response.status_code == 200:
                    print(f"✅ Successfully accessed page {page}")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check for CAPTCHA
                    if "Enter the characters you see below" in response.text:
                        print("⚠ CAPTCHA detected! Retrying...")
                        retry_count += 1
                        time.sleep(random.uniform(30, 60))
                        continue
                    # Extract products
                    laptop_items = soup.select('div[data-component-type="s-search-result"]')
                    
                    for item in laptop_items:
                        laptop = {}
                        
                        # Extract title
                        title_element = item.select_one('h2 span')
                        laptop['title'] = title_element.text.strip() if title_element else "Not Available"
                        
                        # Extract price
                        price_element = item.select_one('.a-price-whole')
                        laptop['price'] = price_element.text.strip() if price_element else "Not Available"
                        
                        # Extract product link
                        link_element = item.select_one('h2')
                        laptop['link'] = "https://www.amazon.com" + link_element['href'] if link_element else "Not Available"
                        
                        # Extract image URL
                        image_element = item.select_one('.s-image')
                        laptop['image'] = image_element['src'] if image_element else "Not Available"
                        
                        all_laptops.append(laptop)
                    
                    print(f"📌 Extracted {len(laptop_items)} products from page {page}")
                    success = True
                elif response.status_code in [403, 503]:
                    print(f"⚠ Blocked! Status Code: {response.status_code}. Retrying...")
                    retry_count += 1
                    time.sleep(random.uniform(60, 180))
                else:
                    print(f"❌ Failed to access page {page}. Status Code: {response.status_code}")
                    retry_count += 1
            
            except Exception as e:
                print(f"⚠ Error while fetching page {page}: {str(e)}")
                retry_count += 1
                time.sleep(random.uniform(10, 30))
        
        time.sleep(random.uniform(20, 45))  # Wait between pages
    
    return all_laptops

def save_to_json(laptops, filename='amazon_laptops.json'):
    """Save extracted data to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(laptops, file, ensure_ascii=False, indent=4)
    print(f"✅ Data saved to {filename}")

def main():
    """
    Main function to run the scraper
    """
    print("📌 Starting Amazon laptop data extraction...")
    laptops = get_amazon_laptops(pages=2, retry_limit=3, use_proxies=False)
    
    if laptops:
        save_to_json(laptops)
    else:
        print("❌ No data extracted!")

if __name__ == "__main__":
    main()