#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "${script_dir}/../.." && pwd)
cd "$repo_root"

env_file=${ENV_FILE:-.env.example}
if [ ! -f "$env_file" ]; then
    echo "Missing ENV_FILE: $env_file" >&2
    exit 1
fi

export COMPOSE_PROJECT_NAME="campaignos-e2e-$$"
export CAMPAIGNOS_API_PORT=0
export POSTGRES_PORT=0
export S3MOCK_PORT=0
export MAILPIT_SMTP_PORT=0
export MAILPIT_UI_PORT=0

compose() {
    docker compose --env-file "$env_file" "$@"
}

cleanup() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$status" -ne 0 ]; then
        compose ps >&2 || true
        compose logs --no-color --tail=100 >&2 || true
    fi
    compose down --volumes --remove-orphans >/dev/null 2>&1 || true
    exit "$status"
}
trap cleanup EXIT HUP INT TERM

compose up --detach --build --wait --wait-timeout 240

compose run --rm --no-deps migrate alembic check

compose exec -T postgres sh -ec '
    result=$(psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --tuples-only --no-align --command "SELECT 1")
    test "$result" = "1"
'

compose exec -T api python - <<'PY'
from email.message import EmailMessage
import os
import smtplib
import socket
import json
import urllib.error
import urllib.request

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["CAMPAIGNOS_DATABASE_URL"])
with engine.connect() as connection:
    role = connection.execute(
        text(
            "SELECT current_user, rolsuper, rolbypassrls "
            "FROM pg_roles WHERE rolname = current_user"
        )
    ).one()
if role.current_user != "campaignos_app" or role.rolsuper or role.rolbypassrls:
    raise RuntimeError(f"API is not using the constrained application role: {role}")
engine.dispose()

checks = {
    "api": "http://127.0.0.1:8000/api/v1/health",
    "s3mock": "http://s3mock:9090/favicon.ico",
    "mailpit": "http://mailpit:8025/readyz",
}
for name, url in checks.items():
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise RuntimeError(f"{name} returned HTTP {response.status}")

bucket = os.environ["CAMPAIGNOS_OBJECT_STORAGE_BUCKET"]
request = urllib.request.Request(f"http://s3mock:9090/{bucket}/", method="HEAD")
with urllib.request.urlopen(request, timeout=5) as response:
    if response.status != 200:
        raise RuntimeError(f"S3Mock bucket {bucket!r} returned HTTP {response.status}")

try:
    urllib.request.urlopen("http://127.0.0.1:8000/api/v1/ready", timeout=5)
except urllib.error.HTTPError as exc:
    if exc.code != 503:
        raise
    readiness = json.loads(exc.read())
else:
    raise RuntimeError("readiness must fail closed while local OIDC is absent")
checks_by_name = {item["name"]: item for item in readiness["checks"]}
if not checks_by_name["database"]["ready"] or checks_by_name["identity"]["ready"]:
    raise RuntimeError(f"unexpected dependency readiness: {readiness}")

with socket.create_connection(("postgres", 5432), timeout=5):
    pass

message = EmailMessage()
message["From"] = "campaignos@localhost"
message["To"] = "e2e@localhost"
message["Subject"] = "CampaignOS local-stack e2e"
message.set_content("CampaignOS Mailpit delivery check")
with smtplib.SMTP("mailpit", 1025, timeout=5) as smtp:
    smtp.send_message(message)

print(
    "CampaignOS e2e: constrained API role, PostgreSQL, initialized S3Mock, "
    "and Mailpit are reachable"
)
PY
