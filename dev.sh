#!/usr/bin/env sh
set -eu

# 스크립트를 어디서 실행하든 프로젝트 루트 기준으로 동작하게 이동합니다.
cd "$(dirname "$0")"

# docker compose 서비스 이름입니다. docker-compose.yml의 services 키와 맞아야 합니다.
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

# Docker 캐시를 사용하므로 변경이 없으면 빠르게 지나갑니다.
# requirements.txt, package.json, Dockerfile 변경을 사람이 판단하지 않아도 됩니다.
info "Building Docker images. Docker will reuse cache when nothing changed."
$COMPOSE build "$BACKEND_SERVICE" "$FRONTEND_SERVICE"

# backend가 DB에 너무 빨리 접속하지 않도록 DB부터 먼저 실행합니다.
info "Starting database."
$COMPOSE up -d "$DB_SERVICE"

# healthcheck가 healthy가 될 때까지 기다린 뒤 backend를 실행합니다.
info "Waiting for database healthcheck."
wait_for_healthy "$DB_SERVICE" 120

# DB 준비가 끝났으므로 Django와 Vite 개발 서버를 실행합니다.
info "Starting backend and frontend."
$COMPOSE up -d "$BACKEND_SERVICE" "$FRONTEND_SERVICE"

# 새 DB이거나 migration이 추가된 경우를 위해 항상 migrate를 실행합니다.
# 이미 적용된 migration은 Django가 알아서 건너뜁니다.
info "Applying Django migrations."
$COMPOSE exec "$BACKEND_SERVICE" python manage.py migrate

# .env에 포트가 지정되어 있으면 그 값을, 없으면 compose 기본값을 출력합니다.
FRONTEND_PORT="$(env_value_or_default FRONTEND_PORT 5173)"
BACKEND_PORT="$(env_value_or_default BACKEND_PORT 8000)"

info "Done."
printf 'Frontend: http://localhost:%s\n' "$FRONTEND_PORT"
printf 'Backend : http://localhost:%s\n' "$BACKEND_PORT"
printf '\nUse "docker compose logs -f" to watch logs.\n'
