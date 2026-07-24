SHELL := /bin/sh

UV ?= uv
TERRAFORM ?= terraform
RECOVERY_CLIENT_IMAGE ?= postgres:18.3-alpine3.23@sha256:54451ecb8ab38c24c3ec123f2fd501303a3a1856a5c66e98cecf2460d5e1e9d7
RECOVERY_OUTPUT_DIR ?= artifacts/c3-obs-001
RECOVERY_TARGET_DATABASE ?= campaignos_recovery_restore_test
ENV_FILE ?= $(if $(wildcard .env),.env,.env.example)
COMPOSE = docker compose --env-file $(ENV_FILE)

.DEFAULT_GOAL := help

.PHONY: help bootstrap dev functional-dev functional-down dev-seed test test-postgres lint format-check typecheck migrate e2e verify program-verify compose-config down logs ps worker-once frontend-install frontend-verify frontend-e2e frontend-functional-e2e frontend-image-verify secret-scan-worktree supply-chain-verify supply-chain-evidence github-security-verify terraform-verify security-verify recovery-verify

help: ## Show the available developer commands.
	@awk 'BEGIN {FS = ":.*## "; printf "CampaignOS developer commands:\n\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: compose-config ## Install locked Python dependencies and build/pull the local stack.
	@command -v $(UV) >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
	$(UV) sync --locked --all-groups
	$(COMPOSE) pull postgres s3mock mailpit
	$(COMPOSE) build api migrate

dev: compose-config ## Build and run the local stack with API hot reload.
	$(COMPOSE) up --build --remove-orphans

functional-dev: frontend-install ## Run the API-backed local onboarding journey.
	./scripts/dev/functional_frontend.sh

functional-down: ## Stop the local functional stack and preserve its named volumes.
	docker compose --env-file .env.functional.example down --remove-orphans

dev-seed: ## Seed the bounded localhost operator and exact guided-intake grants.
	$(UV) run --locked python scripts/dev/seed_local_operator.py --database-url "$${CAMPAIGNOS_ADMIN_DATABASE_URL:-postgresql+psycopg://campaignos_admin:campaignos_admin_dev_only@127.0.0.1:5432/campaignos}"

test: ## Run the complete locked pytest suite with the enforced coverage floor.
	$(UV) run --locked pytest -W error --cov=campaignos --cov-report=term-missing --cov-fail-under=90

test-postgres: ## Run isolated PostgreSQL migration and RLS tests (requires *_test URL).
	@test -n "$(CAMPAIGNOS_TEST_DATABASE_URL)" || { echo "CAMPAIGNOS_TEST_DATABASE_URL is required" >&2; exit 1; }
	CAMPAIGNOS_TEST_DATABASE_URL="$(CAMPAIGNOS_TEST_DATABASE_URL)" $(UV) run --locked pytest -W error -m postgres backend/tests/test_database.py backend/tests/test_campaign_create_postgres.py backend/tests/test_identity_lifecycle_postgres.py backend/tests/test_guided_intake_postgres.py backend/tests/test_candidate_workspace_postgres.py backend/tests/test_team_workspace_postgres.py backend/tests/test_campaign_operations_postgres.py backend/tests/test_strategy_workspace_postgres.py backend/tests/test_agent_run_postgres.py backend/tests/test_security_postgres.py

lint: ## Run Ruff against the maintained backend, migrations and tests.
	$(UV) run --locked ruff check backend

format-check: ## Verify Ruff formatting without rewriting files.
	$(UV) run --locked ruff format --check backend

typecheck: ## Run strict mypy checks for the CampaignOS package.
	$(UV) run --locked mypy

frontend-install: ## Install the exact frontend dependency graph.
	@command -v npm >/dev/null 2>&1 || { echo "npm is required" >&2; exit 1; }
	cd frontend && npm ci

frontend-verify: frontend-install ## Lint, type-check, test, build and audit the dynamic frontend.
	cd frontend && CAMPAIGNOS_FRONTEND_MODE=demo_read_only CAMPAIGNOS_FRONTEND_ENVIRONMENT=test NEXT_TELEMETRY_DISABLED=1 npm run verify

frontend-e2e: ## Review the production frontend build in Chromium.
	./scripts/frontend/e2e_dynamic_shell.sh

