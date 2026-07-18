# Bounded Context: Audit Observability and Cryptographic Integrity Read Model

This document defines the queryable projection (CQRS Read Model) and integrity verifier for the CampaignOS persistence store.

## Propósito
El propósito de este contexto es proporcionar una interfaz de consulta y verificación sobre el historial inmutable de decisiones. Permite a auditores humanos y agentes autorizados verificar la validez del historial y consultar eventos específicos sin alterar el estado del sistema.

## Componentes

### 1. AuditIntegrityReadModel
- **Verificación de Integridad (`verify_integrity`)**:
  - Re-calcula el hash criptográfico de cada evento utilizando SHA-256.
  - Verifica la continuidad de la cadena de hashes (`previous_hash`).
  - Detecta cualquier brecha en la secuencia (`aggregate_version`), eliminación de eventos intermedios, duplicación de claves de idempotencia o duplicación de IDs de eventos.
  - Compara el hash del último evento con el `last_event_hash` del store.
- **Consultas Filtradas (`query`)**:
  - Permite filtrar eventos por actor principal (`principal_id`), recurso modificado (`resource_id`), tipo de recurso (`resource_type`) u operación ejecutada (`operation`).

### 2. CLI generate_audit_report
- Utilidad de línea de comandos para auditoría:
  ```bash
  python3 scripts/campaign/generate_audit_report.py --store <path> --output-dir <path>
  ```
- Genera un reporte detallado en Markdown que enumera metadatos del almacén, el estado de integridad y el log histórico completo de operaciones.
