# Training Academy

Training Academy is an internal CampaignOS learning surface for campaign teams. It turns approved, versioned product guidance into short bilingual learning paths, structured lessons, bounded knowledge checks, and attributable completion receipts.

The academy supports preparation before execution. It does not publish content, contact citizens, spend money, activate campaign operations, or grant application authority.

## What the user sees

The academy appears inside the **Equipo** chapter before compact training/access/audit metadata. A permitted learner can see:

- an assigned learning path and its purpose;
- completed modules and the next lesson;
- learning objectives and reviewed lesson text;
- repository source references;
- one bounded knowledge check per initial module;
- educational feedback after an attempt;
- internal completion receipts.

A permitted manager can assign an approved path to an active principal in the same tenant and campaign. In the non-production demo, the surface is explicitly read-only.

## Initial learning paths

The repository-owned `1.0.0` catalog contains six paths:

1. research before action;
2. candidate evidence and risk;
3. team accountability;
4. strategy and human decisions;
5. War Room measurement and learning;
6. safety, privacy, and authority.

Each module has one Spanish and one English version with the same stable lesson, objective, question, option, and answer identifiers. Text can differ by language; structure and answer keys cannot drift.

## Content governance

Training content is code-reviewed and immutable at runtime for this increment. The catalog rejects:

- unknown fields;
- raw HTML, scripts, iframes, remote media, and remote URLs;
- undeclared repository sources;
- locale structure or answer-key drift;
- unknown module references;
- any authority or external effect other than `NONE`.

The frontend receives questions and options but never answer keys. It renders structured text through normal React components and never uses raw HTML.

## Educational assessment

Knowledge checks are deterministic and bounded:

- one to twenty questions per module;
- two to six reviewed options per question;
- at most ten attempts per assigned module;
- exact module version and catalog digest required;
- stale assignment or progress versions fail closed;
- pass/fail and explanations only.

Training does not rank people, infer traits, assess job performance, or create a behavioral profile. Raw answers are not retained in audit events or completion receipts.

## Authority boundary

Learning paths are recommendations. Assignment, attempt, pass/fail, and completion all have `authority_effect=NONE` and `external_effects=NONE`.

Completion never creates or changes:

- memberships;
- roles;
- permission grants;
- access recommendations;
- staffing acceptance;
- campaign activation;
- publication, spending, contact, or mobilization authority.

An internal completion receipt is not a professional, legal, regulatory, or academic accreditation.

## Data minimization

The durable learner record contains only the tenant/campaign/principal scope, approved path/module versions, bounded attempt count, pass/fail state, timestamps, catalog digest, audit linkage, and append-only completion receipt. Free-text learner profiles, comparative scores, psychological attributes, and persuasion data are excluded.

## Product limits

This baseline intentionally excludes external LMS integration, video hosting, user-authored course HTML, live AI tutoring, adaptive assessment, proctoring, biometrics, public certificates, paid content, and cloud learning infrastructure.
