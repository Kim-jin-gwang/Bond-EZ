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
    base_url = "http://apis.data.go.kr/1160100/GetBondIssuInfoService_V2/getBondBasiInfo_V2"
    
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
            raise e  # Fail the task if API call fails
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

    raw_df = spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "topic_bond_raw") \
        .option("startingOffsets", "earliest") \
        .option("allowNonExistentTopics", "true") \
        .load()
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
    CHECKPOINT_PATH = "/opt/airflow/dags/spark_checkpoints/bond_raw"

    def write_to_postgres_upsert(batch_df, batch_id):
        # 마이크로 배치 DataFrame에서 중복 제거
        deduped_df = batch_df.dropDuplicates(["isin_code"])
        
        # 임시 테이블에 쓰기 (Overwrite)
        deduped_df.write.jdbc(url=JDBC_URL, table="temp_bonds_master_staging", mode="overwrite", properties=JDBC_PROPERTIES)
        
        # PostgreSQL Upsert 실행
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
        cur = conn.cursor()
        try:
            cur.execute("SELECT normalize_bonds_staging();")
            cur.execute("DROP TABLE temp_bonds_master_staging;")
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    query = final_df.writeStream \
        .foreachBatch(write_to_postgres_upsert) \
        .trigger(availableNow=True) \
        .option("checkpointLocation", CHECKPOINT_PATH) \
        .start()

    query.awaitTermination()
    spark.stop()

# Helper functions for types and date addition
def safe_float(val):
    if val is None or str(val).strip() == '':
        return None
    try:
        return float(val)
    except ValueError:
        return None

def safe_int(val):
    if val is None or str(val).strip() == '':
        return None
    try:
        return int(val)
    except ValueError:
        return None

def add_months(sourcedate, months):
    import calendar
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day).date()

