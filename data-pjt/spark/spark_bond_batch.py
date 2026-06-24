'''
Spark 로직을 단독으로 실행하기 위해 만든 스크립트
Airflow에 올리기 전 로컬로 테스트할 때 사용합니다.



'''



import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, when, udf, regexp_replace, to_date, least, greatest
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, LongType, DateType
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 설정
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

# PostgreSQL 접속 정보
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
JDBC_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# 1. Spark 세션 생성 (Kafka 및 PostgreSQL 패키지 포함)
spark = SparkSession.builder \
    .appName("BondDataKafkaToPostgres") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4,org.postgresql:postgresql:42.7.2") \
    .getOrCreate()

# 2. Kafka 데이터 스키마 정의 (Source)
kafka_schema = StructType([
    StructField("isinCd", StringType()),
    StructField("isinCdNm", StringType()),
    StructField("crno", StringType()),
    StructField("bondIsurNm", StringType()),
    StructField("sicNm", StringType()),
    StructField("bondIssuDt", StringType()),
    StructField("bondExprDt", StringType()),
    StructField("bondSrfcInrt", StringType()),
    StructField("bondIssuAmt", StringType()),
    StructField("scrsItmsKcdNm", StringType()),
    StructField("bondRnknDcdNm", StringType()),
    StructField("optnTcdNm", StringType()),
    StructField("bondIntTcdNm", StringType()),
    StructField("intPayCyclCtt", StringType()),
    StructField("grnDcdNm", StringType()),
    StructField("bondUndtInstNm", StringType()),
    StructField("kisScrsItmsKcdNm", StringType()),
    StructField("kbpScrsItmsKcdNm", StringType()),
    StructField("niceScrsItmsKcdNm", StringType()),
    StructField("fnScrsItmsKcdNm", StringType())
])

# 3. Kafka에서 데이터 읽기 (Batch)
raw_df = spark.read \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "topic_bond_raw") \
    .option("startingOffsets", "earliest") \
    .load()

# JSON 파싱
parsed_df = raw_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), kafka_schema).alias("data")) \
    .select("data.*")

# 4. 신용등급 최저 등급 산출 로직 (AAA -> D 순)
# 등급 순서 정의 (낮을수록 인덱스가 높음)
rating_order = [
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", 
    "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", 
    "B+", "B", "B-", "CCC", "CC", "C", "D"
]

@udf(returnType=StringType())
def get_lowest_rating(kis, kbp, nice, fn):
    ratings = [r for r in [kis, kbp, nice, fn] if r and r.strip()]
    if not ratings:
        return None
    
    # 등급별 인덱스 추출 (정의되지 않은 등급은 가장 낮은 등급보다 뒤로 처리)
    def rating_index(r):
        try:
            return rating_order.index(r.upper())
        except (ValueError, AttributeError):
            return len(rating_order)

    # 인덱스가 가장 높은 것(가장 낮은 등급) 선택
    lowest = max(ratings, key=rating_index)
    return lowest

# 5. 데이터 변환 및 가공
transformed_df = parsed_df \
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
    .withColumn("credit_rating", get_lowest_rating(col("kisScrsItmsKcdNm"), col("kbpScrsItmsKcdNm"), col("niceScrsItmsKcdNm"), col("fnScrsItmsKcdNm")))


# 필요한 컬럼만 선택
final_df = transformed_df.select(
    "isin_code", "bond_name", "company_id", "company_name", "industry",
    "issue_date", "maturity_date", "coupon_rate", "issue_amount",
    "bond_type", "seniority", "call_put_option", "interest_type",
    "payment_cycle", "guarantee_status", "underwriter", "credit_rating"
)

# 6. PostgreSQL에 Upsert 방식으로 저장
# Spark JDBC는 기본 Upsert를 지원하지 않으므로, 임시 테이블을 통한 병합 방식 사용
STAGING_TABLE = "temp_bonds_master_staging"
TARGET_TABLE = "bonds_master"

print(f"Saving data to {TARGET_TABLE} via {STAGING_TABLE}...")

# 스테이징 테이블에 쓰기 (Overwrite)
final_df.write \
    .jdbc(url=JDBC_URL, table=STAGING_TABLE, mode="overwrite", properties=JDBC_PROPERTIES)

# PostgreSQL Upsert SQL 실행
upsert_sql = f"""
    INSERT INTO {TARGET_TABLE} (
        isin_code, bond_name, company_id, company_name, industry,
        issue_date, maturity_date, coupon_rate, issue_amount,
        bond_type, seniority, call_put_option, interest_type,
        payment_cycle, guarantee_status, underwriter, credit_rating
    )
    SELECT * FROM {STAGING_TABLE}
    ON CONFLICT (isin_code) DO UPDATE SET
        bond_name = EXCLUDED.bond_name,
        company_id = EXCLUDED.company_id,
        company_name = EXCLUDED.company_name,
        industry = EXCLUDED.industry,
        issue_date = EXCLUDED.issue_date,
        maturity_date = EXCLUDED.maturity_date,
        coupon_rate = EXCLUDED.coupon_rate,
        issue_amount = EXCLUDED.issue_amount,
        bond_type = EXCLUDED.bond_type,
        seniority = EXCLUDED.seniority,
        call_put_option = EXCLUDED.call_put_option,
        interest_type = EXCLUDED.interest_type,
        payment_cycle = EXCLUDED.payment_cycle,
        guarantee_status = EXCLUDED.guarantee_status,
        underwriter = EXCLUDED.underwriter,
        credit_rating = EXCLUDED.credit_rating;
"""

# JDBC를 사용하여 SQL 실행
import psycopg2

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()
    
    # 1. 테이블이 없을 경우 생성 (스키마 정의)
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
        isin_code VARCHAR(50) PRIMARY KEY,
        bond_name VARCHAR(255),
        company_id VARCHAR(50),
        company_name VARCHAR(255),
        industry VARCHAR(255),
        issue_date DATE,
        maturity_date DATE,
        coupon_rate DECIMAL(10, 4),
        issue_amount BIGINT,
        bond_type VARCHAR(100),
        seniority VARCHAR(100),
        call_put_option VARCHAR(100),
        interest_type VARCHAR(100),
        payment_cycle VARCHAR(100),
        guarantee_status VARCHAR(100),
        underwriter VARCHAR(255),
        credit_rating VARCHAR(50)
    );
    """
    cur.execute(create_table_sql)
    
    # 2. Upsert 수행
    cur.execute(upsert_sql)
    
    # 3. 스테이징 테이블 삭제
    cur.execute(f"DROP TABLE {STAGING_TABLE}")
    
    conn.commit()
    print("Successfully upserted data to PostgreSQL.")
except Exception as e:
    print(f"Error during Upsert: {e}")
    if conn:
        conn.rollback()
finally:
    if cur: cur.close()
    if conn: conn.close()

spark.stop()

