#!/usr/bin/env sh
set -eu

# 스크립트를 어디서 실행하든 프로젝트 루트 기준으로 동작하게 이동합니다.
cd "$(dirname "$0")"

# docker compose 명령어 설정
COMPOSE="docker compose"
DB_SERVICE="db"
BACKEND_SERVICE="backend"
FRONTEND_SERVICE="frontend"

# 진행 상황을 보기 좋게 출력합니다.
info() {
  printf '\n\033[1;34m[dev]\033[0m %s\n' "$1"
}

# 에러 메시지를 보기 좋게 출력합니다.
error() {
  printf '\n\033[1;31m[dev:error]\033[0m %s\n' "$1" >&2
}

# 필요한 명령어가 설치되어 있는지 확인할 때 사용합니다.
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# .env에서 포트 값을 읽고, 값이 없으면 기본 포트를 사용합니다.
env_value_or_default() {
  key="$1"
  default="$2"
  value="$(grep -E "^${key}=" .env 2>/dev/null | tail -n 1 | cut -d '=' -f 2- || true)"
  value="$(printf '%s' "$value" | tr -d '"' | tr -d "'")"

  if [ -n "$value" ]; then
    printf '%s' "$value"
  else
    printf '%s' "$default"
  fi
}

# DB처럼 healthcheck가 있는 서비스가 준비될 때까지 기다립니다.
wait_for_healthy() {
  service="$1"
  timeout="${2:-120}"
  elapsed=0

  # compose 서비스 이름으로 실제 컨테이너 ID를 찾습니다.
  container_id="$($COMPOSE ps -q "$service")"
  if [ -z "$container_id" ]; then
    error "Cannot find container for service '$service'."
    exit 1
  fi

  while [ "$elapsed" -lt "$timeout" ]; do
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id")"

    if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
      return 0
    fi

    if [ "$health" = "unhealthy" ]; then
      error "Service '$service' became unhealthy."
      $COMPOSE logs "$service"
      exit 1
    fi

    sleep 2
    elapsed=$((elapsed + 2))
  done

  error "Timed out waiting for service '$service' to become healthy."
  $COMPOSE logs "$service"
  exit 1
}

# Docker 확인
if ! command_exists docker; then
  error "Docker is not installed."
  exit 1
fi

if ! $COMPOSE version >/dev/null 2>&1; then
  error "Docker Compose v2 is required."
  exit 1
fi

# .env 준비
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    info ".env was not found. Creating it from .env.example."
    cp .env.example .env
  else
    error ".env.example not found."
    exit 1
  fi
fi

# 1. 전체 프로젝트 빌드
info "Building all Docker images (this may take a while)..."
$COMPOSE build

# 2. 인프라 서비스 먼저 실행 (DB, Kafka, Hadoop HDFS)
info "Starting infrastructure services (DB, Zookeeper, Kafka, Hadoop HDFS)..."
$COMPOSE up -d db zookeeper kafka namenode datanode

# 3. DB 준비 대기 (Airflow와 Backend가 DB에 의존함)
info "Waiting for database to be healthy..."
wait_for_healthy "$DB_SERVICE"

# 4. 나머지 모든 서비스 실행 (Crawler, Airflow, Spark, Flink, Web)
info "Starting all remaining pipeline and application services..."
$COMPOSE up -d

# 5. Django 마이그레이션 및 기초 데이터 적재 실행
info "Applying Django migrations..."
$COMPOSE exec "$BACKEND_SERVICE" python manage.py migrate

info "Loading Glossary data from CSV into PostgreSQL..."
$COMPOSE exec news-crawler python glossary/glossary_pipeline.py --load

# HDFS 디렉토리 초기 설정 (/raw/bonds, /raw/news)
info "Initializing HDFS directories (/raw/bonds, /raw/news)..."
for i in $(seq 1 15); do
  if docker exec namenode hdfs dfs -mkdir -p /raw/bonds /raw/news >/dev/null 2>&1; then
    info "Successfully initialized HDFS directories."
    break
  fi
  info "Waiting for NameNode to finish formatting/startup... ($i/15)"
  sleep 2
done

# 접속 정보 출력
FRONTEND_PORT="$(env_value_or_default FRONTEND_PORT 5173)"
BACKEND_PORT="$(env_value_or_default BACKEND_PORT 8000)"

info "Deployment Complete!"
printf '%s\n' '--------------------------------------------------'
printf '🚀 Services are running at:\n'
printf '  - Frontend      : http://localhost:%s\n' "$FRONTEND_PORT"
printf '  - Backend API   : http://localhost:%s\n' "$BACKEND_PORT"
printf '  - Airflow UI    : http://localhost:8081\n'
printf '  - Spark Master  : http://localhost:8080\n'
printf '  - Flink UI      : http://localhost:8082\n'
printf '  - Hadoop Web UI : http://localhost:9870\n'
printf '%s\n' '--------------------------------------------------'
printf 'Use "docker compose logs -f" to watch logs.\n'
