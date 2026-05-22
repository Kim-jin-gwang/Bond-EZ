import os
import json
import requests
import time
import psycopg2
import pendulum
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from kafka import KafkaProducer
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf, regexp_replace, to_date
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, LongType

# 한국 타임존 설정
local_tz = pendulum.timezone("Asia/Seoul")

# 환경 변수 설정
API_KEY = os.getenv("DATA_PORTAL_API_KEY")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- 1. API 수집 함수 ---
# ... (생략된 함수들은 동일함)
def fetch_and_produce_bond_data():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        acks='all'
    )
    topic = 'topic_bond_raw'
    base_url = "http://apis.data.go.kr/1160100/service/GetBondIssuInfoService/getBondIssuInfo"
    
    total_count = 1000
    page_size = 100
    total_pages = total_count // page_size
    
    for page in range(1, total_pages + 1):
        url = f"{base_url}?serviceKey={API_KEY}&numOfRows={page_size}&pageNo={page}&resultType=json"
        try:
            print(f"Fetching page {page}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            
            if not items: break
            for item in items:
                producer.send(topic, item)
            producer.flush()
            print(f"Sent {len(items)} items from page {page} to Kafka.")
            time.sleep(1)
        except Exception as e:
            print(f"Error at page {page}: {e}")
    producer.close()

# --- 2. Spark 가공 함수 ---
def run_spark_bond_batch():
    spark = SparkSession.builder \
        .appName("Airflow-BondBatch") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4,org.postgresql:postgresql:42.7.2") \
        .getOrCreate()

    kafka_schema = StructType([
        StructField("isinCd", StringType()), StructField("isinCdNm", StringType()),
        StructField("crno", StringType()), StructField("bondIsurNm", StringType()),
        StructField("sicNm", StringType()), StructField("bondIssuDt", StringType()),
        StructField("bondExprDt", StringType()), StructField("bondSrfcInrt", StringType()),
        StructField("bondIssuAmt", StringType()), StructField("scrsItmsKcdNm", StringType()),
        StructField("bondRnknDcdNm", StringType()), StructField("optnTcdNm", StringType()),
        StructField("bondIntTcdNm", StringType()), StructField("intPayCyclCtt", StringType()),
        StructField("grnDcdNm", StringType()), StructField("bondUndtInstNm", StringType()),
        StructField("kisScrsItmsKcdNm", StringType()), StructField("kbpScrsItmsKcdNm", StringType()),
        StructField("niceScrsItmsKcdNm", StringType()), StructField("fnScrsItmsKcdNm", StringType())
    ])

    rating_order = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D"]

    @udf(returnType=StringType())
    def get_lowest_rating(kis, kbp, nice, fn):
        ratings = [r for r in [kis, kbp, nice, fn] if r and r.strip()]
        if not ratings: return None
        def rating_index(r):
            try: return rating_order.index(r.upper())
            except: return len(rating_order)
        return max(ratings, key=rating_index)

    raw_df = spark.read.format("kafka").option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS).option("subscribe", "topic_bond_raw").option("startingOffsets", "earliest").load()
    parsed_df = raw_df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"), kafka_schema).alias("data")).select("data.*")

    final_df = parsed_df \
        .withColumn("isin_code", col("isinCd")) \
        .withColumn("bond_name", col("isinCdNm")) \
        .withColumn("company_id", col("crno")) \
        .withColumn("company_name", col("bondIsurNm")) \
        .withColumn("industry", col("sicNm")) \
        .withColumn("issue_date", to_date(col("bondIssuDt"), "yyyyMMdd")) \
        .withColumn("maturity_date", to_date(col("bondExprDt"), "yyyyMMdd")) \
        .withColumn("coupon_rate", col("bondSrfcInrt").cast(DecimalType(10, 4))) \
        .withColumn("issue_amount", regexp_replace(col("bondIssuAmt"), "[^0-9]", "").cast(LongType())) \
        .withColumn("bond_type", col("scrsItmsKcdNm")) \
        .withColumn("seniority", col("bondRnknDcdNm")) \
        .withColumn("call_put_option", col("optnTcdNm")) \
        .withColumn("interest_type", col("bondIntTcdNm")) \
        .withColumn("payment_cycle", col("intPayCyclCtt")) \
        .withColumn("guarantee_status", col("grnDcdNm")) \
        .withColumn("underwriter", col("bondUndtInstNm")) \
        .withColumn("credit_rating", get_lowest_rating(col("kisScrsItmsKcdNm"), col("kbpScrsItmsKcdNm"), col("niceScrsItmsKcdNm"), col("fnScrsItmsKcdNm"))) \
        .select("isin_code", "bond_name", "company_id", "company_name", "industry", "issue_date", "maturity_date", "coupon_rate", "issue_amount", "bond_type", "seniority", "call_put_option", "interest_type", "payment_cycle", "guarantee_status", "underwriter", "credit_rating")

    JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
    JDBC_PROPERTIES = {"user": POSTGRES_USER, "password": POSTGRES_PASSWORD, "driver": "org.postgresql.Driver"}

    final_df.write.jdbc(url=JDBC_URL, table="temp_bonds_master_staging", mode="overwrite", properties=JDBC_PROPERTIES)

    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS bonds_master (isin_code VARCHAR(50) PRIMARY KEY, bond_name VARCHAR(255), company_id VARCHAR(50), company_name VARCHAR(255), industry VARCHAR(255), issue_date DATE, maturity_date DATE, coupon_rate DECIMAL(10, 4), issue_amount BIGINT, bond_type VARCHAR(100), seniority VARCHAR(100), call_put_option VARCHAR(100), interest_type VARCHAR(100), payment_cycle VARCHAR(100), guarantee_status VARCHAR(100), underwriter VARCHAR(255), credit_rating VARCHAR(50));")
    cur.execute("INSERT INTO bonds_master SELECT * FROM temp_bonds_master_staging ON CONFLICT (isin_code) DO UPDATE SET bond_name = EXCLUDED.bond_name, company_id = EXCLUDED.company_id, company_name = EXCLUDED.company_name, industry = EXCLUDED.industry, issue_date = EXCLUDED.issue_date, maturity_date = EXCLUDED.maturity_date, coupon_rate = EXCLUDED.coupon_rate, issue_amount = EXCLUDED.issue_amount, bond_type = EXCLUDED.bond_type, seniority = EXCLUDED.seniority, call_put_option = EXCLUDED.call_put_option, interest_type = EXCLUDED.interest_type, payment_cycle = EXCLUDED.payment_cycle, guarantee_status = EXCLUDED.guarantee_status, underwriter = EXCLUDED.underwriter, credit_rating = EXCLUDED.credit_rating;")
    cur.execute("DROP TABLE temp_bonds_master_staging")
    conn.commit()
    cur.close()
    conn.close()
    spark.stop()

# --- 3. 검증 함수 ---
def verify_data_count():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM bonds_master;")
    count = cur.fetchone()[0]
    print(f"Total records in bonds_master: {count}")
    if count >= 1000:
        print("Verification SUCCESS: 1,000 or more records loaded.")
    else:
        print(f"Verification WARNING: Only {count} records found.")
    cur.close()
    conn.close()

# --- DAG 설정 ---
default_args = {
    'owner': 'ssafy',
    'start_date': datetime(2026, 5, 22, tzinfo=local_tz),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'bond_full_pipeline_dag',
    default_args=default_args,
    schedule_interval='0 0 * * *',
    catchup=False,
    tags=['bond', 'pipeline'],
) as dag:

    collect_task = PythonOperator(
        task_id='collect_api_to_kafka',
        python_callable=fetch_and_produce_bond_data,
    )

    spark_task = PythonOperator(
        task_id='spark_process_kafka_to_db',
        python_callable=run_spark_bond_batch,
    )

    verify_task = PythonOperator(
        task_id='verify_db_load',
        python_callable=verify_data_count,
    )

    collect_task >> spark_task >> verify_task
