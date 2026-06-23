import os
import time
import json
import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer
from datetime import datetime

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC_NAME = "topic_news_raw"

def get_kafka_producer(retries=20, delay=5):
    """Wait for Kafka to be ready and return a producer instance."""
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Successfully connected to Kafka.")
            return producer
        except Exception as e:
            print(f"Waiting for Kafka... ({i+1}/{retries}) - {e}")
            time.sleep(delay)
    raise Exception("Failed to connect to Kafka after multiple retries.")

producer = get_kafka_producer()

def scrape_naver_finance():
    """Naver Finance Main News Scraper"""
    url = "https://finance.naver.com/news/mainnews.naver"
    articles = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Naver Finance news items are usually in 'ul.newsList'
        news_list = soup.select('.newsList > li')
        for item in news_list:
            title_tag = item.select_one('dl > dd.articleSubject > a')
            if not title_tag:
                title_tag = item.select_one('dl > dt.articleSubject > a')
                
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = "https://finance.naver.com" + title_tag['href']
                source = item.select_one('.press').get_text(strip=True) if item.select_one('.press') else "Naver Finance"
                date_str = item.select_one('.wdate').get_text(strip=True) if item.select_one('.wdate') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                articles.append({
                    'title': title,
                    'source': source,
                    'url': link,
                    'write_date': date_str
                })
    except Exception as e:
        print(f"Error scraping Naver Finance: {e}")
    return articles

def scrape_einfomax():
    """Yonhap Infomax News Scraper"""
    url = "https://news.einfomax.co.kr/news/articleList.html"
    articles = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Yonhap Infomax article list items
        list_items = soup.select('#user-container > div.float-center.custom-m > div.col-x8.float-left > section > article > div.user-section.ui-block > div.list-block')
        for item in list_items:
            title_tag = item.select_one('.list-titles > a')
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = "https://news.einfomax.co.kr" + title_tag['href']
                source = "연합인포맥스"
                date_str = item.select_one('.list-dated').get_text(strip=True).split('|')[-1].strip() if item.select_one('.list-dated') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                articles.append({
                    'title': title,
                    'source': source,
                    'url': link,
                    'write_date': date_str
                })
    except Exception as e:
        print(f"Error scraping Yonhap Infomax: {e}")
    return articles

def main():
    print(f"Starting News Crawler. Sending to Kafka topic: {TOPIC_NAME}")
    sent_urls = set()
    while True:
        naver_news = scrape_naver_finance()
        infomax_news = scrape_einfomax()
        
        all_news = naver_news + infomax_news
        new_articles = []
        
        for news in all_news:
            url = news.get('url')
            if url and url not in sent_urls:
                new_articles.append(news)
                sent_urls.add(url)
                
        # Bounded cache size to prevent memory leaks
        if len(sent_urls) > 1000:
            # Keep only the last 500 URLs
            sent_urls = set(list(sent_urls)[-500:])
            
        for news in new_articles:
            producer.send(TOPIC_NAME, news)
            print(f"Sent: {news['title']} ({news['source']})")
            
        if new_articles:
            producer.flush()
            print(f"Successfully sent {len(new_articles)} new articles. Sleeping for 60 seconds...")
        else:
            print("No new articles found. Sleeping for 60 seconds...")
            
        time.sleep(60)

if __name__ == "__main__":
    main()
