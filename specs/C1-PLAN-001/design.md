# Diseño — C1-PLAN-001

## Límite de autoridad

El incremento produce documentos internos, protocolos, registros de evidencia y rutinas de dirección. No ejecuta actividades de campo, no contacta personas, no publica contenido y no compromete recursos.

## Modelo de información

Toda entrada se clasifica como una de:

- fuente oficial;
- investigación de campaña;
- reporte del usuario pendiente de verificación;
- percepción agregada;
- hipótesis;
- desconocido.

La asistencia a una actividad, una visualización de video o una conversación comunitaria nunca se interpreta como apoyo electoral.

## Flujo

```text
inventario
→ clasificación de evidencia
→ problema municipal
→ viabilidad y competencia
→ escucha consentida
→ piloto interno aprobado
→ medición agregada
→ brief de decisión humana
```

## DeerFlow

La referencia a DeerFlow es una propuesta de adaptador de ejecución para investigación paralela. No es dependencia de runtime y no modifica el Graph Harness. Cualquier integración futura necesita especificación independiente, revisión de seguridad y aprobación humana.

## Evidencia local

Los paths `/Volumes/SSD/...` no son accesibles desde Cloud Sandbox. El manifiesto de incorporación define cómo adjuntar, clasificar, escanear y versionar esos materiales sin afirmar acceso inexistente.

## Riesgos

- instrumentalización de mujeres o deporte;
- confundir asistencia con apoyo;
- registrar datos personales innecesarios;
- mezclar servicio o entrega de recursos con persuasión;
- presentar un borrador interno como decisión pública;
- importar archivos locales con secretos o derechos no aclarados.

## Verificación

- revisión semántica de límites;
- `git diff --check`;
- `make program-verify`;
- `make secret-scan-worktree`;
- suite completa si el merge con `main` modifica contratos ejecutables;
- CI exact-head y revisión de PR.
