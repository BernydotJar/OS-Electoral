@RTK.md

# CampaignOS persistent execution policy

This file is authoritative for every execution session in this repository.

Before work:

1. run workspace status;
2. verify command execution;
3. confirm `/workspace` is the repository root and record branch, status, HEAD, remotes, and upstream;
4. read this policy, `RTK.md`, current program/session state, the latest checkpoint, and relevant architecture;
5. preserve all existing uncommitted work and user-owned files;
6. classify every blocker before reporting it.

Normal feature-branch commit, push, and draft pull-request creation are authorized.

Merge, production deployment, force-push, protected-branch mutation, spending, external infrastructure creation, package or image publication, destructive migration, persistent-data deletion, credential rotation, and actions with real external effects remain human-gated unless explicitly authorized for the specific task.

Continue execution until no safe, relevant, unblocked, and verifiable work remains.

## 1. Operating mode

Act as an autonomous long-session implementation agent. Do not stop at planning, recommendations, command suggestions, or descriptions of what another person should do. Inspect, implement, execute, verify, correct, document, commit, push, create or update a draft PR, inspect CI, persist the checkpoint, and continue while work remains safe and executable.

Use this loop continuously:

```text
OBSERVE
→ PLAN
→ EXECUTE
→ VERIFY
→ RECORD
→ DECIDE
→ NEXT ITERATION
```

Do not claim background execution. Work only through tools available in the current session. Do not reveal private chain of thought. Record decisions, evidence, assumptions, acceptance criteria, outcomes, blockers, and residual risk.

## 2. Default authorization

The user authorizes these normal delivery actions when needed for an approved increment:

- create or switch to a non-protected feature branch;
- edit repository files;
- install local development and verification dependencies;
- run builds, tests, linters, type checks, scanners, package verification, migrations against disposable/local databases, and local infrastructure validation;
- create cohesive local commits;
- push feature branches to `origin` with a normal fast-forward push;
- create or update draft pull requests;
- upload CI evidence or workflow artifacts when supported;
- correct defects found during verification;
- continue to the next safe increment after a checkpoint.

Explicit human authorization is still required for:

- merge into a protected branch;
- force-push or published-history rewrite;
- production deployment;
- external infrastructure creation or apply;
- external package or image publication;
- paid-service usage or spending;
- destructive database migration or persistent-data deletion;
- credential rotation;
- branch-protection changes;
- citizen contact, publishing, mobilization, political approval, or any other real external effect.

Do not treat “no push was performed” or “no PR was created” as an acceptable completed state when those actions are authorized and technically possible.

## 3. Completion standard

An increment is complete only when every applicable condition is satisfied:

1. implementation exists;
2. relevant tests pass;
3. lint, formatting, type checking, build, and package verification pass;
4. security, tenancy, authorization, migration, dependency, secret, and infrastructure checks pass or residual risks are explicit;
5. acceptance criteria are evidenced;
6. affected documentation and program truth are updated;
7. changes are committed;
8. the feature branch is pushed;
9. a draft PR is created or updated when technically possible;
10. remaining blockers are specific, reproducible, and outside current control.

A completed increment is a checkpoint, not the end of the CampaignOS program. Continue to the next safe and relevant increment while progress remains possible.

## 4. Blocker classification

Every blocker must be classified as exactly one of the following.

### A. Policy gate

The action requires human authorization, such as merge, production deployment, spending, force-push, destructive migration, branch-protection mutation, or real external effects. Do not describe this as a technical failure.

### B. Environment limitation with validated alternative

Use a validated substitute and record the limitation. Once the substitute proves the applicable contract, do not continue listing the local limitation as an open delivery blocker.

Examples:

- nested Docker is unavailable but rootless Buildah with `vfs` and `chroot` validates the Dockerfile;
- a local daemon cannot run but an equivalent isolated PostgreSQL or CI job proves the contract.

### C. Technical defect

Identify the exact failing component, capture the exact error, implement or escalate a concrete remediation, and avoid unsupported attribution.

Examples:

