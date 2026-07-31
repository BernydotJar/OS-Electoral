#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${ENV_FILE:-"$ROOT/.env.functional.example"}
[ -f "$ENV_FILE" ] || { echo "Missing functional environment: $ENV_FILE" >&2; exit 1; }

# Functional development always uses the repository's locked environment. An
# activated environment from another checkout must not influence this launcher.
unset VIRTUAL_ENV

set -a
# This file is versioned, local-only, and contains no shell expressions.
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

cd "$ROOT"

requested_api_port=${CAMPAIGNOS_API_PORT:-8000}
requested_postgres_port=${POSTGRES_PORT:-5432}
requested_s3mock_port=${S3MOCK_PORT:-9090}
requested_mailpit_smtp_port=${MAILPIT_SMTP_PORT:-1025}
requested_mailpit_ui_port=${MAILPIT_UI_PORT:-8025}
requested_frontend_port=${CAMPAIGNOS_FRONTEND_PORT:-3000}

resolved_ports=$(
  uv run --locked python scripts/dev/resolve_local_ports.py \
    "CAMPAIGNOS_API_PORT=$requested_api_port" \
    "POSTGRES_PORT=$requested_postgres_port" \
    "S3MOCK_PORT=$requested_s3mock_port" \
    "MAILPIT_SMTP_PORT=$requested_mailpit_smtp_port" \
    "MAILPIT_UI_PORT=$requested_mailpit_ui_port" \
    "CAMPAIGNOS_FRONTEND_PORT=$requested_frontend_port"
)

while IFS='=' read -r name value; do
  case "$name" in
    CAMPAIGNOS_API_PORT) export CAMPAIGNOS_API_PORT="$value" ;;
    POSTGRES_PORT) export POSTGRES_PORT="$value" ;;
    S3MOCK_PORT) export S3MOCK_PORT="$value" ;;
    MAILPIT_SMTP_PORT) export MAILPIT_SMTP_PORT="$value" ;;
    MAILPIT_UI_PORT) export MAILPIT_UI_PORT="$value" ;;
    CAMPAIGNOS_FRONTEND_PORT) export CAMPAIGNOS_FRONTEND_PORT="$value" ;;
    *) echo "Unexpected local port assignment: $name" >&2; exit 1 ;;
  esac
done <<EOF
$resolved_ports
EOF

export CAMPAIGNOS_API_BASE_URL="http://127.0.0.1:$CAMPAIGNOS_API_PORT"

report_port() {
  service=$1
  requested=$2
  effective=$3
  if [ "$requested" = "$effective" ]; then
    printf '%s\n' "[OK] $service port $effective is available"
  else
    printf '%s\n' "[INFO] $service port $requested is occupied; using $effective"
  fi
}

report_port "API" "$requested_api_port" "$CAMPAIGNOS_API_PORT"
report_port "PostgreSQL" "$requested_postgres_port" "$POSTGRES_PORT"
report_port "S3Mock" "$requested_s3mock_port" "$S3MOCK_PORT"
report_port "Mailpit SMTP" "$requested_mailpit_smtp_port" "$MAILPIT_SMTP_PORT"
report_port "Mailpit UI" "$requested_mailpit_ui_port" "$MAILPIT_UI_PORT"
report_port "Frontend" "$requested_frontend_port" "$CAMPAIGNOS_FRONTEND_PORT"

compose_up() {
  local build_log status
  build_log=$(mktemp "${TMPDIR:-/tmp}/campaignos-functional-build.XXXXXX")

  if docker compose --env-file "$ENV_FILE" up -d --build --remove-orphans \
    postgres s3mock mailpit migrate api 2>&1 | tee "$build_log"; then
    rm -f "$build_log"
    return 0
  else
    status=$?
  fi

  if ! grep -Fq "frontend grpc server closed unexpectedly" "$build_log"; then
    rm -f "$build_log"
    return "$status"
  fi

  printf '%s\n' \
    "[WARN] Docker BuildKit closed its Dockerfile frontend; bootstrapping the selected builder and retrying once." >&2
  if ! docker buildx inspect --bootstrap; then
    rm -f "$build_log"
    printf '%s\n' \
      "[ERROR] Docker BuildKit could not bootstrap its selected builder." \
      "[INFO] Restart Docker Desktop with: docker desktop restart" \
      "[INFO] Then retry: make functional-dev" >&2
    return "$status"
  fi

  : >"$build_log"
  if docker compose --env-file "$ENV_FILE" up -d --build --remove-orphans \
    postgres s3mock mailpit migrate api 2>&1 | tee "$build_log"; then
    rm -f "$build_log"
    return 0
  else
    status=$?
  fi

  if grep -Fq "frontend grpc server closed unexpectedly" "$build_log"; then
    printf '%s\n' \
      "[ERROR] Docker BuildKit closed its Dockerfile frontend twice." \
      "[INFO] Restart Docker Desktop with: docker desktop restart" \
      "[INFO] Then retry: make functional-dev" >&2
  fi
  rm -f "$build_log"
  return "$status"
}

compose_up

attempt=1
while [ "$attempt" -le 40 ]; do
  if curl --fail --silent "${CAMPAIGNOS_API_BASE_URL}/api/v1/ready" >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 40 ]; then
    docker compose --env-file "$ENV_FILE" logs --tail=120 api migrate postgres >&2
    echo "CampaignOS API did not become ready" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 1
done

CAMPAIGNOS_ADMIN_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/${POSTGRES_DB}" \
  make dev-seed

frontend_base_url="http://127.0.0.1:${CAMPAIGNOS_FRONTEND_PORT}"
backend_ready_url="${CAMPAIGNOS_API_BASE_URL}/api/v1/ready"
frontend_ready_url="${frontend_base_url}/api/v1/ready"

printf '%s\n' \
  "" \
  "[READY] CampaignOS functional environment" \
  "  Frontend (ES):      ${frontend_base_url}/es" \
  "  Frontend (EN):      ${frontend_base_url}/en" \
  "  Browser readiness:  ${frontend_ready_url}" \
  "  Backend API:        ${CAMPAIGNOS_API_BASE_URL}" \
  "  Backend readiness:  ${backend_ready_url}" \
  "  Mailpit UI:         http://127.0.0.1:${MAILPIT_UI_PORT}" \
  "" \
  "[INFO] Use the Browser readiness URL when checking from the frontend port." \
  "[OK] Starting the live frontend. Keep this terminal open."
exec npm --prefix frontend run dev -- \
  --hostname 127.0.0.1 \
  --port "$CAMPAIGNOS_FRONTEND_PORT"
