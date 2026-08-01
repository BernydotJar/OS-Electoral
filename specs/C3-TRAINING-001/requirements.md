# C3-TRAINING-001 Requirements

## Summary

Add a governed, role-aware and bilingual Training Academy baseline for CampaignOS. The academy must turn approved internal operating guidance into clear learning paths, short lessons, bounded knowledge checks and attributable completion receipts without creating application authority, professional accreditation, employee scoring or political targeting capability.

This is a SHIP-mode product increment. It closes only the repository-level `training-academy` baseline. Live learning providers, customer-authored public courses, video hosting, professional certification, managed environments and production acceptance remain separate gates.

## Product Lens

The user-provided Campol source and the existing evaluation in `docs/testing/c3-front-011-campol-consultant-evaluation.md` emphasize a practical sequence: investigate before acting, turn findings into strategy, organize accountable work, communicate after preparation, and measure results. CampaignOS may use that sequence to organize learning and next actions.

CampaignOS must not adopt the source's person-level voter databases, individualized vote-preference checks, persuasion scoring or microtargeting. Training content must remain aggregate, lawful, evidence-based and separated from external campaign execution.

## Mode

SHIP.

## Acceptance Criteria

- [ ] A strict versioned catalog defines approved modules, locales, owners, review state, learning objectives, source references, lesson order, bounded assessments and content digests.
- [ ] Spanish and English module versions have deterministic parity for structure, objectives, assessment keys and governance metadata.
- [ ] Initial learning paths cover research-first planning, candidate evidence and risk, team/RACI operations, strategy and decisions, daily War Room/measurement, and safety/privacy governance.
- [ ] Learning paths can be recommended by existing campaign role blueprint without turning a role label or recommendation into application authority.
- [ ] Authorized users can assign an approved learning path to a principal in the same tenant/campaign; self-view and completion use exact tenant, campaign, principal, action, resource and purpose checks.
- [ ] Starting, answering and completing a module are idempotent, version-aware and attributable; stale catalog or assignment versions fail closed.
- [ ] Knowledge checks are bounded, deterministic and educational. They record pass/fail and explanation visibility, not comparative rankings, persuasion traits, productivity scores or behavioral profiles.
- [ ] Completion receipts record only minimal tenant/campaign/principal references, module/version, assignment, result, timestamps, catalog digest and audit linkage.
- [ ] Completion, assessment result or learning-path recommendation has `authority_effect=NONE` and never creates memberships, grants, invitations, campaign activation, publication, spending or contact permission.
- [ ] Content must be repository-owned or explicitly approved, source-attributed and reviewable. Arbitrary remote HTML, scripts, embeds and live AI-generated lessons are prohibited.
- [ ] Retired or superseded module versions remain readable through historical receipts but cannot receive new assignments.
- [ ] The team workspace can project required, in-progress and completed learning without automatically changing access recommendations or human staffing acceptance.
- [ ] The frontend provides a plain-language ES/EN academy surface with current path, next lesson, progress, assessment feedback, governance disclosure and accessible keyboard/mobile/reduced-motion behavior.
- [ ] RLS, append-only audit, idempotency, version conflict, BOLA, cross-tenant isolation, secret scanning, supply chain and complete repository gates remain green.

## Bounded Product Envelope

- maximum 50 approved modules in the repository catalog for this increment;
- maximum 20 lessons and 20 assessment questions per module;
- maximum 25 active assignments per principal and 200 per campaign;
- maximum 10 attempts per module assignment, with no hidden adaptive scoring;
- no arbitrary user-authored HTML, executable content, file upload, remote media fetch or live provider;
- no public certificate, credential, badge marketplace or professional-accreditation claim;
- no automated permission, staffing, disciplinary or campaign decision from learning data;
- no voter, supporter, volunteer or citizen profiling.

## Initial Learning Paths

1. `research_foundations`: research before communication or spending; evidence quality; aggregate and lawful research boundaries.
2. `candidate_evidence_and_risk`: statements, independent evidence, contradictions, development and reputational risk.
3. `team_accountability`: role purpose, RACI, vacancies, capacity, onboarding, well-being and escalation.
4. `strategy_and_decisions`: falsifiable hypotheses, options, objectives, evidence, red-team review and human receipts.
5. `war_room_and_measurement`: daily operating brief, measurable objectives, check-ins, indicators, learning and adjustment.
6. `safety_privacy_and_authority`: authorization, data minimization, prohibited targeting, external-effect gates and incident escalation.

## Non-Goals

- Teaching individualized persuasion, turnout manipulation, voter scoring, opposition harassment or disinformation.
- Importing or reproducing a third-party course, transcript or proprietary slide deck.
- Live AI tutoring, adaptive psychological assessment, proctoring, biometrics or surveillance.
- Automatic grants, role assignment, hiring, discipline, performance management or campaign activation.
- Public content publication, citizen contact, paid media, field mobilization or spending.
- Hosting videos, SCORM/xAPI/LTI integration, external LMS synchronization or paid content services.
- Professional accreditation, legal/compliance certification or regulatory training acceptance.
- Provisioning cloud storage, CDN, queues, analytics or managed learning infrastructure.

## MVP Criteria

- Strict bilingual content and learning-path contracts.
- Repository-owned initial catalog with source/governance metadata.
- Durable tenant/campaign assignment, attempt and completion records with RLS and append-only audit.
- Exact authorized API and deterministic assessments.
- ES/EN accessible academy journey integrated with the team chapter.
- Complete local/PostgreSQL/browser tests and sanitized retained evidence.

## SHIP Criteria

- security: exact authorization, BOLA isolation, RLS, idempotency, version checks and content sanitization pass;
- data correctness: catalog digest, assignment lifecycle, attempt limits, completion receipts and retired-version behavior are deterministic;
- privacy: minimal learner records, no person scoring, no remote tracking and no authority effect;
- failure modes: stale versions, unknown/retired modules, duplicate submission, cross-tenant references, malformed answers and audit failure fail closed;
- accessibility/i18n: ES/EN parity, keyboard, mobile, reduced motion and WCAG checks pass;
- operations: content approval, versioning, retirement, correction and rollback/forward-fix procedures are documented;
- release: producer, critic/red-team, fixer, independent verifier and exact-head evidence are persisted while production remains `BLOCKED`.
