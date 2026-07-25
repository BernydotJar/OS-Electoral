# C3-DEVEX-001 local port-collision hardening evidence

Date: `2026-07-24 America/Guatemala`

## Defect

The one-command functional journey loaded fixed loopback ports from
`.env.functional.example`. When another local PostgreSQL process already owned
`127.0.0.1:5432`, Docker Compose failed before migrations or API startup with:

```text
ports are not available: listen tcp4 127.0.0.1:5432: bind: address already in use
```

The same failure mode could affect the API, S3Mock, Mailpit or Next.js ports.
This is a developer-experience defect, not a database or application defect.

## Remediation

- `scripts/dev/resolve_local_ports.py` validates requested `NAME=PORT` values.
- Available configured ports are preserved.
- Occupied or duplicate ports are replaced with ephemeral loopback ports.
- All candidate sockets remain reserved until the complete set is selected, so
  one invocation cannot return duplicate ports.
- `scripts/dev/functional_frontend.sh` propagates the resolved ports to Docker
  Compose, the PostgreSQL seed URL, the API base URL and the Next.js CLI.
- The effective endpoints are printed before startup.
- `make functional-down` remains unchanged and preserves named volumes.

## Verification

- Focused port-resolution and functional-script tests: `10 passed`.
- Full locked Python suite: `708 passed`, `10 skipped`, `90.40%` coverage.
- Ruff lint and format: PASS.
- Strict mypy across 66 source files: PASS.
- POSIX shell syntax check: PASS.
- Frontend lint, typecheck, 60 tests, production build and npm audit: PASS with
  zero vulnerabilities.
- Supply-chain policy and program/security/release/eval validators: PASS.
- `git diff --check`: PASS.

The sandbox used for this implementation does not expose the Docker Compose or
Terraform CLIs. Exact-head hosted CI is therefore required to prove Compose
interpolation, container startup, migrations, PostgreSQL recovery, Terraform
plan-only policy and the browser-backed functional journey.

## Safety and release boundary

This change creates no infrastructure, deployment, publication, citizen
contact, political targeting, spending or other external campaign effect.
Production remains `BLOCKED` and the release decision remains `DENY_RELEASE`.
