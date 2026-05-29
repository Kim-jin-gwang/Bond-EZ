import os
from pyflink.table import EnvironmentSettings, TableEnvironment

def run_news_processor():
    # 1. Create Streaming Table Environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    table_env = TableEnvironment.create(env_settings)

    # Kafka and DB Config from environment or defaults
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")

    # 2. Define Kafka Source Table
    # The data is expected to be in JSON format with fields: title, source, url, write_date
    table_env.execute_sql(f"""
        CREATE TABLE kafka_news_raw (
            title STRING,
            source STRING,
            url STRING,
            write_date STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'topic_news_raw',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id' = 'flink-news-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    # 3. Define PostgreSQL Sink Table
    # Using JDBC connector to write to bonds_db.news_article
    # We define 'url' as PRIMARY KEY here so Flink uses UPSERT (ON CONFLICT) logic
    table_env.execute_sql(f"""
        CREATE TABLE postgres_news_article (
            title STRING,
            source STRING,
            url STRING,
            write_date TIMESTAMP(3),
            PRIMARY KEY (url) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://{DB_HOST}:{DB_PORT}/{POSTGRES_DB}',
            'table-name' = 'news_article',
            'username' = '{POSTGRES_USER}',
            'password' = '{POSTGRES_PASSWORD}',
            'sink.buffer-flush.max-rows' = '1'
        )
    """)

    # 4. Transform and Insert
    # We parse the date string. Note: In a production environment, you might need more complex parsing logic.
    # PostgreSQL expects YYYY-MM-DD HH:MM:SS format.
    # Naver/Yonhap dates often look like '2026.05.29 14:00'. We replace '.' with '-' to make it ISO-like.
    table_env.execute_sql("""
        INSERT INTO postgres_news_article
        SELECT 
            title, 
            source, 
            url, 
            TO_TIMESTAMP(REPLACE(write_date, '.', '-'), 'YYYY-MM-DD HH:mm')
        FROM kafka_news_raw
    """).wait()

if __name__ == '__main__':
    run_news_processor()
