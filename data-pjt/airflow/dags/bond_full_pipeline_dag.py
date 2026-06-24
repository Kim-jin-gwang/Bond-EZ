from datetime import datetime, timedelta
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

# 한국 타임존 설정
local_tz = pendulum.timezone("Asia/Seoul")

# 개별 모듈화된 태스크 함수 임포트
from tasks.bond_collector import fetch_and_produce_bond_data
from tasks.spark_tasks import run_spark_kafka_to_hdfs, run_spark_hdfs_to_postgres
from tasks.db_tasks import ingest_option_cashflow_details, ingest_daily_market_data, verify_data_count
from tasks.hdfs_tasks import cleanup_old_hdfs_partitions

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

    spark_kafka_to_hdfs = PythonOperator(
        task_id='spark_kafka_to_hdfs',
        python_callable=run_spark_kafka_to_hdfs,
    )

    spark_hdfs_to_postgres = PythonOperator(
        task_id='spark_hdfs_to_postgres',
        python_callable=run_spark_hdfs_to_postgres,
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

    hdfs_cleanup_task = PythonOperator(
        task_id='hdfs_cleanup_task',
        python_callable=cleanup_old_hdfs_partitions,
    )

    collect_task >> spark_kafka_to_hdfs >> spark_hdfs_to_postgres >> [ingest_details_task, ingest_market_data_task] >> verify_task >> hdfs_cleanup_task
