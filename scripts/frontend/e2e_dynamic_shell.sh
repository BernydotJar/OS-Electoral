#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
FRONTEND_DIR="$ROOT/frontend"
ARTIFACT_DIR=${CAMPAIGNOS_FRONTEND_ARTIFACT_DIR:-"$ROOT/artifacts/c3-front-001"}
if [ -n "${CAMPAIGNOS_FRONTEND_PORT:-}" ]; then
  PORT=$CAMPAIGNOS_FRONTEND_PORT
else
  PORT=$(uv run --locked python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()")
fi
BASE_URL="http://127.0.0.1:$PORT"
SERVER_LOG="$ARTIFACT_DIR/server.log"
RUNTIME_DIR="$FRONTEND_DIR/.next/standalone"
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

command -v npm >/dev/null 2>&1 || {
  echo "npm is required" >&2
  exit 1
}
command -v uv >/dev/null 2>&1 || {
  echo "uv is required" >&2
  exit 1
}
[ -f "$FRONTEND_DIR/.next/BUILD_ID" ] || {
  echo "Missing production frontend build; run make frontend-verify first" >&2
  exit 1
}

mkdir -p "$ARTIFACT_DIR"
rm -rf "$RUNTIME_DIR/.next/static" "$RUNTIME_DIR/public"
mkdir -p "$RUNTIME_DIR/.next"
cp -R "$FRONTEND_DIR/.next/static" "$RUNTIME_DIR/.next/static"
cp -R "$FRONTEND_DIR/public" "$RUNTIME_DIR/public"

cd "$RUNTIME_DIR"
CAMPAIGNOS_FRONTEND_MODE=demo_read_only \
CAMPAIGNOS_FRONTEND_ENVIRONMENT=test \
NEXT_TELEMETRY_DISABLED=1 \
HOSTNAME=127.0.0.1 \
PORT="$PORT" \
node server.js >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
cd "$ROOT"

attempt=1
while [ "$attempt" -le 40 ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$SERVER_LOG" >&2
    exit 1
  fi
  if curl --fail --silent "$BASE_URL/es" >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 40 ]; then
    cat "$SERVER_LOG" >&2
    echo "CampaignOS frontend did not become ready" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 1
done

CAMPAIGNOS_FRONTEND_URL="$BASE_URL" \
CAMPAIGNOS_FRONTEND_ARTIFACT_DIR="$ARTIFACT_DIR" \
uv run --locked python "$ROOT/scripts/frontend/review_dynamic_shell.py"
