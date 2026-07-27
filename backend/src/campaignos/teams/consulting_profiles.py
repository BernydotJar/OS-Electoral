"""Consultant-grade, non-authoritative operating profiles for campaign functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BlueprintLocale = Literal["es", "en"]


@dataclass(frozen=True, slots=True)
class RoleConsultingProfile:
    decision_scope: tuple[str, ...]
    deliverables: tuple[str, ...]
    collaboration_points: tuple[str, ...]
    success_signals: tuple[str, ...]


def _build(items: tuple[str, ...]) -> RoleConsultingProfile:
    if len(items) != 10:
        raise ValueError("consulting profile requires exactly ten items")
    return RoleConsultingProfile(items[:2], items[2:5], items[5:7], items[7:10])


_ES_DATA: dict[str, tuple[str, ...]] = {
    "campaign_direction": (
        "Prepara prioridades, tradeoffs y escalaciones para decisión humana.",
        "Eleva cambios de alcance, presupuesto, riesgo o calendario que requieren aprobación.",
        "Agenda semanal con resultados y responsables.",
        "Registro de decisiones, supuestos, aprobaciones y revisiones.",
        "Mapa de bloqueos, dependencias y escalaciones.",
        "Investigación y estrategia para validar cada prioridad.",
        "Territorio, comunicación, legal y finanzas para coordinar límites y ejecución autorizada.",
        "Cada prioridad tiene resultado, responsable, fecha y evidencia.",
        "Las decisiones pendientes y sus consecuencias permanecen visibles.",
        "Ninguna prioridad se interpreta como permiso para actuar externamente.",
    ),
    "research_evidence": (
        "Recomienda si la evidencia permite comparar opciones sin tomar la decisión política.",
        "Eleva contradicciones, incógnitas y fuentes obsoletas que cambian una hipótesis.",
        "Registro de fuentes con procedencia, fecha y verificación.",
        "Síntesis que separa hechos, inferencias e incógnitas.",
        "Matriz de contradicciones, preguntas y evidencia requerida.",
        "Candidatura y territorio para formular preguntas verificables.",
        "Estrategia, comunicación y legal para comprobar supuestos y afirmaciones.",
        "Toda afirmación relevante se rastrea a una fuente y fecha.",
        "Hechos, inferencias e incógnitas permanecen distintos.",
        "La evidencia desactualizada o contradictoria dispara revisión.",
    ),
    "territory_organization": (
        "Prepara cobertura agregada, coordinación y logística para aprobación humana.",
        "Eleva vacíos de responsables, seguridad, transporte o capacidad.",
        "Mapa agregado de cobertura, coordinaciones y vacantes.",
        "Plan logístico con recursos, dependencias y riesgos.",
        "Reporte de avances e incidentes sin perfiles individuales.",
        "Dirección para alinear objetivos y límites de autoridad.",
        "Investigación, legal y finanzas para revisar territorio, recursos y riesgos.",
        "Cada zona agregada tiene responsable y estado observable.",
        "Los riesgos se escalan con contexto y evidencia.",
        "No se almacenan ni infieren preferencias políticas individuales.",
    ),
    "communications_narrative": (
        "Prepara prioridades editoriales y opciones de narrativa basadas en estrategia aprobada.",
        "Eleva afirmaciones sin fuente, conflictos de tono y materiales pendientes de aprobación.",
        "Calendario editorial con objetivo, audiencia agregada, evidencia y revisión.",
        "Briefs y borradores versionados con fuentes y responsables.",
        "Matriz de vocerías, preguntas, límites y aprobaciones.",
        "Investigación para verificar afirmaciones y contexto.",
        "Estrategia, dirección, legal y vocerías para revisar antes de publicar.",
        "Cada pieza se rastrea a un brief, fuente y aprobación.",
        "Cambios y correcciones permanecen versionados.",
        "Preparar una pieza no autoriza su publicación.",
    ),
    "administration_legal_finance": (
        "Prepara escenarios de presupuesto, contratación y cumplimiento para aprobación humana.",
        "Eleva gastos, proveedores u obligaciones fuera de límites documentados.",
        "Presupuesto versionado con supuestos y compromisos.",
        "Registro de proveedores, contratos, comprobantes y revisores.",
        "Calendario de obligaciones legales, fiscales y electorales.",
        "Dirección para traducir prioridades en límites de recursos.",
        "Áreas solicitantes y revisión legal o contable para documentar necesidad y aprobación.",
        "Cada compromiso tiene monto, propósito, evidencia y responsable.",
        "Obligaciones y vencimientos se revisan antes de incidentes.",
        "Ningún registro interno autoriza gasto o acceso financiero.",
    ),
    "digital_strategy": (
        "Prepara hipótesis de canal, conversión y medición para decisión humana.",
        "Eleva riesgos de privacidad, plataforma, datos o aprobación antes de activar.",
        "Plan digital con objetivos, hipótesis y canales propios.",
        "Especificación de métricas, fuentes y frecuencia de revisión.",
        "Checklist de privacidad, plataforma, seguridad y aprobaciones.",
        "Investigación y estrategia para sustentar hipótesis.",
        "Contenido, legal, privacidad y distribución para revisar requisitos.",
        "Cada hipótesis tiene métrica y criterio de aprendizaje.",
        "Los datos se minimizan dentro del propósito documentado.",
        "No se publica, pauta ni contacta sin autorización separada.",
    ),
    "political_content": (
        "Prepara briefs y borradores que responden a objetivo y evidencia aprobados.",
        "Eleva vacíos de fuente, contradicciones y revisiones pendientes.",
        "Brief con objetivo, audiencia agregada, mensaje, fuentes y restricciones.",
        "Borrador versionado con comentarios y estado de aprobación.",
        "Checklist de afirmaciones, citas, accesibilidad y publicación.",
        "Investigación para comprobar hechos y contexto.",
        "Narrativa, estrategia, legal y distribución para revisión separada.",
        "Toda afirmación verificable tiene fuente y revisor.",
        "Los borradores muestran claramente qué falta.",
        "Preparar contenido no equivale a autorizar publicación.",
    ),
    "paid_media_distribution": (
        "Prepara distribución, presupuesto y medición para aprobación exacta.",
        "Eleva segmentos, territorios o proveedores sin base legal o estratégica.",
        "Plan de medios con objetivo, alcance agregado, canales y supuestos.",
        "Escenarios de presupuesto con límites y condición de aprobación.",
        "Matriz de cumplimiento, medición y calidad de datos.",
        "Digital y contenido para recibir planes y materiales revisados.",
        "Investigación, legal y finanzas para validar medición, proveedor y gasto.",
        "Cada escenario declara costo, medición, riesgo y responsable.",
        "Los segmentos agregados no crean perfiles individuales.",
        "Gasto y activación permanecen bloqueados hasta aprobación.",
    ),
    "storytelling_media_training": (
        "Prepara recomendaciones de ensayo, vocería y corrección para decisión humana.",
        "Eleva afirmaciones no sustentadas y límites que requieren revisión especializada.",
        "Guía de mensajes con evidencia, límites y respuestas revisables.",
        "Plan de ensayo con escenarios, objetivos y observaciones.",
        "Registro de retroalimentación, mejoras y correcciones.",
        "Investigación y contenido para sustentar cada mensaje.",
        "Dirección, estrategia, legal y vocerías para priorizar riesgos.",
        "La candidatura distingue hechos, opinión e hipótesis.",
        "Cada ensayo produce observaciones y una siguiente práctica.",
        "Las correcciones no inventan posicionamientos ni promesas.",
    ),
    "tracking_risks_learning": (
        "Prepara la revisión diaria y escalaciones para decisión humana.",
        "Eleva desvíos, riesgos y bloqueos que cambian objetivo o plazo.",
        "Snapshot de War Room con cambios, datos y decisiones pendientes.",
        "Registro de decisiones, bloqueos, riesgos y responsables.",
        "Ciclo de aprendizaje con hipótesis, resultado y ajuste propuesto.",
        "Todas las áreas para recopilar estado y dependencias.",
        "Dirección, investigación y datos para decidir y validar aprendizaje.",
        "Cada indicador tiene definición, fuente y responsable.",
        "Cada decisión se vincula a evidencia y seguimiento.",
        "El War Room coordina; no ejecuta acciones externas automáticamente.",
    ),
}

_EN_DATA: dict[str, tuple[str, ...]] = {
    "campaign_direction": (
        "Prepare priorities, tradeoffs, and escalations for human decision.",
        "Elevate scope, budget, risk, or schedule changes requiring approval.",
        "Weekly agenda with outcomes and owners.",
        "Decision register with assumptions, approvals, and reviews.",
        "Map of blockers, dependencies, and escalations.",
        "Research and strategy to validate each priority.",
        (
            "Field, communications, legal, and finance to coordinate boundaries and "
            "authorized execution."
        ),
        "Every priority has an outcome, owner, date, and evidence.",
        "Pending decisions and consequences remain visible.",
        "No priority is interpreted as permission for external action.",
    ),
    "research_evidence": (
        "Recommend whether evidence supports comparison without making the political decision.",
        "Elevate contradictions, unknowns, and stale sources that change a hypothesis.",
        "Source register with provenance, date, and verification.",
        "Brief separating facts, inferences, and unknowns.",
        "Matrix of contradictions, questions, and required evidence.",
        "Candidate and field teams to formulate verifiable questions.",
        "Strategy, communications, and legal to test assumptions and claims.",
        "Every material claim traces to a source and date.",
        "Facts, inferences, and unknowns remain distinct.",
        "Stale or contradictory evidence triggers review.",
    ),
    "territory_organization": (
        "Prepare aggregate coverage, coordination, and logistics for human approval.",
        "Elevate owner, safety, transport, or capacity gaps.",
        "Aggregate coverage map with coordinations and vacancies.",
        "Logistics plan with resources, dependencies, and risks.",
        "Progress and incident report without individual profiles.",
        "Leadership to align objectives and authority boundaries.",
        "Research, legal, and finance to review territory, resources, and risk.",
        "Every aggregate area has an owner and observable state.",
        "Risks are escalated with context and evidence.",
        "No individual political preferences are stored or inferred.",
    ),
    "communications_narrative": (
        "Prepare editorial priorities and narrative options from approved strategy.",
        "Elevate unsourced claims, tone conflicts, and materials awaiting approval.",
        "Editorial calendar with objective, aggregate audience, evidence, and review.",
        "Versioned briefs and drafts with sources and owners.",
        "Spokesperson matrix with questions, boundaries, and approvals.",
        "Research to verify claims and context.",
        "Strategy, leadership, legal, and spokespeople to review before publication.",
        "Every asset traces to a brief, source, and approval.",
        "Changes and corrections remain versioned.",
        "Preparing an asset does not authorize publication.",
    ),
    "administration_legal_finance": (
        "Prepare budget, contracting, and compliance scenarios for human approval.",
        "Elevate spending, vendors, or obligations outside documented limits.",
        "Versioned budget with assumptions and commitments.",
        "Vendor, contract, receipt, and reviewer register.",
        "Legal, fiscal, and electoral obligations calendar.",
        "Leadership to translate priorities into resource limits.",
        "Requesting teams and legal or accounting review to document need and approval.",
        "Every commitment has amount, purpose, evidence, and owner.",
        "Obligations and deadlines are reviewed before incidents.",
        "No internal record authorizes spending or financial access.",
    ),
    "digital_strategy": (
        "Prepare channel, conversion, and measurement hypotheses for human decision.",
        "Elevate privacy, platform, data, or approval risks before activation.",
        "Digital plan with objectives, hypotheses, and owned channels.",
        "Metric specification with sources and review frequency.",
        "Privacy, platform, security, and approval checklist.",
        "Research and strategy to support hypotheses.",
        "Content, legal, privacy, and distribution to review requirements.",
        "Every hypothesis has a metric and learning criterion.",
        "Data is minimized within its documented purpose.",
        "No publication, media activation, or contact occurs without separate approval.",
    ),
    "political_content": (
        "Prepare briefs and drafts answering an approved objective and evidence base.",
        "Elevate source gaps, contradictions, and pending reviews.",
        "Brief with objective, aggregate audience, message, sources, and constraints.",
        "Versioned draft with comments and approval state.",
        "Claims, citations, accessibility, and publication checklist.",
        "Research to verify facts and context.",
        "Narrative, strategy, legal, and distribution for separate review.",
        "Every verifiable claim has a source and reviewer.",
        "Drafts state clearly what remains incomplete.",
        "Preparing content does not authorize publication.",
    ),
    "paid_media_distribution": (
        "Prepare distribution, budget, and measurement for exact approval.",
        "Elevate segments, territories, or vendors lacking legal or strategic basis.",
        "Media plan with objective, aggregate reach, channels, and assumptions.",
        "Budget scenarios with limits and approval condition.",
        "Compliance, measurement, and data-quality matrix.",
        "Digital and content teams to receive reviewed plans and materials.",
        "Research, legal, and finance to validate measurement, vendor, and spend.",
        "Every scenario declares cost, measurement, risk, and owner.",
        "Aggregate segments create no individual profiles.",
        "Spending and activation remain blocked until approval.",
    ),
    "storytelling_media_training": (
        "Prepare rehearsal, spokesperson, and correction recommendations for human decision.",
        "Elevate unsupported claims and boundaries requiring specialist review.",
        "Message guide with evidence, boundaries, and reviewable answers.",
        "Rehearsal plan with scenarios, objectives, and observations.",
        "Feedback register with improvements and corrections.",
        "Research and content to support each message.",
        "Leadership, strategy, legal, and spokespeople to prioritize risk.",
        "The candidate distinguishes facts, opinion, and hypotheses.",
        "Every rehearsal produces observations and a next practice.",
        "Corrections invent no positions or promises.",
    ),
    "tracking_risks_learning": (
        "Prepare daily review and escalations for human decision.",
        "Elevate deviations, risks, and blockers changing objective or timing.",
        "War Room snapshot with changes, data, and pending decisions.",
        "Decision, blocker, risk, and owner register.",
        "Learning loop with hypothesis, result, and proposed adjustment.",
        "Every team to collect state and dependencies.",
        "Leadership, research, and data to decide and validate learning.",
        "Every indicator has definition, source, and owner.",
        "Every decision links to evidence and follow-up.",
        "The War Room coordinates; it does not execute external actions automatically.",
    ),
}


def consulting_profile(key: str, locale: BlueprintLocale) -> RoleConsultingProfile:
    data = _ES_DATA if locale == "es" else _EN_DATA
    try:
        return _build(data[key])
    except KeyError as exc:
        raise ValueError(f"missing consulting profile for blueprint key: {key}") from exc
