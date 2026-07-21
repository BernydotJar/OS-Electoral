# AutoSkills dry-run review

## Decision

`NO_INSTALL`

AutoSkills was evaluated strictly as development tooling. The current review pinned `autoskills@0.3.6`, downloaded the npm tarball without running lifecycle scripts, verified npm integrity metadata, inspected its manifest and packaged registry, and then executed only `--dry-run`.

## Package evidence

| Field | Observed value |
|---|---|
| Package | `autoskills@0.3.6` |
| License | `CC-BY-NC-4.0` |
| npm integrity | `sha512-yNcj7Y/USPyJINxCWDaVVu17UaFokWgGtpX57PQUOA4i3s3vIDezaGZ/64KyMGb5CsLTvMb/L8WOX6R/ozhWIg==` |
| npm shasum | `490cda87dc275465e12fc694377ef3631b6fd138` |
| Runtime dependencies | none declared |
| Lifecycle scripts | no `preinstall`, `install`, or `postinstall` script |
| CLI entrypoint | `index.mjs` |
| Dry-run repository mutation | none |

The package includes a generated skill registry with source coordinates, file lists, hashes, and security-review summaries. That package-level evidence does not by itself prove the license, exact fetched revision, final installation path, or prompt safety of every third-party skill payload that the CLI could later retrieve.

## Dry-run result

The pinned command detected Bash, Python, FastAPI, Pydantic, SQLAlchemy, and Pytest, selected the `universal` agent, proposed eleven skills, and reported `--dry-run: nothing was installed`.

Suggestions reported:

1. `wshobson › bash-defensive-patterns`
2. `inferen-sh › python-executor` — registry security warning present
3. `wshobson › python-testing-patterns`
4. `wshobson › fastapi-templates`
5. `mindrally › fastapi-python`
6. `bobmatnyc › pydantic`
7. `bobmatnyc › sqlalchemy`
8. `wispbit-ai › sqlalchemy-alembic-expert-best-practices-code-review`
9. `anthropics › frontend-design`
10. `addyosmani › accessibility`
11. `addyosmani › seo`

## Review findings

- The AutoSkills package itself is distributed under a non-commercial Creative Commons license, requiring explicit legal review before incorporation into a commercial workflow or distribution.
- Suggested skills originate from multiple third-party repositories and are not npm dependencies of AutoSkills; their final payloads were not fetched or installed in this review.
- At least one suggestion is explicitly marked with a security warning, and the packaged registry contains examples of skills with broad execution or installation guidance.
- The dry-run output does not provide a complete path/overwrite preview or per-suggestion license summary.
- No suggested content is necessary to execute the current CampaignOS increment.

## Gate

Installation remains denied until the proposed payload has all of the following:

1. exact source revision and complete manifest;
2. cryptographic hashes for every installed file;
3. destination and overwrite preview;
4. license review for each skill and embedded asset;
5. prompt-injection, command-execution, and supply-chain review;
6. compatibility review against repository and political-safety instructions;
7. explicit human approval and an updated `skills-lock.json`.

`skills-lock.json` therefore records zero installed skills. The eleven suggestions are evidence only and are not trusted runtime instructions.
