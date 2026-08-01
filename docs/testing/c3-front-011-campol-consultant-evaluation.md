# C3-FRONT-011 — Campol consultant functional evaluation

## Source and evaluation lens

Basis: the user-provided Spanish auto-transcript of “Cómo iniciar una campaña electoral — Ep. 1 — Podcast Campol”. This document paraphrases the source; it does not reproduce the transcript.

The speakers repeatedly organize campaign work into a practical sequence:

1. investigate before communicating or spending;
2. turn findings into strategy and planning;
3. define organization, roles and operating cadence;
4. communicate only after the earlier work exists;
5. measure results and adjust.

They also describe a common failure mode: candidates act before knowing what must be researched, who owns the work or how results will be measured.

## Evaluation as those consultants

### What already works

- CampaignOS has a staged journey rather than a content-first dashboard.
- Candidate evidence, team responsibilities, strategy and daily operations are separated.
- Human approval, evidence provenance and access boundaries are visible.
- The product can preserve research and organizational work before any external action.

### What would confuse a candidate

- Candidate chapter presented “Qué hacer ahora”, “Perfil y riesgos” and “Fuentes y evidencia” as equal destinations. A candidate must instead understand one profile: what is known, what is risky, what evidence supports it and what to do next.
- Chapter position was visually secondary even though sequence is central to the method.
- Campaign context allowed switching but did not clearly offer the first practical action: start another draft candidacy.
- Training/access/read-receipt metadata was too prominent for daily work.
- Several labels described system architecture rather than the decision a campaign team needs to make.

### Functional verdict before repair

`PARTIALLY_FUNCTIONAL_FOR_EXPERT_OPERATOR`

The app contained the correct governed capabilities, but an experienced consultant still had to explain the order and relationship between them. That is not sufficient for self-guided candidate use.

## Product changes required for a passing verdict

- one candidate profile with risk, evidence and next action together;
- visible “where you are / why it matters / what follows” on all five chapters;
- an authorized, clearly bounded “Nueva candidatura” entry point;
- plain-language labels;
- technical/audit metadata available but visually subordinate.

## Safety correction to the source

The transcript also discusses person-level “potential voter” databases, individualized vote preference checks and persuasion-oriented segments. CampaignOS does **not** adopt those practices. Any research supported by the product must remain aggregate, consented, purpose-limited and separated from contact execution. The application does not create voter profiles, persuasion scores or individualized targeting.
