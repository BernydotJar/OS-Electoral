# ADR 001: Open-source-first application on AWS managed services

Status: **PLAN-ONLY BASELINE IMPLEMENTED; LIVE ENVIRONMENTS NOT AUTHORIZED**
Date: `2026-07-19`

## Context

CampaignOS needs portable application code and a supportable initial production platform. The team must avoid unnecessary proprietary coupling while using managed controls for database, identity, queues, encryption, observability, and container operations.

## Decision

Build the application from open-source frameworks and standard protocols, package it as OCI containers, and define the initial AWS runtime with Terraform. The target baseline is ECS Fargate, ECR, ALB, RDS PostgreSQL, S3, CloudFront, Cognito or another compatible OIDC provider, Secrets Manager, KMS, SQS, EventBridge, CloudWatch, WAF, Route 53, and ACM.

Application authorization, tenant semantics, domain models, provider interfaces, migrations, and export formats remain portable. AWS-specific behavior lives behind infrastructure or integration adapters.

## Consequences

- Managed services reduce undifferentiated operations but require cost, outage, IAM, quota, and regional-dependency analysis.
- Terraform state, credentials, and resources must be separated by environment.
- No service is “implemented” because it appears in this ADR; reviewed IaC and environment evidence are required.
- A material provider substitution requires compatibility tests and an ADR update.
- Production apply remains human-gated.


## Implementation note — 2026-07-21

Terraform now encodes the bounded ECS/ECR/ALB, VPC/endpoints, KMS/S3 and private RDS target with exact CLI/provider pins and mocked plan tests. Services remain disabled by default. The implementation is not an AWS deployment receipt and does not authorize remote state creation, credentials, apply or spending.
