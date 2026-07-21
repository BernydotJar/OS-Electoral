#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${CAMPAIGNOS_DATABASE_USER:?CAMPAIGNOS_DATABASE_USER is required}"
: "${CAMPAIGNOS_DATABASE_PASSWORD:?CAMPAIGNOS_DATABASE_PASSWORD is required}"

psql \
    --set=ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=admin_user="$POSTGRES_USER" \
    --set=database_name="$POSTGRES_DB" \
    --set=app_user="$CAMPAIGNOS_DATABASE_USER" \
    --set=app_password="$CAMPAIGNOS_DATABASE_PASSWORD" <<'SQL'
SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
    :'app_user',
    :'app_password'
) \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'app_user') \gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'app_user') \gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
    :'admin_user',
    :'app_user'
) \gexec
SQL
