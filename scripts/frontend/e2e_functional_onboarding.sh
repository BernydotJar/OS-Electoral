#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
FRONTEND_DIR="$ROOT/frontend"
BASE_ENV_FILE=${CAMPAIGNOS_FUNCTIONAL_ENV_FILE:-"$ROOT/.env.functional.example"}
ARTIFACT_DIR=${CAMPAIGNOS_FRONTEND_ARTIFACT_DIR:-"$ROOT/artifacts/c3-front-002"}
case "$ARTIFACT_DIR" in
  /*) ;;
  *) ARTIFACT_DIR="$ROOT/$ARTIFACT_DIR" ;;
esac
[ -f "$BASE_ENV_FILE" ] || { echo "Missing functional environment file" >&2; exit 1; }
[ -f "$FRONTEND_DIR/.next/BUILD_ID" ] || {
  echo "Missing production frontend build; run make frontend-verify first" >&2
  exit 1
}

free_port() {
  uv run --locked python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()"
}

set -a
. "$BASE_ENV_FILE"
set +a
export COMPOSE_PROJECT_NAME="campaignos-functional-e2e-$$"
export CAMPAIGNOS_API_PORT=$(free_port)
export POSTGRES_PORT=$(free_port)
export S3MOCK_PORT=$(free_port)
export MAILPIT_SMTP_PORT=$(free_port)
export MAILPIT_UI_PORT=$(free_port)
export CAMPAIGNOS_API_BASE_URL="http://127.0.0.1:$CAMPAIGNOS_API_PORT"
FRONTEND_PORT=$(free_port)
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  docker compose --env-file "$BASE_ENV_FILE" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

cd "$ROOT"
docker compose --env-file "$BASE_ENV_FILE" up -d --build --remove-orphans \
  postgres s3mock mailpit migrate api
attempt=1
while [ "$attempt" -le 60 ]; do
  if curl --fail --silent "$CAMPAIGNOS_API_BASE_URL/api/v1/ready" >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    docker compose --env-file "$BASE_ENV_FILE" logs --tail=160 api migrate postgres >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 1
done

uv run --locked python scripts/dev/seed_local_operator.py \
  --database-url "postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/${POSTGRES_DB}"

RUNTIME_DIR="$FRONTEND_DIR/.next/standalone"
mkdir -p "$ARTIFACT_DIR" "$RUNTIME_DIR/.next"
rm -rf "$RUNTIME_DIR/.next/static" "$RUNTIME_DIR/public"
cp -R "$FRONTEND_DIR/.next/static" "$RUNTIME_DIR/.next/static"
cp -R "$FRONTEND_DIR/public" "$RUNTIME_DIR/public"

cd "$RUNTIME_DIR"
CAMPAIGNOS_FRONTEND_MODE=live \
CAMPAIGNOS_FRONTEND_ENVIRONMENT=development \
CAMPAIGNOS_API_BASE_URL="$CAMPAIGNOS_API_BASE_URL" \
CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN="$CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN" \
CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID="$CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID" \
NEXT_TELEMETRY_DISABLED=1 \
HOSTNAME=127.0.0.1 \
PORT="$FRONTEND_PORT" \
node server.js >"$ARTIFACT_DIR/server.log" 2>&1 &
SERVER_PID=$!
cd "$ROOT"

attempt=1
while [ "$attempt" -le 40 ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$ARTIFACT_DIR/server.log" >&2
    exit 1
  fi
  if curl --fail --silent "http://127.0.0.1:$FRONTEND_PORT/es" >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 40 ]; then
    cat "$ARTIFACT_DIR/server.log" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 1
done

CAMPAIGNOS_FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT" \
CAMPAIGNOS_FRONTEND_ARTIFACT_DIR="$ARTIFACT_DIR" \
uv run --locked python scripts/frontend/review_functional_onboarding.py
