# Zero-cost hosting and cloud-cost audit - 2026-08-11

## Decision

Use the repository's existing GitHub Pages workflow as the public marketing/demo surface. Do not create a new AWS, GCP, Vercel, or other paid runtime for this milestone.

Public static surfaces after the approved Pages publish:

- marketing: `/OS-Electoral/marketing/`
- existing static product demo: `/OS-Electoral/`

The Pages workflow remains manual, main-only, and classified `DEMO_NON_PRODUCTION`. This does not change CampaignOS production status or authorize a production deployment.

## AWS audit

Authenticated profile available for inspection:

- profile: `constructhub-dev`
- account: `379632383616`

Other configured AWS profiles could not be inspected because their sessions/tokens were expired or unavailable. No credentials or token values were captured.

Cost Explorer showed August charges historically associated mainly with ELB, RDS, and VPC in `us-east-1`, plus a small S3 amount in `us-east-2`. A targeted live inventory found no current RDS instances, ELBv2 load balancers, NAT gateways, Elastic IPs, VPC endpoints, Secrets Manager secrets, ECR repositories, ECS clusters/services, or S3 buckets in the accessible account. A second `us-east-2` inventory also found no RDS, ELB, NAT, EIP, or S3 resources.

Daily cost from 2026-08-07 through 2026-08-11 showed only small S3 charges, approximately USD 0.005/day before the partial current day, while the live bucket inventory was empty. This is consistent with historical/lagged billing or recently removed storage activity; it is not evidence of a currently identifiable resource that can safely be deleted.

**Action taken:** no AWS deletion was issued because no live billable CampaignOS resource was identified. Deleting unrelated account resources without identification would be unsafe.

## GCP audit

`gcloud` is not installed/authenticated in the persistent sandbox. Therefore no GCP project or resource inventory can be verified from this environment and no deletion claim is made.

## Cost-control boundary

- No new paid cloud resources are authorized for the marketing milestone.
- Static marketing must use GitHub Pages already configured for the repository.
- Production remains `BLOCKED` and release remains `DENY_RELEASE`.
- Future managed staging/production infrastructure requires a separate bounded-cost authorization and normal production gates.
