# Candidate Brand and Reputation Workspace

C2-PROD-001 adds a tenant-scoped, read-only bounded aggregate for candidate identity, biography, purpose, values, attributes, proof points, perception gaps, behavioral consistency and reputation risks.

## Operating boundary

The workspace may organize evidence and prepare an internal assessment. It does not approve public positioning, produce political content, publish, contact citizens, activate paid media or mobilize field teams.

A candidate self-assessment is never verified evidence. A `VERIFIED` claim or attribute requires enabling `OFFICIAL_SOURCE` or `CAMPAIGN_RESEARCH` evidence from the same tenant, campaign and workspace. `PERCEPTION` evidence may document an aggregate perception gap but cannot independently verify an attribute.

## Run

```bash
python3 scripts/campaign/validate_c2_prod_001.py

python3 scripts/campaign/run_candidate_brand_assessment.py \
  --workspace campaigns/antigua-guatemala/workspace.json \
  --brand fixtures/candidate-brand/antigua-candidate-brand.json \
  --output artifacts/candidate-brand/antigua-brand-assessment.json
```

The CLI accepts repository-relative JSON paths, rejects traversal and symbolic links, and writes only below `artifacts/candidate-brand/`.

## Human approval

Brand approvals require `actor_type: HUMAN`, a role and one or more explicit `supports_sections` values. Section approval does not authorize public use. The aggregate cannot declare itself `APPROVED` unless all populated sections have human approvals, all core claims are verified and no CRITICAL/HIGH reputation risk remains open.

## Antigua operator state

The Antigua fixture is intentionally `SETUP_REQUIRED`. Identity and biography are `UNKNOWN`, purpose is a hypothesis under review, no attributes are inferred, and a HIGH evidence-gap risk blocks public use. The next safe action is a governed Candidate Identity Interview followed by evidence collection.

## Prohibited data and behavior

The model rejects psychological profiles, persuadability scores, voter profiles, voter IDs, microtargeting, sensitive targeting and manipulation scoring. No voter-level data belongs in this workspace.
