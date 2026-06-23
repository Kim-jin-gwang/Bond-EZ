import os
from pyflink.table import EnvironmentSettings, TableEnvironment

def run_news_processor():
    # 1. Create Streaming Table Environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    table_env = TableEnvironment.create(env_settings)

    # Enable Checkpoint (important for filesystem connector rolling policy)
    table_env.get_config().get_configuration().set_string("execution.checkpointing.interval", "10000")

    # Kafka and DB Config from environment or defaults
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")

    # 2. Define Kafka Source Table
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
    ssl_param = "?sslmode=require" if DB_HOST != "db" else ""
    table_env.execute_sql(f"""
        CREATE TABLE postgres_news_article (
            title STRING,
            source STRING,
            url STRING,
            write_date TIMESTAMP(3),
            PRIMARY KEY (url) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://{DB_HOST}:{DB_PORT}/{POSTGRES_DB}{ssl_param}',
            'table-name' = 'news_article',
            'username' = '{POSTGRES_USER}',
            'password' = '{POSTGRES_PASSWORD}',
            'sink.buffer-flush.max-rows' = '50',
            'sink.buffer-flush.interval' = '1s'
        )
    """)

    # Define HDFS Sink Table (Partitioned by bas_dt)
    table_env.execute_sql(f"""
        CREATE TABLE hdfs_news_raw (
            title STRING,
            source STRING,
            url STRING,
            write_date STRING,
            bas_dt STRING
        ) PARTITIONED BY (bas_dt) WITH (
            'connector' = 'filesystem',
            'path' = 'hdfs://namenode:9000/raw/news',
            'format' = 'json'
        )
    """)

    # 4. Transform and Insert to Postgres & HDFS simultaneously using StatementSet
    statement_set = table_env.create_statement_set()

    # Add Postgres Insert Statement
    statement_set.add_insert_sql("""
        INSERT INTO postgres_news_article
        SELECT 
            title, 
            source, 
            url, 
            TO_TIMESTAMP(REPLACE(write_date, '.', '-'), 'YYYY-MM-DD HH:mm')
        FROM kafka_news_raw
    """)

    # Add HDFS Insert Statement (Parse bas_dt from write_date, handling both '.' and '-')
    statement_set.add_insert_sql("""
        INSERT INTO hdfs_news_raw
        SELECT 
            title, 
            source, 
            url, 
            write_date,
            SUBSTR(REPLACE(REPLACE(write_date, '.', ''), '-', ''), 1, 8) AS bas_dt
        FROM kafka_news_raw
    """)

    statement_set.execute().wait()

if __name__ == '__main__':
    run_news_processor()

