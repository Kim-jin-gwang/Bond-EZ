import time
import requests
import feedparser
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime

RSS_FEED_URL = "https://www.khan.co.kr/rss/rssdata/total_news.xml"

# PostgreSQL 연결 
def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="news",
        user="ssafyuser",
        password="ssafy"
    )

# DB INSERT
def save_article_to_db(article):

    query = """
        INSERT INTO news_article 
            (title, writer, write_date, category, content, url)
        VALUES 
            (%(title)s, %(writer)s, %(write_date)s, %(category)s, %(content)s, %(url)s)
        ON CONFLICT (url) DO NOTHING;
    """

    try:
        conn = get_connection()  # 데이터베이스 연결
        cur = conn.cursor()  # 커서 객체 생성
        cur.execute(query, article)  # 쿼리 실행
        conn.commit()  # 변경사항 커밋
        cur.close()  # 커서 닫기
        conn.close()  # 연결 닫기

        print(f"[DB 저장 완료] {article['title']}")
    except Exception as e:
        print(f"[DB 저장 오류] {e}")

def main():
    seen_links = set()

    while True:
        print("\n[RSS 확인 중...]")
        feed = feedparser.parse(RSS_FEED_URL)

        for entry in feed.entries:  # 피드의 각 항목에 대해 반복
            url = entry.link  # 기사 URL

            if url in seen_links:  # 이미 처리한 URL이면 건너뜀
                continue
            seen_links.add(url)  # 새로운 URL을 집합에 추가

            title = entry.title  # 기사 제목
            writer = getattr(entry, "author", "Unknown")  # 기자 (없으면 "Unknown")
            category = entry.get("category", "Unknown")  # 카테고리 (없으면 "Unknown")
            description = getattr(entry, "description", "")  # 기사 내용 (없으면 빈 문자열)
            
            # 날짜 파싱
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                write_date = datetime(*entry.updated_parsed[:6])  # 'updated_parsed'가 있으면 해당 날짜 사용
            elif hasattr(entry, "published_parsed") and entry.published_parsed:
                write_date = datetime(*entry.published_parsed[:6])  # 'published_parsed'가 있으면 해당 날짜 사용
            else:
                write_date = datetime.now()  # 날짜가 없으면 현재 날짜 사용
            
            # 날짜 파싱
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                write_date = datetime(*entry.updated_parsed[:6])
            elif hasattr(entry, "published_parsed") and entry.published_parsed:
                write_date = datetime(*entry.published_parsed[:6])
            else:
                write_date = datetime.now()

            # 출력
            print(f"\n[새 기사] {title}")
            print(f"[링크] {url}")
            print(f"[기자] {writer}")
            print(f"[카테고리] {category}")
            print(f"[작성일] {write_date}")
            print(f"\n[내용]\n{description}\n")

            # DB 저장용 데이터
            article = {
                "title": title,
                "writer": writer,
                "write_date": write_date,
                "category": category,
                "content": description,
                "url": url
            }

            save_article_to_db(article)

        print(f"\n[총 수집 기사 수] {len(seen_links)}")
        print("[60초 대기 후 재확인]")
        time.sleep(60)


if __name__ == "__main__":
    main()
