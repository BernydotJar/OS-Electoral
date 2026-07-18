# Bounded Context: Read-Only Application Service Contracts

This document defines the query contracts and facade interfaces exposed by the CampaignOS application layer.

## Propósito
El propósito de este contexto es exponer un punto de acceso unificado y de solo lectura para consultar los resúmenes y estados agregados de Campaign Workspace, Candidate Brand, Approval Ledger, Daily Operations y Persistence Stores.

## Componentes

### ReadOnlyApplicationService
El servicio `ReadOnlyApplicationService` encapsula las consultas complejas y asegura que todas las llamadas de lectura pasen por controles estrictos de seguridad e integridad:
- **Aislamiento Multitenant**: Valida que los parámetros de consulta `tenant_id`, `campaign_id` y `workspace_id` tengan el formato correcto (`SAFE_ID`) y coincidan exactamente con los metadatos almacenados en los agregados de dominio correspondientes.
- **Resúmenes Simplificados**:
  - `get_workspace_summary(...)`: Retorna el estado actual, el número de objetivos políticos y la lista consolidada de estados para todas las compuertas estratégicas.
  - `get_candidate_brand_status(...)`: Expone el estado del branding y la validación de reclamos.
  - `get_pending_approvals(...)`: Devuelve la bandeja de entrada consolidada de aprobaciones pendientes de acción humana.
  - `get_daily_workflow_timeline(...)`: Ofrece métricas rápidas de operaciones diarias, blockers activos y reuniones programadas.
  - `get_audit_integrity_status(...)`: Expone el resultado del análisis criptográfico del ledger.
