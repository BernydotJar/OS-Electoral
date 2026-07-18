# Integration Harness: Cross-Tenant Adversarial Checks

This document explains the design and scope of the adversarial integration test harness.

## Propósito
El propósito de este arnés es validar de forma integrada que los límites de seguridad de multitenencia, el modelo de control de acceso a operaciones sensibles (humano vs. máquina) y la integridad criptográfica de persistencia funcionen juntos como una arquitectura defensiva coherente.

## Escenarios de Ataque Probados

### 1. Fuga de Datos Transaccionales entre Tenientes
Verifica que un intento de inyectar identificadores ajenos en write intents o cargar estados fuera del ámbito autorizado por la Unit of Work falle de inmediato antes de alterar la persistencia in-memory.

### 2. Escalamiento de Privilegios de Agentes (Máquinas)
Asegura que un actor del tipo `AGENT` o `SYSTEM` que intente usurpar authority humana (para ejecutar compuertas como `APPROVE_POLITICAL`) sea rechazado inmediatamente por el validador estricto del adapter de persistencia.

### 3. Alteración Criptográfica Histórica
Comprueba que cualquier cambio arbitrario fuera de las transacciones sobre digests de payloads o hashes enlazados en el ledger histórico cause que el modelo de lectura observable reporte un estado `CORRUPTED`, activando alertas de gobernanza.
