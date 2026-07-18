# Bounded Context: Evidence-Grounded Extraction and Citation Contracts

This document explains the design and interfaces of the claim extraction and verification contracts.

## Propósito
El propósito de este contexto es definir los contratos y la lógica necesaria para validar reclamos e hipótesis sobre los atributos de la marca del candidato o las metas de campaña contra el registro oficial de evidencias del espacio de trabajo (`workspace.json` evidence array).

## Componentes

### EvidenceGroundedExtractionService
Interfaz abstracta que define la firma para verificar reclamos contra una lista consolidada de evidencias de campaña.

### LocalExtractionEngine
Una implementación puramente determinista y local (offline) que evalúa los reclamos utilizando reglas heurísticas y análisis de términos clave sobre las descripciones y fuentes de la evidencia.
- **Detección de Contradicciones**: Identifica si la evidencia contiene negaciones explícitas (por ejemplo, "no corporate donations") ante afirmaciones del candidato.
- **Puntuación de Confianza**: Asigna puntuaciones fijas de confianza basadas en la exactitud y coincidencia del origen de la evidencia.
- **Sin Dependencias de Red**: Garantiza que las verificaciones se realicen sin necesidad de credenciales de modelos externos en entornos de testing o air-gapped.
