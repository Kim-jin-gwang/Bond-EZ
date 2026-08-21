# Bond-EZ 백엔드 (Django + Gunicorn)
# 단독 실행보다는 저장소 루트의 docker-compose.yml 사용을 권장
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# bootstrap_demo: 스키마 생성 + 마이그레이션 + 데모 시드(오늘 날짜 기준 시세) — 재실행 안전
CMD ["sh", "-c", "python manage.py bootstrap_demo && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
