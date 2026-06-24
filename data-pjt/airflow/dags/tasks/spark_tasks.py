import psycopg2
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf, regexp_replace, to_date
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, LongType
from tasks.helpers import (
    KAFKA_BOOTSTRAP_SERVERS, POSTGRES_DB, POSTGRES_USER, 
    POSTGRES_PASSWORD, DB_HOST, DB_PORT
)

def run_spark_kafka_to_hdfs():
    spark = SparkSession.builder \
        .appName("Airflow-SparkKafkaToHDFS") \
        .master("spark://spark-master:7077") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .config("spark.testing.memory", "471859200") \
        .getOrCreate()

    # Kafka Topic에서 스트림 읽기
    kafka_df = spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "topic_bond_raw") \
        .option("startingOffsets", "earliest") \
        .option("allowNonExistentTopics", "true") \
        .load()
    
    # Kafka의 value 컬럼은 binary 형식이므로 string으로 변환
    raw_df = kafka_df.selectExpr("CAST(value AS STRING) as json_value")
    
    # json_value에서 basDt 추출하여 bas_dt 컬럼으로 추가 (HDFS 파티션용)
    from pyspark.sql.functions import json_tuple
    partitioned_raw_df = raw_df.select("json_value", json_tuple("json_value", "basDt").alias("bas_dt"))
    
    # HDFS /raw/bonds 경로에 parquet 형식으로 쓰기 (bas_dt 컬럼으로 파티션)
    checkpoint_path = "hdfs://namenode:9000/spark/checkpoints/kafka_to_hdfs"
    hdfs_raw_path = "hdfs://namenode:9000/raw/bonds"
    
    query = partitioned_raw_df.writeStream \
        .format("parquet") \
        .partitionBy("bas_dt") \
        .trigger(availableNow=True) \
        .option("checkpointLocation", checkpoint_path) \
        .start(hdfs_raw_path)
        
    query.awaitTermination()
    spark.stop()

def run_spark_hdfs_to_postgres(**kwargs):
    # Airflow XCom 또는 context에서 target_date 가져오기
    ti = kwargs.get('ti')
    target_date = None
    if ti:
        target_date = ti.xcom_pull(task_ids='collect_api_to_kafka')
    if not target_date:
        target_date = kwargs.get('ds_nodash')
    if not target_date:
        target_date = datetime.now().strftime("%Y%m%d")
        
    print(f"Incremental Spark HDFS to Postgres processing for bas_dt = {target_date}")

    spark = SparkSession.builder \
        .appName("Airflow-SparkHDFSToPostgres") \
        .master("spark://spark-master:7077") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.2") \
        .config("spark.testing.memory", "471859200") \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .getOrCreate()
        
    # HDFS /raw/bonds에서 Parquet 읽기
    hdfs_raw_path = "hdfs://namenode:9000/raw/bonds"
    
    try:
        # partition pruning을 활용하여 해당하는 bas_dt 폴더만 스캔하도록 필터링
        raw_df = spark.read.parquet(hdfs_raw_path).filter(col("bas_dt") == target_date)
    except Exception as e:
        print(f"No parquet files found at HDFS raw directory for bas_dt = {target_date}: {e}")
        spark.stop()
        return

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

    parsed_df = raw_df.select(from_json(col("json_value"), kafka_schema).alias("data"), col("bas_dt")).select("data.*", "bas_dt")

    dw_df = parsed_df \
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
        .select("isin_code", "bond_name", "company_id", "company_name", "industry", "issue_date", "maturity_date", "coupon_rate", "issue_amount", "bond_type", "seniority", "call_put_option", "interest_type", "payment_cycle", "guarantee_status", "underwriter", "credit_rating", "bas_dt")

    deduped_df = dw_df.dropDuplicates(["isin_code"])

    # HDFS /dw/bonds 경로에 정규화 DW 형태로 쓰기 (bas_dt 컬럼으로 파티션)
    hdfs_dw_path = "hdfs://namenode:9000/dw/bonds"
    deduped_df.write.mode("overwrite").partitionBy("bas_dt").parquet(hdfs_dw_path)
    print("SUCCESS: Standardized DW Parquet loaded to HDFS /dw/bonds with partitioning.")

    JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
    JDBC_PROPERTIES = {"user": POSTGRES_USER, "password": POSTGRES_PASSWORD, "driver": "org.postgresql.Driver"}
    if DB_HOST != "db":
        JDBC_PROPERTIES["ssl"] = "true"
        JDBC_PROPERTIES["sslmode"] = "require"

    # DB에 적재할 데이터프레임에서는 HDFS 파티션 컬럼(bas_dt) 제거
    db_df = deduped_df.drop("bas_dt")

    # 스테이징 테이블에 OVERWRITE 적재
    db_df.write.jdbc(url=JDBC_URL, table="temp_bonds_master_staging", mode="overwrite", properties=JDBC_PROPERTIES)

    # PostgreSQL Upsert 실행
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    try:
        cur.execute("SELECT normalize_bonds_staging();")
        cur.execute("DROP TABLE temp_bonds_master_staging;")
        conn.commit()
        print("SUCCESS: PostgreSQL DB load complete!")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

    spark.stop()
