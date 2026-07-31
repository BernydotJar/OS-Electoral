# C3-FRONT-008R1 — QA command surface and local readiness repair

## Mode

SHIP localized repair.

## Trigger evidence

Human QA on the local functional environment reported two reproducible defects:

1. the dynamic frontend port was mistaken for the API port, so `/api/v1/ready` rendered the CampaignOS frontend 404 page;
2. the overview repeated a dominant active-mission hero before the campaign path, while chapter routes still devoted too much initial space to navigation instead of the requested workspace.

The same QA accepted guided setup, candidate workspace, bilingual behavior and responsive behavior as directionally correct and requested a more premium, interactive and non-generic command experience.

## Acceptance criteria

- [ ] The overview renders one restrained, interactive campaign command surface and no separate active-mission hero.
- [ ] The current stage exposes status, expected outcome and one honest action without implying publication, spending, contact, mobilization or release authority.
- [ ] The complete five-stage path remains keyboard-operable through progressive disclosure.
- [ ] Chapter routes render a compact command bar followed immediately by exactly one requested workspace.
- [ ] Previous, next, overview, browser history and locale changes preserve chapter context.
- [ ] The frontend port serves `/api/v1/ready` as a same-origin, sanitized proxy to the configured backend readiness endpoint.
- [ ] `make functional-dev` prints unambiguous frontend, backend, readiness and Mailpit URLs when ports are reassigned.
- [ ] Desktop, mobile, ES/EN, reduced motion and WCAG 2.2 AA automated review pass with no horizontal overflow.
- [ ] Candidate workspace receives an explicit evaluator report for use by a United States campaign strategist, separating usable capability from jurisdiction-specific production gaps.
- [ ] No third-party media, generated campaign imagery, new paid service, live provider, external political effect or production-capacity claim is introduced.

## Non-goals

- Personal work projections, voter-file integration, political targeting or individual scoring.
- United States federal, state or local compliance automation.
- Production identity, deployment, infrastructure provisioning or load certification.
- Campaign data import from inaccessible local disk paths.
- Image or video generation merely to decorate the interface.

## Human approval

The product owner explicitly directed continued Graph Harness execution, premium frontend repair and evaluation of the reported QA findings. This authorizes the bounded SHIP repair only; production deployment and political external effects remain blocked.
