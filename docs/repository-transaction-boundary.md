# Bounded Context: Repository Interfaces and Transaction Boundary

This document defines the tenant-scoped repository interfaces and transaction boundaries for CampaignOS.

## Propósito
El propósito de este contexto es desacoplar el dominio de la persistencia de datos mediante el patrón Repository, e implementar un gestor de transacciones utilizando el patrón Unit of Work (UOW). Esto asegura atomicidad y consistencia en los cambios a través de múltiples agregados de dominio.

## Patrones Implementados

### 1. Repository Pattern
Se definen interfaces abstractas y adaptadores en memoria para las raíces de agregación:
- `WorkspaceRepository`: Operaciones sobre Campaign Workspaces.
- `CandidateBrandRepository`: Operaciones sobre Candidate Brand context.
- `ApprovalLedgerRepository`: Operaciones sobre el Approval Inbox y Ledger.
- `DailyWorkflowRepository`: Operaciones sobre Daily Operating Workflows.
- `PersistenceStoreRepository`: Operaciones sobre el almacén de eventos de persistencia.

Cada método `save` realiza validaciones automáticas invocando las funciones puras de validación de su respectivo dominio.

### 2. Unit of Work (Transaction Boundary)
El gestor `UnitOfWork` coordina transacciones de la siguiente manera:
- **Carga en memoria**: Los agregados modificados durante la transacción se cargan y registran.
- **Rollback automático**: En caso de excepción, restaura el estado original en memoria de todos los agregados cargados.
- **Commit atómico**: Al guardar los cambios, valida todas las reglas (incluyendo validaciones cruzadas entre Candidate Brand y Campaign Workspace), integra la planificación de escrituras (`plan_append` y `apply_in_memory`), actualiza los almacenes correspondientes y confirma la persistencia de forma atómica.
