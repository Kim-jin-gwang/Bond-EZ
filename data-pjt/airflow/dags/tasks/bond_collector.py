import time
import json
import math
import requests
import psycopg2
from datetime import datetime, timedelta
from kafka import KafkaProducer
from tasks.helpers import (
    API_KEY, KAFKA_BOOTSTRAP_SERVERS, POSTGRES_DB, 
    POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, DB_PORT
)

def fetch_and_produce_bond_data():
    # 1. DB에서 기존 적재된 isin_code 목록 조회
    existing_codes = set()
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        cur.execute('SELECT isin_code FROM bond;')
        existing_codes = {row[0] for row in cur.fetchall() if row[0]}
        cur.close()
        conn.close()
        print(f"Loaded {len(existing_codes)} existing bond codes from DB.")
    except Exception as e:
        print(f"Could not load existing bond codes (DB might be empty or table not created yet): {e}")

    # 2. 공공데이터포털 API에서 최신 데이터가 존재하는 기준일자(basDt) 탐색
    base_url = "http://apis.data.go.kr/1160100/GetBondIssuInfoService_V2/getBondBasiInfo_V2"
    today = datetime.now()
    target_date = None
    total_count = 0
    
    # 최근 10일간을 탐색하여 데이터가 존재하는 가장 최신 날짜를 찾습니다.
    for i in range(10):
        check_date = (today - timedelta(days=i)).strftime("%Y%m%d")
        test_url = f"{base_url}?serviceKey={API_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt={check_date}"
        try:
            resp = requests.get(test_url, timeout=15)
            if resp.status_code == 200:
                resp_json = resp.json()
                body = resp_json.get("response", {}).get("body", {})
                count = body.get("totalCount", 0)
                if count > 0:
                    target_date = check_date
                    total_count = count
                    break
        except Exception as e:
            print(f"Error checking date {check_date}: {e}")
            
    if not target_date:
        print("Error: Could not find any valid target date with bond data from API.")
        return
        
    print(f"Target Date selected: {target_date} (Total API records: {total_count})")
    
    # 3. Kafka Producer 설정
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        acks='all'
    )
    topic = 'topic_bond_raw'
    page_size = 100
    total_pages = math.ceil(total_count / page_size)
    
    is_initial_load = len(existing_codes) == 0
    mode_str = "Initial Load (Full)" if is_initial_load else "Daily Incremental"
    print(f"Starting ingestion in {mode_str} mode...")
    
    sent_count = 0
    for page in range(1, total_pages + 1):
        url = f"{base_url}?serviceKey={API_KEY}&numOfRows={page_size}&pageNo={page}&resultType=json&basDt={target_date}"
        try:
            print(f"Fetching page {page}/{total_pages}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            
            if not items: 
                break
                
            page_sent = 0
            for item in items:
                isin_cd = item.get('isinCd')
                if not isin_cd:
                    continue
                # 초기 수집 모드이거나, DB에 존재하지 않는 신규 채권인 경우에만 Kafka로 전송
                if is_initial_load or (isin_cd not in existing_codes):
                    producer.send(topic, item)
                    page_sent += 1
                    sent_count += 1
                    
            producer.flush()
            if page_sent > 0:
                print(f"Sent {page_sent} new items from page {page} to Kafka.")
            time.sleep(0.5)  # API Rate limit 고려
        except Exception as e:
            print(f"Error at page {page}: {e}")
            raise e
            
    producer.close()
    print(f"Bond ingestion completed. Total sent to Kafka: {sent_count} bonds.")
    return target_date
