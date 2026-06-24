#!/usr/bin/env sh
set -eu

# 스크립트를 어디서 실행하든 프로젝트 루트 기준으로 동작하게 이동합니다.
cd "$(dirname "$0")"

# docker compose 명령어 설정
COMPOSE="docker compose -f docker-compose.yml"
DB_SERVICE="db"
BACKEND_SERVICE="backend"

# 진행 상황을 보기 좋게 출력합니다.
info() {
  printf '\n\033[1;34m[service]\033[0m %s\n' "$1"
}

# 에러 메시지를 보기 좋게 출력합니다.
error() {
  printf '\n\033[1;31m[service:error]\033[0m %s\n' "$1" >&2
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
# Postgres는 최초 실행 시 init.sql, DB 생성 등을 마친 뒤에야 안전하게 접속할 수 있습니다.
wait_for_healthy() {
  service="$1"
  timeout="${2:-90}"
  elapsed=0

  # compose 서비스 이름으로 실제 컨테이너 ID를 찾습니다.
  container_id="$($COMPOSE ps -q "$service")"
  if [ -z "$container_id" ]; then
    error "Cannot find container for service '$service'."
    exit 1
  fi

  while [ "$elapsed" -lt "$timeout" ]; do
    # healthcheck가 없으면 none, 준비 중이면 starting, 성공하면 healthy가 됩니다.
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

# Docker CLI가 없으면 이후 명령이 전부 실패하므로 먼저 확인합니다.
if ! command_exists docker; then
  error "Docker is not installed or not available in PATH."
  exit 1
fi

# 이 프로젝트는 docker compose v2 형식의 명령을 사용합니다.
if ! docker compose version >/dev/null 2>&1; then
  error "'docker compose' is not available. Please install Docker Compose v2."
  exit 1
fi

# 협업자가 처음 clone한 경우를 위해 .env.example을 복사해 기본 .env를 만듭니다.
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    info ".env was not found. Creating it from .env.example."
    cp .env.example .env
  else
    error ".env was not found, and .env.example does not exist."
    exit 1
  fi
fi

# 1. 전체 프로젝트 빌드
info "Building application Docker images..."
$COMPOSE build

# 2. 인프라 서비스 먼저 실행 (DB, Elasticsearch, Kibana)
info "Starting infrastructure services (DB, Elasticsearch, Kibana)..."
$COMPOSE up -d db elasticsearch kibana

# 3. DB 준비 대기
info "Waiting for database to be healthy..."
wait_for_healthy "$DB_SERVICE"

# 4. 애플리케이션 서비스 실행 (Backend, Frontend)
info "Starting Django backend and Vue frontend..."
$COMPOSE up -d

# 5. Django 마이그레이션 적용
info "Applying Django migrations..."
$COMPOSE exec "$BACKEND_SERVICE" python manage.py migrate

# 접속 정보 출력
FRONTEND_PORT="$(env_value_or_default FRONTEND_PORT 5173)"
BACKEND_PORT="$(env_value_or_default BACKEND_PORT 8000)"

info "Application Services Deployment Complete!"
printf '%s\n' '--------------------------------------------------'
printf '🚀 Services are running at:\n'
printf '  - Frontend      : http://localhost:%s\n' "$FRONTEND_PORT"
printf '  - Backend API   : http://localhost:%s\n' "$BACKEND_PORT"
printf '  - Kibana UI     : http://localhost:5601\n'
printf '%s\n' '--------------------------------------------------'
printf 'Use "docker compose -f docker-compose.yml logs -f" to watch logs.\n'