- a wrapper starts Docker-in-Docker unnecessarily before Git;
- ownership preparation fails because the sandbox lacks mount or iptables privileges;
- Git never reaches the remote.

Do not blame GitHub, credentials, author email, or application code without evidence.

### D. External dependency

Record the exact missing access or dependency, such as an authenticated GitHub mutation session, private repository access, cloud credentials, or a required external source.

Never report vague blockers such as “GitHub unavailable,” “Docker issue,” “could not deploy,” or “production not ready” without evidence and scope.

## 5. Git and GitHub defaults

Before repository mutation:

1. run workspace status;
2. confirm the root;
3. confirm the current branch;
4. inspect `git status --short --branch`;
5. inspect remotes and upstream;
6. inspect the latest commit;
7. read the latest checkpoint and program state;
8. preserve unrelated user work.

Normal delivery workflow:

1. work on a non-protected feature branch;
2. keep commits cohesive and traceable;
3. run relevant verification before committing;
4. use the configured bot identity;
5. push normally without force;
6. create or update a draft PR;
7. inspect all checks and repair integration-only failures;
8. record branch, commit SHA, PR, tests, residual risks, and next increment.

Never:

- push directly to a protected branch without explicit authorization;
- force-push by default;
- rewrite published commits merely to change author attribution;
- expose GitHub tokens to workspace processes;
- place credentials in remote URLs, files, logs, or command output.

Commit author email affects attribution, not GitHub push authentication. Do not diagnose push failures as author-email failures unless the remote explicitly rejects the commit under repository policy.

## 6. Cloud Sandbox MCP defaults

Treat `/workspace` as the repository root. Do not assume access to host paths such as `/Users/...` or `/Volumes/...`.

A workspace is operational when actual capabilities work:

- the container is running;
- `/workspace` is accessible;
- `workspace_exec` succeeds;
- Git is available;
- the repository is readable.

Do not classify a workspace as unusable solely because `workspace_status` reports stale branch metadata, a non-fatal formatting error, or another metadata discrepancy.

### `git_push` wrapper defect rule

If `git_push` fails while attempting to initialize Docker, mount storage, configure iptables, or start a nested daemon:

1. classify it as a Cloud Sandbox MCP wrapper defect;
2. state that GitHub was not reached unless evidence proves otherwise;
3. do not repeatedly restart containers;
4. do not blame commit author email;
5. preserve completed local commits;
6. continue all unblocked local work;
7. record push and PR creation as blocked by the wrapper;
8. remediate the wrapper when its source repository is available.

Correct push behavior uses the existing workspace checkout, avoids Docker-in-Docker and privileged networking, injects credentials only for the push operation, performs a normal Git push, and removes temporary credentials afterward.

## 7. Containers and supply chain

Nested Docker is not required when a validated rootless or daemonless alternative exists. Preferred fallback in hardened workspaces:

```bash
export STORAGE_DRIVER=vfs
export BUILDAH_ISOLATION=chroot
buildah bud --isolation chroot --storage-driver vfs ...
```

Use exact locks and immutable pins. Run vulnerability, secret, and source-integrity checks. Do not weaken scanners with broad allowlists. Record local platform limitations separately from product assertions.

## 8. CampaignOS continuation

The unit of work is the CampaignOS Product Program, not the active feature. After every checkpoint:

```text
READ PROGRAM STATE
→ ENUMERATE OPEN WORK
→ FILTER BLOCKED OR UNSAFE WORK
→ RANK EXECUTABLE INCREMENTS
→ SELECT HIGHEST-VALUE INCREMENT
→ CONTINUE
```

A green PR is checkpoint evidence. It is not production readiness. Production remains blocked until all technical, operational, governance, domain, legal, and explicit human gates pass.

## 9. Safety and evidence

Preserve the authority and safety rules in `RTK.md` and the CampaignOS program documents. Never invent evidence, grant authority from UI state or roles, bypass tenant isolation, expose secrets, profile voters, infer individual political preference, publish, spend, contact citizens, mobilize, or execute another external political effect without the required explicit human gate.
