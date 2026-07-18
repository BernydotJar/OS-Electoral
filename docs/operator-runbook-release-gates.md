# Operator Runbook and Release Gate Guide

This guide describes operational procedures, incident response protocols, and human release gates for CampaignOS.

## Gestión de Incidentes: Integración Corrupta (`CORRUPTED`)

Si la consulta del modelo de lectura observable o el reporte de auditoría de integridad retorna un estado de `CORRUPTED`:

### Procedimiento de Respuesta a Incidentes
1. **Identificación**: Ejecute el CLI de reportes de auditoría:
   ```bash
   python3 scripts/campaign/generate_audit_report.py \
     --store fixtures/persistence/antigua-store.json \
     --output artifacts/persistence-audit/incident-report.md
   ```
2. **Análisis**: Inspeccione el reporte generado. Busque la línea que indique el índice del evento corrupto, la causa (por ejemplo, hash mismatch o versión de agregado fuera de secuencia).
3. **Validación**: Compare el digest del payload y la firma criptográfica del evento reportado con la bitácora física o copias de seguridad de intents aprobados.
4. **Remediación**:
   - Detenga inmediatamente el procesamiento de nuevos intents de escritura.
   - Restaure el archivo de persistencia (`store.json`) al último estado hash-chained verificado y limpio.
   - Revoque y genere nuevas llaves de firma para los principales involucrados en la discrepancia.

---

## Compuertas de Lanzamiento y Transición (Release Gates)

CampaignOS opera bajo el principio de estricta separación de responsabilidades y veto humano.

### Checklist de Promoción de Candidatura
Para transicionar de la etapa `EXPLORATORY_PRE_CANDIDACY` a `OFFICIAL_CANDIDACY`:

- [ ] **Verificación de Identidad**: La identidad y biografía del candidato deben estar marcadas como `VERIFIED` en el Candidate Brand.
- [ ] **Riesgo Reputacional Cero**: No deben existir hallazgos (`findings`) de severidad CRITICAL o HIGH pendientes en el historial de marca.
- [ ] **Límites Financieros**: Los topes y asignaciones presupuestarias deben estar aprobados por firma física de los oficiales de finanzas del partido.
- [ ] **Compuertas Estratégicas**: Todas las compuertas de contenido político y posicionamiento público deben ser firmadas manualmente en el inbox.

---

## Compuertas Humanas de Veto
Las siguientes acciones **nunca** pueden ser ejecutadas de forma autónoma por agentes o scripts del sistema:

1. **MERGE_STACK**: Integración de cambios de código a la rama principal (`main`).
2. **DEPLOYMENT**: Despliegue de infraestructura o software en ambientes de producción.
3. **APPROVE_POSITIONING**: Definición de discursos o posturas del candidato.
4. **APPROVE_SPENDING**: Ejecución o autorización de transacciones financieras.
5. **ACTIVATE_PAID_MEDIA**: Activación de anuncios y pauta de medios.
6. **ACTIVATE_FIELD_MOBILIZATION**: Movilización física o logística de voluntarios y activistas.
7. **CONTACT_CITIZENS**: Contacto directo y recolección de firmas o datos de ciudadanos.