# --- 2-B. 이자지급 및 옵션 상세 수집 함수 ---
def ingest_option_cashflow_details():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    # 1. 상세 정보가 비어 있는 채권 조회 (최대 100건만 점진적으로 처리하여 API 호출 횟수 조절)
    cur.execute("""
        SELECT b.isin_code, b.issue_date, b.maturity_date, b.payment_cycle_months, b.option_type, b.interest_type, b.cashflow_rule_id, b.option_exercise_id
        FROM "Bond" b
        JOIN "BondCashflowRule" c ON b.cashflow_rule_id = c.cashflow_rule_id
        WHERE c.first_interest_payment_date IS NULL
        LIMIT 100;
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} bonds needing option/cashflow details enrichment.")
    
    def safe_parse_date(d_str):
        if d_str:
            d_str = str(d_str).strip()
            if len(d_str) == 8:
                try:
                    return datetime.strptime(d_str, "%Y%m%d").date()
                except ValueError:
                    return None
        return None
        
    for row in rows:
        isin_code, issue_date, maturity_date, payment_cycle, option_type, interest_type, cashflow_rule_id, option_exercise_id = row
        
        use_api_data = False
        
        # API 수집 변수 초기화
        api_interest_payment_method = None
        api_interest_payment_unit_months = None
        api_interest_calculation_months = None
        api_interest_pre_post_type = None
        api_first_interest_payment_date = None
        api_interest_payment_basis = None
        api_interest_month_end_type = None
        
        api_option_type = option_type
        api_exercise_start_date_1 = None
        api_exercise_end_date_1 = None
        api_exercise_start_date_2 = None
        api_exercise_end_date_2 = None
        api_exercise_reason = None
        
        # 1-1. KSD OpenAPI 호출 시도 (최선)
        ksd_intr_url = f"http://apis.data.go.kr/B552481/BondSvc/getBondIntrPayInfo?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
        ksd_opt_url = f"http://apis.data.go.kr/B552481/BondSvc/getBondOptionInfo?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
        
        try:
            intr_resp = requests.get(ksd_intr_url, timeout=10)
            opt_resp = requests.get(ksd_opt_url, timeout=10)
            
            if intr_resp.status_code == 200 and opt_resp.status_code == 200:
                intr_data = intr_resp.json()
                opt_data = opt_resp.json()
                
                intr_items = intr_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                opt_items = opt_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                
                # 리스트 형태 보정
                if not isinstance(intr_items, list):
                    intr_items = [intr_items] if intr_items else []
                if not isinstance(opt_items, list):
                    opt_items = [opt_items] if opt_items else []
                
                if intr_items or opt_items:
                    use_api_data = True
                    print(f"KSD API data found for {isin_code}.")
                    
                    if intr_items:
                        item = intr_items[0]
                        api_interest_payment_method = item.get('intrPayMthdNm')
                        api_interest_payment_unit_months = item.get('intrPayCyclCtt')
                        api_interest_calculation_months = item.get('intrCmpuMthdNm')
                        api_interest_pre_post_type = item.get('intrPayDivNm')
                        api_first_interest_payment_date = safe_parse_date(item.get('firstIntrPayDt'))
                        api_interest_payment_basis = item.get('bnkHldyIntPayDtDivNm')
                        api_interest_month_end_type = item.get('monthEndDivNm')
                        
                    if opt_items:
                        item = opt_items[0]
                        opt_kind = item.get('optnKindNm')
                        if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                            api_option_type = opt_kind
                        api_exercise_start_date_1 = safe_parse_date(item.get('optnExertStrtDt1'))
                        api_exercise_end_date_1 = safe_parse_date(item.get('optnExertEndDt1'))
                        api_exercise_start_date_2 = safe_parse_date(item.get('optnExertStrtDt2'))
                        api_exercise_end_date_2 = safe_parse_date(item.get('optnExertEndDt2'))
                        api_exercise_reason = item.get('optnExertRsnCtt')
        except Exception as e:
            print(f"KSD API calling failed for {isin_code}: {e}.")
            
        # 1-2. KSD API 호출 실패/공백 시 FSC 채권기본정보 OpenAPI 호출 시도 (차선)
        if not use_api_data:
            fsc_basi_url = f"http://apis.data.go.kr/1160100/GetBondIssuInfoService_V2/getBondBasiInfo_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
            try:
                print(f"Trying FSC Basic Info API for {isin_code}...")
                fsc_resp = requests.get(fsc_basi_url, timeout=20)
                if fsc_resp.status_code == 200:
                    fsc_data = fsc_resp.json()
                    fsc_items = fsc_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if not isinstance(fsc_items, list):
                        fsc_items = [fsc_items] if fsc_items else []
                        
                    if fsc_items:
                        use_api_data = True
                        item = fsc_items[0]
                        print(f"FSC Basic Info API data found for {isin_code}.")
                        
                        api_interest_payment_method = item.get('bondIntTcdNm')
                        api_interest_payment_unit_months = item.get('intPayCyclCtt')
                        api_interest_calculation_months = item.get('intCmpuMcdNm')
                        api_interest_pre_post_type = item.get('intPayMmntDcdNm')
                        
                        # 차기 이자지급일을 활용하거나 발행일 + 주기 계산
                        nxt_dt = safe_parse_date(item.get('nxtmCopnDt'))
                        if nxt_dt:
                            api_first_interest_payment_date = nxt_dt
                        else:
                            api_first_interest_payment_date = add_months(issue_date, payment_cycle)
                            
                        api_interest_payment_basis = item.get('bnkHldyIntPydyDcdNm')
                        api_interest_month_end_type = item.get('sttrHldyIntPydyDcdNm')
                        
                        # 옵션타입 싱크
                        opt_kind = item.get('optnTcdNm')
                        if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                            api_option_type = opt_kind
            except Exception as e:
                print(f"FSC Basic Info API calling failed for {isin_code}: {e}.")

        # 1-3. FSC 채권권리일정정보 OpenAPI 호출 시도 (최초이자지급일 및 옵션행사일 보완)
        fsc_righ_url = f"http://apis.data.go.kr/1160100/GetBondRighScheInfoService_V2/getBondRighExerSche_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}&numOfRows=1000"
        try:
            print(f"Trying FSC Rights Schedule API for {isin_code}...")
            righ_resp = requests.get(fsc_righ_url, timeout=20)
            if righ_resp.status_code == 200:
                righ_data = righ_resp.json()
                righ_items = righ_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                if not isinstance(righ_items, list):
                    righ_items = [righ_items] if righ_items else []
                
                valid_interest_dates = []
                valid_exercise_dates = []
                
                for item in righ_items:
                    scrs_sced_nm = item.get('scrsScedDcdNm')
                    event_date = safe_parse_date(item.get('basDt'))
                    if not event_date:
                        continue
                    
                    if scrs_sced_nm == '원리금지급일':
                        if event_date >= issue_date:
                            valid_interest_dates.append(event_date)
                    elif scrs_sced_nm == '조기상환일':
                        if event_date >= issue_date:
                            valid_exercise_dates.append(event_date)
                
                if valid_interest_dates:
                    api_first_interest_payment_date = min(valid_interest_dates)
                    use_api_data = True
                    print(f"FSC Rights Schedule API first interest date found: {api_first_interest_payment_date}")
                    
                if valid_exercise_dates:
                    valid_exercise_dates.sort()
                    api_exercise_start_date_1 = valid_exercise_dates[0]
                    api_exercise_end_date_1 = valid_exercise_dates[-1]
                    api_exercise_reason = f"조기상환 권리 행사 일정 수집 완료 (행사 가능일수: {len(valid_exercise_dates)}개)"
                    use_api_data = True
                    print(f"FSC Rights Schedule API exercise date(s) found: {valid_exercise_dates}")
        except Exception as e:
            print(f"FSC Rights Schedule API calling failed for {isin_code}: {e}.")

        # 1-4. FSC 채권권리행사정보 OpenAPI 호출 시도 (조기행사 옵션 시작일 추가 보완)
        if option_type in ('CALL', 'PUT', 'CALL+PUT'):
            fsc_rede_url = f"http://apis.data.go.kr/1160100/GetBondRedeInfoService_V2/getEarlExerOpti_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}&numOfRows=1000"
            try:
                print(f"Trying FSC Rights Exercise API for {isin_code}...")
                rede_resp = requests.get(fsc_rede_url, timeout=20)
                if rede_resp.status_code == 200:
                    rede_data = rede_resp.json()
                    rede_items = rede_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if not isinstance(rede_items, list):
                        rede_items = [rede_items] if rede_items else []
                    
                    if rede_items:
                        use_api_data = True
                        item = rede_items[0]
                        strt_dt = safe_parse_date(item.get('optiExerStrtDt'))
                        if strt_dt:
                            api_exercise_start_date_1 = strt_dt
                            print(f"FSC Rights Exercise Option Start Date found: {api_exercise_start_date_1}")
                            
                            opt_kind = item.get('optiTpCd')
                            if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                                api_option_type = opt_kind
                            
                            exer_amt = item.get('optiExerAmt')
                            if exer_amt:
                                api_exercise_reason = f"조기상환 권리 행사 (행사금액: {exer_amt})"
            except Exception as e:
                print(f"FSC Rights Exercise API calling failed for {isin_code}: {e}.")
                
        # 1-3. 데이터베이스 적재 (API 데이터 vs 계산 Fallback)
        if use_api_data:
            print(f"Updating DB with actual API data for {isin_code}.")
            
            # 이자지급조건 업데이트 (결측치에 한해 Fallback 적용)
            cur.execute("""
                UPDATE "BondCashflowRule" SET
                    interest_payment_method = %s,
                    interest_payment_unit_months = %s,
                    interest_calculation_months = %s,
                    interest_pre_post_type = %s,
                    first_interest_payment_date = %s,
                    interest_payment_basis = %s,
                    interest_month_end_type = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cashflow_rule_id = %s;
            """, (
                api_interest_payment_method or interest_type,
                api_interest_payment_unit_months or f"{payment_cycle}개월",
                api_interest_calculation_months or "정형",
                api_interest_pre_post_type or ("선급" if interest_type == "할인채" else "후급"),
                api_first_interest_payment_date or add_months(issue_date, payment_cycle),
                api_interest_payment_basis or "직후영업일",
                api_interest_month_end_type or "직후영업일",
                cashflow_rule_id
            ))
            
            # 옵션 정보 업데이트 (결측치인 경우 룰 기반 계산 대입)
            has_option = api_option_type in ('CALL', 'PUT', 'CALL+PUT')
            default_start_1 = add_months(issue_date, 12) if has_option else None
            default_end_1 = add_months(maturity_date, -1) if has_option else None
            default_start_2 = add_months(issue_date, 24) if api_option_type == 'CALL+PUT' else None
            default_end_2 = add_months(maturity_date, -1) if api_option_type == 'CALL+PUT' else None
            default_reason = "투자자/발행인 선택에 의한 조기상환 권리 행사" if has_option else None
            
            cur.execute("""
                UPDATE "BondOptionExercise" SET
                    option_type = %s,
                    exercise_start_date_1 = %s,
                    exercise_end_date_1 = %s,
                    exercise_start_date_2 = %s,
                    exercise_end_date_2 = %s,
                    exercise_reason = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE option_exercise_id = %s;
            """, (
                api_option_type,
                api_exercise_start_date_1 or default_start_1,
                api_exercise_end_date_1 or default_end_1,
                api_exercise_start_date_2 or default_start_2,
                api_exercise_end_date_2 or default_end_2,
                api_exercise_reason or default_reason,
                option_exercise_id
            ))
            
            # 마스터 테이블 옵션 싱크
            if api_option_type != option_type:
                cur.execute("""
                    UPDATE "Bond" SET option_type = %s, updated_at = CURRENT_TIMESTAMP WHERE bond_id = (
                        SELECT bond_id FROM "Bond" WHERE isin_code = %s
                    );
                """, (api_option_type, isin_code))
                
        else:
            print(f"Running fallback calculation for {isin_code}.")
            # 1) 이자지급 상세 조건 계산
            first_interest_date = add_months(issue_date, payment_cycle)
            pre_post_type = "선급" if interest_type == "할인채" else "후급"
            
            cur.execute("""
                UPDATE "BondCashflowRule" SET
                    interest_payment_method = %s,
                    interest_payment_unit_months = %s,
                    interest_calculation_months = %s,
                    interest_pre_post_type = %s,
                    first_interest_payment_date = %s,
                    interest_payment_basis = %s,
                    interest_month_end_type = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cashflow_rule_id = %s;
            """, (
                interest_type,
                f"{payment_cycle}개월",
                "정형",
                pre_post_type,
                first_interest_date,
                "직후영업일",
                "직후영업일",
                cashflow_rule_id
            ))
            
            # 2) 옵션 행사 상세 조건 계산
            has_option = option_type in ('CALL', 'PUT', 'CALL+PUT')
            ex_start_1 = add_months(issue_date, 12) if has_option else None
            ex_end_1 = add_months(maturity_date, -1) if has_option else None
            ex_start_2 = add_months(issue_date, 24) if option_type == 'CALL+PUT' else None
            ex_end_2 = add_months(maturity_date, -1) if option_type == 'CALL+PUT' else None
            ex_reason = "투자자/발행인 선택에 의한 조기상환 권리 행사" if has_option else None
            
            cur.execute("""
                UPDATE "BondOptionExercise" SET
                    option_type = %s,
                    exercise_start_date_1 = %s,
                    exercise_end_date_1 = %s,
                    exercise_start_date_2 = %s,
                    exercise_end_date_2 = %s,
                    exercise_reason = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE option_exercise_id = %s;
            """, (
                option_type,
                ex_start_1,
                ex_end_1,
                ex_start_2,
                ex_end_2,
                ex_reason,
                option_exercise_id
            ))
            
        print(f"Successfully enriched {isin_code} details.")
        
    conn.commit()
    cur.close()
    conn.close()

# --- 2-C. 일별 시세 데이터 수집 함수 ---
def ingest_daily_market_data():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    # 최근 3일의 일별 시세를 수집 (주말/공휴일 공백 대비)
    today = datetime.now()
    dates_to_query = [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(1, 4)]
    
    for date_str in dates_to_query:
        print(f"Fetching daily price data for date: {date_str}")
        url = f"http://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondPriceInfo?serviceKey={API_KEY}&numOfRows=1000&pageNo=1&resultType=json&basDt={date_str}"
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                print(f"Received {len(items)} price records for {date_str}.")
                
                for item in items:
                    isin_code = item.get('isinCd')
                    short_code = item.get('srtnCd')
                    short_name = item.get('itmsNm')
                    price_str = item.get('clprPrc')
                    ytm_str = item.get('clprBnfRt')
                    volume_str = item.get('trqu')
                    change_rate_str = item.get('clprVs')
                    
                    # 1) Bond 테이블에서 bond_id 조회
                    cur.execute('SELECT bond_id FROM "Bond" WHERE isin_code = %s;', (isin_code,))
                    res = cur.fetchone()
                    if res:
                        bond_id = res[0]
                        
                        # 2) Bond 테이블의 short_code / short_name 업데이트
                        cur.execute("""
                            UPDATE "Bond" SET
                                short_code = COALESCE(short_code, %s),
                                short_name = COALESCE(short_name, %s),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE bond_id = %s;
                        """, (short_code, short_name, bond_id))
                        
                        # 3) BondMarketData 테이블에 적재 (UPSERT)
                        price = safe_float(price_str)
                        ytm = safe_float(ytm_str)
                        volume = safe_int(volume_str)
                        
                        base_date = datetime.strptime(date_str, "%Y%m%d").date()
                        
                        cur.execute("""
                            INSERT INTO "BondMarketData" (
                                bond_id, base_date, price, ytm, trading_volume, price_change_rate, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (bond_id, base_date) DO UPDATE SET
                                price = EXCLUDED.price,
                                ytm = EXCLUDED.ytm,
                                trading_volume = EXCLUDED.trading_volume,
                                price_change_rate = EXCLUDED.price_change_rate,
                                updated_at = CURRENT_TIMESTAMP;
                        """, (bond_id, base_date, price, ytm, volume, change_rate_str))
                        
            else:
                print(f"Failed to fetch market data for {date_str}. Status code: {resp.status_code}")
        except Exception as e:
            print(f"Error fetching/processing market data for {date_str}: {e}")
            
    conn.commit()
    cur.close()
    conn.close()

# --- 3. 검증 함수 ---
def verify_data_count():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM \"Bond\";")
    bond_count = cur.fetchone()[0]
    print(f"Total records in Bond table: {bond_count}")
    
    cur.execute("SELECT count(*) FROM \"BondCashflowRule\" WHERE first_interest_payment_date IS NOT NULL;")
    cashflow_count = cur.fetchone()[0]
    print(f"Enriched records in BondCashflowRule table: {cashflow_count}")
    
    cur.execute("SELECT count(*) FROM \"BondOptionExercise\" WHERE exercise_start_date_1 IS NOT NULL OR option_type = '옵션해당사항없음';")
    option_count = cur.fetchone()[0]
    print(f"Enriched records in BondOptionExercise table: {option_count}")
    
    cur.execute("SELECT count(*) FROM \"BondMarketData\";")
    market_count = cur.fetchone()[0]
    print(f"Total records in BondMarketData table: {market_count}")
    
    if bond_count >= 1000:
        print("Verification SUCCESS: 1,000 or more records loaded.")
    else:
        print(f"Verification WARNING: Only {bond_count} records found.")
        
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

    ingest_details_task = PythonOperator(
        task_id='ingest_option_cashflow_details',
        python_callable=ingest_option_cashflow_details,
    )

    ingest_market_data_task = PythonOperator(
        task_id='ingest_daily_market_data',
        python_callable=ingest_daily_market_data,
    )

    verify_task = PythonOperator(
        task_id='verify_db_load',
        python_callable=verify_data_count,
    )

    collect_task >> spark_task >> [ingest_details_task, ingest_market_data_task] >> verify_task
