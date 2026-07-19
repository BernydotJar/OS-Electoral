# AutoSkills dry-run review

## Decision

`NO_INSTALL`

AutoSkills was evaluated strictly as development tooling. The reviewed dry-run used `midudev/autoskills` version `0.3.6`, detected the agents `universal` and `kiro-cli`, proposed three frontend-oriented skills, and concluded that nothing was installed.

## Dry-run result

| Field | Observed value |
|---|---|
| Command mode | `--dry-run` |
| AutoSkills version | `0.3.6` |
| Detected agents | `universal`, `kiro-cli` |
| Suggestions | 3 |
| Install result | `nothing was installed` |

Suggestions reported by the dry-run:

1. `anthropics › frontend-design` — Frontend
2. `addyosmani › accessibility` — Frontend
3. `addyosmani › seo` — Frontend

## Review findings

The retained dry-run output did not expose, per suggested skill:

- a complete manifest;
- immutable content hashes;
- installation paths;
- transitive content or dependencies;
- license metadata;
- a prompt-injection assessment;
- provenance sufficient to reproduce the exact proposed payload.

AutoSkills itself is distributed under CC BY-NC 4.0. That license and the missing per-skill evidence require a separate commercial-use and redistribution review. No suggested content may enter CampaignOS runtime or commercial distributions based only on this dry-run.

## Risk decision

Installation is denied until all of the following are available and reviewed:

1. manifest and exact source revision;
2. cryptographic hashes for every installed file;
3. path and overwrite preview;
4. license for each proposed skill and embedded asset;
5. prompt-injection and supply-chain review;
6. compatibility with repository instructions;
7. an updated `skills-lock.json` approved by a human reviewer.

`skills-lock.json` therefore records zero installed skills and preserves the three uninstalled suggestions as review evidence only.
