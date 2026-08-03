# C3-FRONT-012 review

Review state: `REVIEWED_LOCAL`; complete repository gate passes.

## Producer

Reordered the exact-grant sidebar, moved readiness into chapter 1, separated candidate summary from candidate profile, removed specialist terminology and preserved evidence as a subordinate disclosure.

## Critic / red team

- no readiness link remains in the sidebar;
- preparation is the first chapter link after Resumen;
- candidate chapter contains neither Resumen de candidatura nor Qué hacer ahora;
- overview contains both candidate progress and Qué hacer ahora;
- exact campaign grant checks remain unchanged;
- ES/EN, mobile, keyboard, reduced motion, zero overflow and axe pass.

## Complete local gate

`make verify` passes with 821 Python tests, 12 controlled skips, 90.11% coverage and 145 frontend tests.

## Gate

Production remains blocked. No external effect, authority change or deployment is included.

## Hosted critic finding

The first hosted run failed closed because the reviewer expected the pre-change action label inside Candidatura. The repaired reviewer now proves that action guidance belongs to Resumen and is absent from Candidatura in both locales. The failed run remains retained as superseded evidence pending a repaired exact-head run.
