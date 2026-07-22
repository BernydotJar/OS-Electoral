# CampaignOS Terraform plan-only operations

Status: **TESTED LOCALLY; NO APPLY AUTHORIZED**

This repository contains a reproducible Terraform baseline for the proposed CampaignOS AWS architecture. It is review and plan evidence only. It does not identify an AWS account, obtain credentials, create state, allocate resources, incur approved cost or authorize deployment.

## Safe verification

Use the exact CLI in `.terraform-version` and the locked AWS provider in each root:

```bash
make terraform-verify
```

The target performs only:

- recursive formatting checks;
- `terraform init -backend=false -lockfile=readonly`;
- `terraform validate`;
- `terraform test` with `mock_provider` and `command = plan`;
- deterministic repository policy checks.

`AWS_EC2_METADATA_DISABLED=true` is set, remote backends are disabled and no AWS credential is required. The policy checker rejects executable `apply`, `destroy`, `import`, state mutation, force-unlock and auto-approve commands.

## Roots

- `infra/terraform/bootstrap`: proposed private versioned S3 state bucket, customer-managed KMS key, TLS-only and encrypted-write bucket policy, and S3 lockfile metadata.
- `infra/terraform/stacks/platform`: partial S3 backend plus reusable security, network, runtime and data modules.

## Bounded design evidence

The platform mock plan verifies:

- public ALB subnets and isolated application/data subnets in at least two explicit AZs;
- no NAT gateway and six private AWS service endpoints;
- digest-only application images;
- non-root, read-only, non-privileged Fargate task definitions with ECS Exec disabled;
- immutable ECR tags and scan-on-push;
- private encrypted PostgreSQL with deletion protection, managed master credentials and backups configured;
- private versioned encrypted S3 application storage;
- services disabled by default;
- `production_status=BLOCKED` and `external_effects=NONE`.

## Human gates

The following remain prohibited unless separately authorized:

- selecting or creating an AWS account or role;
- issuing or using AWS credentials;
- creating Terraform backend resources;
- `terraform apply`, import, destroy or state mutation;
- requesting certificates or DNS changes;
- publishing images;
- enabling ECS services;
- creating RDS, S3, ECR, KMS, ALB, VPC or other billable resources;
- dev, staging or production deployment.

## What this does not prove

Mock plans do not prove AWS API compatibility, account quotas, regional availability, runtime connectivity, cost, IAM boundary behavior in a real account, migration safety, backup restoration, monitoring, load, rollback, disaster recovery or customer acceptance. Those remain separate environment and operations gates.
