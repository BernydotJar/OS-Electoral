SHELL := /bin/sh

UV ?= uv
ENV_FILE ?= $(if $(wildcard .env),.env,.env.example)
COMPOSE = docker compose --env-file $(ENV_FILE)

.DEFAULT_GOAL := help

.PHONY: help bootstrap dev test test-postgres lint format-check typecheck migrate e2e verify program-verify compose-config down logs ps worker-once

help: ## Show the available developer commands.
	@awk 'BEGIN {FS = ":.*## "; printf "CampaignOS developer commands:\n\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: compose-config ## Install locked Python dependencies and build/pull the local stack.
	@command -v $(UV) >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
	$(UV) sync --locked --all-groups
	$(COMPOSE) pull postgres s3mock mailpit
	$(COMPOSE) build api migrate

dev: compose-config ## Build and run the local stack with API hot reload.
	$(COMPOSE) up --build --remove-orphans

test: ## Run the complete locked pytest suite.
	$(UV) run --locked pytest -W error

test-postgres: ## Run isolated PostgreSQL migration and RLS tests (requires *_test URL).
	@test -n "$(CAMPAIGNOS_TEST_DATABASE_URL)" || { echo "CAMPAIGNOS_TEST_DATABASE_URL is required" >&2; exit 1; }
	CAMPAIGNOS_TEST_DATABASE_URL="$(CAMPAIGNOS_TEST_DATABASE_URL)" $(UV) run --locked pytest -W error -m postgres backend/tests/test_database.py

lint: ## Run Ruff against the maintained backend, migrations and tests.
	$(UV) run --locked ruff check backend

format-check: ## Verify Ruff formatting without rewriting files.
	$(UV) run --locked ruff format --check backend

typecheck: ## Run strict mypy checks for the CampaignOS package.
	$(UV) run --locked mypy

migrate: ## Upgrade an explicitly configured database to the reviewed Alembic head.
	@test -n "$(CAMPAIGNOS_DATABASE_URL)" || { echo "CAMPAIGNOS_DATABASE_URL is required" >&2; exit 1; }
	CAMPAIGNOS_DATABASE_URL="$(CAMPAIGNOS_DATABASE_URL)" $(UV) run --locked alembic upgrade head

e2e: compose-config ## Build an isolated stack and exercise every local service.
	ENV_FILE="$(ENV_FILE)" ./scripts/dev/e2e.sh

program-verify: ## Validate the machine-readable program truth and safety scanner.
	$(UV) run --locked python scripts/architecture/validate_program_state.py
	$(UV) run --locked python scripts/campaign/scan_c2_safety.py

verify: compose-config lint format-check typecheck test program-verify ## Validate all local quality gates.

compose-config: ## Validate the fully interpolated Compose model.
	@test -f "$(ENV_FILE)" || { echo "Missing ENV_FILE: $(ENV_FILE)" >&2; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required: https://docs.docker.com/get-docker/" >&2; exit 1; }
	@docker compose version >/dev/null
	$(COMPOSE) config --quiet

down: ## Stop the local stack while preserving named-volume data.
	$(COMPOSE) down --remove-orphans

logs: ## Follow local stack logs.
	$(COMPOSE) logs --follow --tail=100

ps: ## Show local stack service and health status.
	$(COMPOSE) ps

worker-once: ## Process one internal outbox pass for an explicit tenant UUID.
	@test -n "$(TENANT_ID)" || { echo "TENANT_ID is required" >&2; exit 2; }
	$(UV) run --locked campaignos-worker --once --tenant-id "$(TENANT_ID)"
