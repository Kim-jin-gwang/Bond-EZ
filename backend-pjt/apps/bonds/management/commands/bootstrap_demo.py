"""라이브 데모용 DB 부트스트랩.

배경: Django 마이그레이션(0001)은 `id` PK 스키마를 만들지만, 현재 모델들은
데이터 파이프라인의 ERD 스키마(`bond_id` 등)를 db_column으로 가리킨다.
따라서 빈 DB에 그냥 migrate하면 모델과 맞지 않는 테이블이 생긴다.

이 커맨드는 올바른 순서를 한 번에 처리한다 (재실행 안전):
  1. deploy/demo_schema.sql  — 모델 정의와 일치하는 테이블/뷰 생성
  2. bonds/glossary/news 마이그레이션을 --fake 처리 (테이블은 1에서 이미 생성됨)
  3. 나머지 앱(accounts, indicators, portfolios, auth 등)은 실제 migrate
  4. deploy/demo_seed.sql 적재 — idempotent 시드가 시세를 CURRENT_DATE 기준
     최근 90일 시계열로 재계산하므로, 서비스가 재기동할 때마다 데이터가 갱신됨

Render 시작 커맨드 예:
  python manage.py bootstrap_demo && gunicorn config.wsgi:application ...
"""
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


DEPLOY_DIR = Path(__file__).resolve().parents[4] / "deploy"
FAKED_APPS = ("bonds", "glossary", "news")


class Command(BaseCommand):
    help = "데모 배포용 DB 스키마/마이그레이션/시드를 순서대로 준비합니다."

    def handle(self, *args, **options):
        self.stdout.write("[bootstrap] 1/4 demo_schema.sql 적용...")
        self._run_sql_file(DEPLOY_DIR / "demo_schema.sql")

        self.stdout.write("[bootstrap] 2/4 파이프라인 스키마 앱 마이그레이션 fake 처리...")
        for app_label in FAKED_APPS:
            call_command("migrate", app_label, fake=True, interactive=False, verbosity=0)

        self.stdout.write("[bootstrap] 3/4 나머지 앱 실제 마이그레이션...")
        call_command("migrate", interactive=False, verbosity=0)

        self.stdout.write("[bootstrap] 4/4 demo_seed.sql 적재 (idempotent — 시세를 오늘 날짜 기준으로 갱신)...")
        self._run_sql_file(DEPLOY_DIR / "demo_seed.sql")

        self.stdout.write(self.style.SUCCESS("[bootstrap] 완료"))

    def _run_sql_file(self, path):
        sql = path.read_text(encoding="utf-8-sig")  # BOM 방어
        with connection.cursor() as cursor:
            cursor.execute(sql)
