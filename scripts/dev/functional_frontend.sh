#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${ENV_FILE:-"$ROOT/.env.functional.example"}
[ -f "$ENV_FILE" ] || { echo "Missing functional environment: $ENV_FILE" >&2; exit 1; }

set -a
# This file is versioned, local-only, and contains no shell expressions.
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
    CAMPAIGNOS_API_PORT) export CAMPAIGNOS_API_PORT=$value ;;
    POSTGRES_PORT) export POSTGRES_PORT=$value ;;
    S3MOCK_PORT) export S3MOCK_PORT=$value ;;
    MAILPIT_SMTP_PORT) export MAILPIT_SMTP_PORT=$value ;;
    MAILPIT_UI_PORT) export MAILPIT_UI_PORT=$value ;;
    CAMPAIGNOS_FRONTEND_PORT) export CAMPAIGNOS_FRONTEND_PORT=$value ;;
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

docker compose --env-file "$ENV_FILE" up -d --build --remove-orphans \
  postgres s3mock mailpit migrate api

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

printf '%s\n' "[OK] Functional local API is ready at ${CAMPAIGNOS_API_BASE_URL}"
printf '%s\n' "[OK] Starting live frontend; open http://127.0.0.1:${CAMPAIGNOS_FRONTEND_PORT}/es"
exec npm --prefix frontend run dev -- \
  --hostname 127.0.0.1 \
  --port "$CAMPAIGNOS_FRONTEND_PORT"
