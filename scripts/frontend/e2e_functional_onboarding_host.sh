#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
FRONTEND_DIR="$ROOT/frontend"
ARTIFACT_DIR=${CAMPAIGNOS_FRONTEND_ARTIFACT_DIR:-"$ROOT/artifacts/c3-front-002"}
case "$ARTIFACT_DIR" in
  /*) ;;
  *) ARTIFACT_DIR="$ROOT/$ARTIFACT_DIR" ;;
esac
ADMIN_URL=${CAMPAIGNOS_FUNCTIONAL_ADMIN_DATABASE_URL:?CAMPAIGNOS_FUNCTIONAL_ADMIN_DATABASE_URL is required}
APP_URL=${CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_URL:?CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_URL is required}
APP_USER=${CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_USER:-campaignos_app}
APP_PASSWORD=${CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_PASSWORD:-campaignos_app_ci_only}
DATABASE_NAME=${CAMPAIGNOS_FUNCTIONAL_DATABASE_NAME:-campaignos_functional_test}
DEVELOPMENT_TOKEN=${CAMPAIGNOS_DEVELOPMENT_ACCESS_TOKEN:-campaignos-local-development-token}
TENANT_ID=${CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID:-11111111-1111-4111-8111-111111111111}

[ -f "$FRONTEND_DIR/.next/BUILD_ID" ] || {
  echo "Missing production frontend build; run make frontend-verify first" >&2
  exit 1
}

free_port() {
  uv run --locked python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()"
}

API_PORT=$(free_port)
FRONTEND_PORT=$(free_port)
API_PID=""
SERVER_PID=""

cleanup() {
  for pid in "$SERVER_PID" "$API_PID"; do
    if [ -n "$pid" ]; then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT INT TERM

cd "$ROOT"
mkdir -p "$ARTIFACT_DIR"

CAMPAIGNOS_FUNCTIONAL_ADMIN_DATABASE_URL="$ADMIN_URL" \
CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_USER="$APP_USER" \
CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_PASSWORD="$APP_PASSWORD" \
CAMPAIGNOS_FUNCTIONAL_DATABASE_NAME="$DATABASE_NAME" \
uv run --locked python - <<'PY'
import os
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

sqlalchemy_url = make_url(os.environ["CAMPAIGNOS_FUNCTIONAL_ADMIN_DATABASE_URL"])
if sqlalchemy_url.drivername != "postgresql+psycopg":
    raise RuntimeError("Functional database URL must use postgresql+psycopg")
conninfo = sqlalchemy_url.set(drivername="postgresql").render_as_string(
    hide_password=False
)
user = os.environ["CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_USER"]
password = os.environ["CAMPAIGNOS_FUNCTIONAL_APP_DATABASE_PASSWORD"]
database = os.environ["CAMPAIGNOS_FUNCTIONAL_DATABASE_NAME"]
with psycopg.connect(conninfo, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,))
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS"
                ).format(sql.Identifier(user), sql.Literal(password))
            )
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(database), sql.Identifier(user)))
        cur.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(user)))
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}").format(sql.Identifier(user))
        )
PY

CAMPAIGNOS_DATABASE_URL="$ADMIN_URL" uv run --locked alembic upgrade head
uv run --locked python scripts/dev/seed_local_operator.py --database-url "$ADMIN_URL"

CAMPAIGNOS_ENVIRONMENT=development \
CAMPAIGNOS_EXPOSE_API_DOCS=true \
CAMPAIGNOS_DATABASE_URL="$APP_URL" \
CAMPAIGNOS_DEVELOPMENT_ACCESS_TOKEN="$DEVELOPMENT_TOKEN" \
CAMPAIGNOS_DEVELOPMENT_PRINCIPAL_SUBJECT=local-operator \
CAMPAIGNOS_DEVELOPMENT_PRINCIPAL_DISPLAY_NAME="Operador local" \
CAMPAIGNOS_DEVELOPMENT_PRINCIPAL_EMAIL=operator@localhost \
uv run --locked uvicorn campaignos.main:app --host 127.0.0.1 --port "$API_PORT" >"$ARTIFACT_DIR/api.log" 2>&1 &
API_PID=$!

attempt=1
while [ "$attempt" -le 40 ]; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    cat "$ARTIFACT_DIR/api.log" >&2
    exit 1
  fi
  if curl --fail --silent "http://127.0.0.1:$API_PORT/api/v1/ready" >/dev/null; then
    break
  fi
  [ "$attempt" -lt 40 ] || { cat "$ARTIFACT_DIR/api.log" >&2; exit 1; }
  attempt=$((attempt + 1))
  sleep 1
done

RUNTIME_DIR="$FRONTEND_DIR/.next/standalone"
mkdir -p "$RUNTIME_DIR/.next"
rm -rf "$RUNTIME_DIR/.next/static" "$RUNTIME_DIR/public"
cp -R "$FRONTEND_DIR/.next/static" "$RUNTIME_DIR/.next/static"
cp -R "$FRONTEND_DIR/public" "$RUNTIME_DIR/public"

cd "$RUNTIME_DIR"
CAMPAIGNOS_FRONTEND_MODE=live \
CAMPAIGNOS_FRONTEND_ENVIRONMENT=development \
CAMPAIGNOS_API_BASE_URL="http://127.0.0.1:$API_PORT" \
CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN="$DEVELOPMENT_TOKEN" \
CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID="$TENANT_ID" \
NEXT_TELEMETRY_DISABLED=1 HOSTNAME=127.0.0.1 PORT="$FRONTEND_PORT" \
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
  [ "$attempt" -lt 40 ] || { cat "$ARTIFACT_DIR/server.log" >&2; exit 1; }
  attempt=$((attempt + 1))
  sleep 1
done

CAMPAIGNOS_FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT" \
CAMPAIGNOS_FRONTEND_ARTIFACT_DIR="$ARTIFACT_DIR" \
uv run --locked python scripts/frontend/review_functional_onboarding.py
