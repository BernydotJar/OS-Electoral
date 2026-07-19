# Skill usage register

| Task | Skill or capability considered | Inputs | Outputs | Evidence | Result | Limitations |
|---|---|---|---|---|---|---|
| C3-FOUND-001A | Repository RTK instructions | `AGENTS.md`, complete `RTK.md` | Compressed read-only inspection commands | `rtk 0.34.1`; repository audit outputs | USED | RTK filters command output; it does not prove semantic completeness. |
| C3-FOUND-001A | Browser control | Live GitHub Pages verification need | None | Browser control was unavailable to this delegated agent; HTTP headers and GitHub deployment metadata were inspected with read-only CLI requests during the audit. | UNAVAILABLE | No authenticated browser interaction or visual browser assertion is claimed. |
| C3-FOUND-001A | Context7 | Current framework documentation | `program/context7-evidence.md` | Resolved IDs and retained documentation summaries with official PyPI cross-checks | EVIDENCE_RECORDED | Context7 CLI/MCP was not installed in the repository; the index lagged FastAPI PyPI. |
| C3-FOUND-001A | AutoSkills | AutoSkills `0.3.6` dry-run | `program/autoskills-review.md`, `skills-lock.json` | Three suggestions; dry-run reported nothing installed | NO_INSTALL | No per-skill manifest, hashes, paths or license evidence was retained. |
| C3-FOUND-001A | Farmtable | Program dependency and readiness semantics | Fallback task graph, ledger and program state | `program/task-graph.yaml`, `program/task-ledger.yaml`, `program/program-state.json` | FALLBACK_USED | Farmtable CLI/runtime was unavailable; no production dependency was introduced. |

No available artifact-generation or repository-specific governance skill matched this narrow program-ledger implementation. No skill was installed or invoked implicitly.
