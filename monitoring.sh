#!/usr/bin/env sh
set -eu

# 스크립트를 어디서 실행하든 프로젝트 루트 기준으로 동작하게 이동합니다.
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose-monitoring.yml"

info() {
  printf '\n\033[1;35m[monitoring]\033[0m %s\n' "$1"
}

error() {
  printf '\n\033[1;31m[monitoring:error]\033[0m %s\n' "$1" >&2
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

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Docker 확인
if ! command_exists docker; then
  error "Docker is not installed."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  error "Docker Compose v2 is required."
  exit 1
fi

# 0. 네트워크 자동 생성 (docker-compose-monitoring.yml에서 external로 명시되어 있으므로, 미리 생성되어 있어야 함)
docker network inspect de_net >/dev/null 2>&1 || {
  info "Creating de_net network..."
  docker network create de_net
}
docker network inspect web_net >/dev/null 2>&1 || {
  info "Creating web_net network..."
  docker network create web_net
}

# 기본 사용법 안내
usage() {
  echo "Usage: sh $0 {up|down|logs}"
  exit 1
}

if [ $# -lt 1 ]; then
  usage
fi

ACTION="$1"

case "$ACTION" in
  up)
    info "Starting Monitoring services (Prometheus, Grafana)..."
    $COMPOSE up -d
    
    PROMETHEUS_PORT="$(get_env_value "PROMETHEUS_PORT" "9090")"
    GRAFANA_PORT="$(get_env_value "GRAFANA_PORT" "3000")"
    
    info "Monitoring Deployment Complete!"
    printf '%s\n' '--------------------------------------------------'
    printf '🚀 Monitoring Services are running at:\n'
    printf '  - Prometheus UI : http://localhost:%s\n' "$PROMETHEUS_PORT"
    printf '  - Grafana UI    : http://localhost:%s\n' "$GRAFANA_PORT"
    printf '%s\n' '--------------------------------------------------'
    ;;
  down)
    info "Stopping Monitoring services..."
    $COMPOSE down
    ;;
  logs)
    info "Viewing logs for Monitoring services..."
    $COMPOSE logs -f
    ;;
  *)
    usage
    ;;
esac
