# C1-FRONT-002 Long-Session Prompt

```text
/goal

Actúa como un autonomous long-session implementation agent.

Repository: BernydotJar/OS-Electoral
Local repository: /Users/eduardosacahui/Github-Repos/OS-Electoral
Base branch: main
Working branch: agent/c1-front-002-campaign-team-command-center
Specification: specs/C1-FRONT-002/
Execution prompt: prompts/long-session/C1-FRONT-002.md
Tracking issue: https://github.com/BernydotJar/OS-Electoral/issues/26
Draft PR: none at session start

## MISIÓN

Implementa un Campaign Team Command Center estático, accesible y read-only sobre el Evidence Control Room fusionado. Presenta al candidato como autoridad humana, al AI Campaign Chief of Staff como coordinador, diez departamentos gobernados, estados y blockers visibles, un detail drawer accesible y el Evidence Control Room como módulo interno.

## FUENTES DE VERDAD

1. Lee AGENTS.md y RTK.md.
2. Lee campaign/current-state.md, campaign/decision-log.md y research/evidence-register.md.
3. Lee feature_list.json y la spec completa.
4. Lee Issue #26.
5. Inspecciona main, rama, working tree, commits y PRs fusionados.
6. Lee el frontend actual antes de reemplazarlo.
7. Usa la memoria CampaignOS y premium-slate-ui solo como dirección; la spec es autoridad.
8. No repitas trabajo correcto.

## FILE BOUNDARIES

Respeta exactamente feature_list.json. No modifiques evidencia electoral, corpus, archivos territoriales, contenido político, media, deployment ni LA_muni_RAG.

## LOOP

0. Resume safely y construye task ledger.
1. Selecciona el incremento ejecutable de mayor valor.
2. Verifica la procedencia de cualquier estado representado.
3. Implementa archivos reales.
4. Valida inmediatamente con ambos validadores, revisión visual y git diff --check.
5. Actualiza Issue #26, crea commit enfocado y actualiza draft PR.
6. Si aparece un blocker, documenta condición exacta y continúa otros incrementos.

## AUTONOMÍA

Puedes leer, editar dentro de límites, ejecutar scripts, corregir errores, crear commits, push, draft PR, screenshots y comentarios. Detente antes de merge, deployment, dependencias no aprobadas, cambio de framework, modificación de evidencia, activación de agentes, apertura de gates o acciones irreversibles.

## DISEÑO

Si `premium-slate-ui` está disponible, úsala como skill de diseño opcional. No copies su SKILL.md ni introduzcas dependencia runtime. Si no está disponible, implementa la dirección obsidian-slate con CSS local, canvas/list parity, circular transitions progresivas, reduced-motion y accesibilidad.

## GATES CERRADOS

Segment selection, territorial ranking, targeting, persuasion scoring, sensitive profiling, paid media, mobilization, automatic publishing, promises, attacks, disinformation, surveillance and voter inference.

## PARADA

COMPLETED cuando toda la Definition of Done pasa. PARTIAL WITH DOCUMENTED BLOCKERS cuando todo lo ejecutable está completo. SAFETY STOP si continuar exige inventar estados, exponer datos o abrir un gate.

## RESPUESTA FINAL

Incluye estado, diagnóstico, artefactos, archivos, commits, PR/issue, validaciones, screenshots, blockers, condición de reanudación, siguiente incremento, USAGE AND COST REPORT y Scholar + PNL Learning Capsule. Nunca inventes telemetría exacta.
```
