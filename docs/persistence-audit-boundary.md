# Bounded Context: Persistence Intent and Audit boundary

This document defines the pure, tenant-scoped, append-only persistence intent and deterministic audit boundary for OS-Electoral.

## Propósito
El propósito de este contexto es definir un adaptador in-memory determinista para almacenar write intents firmados y audit events, sin interactuar directamente con una base de datos real o producir efectos colaterales (red, disco, etc.).

## Modelo de Datos
El adaptador maneja tres entidades fundamentales:
1. **Persistence Store**: Contiene el historial completo de eventos y claves de idempotencia.
2. **Write Intent**: La intención de escritura del dominio, que debe estar vinculada a una decisión de autorización.
3. **Audit Event**: El evento inmutable guardado en el store que forma la cadena criptográfica.

## Controles de Seguridad e Invariantes
- **Optimistic Concurrency**: Se valida que `expected_version` coincida con la versión del store y que `expected_previous_hash` coincida con `last_event_hash`.
- **Idempotency**: Claves repetidas se rechazan automáticamente (`replay rejection`).
- **Cryptographic Hash Chaining**: Cada evento contiene un `previous_hash` que lo enlaza al anterior, y el store valida que toda la secuencia sea coherente desde `GENESIS`.
- **Alignment**: Coincidencia exacta entre el tenant, campaign, workspace, principal, actor y recurso del write intent y de la decisión de autorización.
- **Privilege Separation**: Los actores no humanos (`AGENT` o `SYSTEM`) tienen prohibido ejecutar operaciones que requieran privilegios humanos (`HUMAN_ONLY`).

## Límites de Producción y Non-goals
- Este adaptador in-memory se utiliza únicamente como un test double para verificar la lógica de la frontera. No escribe al filesystem ni a una base de datos de producción (como PostgreSQL, Supabase o Firebase).
- Las decisiones y planes calculados son puros y libres de efectos externos.
