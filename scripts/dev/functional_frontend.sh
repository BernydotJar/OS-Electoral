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
printf '%s\n' "[OK] Starting live frontend; open http://127.0.0.1:3000/es"
exec npm --prefix frontend run dev -- --hostname 127.0.0.1
