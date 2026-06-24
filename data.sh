#!/usr/bin/env sh
set -eu

# 스크립트를 어디서 실행하든 프로젝트 루트 기준으로 동작하게 이동합니다.
cd "$(dirname "$0")"

# docker compose 명령어 설정
COMPOSE_DATA="docker compose -f docker-compose-data.yml"
COMPOSE_APP="docker compose -f docker-compose.yml"
DB_SERVICE="db"

# 진행 상황을 보기 좋게 출력합니다.
info() {
  printf '\n\033[1;36m[data]\033[0m %s\n' "$1"
}

# 에러 메시지를 보기 좋게 출력합니다.
error() {
  printf '\n\033[1;31m[data:error]\033[0m %s\n' "$1" >&2
}

# 필요한 명령어가 설치되어 있는지 확인할 때 사용합니다.
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# .env에서 값을 읽어오는 헬퍼 함수
get_env_value() {
  key="$1"
  default="$2"
  if [ -f ".env" ]; then
    value="$(grep -E "^${key}=" .env 2>/dev/null | tail -n 1 | cut -d '=' -f 2- || true)"
    value="$(printf '%s' "$value" | tr -d '"' | tr -d "'")"
    if [ -n "$value" ]; then
      printf '%s' "$value"
      return
    fi
  fi
  printf '%s' "$default"
}

# DB처럼 healthcheck가 있는 서비스가 준비될 때까지 기다립니다.
# 다른 docker-compose.yml에 있는 컨테이너 상태를 확인합니다.
wait_for_healthy_app_service() {
  service="$1"
  timeout="${2:-120}"
  elapsed=0

  # DB 서비스가 실행 중인지 확인하고, 없으면 자동으로 구동
  container_id="$($COMPOSE_APP ps -q "$service" 2>/dev/null || true)"
  if [ -z "$container_id" ]; then
    info "Database container for service '$service' is not running."
    info "Starting database container automatically..."
    if ! $COMPOSE_APP up -d "$service"; then
      error "Failed to start database service."
      exit 1
    fi
    container_id="$($COMPOSE_APP ps -q "$service" 2>/dev/null || true)"
    if [ -z "$container_id" ]; then
      error "Database container for service '$service' is still not running."
      exit 1
    fi
  fi

  while [ "$elapsed" -lt "$timeout" ]; do
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id")"

    if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
      return 0
    fi

    if [ "$health" = "unhealthy" ]; then
      error "Database service '$service' became unhealthy."
      $COMPOSE_APP logs "$service"
      exit 1
    fi

    sleep 2
    elapsed=$((elapsed + 2))
  done

  error "Timed out waiting for database service '$service' to become healthy."
  $COMPOSE_APP logs "$service"
  exit 1
}

# Docker 확인
if ! command_exists docker; then
  error "Docker is not installed."
  exit 1
fi

if ! $COMPOSE_DATA version >/dev/null 2>&1; then
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

# 0. 네트워크 자동 생성 (docker-compose-data.yml에서 external로 명시되어 있으므로, 미리 생성되어 있어야 함)
docker network inspect de_net >/dev/null 2>&1 || {
  info "Creating de_net network..."
  docker network create de_net
}
docker network inspect web_net >/dev/null 2>&1 || {
  info "Creating web_net network..."
  docker network create web_net
}

# 1. 데이터 파이프라인 DB 및 인프라 상태 확인 대기
DB_HOST="$(get_env_value "DB_HOST" "db")"

# Elasticsearch 상태 확인 및 자동 구동
es_container_id="$($COMPOSE_APP ps -q elasticsearch 2>/dev/null || true)"
if [ -z "$es_container_id" ]; then
  info "Elasticsearch container is not running. Starting elasticsearch automatically..."
  if ! $COMPOSE_APP up -d elasticsearch; then
    error "Failed to start Elasticsearch service."
    exit 1
  fi
fi

if [ "$DB_HOST" = "db" ]; then
  info "Checking if database is ready..."
  wait_for_healthy_app_service "$DB_SERVICE"
else
  info "Using external database at '$DB_HOST'. Skipping local database container check."
fi

# 2. 데이터 파이프라인 이미지 빌드
info "Building data pipeline Docker images..."
$COMPOSE_DATA build

# 3. 파이프라인 기초 인프라 실행 (Zookeeper, Kafka, Hadoop HDFS)
info "Starting pipeline infrastructure services (Zookeeper, Kafka, Hadoop HDFS)..."
$COMPOSE_DATA up -d zookeeper kafka namenode datanode

# 4. 나머지 파이프라인 서비스 실행 (Airflow, Spark, Flink, News Crawler)
info "Starting all remaining data pipeline services..."
$COMPOSE_DATA up -d

# 5. Glossary 데이터 적재 실행 (news-crawler가 실행 중이어야 함)
info "Loading Glossary data from CSV into PostgreSQL..."
$COMPOSE_DATA exec news-crawler python glossary/glossary_pipeline.py --load

# 6. HDFS 디렉토리 초기 설정 (/raw/bonds, /raw/news)
info "Initializing HDFS directories (/raw/bonds, /raw/news)..."
for i in $(seq 1 15); do
  if docker exec namenode hdfs dfs -mkdir -p /raw/bonds /raw/news >/dev/null 2>&1; then
    info "Successfully initialized HDFS directories."
    break
  fi
  info "Waiting for NameNode to finish formatting/startup... ($i/15)"
  sleep 2
done

info "Data Pipeline Deployment Complete!"
printf '%s\n' '--------------------------------------------------'
printf '🚀 Data Pipeline Services are running at:\n'
printf '  - Airflow UI    : http://localhost:8081\n'
printf '  - Spark Master  : http://localhost:8080\n'
printf '  - Flink UI      : http://localhost:8082\n'
printf '  - Hadoop Web UI : http://localhost:9870\n'
printf '%s\n' '--------------------------------------------------'
printf 'Use "docker compose -f docker-compose-data.yml logs -f" to watch logs.\n'
