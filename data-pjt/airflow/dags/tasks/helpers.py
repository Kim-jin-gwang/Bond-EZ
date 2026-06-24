import os
from datetime import datetime

# 환경 변수 및 설정 로드
API_KEY = os.getenv("DATA_PORTAL_API_KEY")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

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
