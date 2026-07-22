# C3-INFRA-001 plan-only evidence

Verified on 2026-07-21 from `agent/c3-infra-001-plan-only-baseline`, based on `agent/c3-ci-001-supply-chain-policy@e4c590389cf7cd8207c5e61eddef9a540767c929`.

```yaml
execution_mode: PLAN_ONLY_NO_APPLY
cost_authorization: PROHIBITED
production_status: BLOCKED
external_effects: NONE
terraform_cli: 1.15.8
aws_provider: 6.55.0
remote_backend: DISABLED_DURING_TESTS
aws_credentials: NOT_USED
aws_api_calls: NONE_BY_TERRAFORM_TESTS
```

## Implemented verification

- Exact Terraform CLI pin and official archive SHA-256 verification.
- Exact AWS provider constraints and lockfile checksums for both roots.
- Bootstrap `fmt`, backend-disabled init, validate and mock plan test.
- Platform `fmt`, backend-disabled init, validate and mock plan test.
- Six adversarial repository-policy tests covering mutation commands, mutable provider constraints, public RDS, ECS Exec and local state artifacts.
- Versioned CI check `Terraform plan-only policy` using no additional GitHub Action.
- Actionlint and CI policy verification with nine desired universal checks.
- Full repository regression: 645 passed, 9 controlled skips, 90.95% coverage, strict mypy over 63 source files.
- Frontend: 48 tests, lint/typecheck/build PASS and zero dependency vulnerabilities.
- PostgreSQL: nine migration/RLS/concurrency slices passed twice through revision `20260721_0010`.

## Defects found and corrected

1. ECS service scalar arguments were encoded as nested blocks, while `network_configuration` was encoded as an argument. Terraform validation rejected the configuration; the HCL forms were corrected.
2. A provider-derived IAM trust document was indeterminate under mocks. The trust policy is now deterministic `jsonencode` data scoped to `ecs-tasks.amazonaws.com`.
3. Provider-computed ECR values made policy assertions indeterminate under mocks. Shared immutable local policy values now configure both resources and test outputs.

## Security and architecture conclusions

- No static AWS credential, account ID or secret is committed.
- Backend configuration is partial and encrypted with S3 lockfile support.
- Application/data subnets have no default internet route and no NAT gateway.
- Only the ALB is modeled as internet-facing; tasks and RDS remain private.
- Fargate task definitions drop all Linux capabilities, use UID/GID `10001:10001`, read-only roots and no privilege.
- RDS is private, encrypted, deletion-protected, backup-enabled and uses AWS-managed master credentials.
- Application and state buckets block public access, require TLS and use KMS encryption.
- The stack creates zero ECS services by default.

## Residual limitations and blockers

- Protected `main` currently requires eight checks; adding the ninth Terraform check is a human-gated branch-protection change.
- No AWS account, role, credential, remote state, plan against a live provider or apply exists.
- No dev/staging/production runtime, smoke test, backup restore, observability, load, rollback or disaster-recovery evidence exists.
- No cost estimate is approval to spend.
- Production remains `BLOCKED` by the platform/environment finding, six historical failed runs and independent human gates.
