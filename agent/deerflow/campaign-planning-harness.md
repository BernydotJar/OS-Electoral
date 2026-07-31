# Harness DeerFlow para planeación de campaña

## Propósito

Usar DeerFlow como orquestador de investigación y producción interna, manteniendo autoridad humana y los gates de CampaignOS. DeerFlow aporta subagentes, memoria, sandbox y ciclos largos; CampaignOS conserva decisiones, aprobaciones, auditoría y límites de acción.

## Arquitectura propuesta

```text
Campaign Chief (humano)
  -> CampaignOS: mandato, gates, evidencia, decisiones
  -> DeerFlow Supervisor
       -> Agente de evidencia electoral
       -> Agente territorial
       -> Agente de mujeres y cuidados
       -> Agente de deporte comunitario
       -> Agente de política pública municipal
       -> Agente legal y cumplimiento
       -> Agente de narrativa y comprensión
       -> Agente evaluador adversarial
  -> Artifact Review
  -> Decisión humana
```

## Roles

### Supervisor

Descompone objetivos, asigna subagentes y consolida hallazgos. No aprueba ni publica.

### Evidencia electoral

Extrae fuentes, clasifica confiabilidad, detecta contradicciones y actualiza propuestas de registro.

### Territorio

Integra comunidades, centros, accesibilidad, demandas y brechas de información. No infiere preferencia política individual.

### Mujeres y cuidados

Analiza barreras de seguridad, movilidad, tiempo, empleo, servicios y participación. Exige diversidad de fuentes.

### Deporte comunitario

Mapea instalaciones, organizaciones, calendarios, acceso, inclusión y riesgos.

### Política pública

Convierte problemas en fichas: competencia municipal, pasos, costo preliminar, KPI y dependencias.

### Legal y cumplimiento

Revisa normativa electoral, privacidad, finanzas, uso de datos y afirmaciones públicas.

### Narrativa y comprensión

Crea prototipos internos y pruebas de claridad. No publica ni segmenta anuncios.

### Evaluador adversarial

Busca evidencia faltante, promesas inviables, sesgos, instrumentalización y riesgos reputacionales.

## Contrato de tarea

Cada ejecución debe recibir:

- objetivo;
- alcance;
- fuentes permitidas;
- entregable;
- criterios de aceptación;
- gates aplicables;
- fecha de corte;
- prohibiciones;
- propietario humano.

## Loop

```text
OBSERVAR
-> FORMULAR HIPÓTESIS
-> INVESTIGAR EN PARALELO
-> CITAR
-> CONTRASTAR
-> EVALUAR
-> PRODUCIR BORRADOR
-> REVISIÓN HUMANA
-> REGISTRAR DECISIÓN
```

## Evals mínimos

1. **Grounding:** cada afirmación material tiene fuente.
2. **Freshness:** fechas y versiones están identificadas.
3. **Municipal viability:** competencia y dependencia explícitas.
4. **Representation:** no se generaliza desde un solo grupo.
5. **Safety:** no hay perfilado político individual ni acción externa.
6. **Actionability:** cada recomendación tiene responsable, plazo y KPI.
7. **Contradiction test:** se presenta evidencia contraria relevante.
8. **Approval test:** ningún borrador se confunde con decisión humana.

## Primera corrida recomendada

Objetivo: producir un `Brief de decisión sobre mujeres y deporte`.

Subtareas:

- inventario de evidencia existente;
- mapa de actores y organizaciones;
- brechas territoriales;
- cinco problemas municipales verificables;
- tres pilotos;
- matriz de riesgos;
- scorecard de avance;
- recomendación: bloquear, investigar, pilotear o aprobar.

## Límites

El harness no puede:

- contactar ciudadanos;
- publicar contenido;
- comprar pauta;
- comprometer recursos;
- aprobar candidaturas;
- inferir afiliación o preferencia política individual;
- sustituir consentimiento o revisión legal.
