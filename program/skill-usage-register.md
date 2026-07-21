# Skill usage register

| Task | Skill or capability considered | Inputs | Outputs | Evidence | Result | Limitations |
|---|---|---|---|---|---|---|
| C3-FOUND-001A | Repository RTK instructions | `AGENTS.md`, complete `RTK.md` | Compressed read-only inspection commands | `rtk 0.34.1`; repository audit outputs | USED | RTK filters command output; it does not prove semantic completeness. |
| C3-FOUND-001A | Browser control | Live GitHub Pages verification need | None | Browser control was unavailable to this delegated agent; HTTP headers and GitHub deployment metadata were inspected with read-only CLI requests during the audit. | UNAVAILABLE | No authenticated browser interaction or visual browser assertion is claimed. |
| C3-FOUND-001A | Context7 | Current framework documentation | `program/context7-evidence.md` | Resolved IDs and retained documentation summaries with official PyPI cross-checks | EVIDENCE_RECORDED | Context7 CLI/MCP was not installed in the repository; the index lagged FastAPI PyPI. |
| C3-FOUND-001A | AutoSkills | AutoSkills `0.3.6` dry-run | `program/autoskills-review.md`, `skills-lock.json` | Three suggestions; dry-run reported nothing installed | NO_INSTALL | No per-skill manifest, hashes, paths or license evidence was retained. |
| C3-FOUND-001A | Farmtable | Program dependency and readiness semantics | Fallback task graph, ledger and program state | `program/task-graph.yaml`, `program/task-ledger.yaml`, `program/program-state.json` | FALLBACK_USED | Farmtable CLI/runtime was unavailable; no production dependency was introduced. |
| C3-RESUME-001 | AutoSkills `0.3.6` pinned package and dry-run | npm integrity metadata, packaged registry, repository technologies | Updated `program/autoskills-review.md` and `skills-lock.json`; zero installs | npm integrity/shasum, `--dry-run`, unchanged Git status | NO_INSTALL | Third-party skill payloads, licenses, destinations and prompt safety were not individually approved. |
| C3-RESUME-001 | Environment remediation | Debian 12 ARM64 sandbox; missing Compose v2, PostgreSQL and Gitleaks | Official Docker APT Compose plugin `5.3.1`, PostgreSQL `15.18`, checksum-verified Gitleaks `8.30.1` | Version commands, Compose config, PostgreSQL integration and secret scans | USED | Installed only inside the workstation container; nested Docker image extraction remains namespace-blocked. |
| C3-RESUME-001 | Farmtable-equivalent fallback | Program dependency and checkpoint state | Reconciled manifest, graph, ledger and iteration record | `make program-verify` | FALLBACK_USED | Farmtable runtime was unavailable; no production dependency was introduced. |

| C3-API-005 | Current framework documentation fallback | FastAPI, Pydantic and SQLAlchemy official documentation; pinned lockfile versions | Transaction/row-lock, dependency/response-model and validator decisions recorded in `program/context7-evidence.md` | Executable tests plus official-source record | FALLBACK_USED | Context7 was unavailable; no MCP retrieval was fabricated. |

No available artifact-generation or repository-specific governance skill matched this narrow program-ledger implementation. No skill was installed or invoked implicitly.
