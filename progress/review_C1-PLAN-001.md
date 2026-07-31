# Revisión SHIP — C1-PLAN-001

## Producer

La rama aporta un sistema coherente de planeación, evidencia y cadencia operativa. La documentación es utilizable para dirección de campaña municipal sin depender de un orquestador externo.

## Critic / Red Team

Veredicto inicial: `CHANGES_REQUIRED`.

Problemas encontrados:

1. lenguaje de segmento y concentración podía derivar hacia targeting;
2. “contactos” no distinguía inventario documental de datos personales;
3. métricas de retorno podían confundirse con apoyo;
4. actividades reportadas por el usuario carecían de clasificación de verificación;
5. paths locales podían inducir una falsa afirmación de acceso.

## Fixer

Se aplicó reparación localizada mediante problemas públicos, datos agregados, consentimiento, minimización, registro `USER_REPORTED`, manifiesto de fuentes locales y límites explícitos para DeerFlow.

## Independent verifier

Estado actual: `PASS_FOR_EXACT_HEAD_CI`.

La revisión independiente debe confirmar:

- ausencia de targeting o perfiles individuales;
- no inferencia de apoyo;
- gates externos cerrados;
- validadores y CI verdes;
- documentación consistente con CampaignOS y Graph Harness.

## Release gate

`DENY_RELEASE`. Este incremento autoriza únicamente planeación e investigación interna. No autoriza publicación, pauta, gasto, contacto, movilización ni producción.