frontend-functional-e2e: ## Exercise the real PostgreSQL/API-backed onboarding journey.
	./scripts/frontend/e2e_functional_onboarding.sh

frontend-image-verify: ## Build and smoke-test the frontend image with daemonless Buildah.
	./scripts/frontend/verify_frontend_image_buildah.sh

secret-scan-worktree: ## Scan tracked and non-ignored worktree files for secrets.
	./scripts/security/scan_effective_worktree.sh

supply-chain-verify: ## Enforce pinned CI policy and generate deterministic evidence in a temporary directory.
	@tmp_dir=$$(mktemp -d); trap 'rm -rf "$$tmp_dir"' EXIT; \
		$(UV) run --locked python scripts/ci/verify_ci_policy.py --report "$$tmp_dir/ci-policy-report.json"; \
		$(UV) run --locked python scripts/ci/generate_supply_chain_evidence.py --output-dir "$$tmp_dir"; \
		test -s "$$tmp_dir/cyclonedx-sbom.json"; \
		test -s "$$tmp_dir/provenance.intoto.json"; \
		test -s "$$tmp_dir/SHA256SUMS"

supply-chain-evidence: ## Generate reviewable unsigned SBOM and provenance artifacts.
	rm -rf artifacts/supply-chain
	$(UV) run --locked python scripts/ci/verify_ci_policy.py --report artifacts/supply-chain/ci-policy-report.json
	$(UV) run --locked python scripts/ci/generate_supply_chain_evidence.py --output-dir artifacts/supply-chain

github-security-verify: ## Compare live GitHub controls with the versioned repository policy.
	$(UV) run --locked python scripts/ci/verify_github_security_settings.py --report artifacts/supply-chain/github-security-report.json

security-verify: ## Validate data policy and append-only security declarations.
	$(UV) run --locked python scripts/security/verify_security_policy.py

recovery-verify: ## Back up PostgreSQL and prove an isolated exact restore.
	@test -n "$$CAMPAIGNOS_RECOVERY_DATABASE_URL" || { echo "CAMPAIGNOS_RECOVERY_DATABASE_URL is required" >&2; exit 1; }
	$(UV) run --locked python scripts/operations/verify_postgres_recovery.py \
		--database-url "$$CAMPAIGNOS_RECOVERY_DATABASE_URL" \
		--output-dir "$(RECOVERY_OUTPUT_DIR)" \
		--target-database "$(RECOVERY_TARGET_DATABASE)" \
		--client-image "$(RECOVERY_CLIENT_IMAGE)"

terraform-verify: ## Validate the exact plan-only Terraform baseline without AWS credentials or remote state.
	@command -v $(TERRAFORM) >/dev/null 2>&1 || { echo "Terraform is required" >&2; exit 1; }
	@$(TERRAFORM) version | head -n 1 | grep -Fx "Terraform v$$(cat .terraform-version)"
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) fmt -check -recursive infra/terraform
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/bootstrap init -backend=false -lockfile=readonly -input=false
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/bootstrap validate
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/bootstrap test -no-color
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/stacks/platform init -backend=false -lockfile=readonly -input=false
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/stacks/platform validate
	TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true $(TERRAFORM) -chdir=infra/terraform/stacks/platform test -no-color
	$(UV) run --locked python scripts/infra/verify_terraform_policy.py

migrate: ## Upgrade an explicitly configured database to the reviewed Alembic head.
	@test -n "$(CAMPAIGNOS_DATABASE_URL)" || { echo "CAMPAIGNOS_DATABASE_URL is required" >&2; exit 1; }
	CAMPAIGNOS_DATABASE_URL="$(CAMPAIGNOS_DATABASE_URL)" $(UV) run --locked alembic upgrade head

e2e: compose-config ## Build an isolated stack and exercise every local service.
	ENV_FILE="$(ENV_FILE)" ./scripts/dev/e2e.sh

program-verify: security-verify ## Validate machine-readable program truth, release readiness, required evals and safety.
	$(UV) run --locked python scripts/architecture/validate_program_state.py
	$(UV) run --locked python scripts/release/validate_release_readiness.py
	$(UV) run --locked python scripts/architecture/validate_eval_catalog.py
	$(UV) run --locked python scripts/campaign/scan_c2_safety.py

verify: compose-config supply-chain-verify terraform-verify lint format-check typecheck test frontend-verify program-verify ## Validate all local quality gates.

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
