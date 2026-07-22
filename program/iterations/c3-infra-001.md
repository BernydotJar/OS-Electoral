# C3-INFRA-001 — Terraform AWS plan-only baseline

- `branch`: `agent/c3-infra-001-plan-only-baseline`
- `base`: `agent/c3-ci-001-supply-chain-policy@e4c590389cf7cd8207c5e61eddef9a540767c929`
- `status`: `TESTED_LOCAL`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`
- `cost_authorization`: `PROHIBITED`

## Bounded objective

Create a reproducible Terraform baseline for the target AWS architecture and verify it entirely through formatting, initialization with remote backends disabled, provider mocks, plan tests and deterministic policy checks. No AWS credential, `terraform apply`, paid resource, DNS change, certificate request, image publication or deployment is authorized.

## Acceptance criteria

1. Terraform CLI and AWS provider versions are exact and lockfile-backed.
2. Remote state bootstrap defines a private versioned S3 bucket, customer-managed KMS key, TLS-only policy and S3 lockfile support.
3. Platform state uses a partial S3 backend with encryption and lockfile enabled; bucket/key/account values are supplied out-of-band.
4. Environment identity, region, CIDRs, image digests and retention settings are variables, never embedded secrets or account IDs.
5. VPC uses public load-balancer subnets and isolated private application/data subnets across at least two AZs.
6. Private runtime access uses explicit VPC endpoints; no NAT gateway is created by the baseline.
7. ECS Fargate tasks are non-root, read-only, non-privileged, log to encrypted CloudWatch groups and run with execute-command disabled.
8. ECR repositories use immutable tags, scan-on-push and lifecycle retention.
9. RDS PostgreSQL is private, encrypted, deletion-protected, backup-enabled and uses managed master credentials.
10. S3 application storage is private, versioned, encrypted and TLS-only.
11. IAM trust is service-scoped and no application role receives wildcard actions.
12. `terraform test` performs plan-only assertions through `mock_provider`; no AWS API is contacted.
13. Workflow/policy checks reject `apply`, auto-approve, local state commits, public databases/buckets, mutable provider versions and unsafe task settings.
14. CI adds a universal Terraform validate/plan-policy job pinned to immutable Action SHAs.
15. Live protected-main required checks and selected Actions policy are updated to include Terraform verification.

## Explicit non-goals

- no `terraform apply`, import, destroy or state mutation;
- no AWS account selection, IAM credential issuance or OIDC role creation;
- no hosted zone, ACM certificate, SES, Cognito, CloudFront or WAF activation;
- no ECS/RDS/S3/ECR resource creation;
- no cost estimate presented as an authorization;
- no production readiness claim.


## Local plan-only checkpoint — 2026-07-21

- Terraform `1.15.8` and AWS provider `6.55.0` are exact-pinned and checksum/lock backed.
- Bootstrap and platform roots pass format, backend-disabled init, validate and one mocked plan test each.
- Six adversarial policy tests reject mutation commands, mutable providers, public RDS, ECS Exec and local state.
- Desired CI policy contains nine universal checks; protected `main` still has eight, so enforcement is a human policy gate.
- Full repository regression passes 645 tests, 9 controlled skips, 90.95% coverage, 48 frontend tests and zero frontend vulnerabilities.
- PostgreSQL passes nine migration/RLS/concurrency slices twice through revision `20260721_0010`.
- No AWS credential, API call, remote state, apply, billable resource, deployment or external effect occurred.
