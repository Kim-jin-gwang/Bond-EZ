from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator


local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    "owner": "ssafy",
    "start_date": datetime(2026, 6, 17, tzinfo=local_tz),
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    "interest_rate_daily_update_dag",
    default_args=default_args,
    schedule_interval="0 7 * * *",
    catchup=False,
    tags=["interest-rate", "deposit-rate", "daily"],
) as dag:
    update_interest_and_deposit_rates = BashOperator(
        task_id="update_interest_and_deposit_rates",
        bash_command=(
            "cd /app && "
            "python producer/interest_rate_loader.py --only all --days-back 60"
        ),
    )
