"""Safe, non-authoritative campaign organization role blueprints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from campaignos.teams.contracts import OrganizationTemplate, TeamRoleCard

BlueprintLocale = Literal["es", "en"]
ROLE_BLUEPRINT_VERSION = "2026-07-25.1"


@dataclass(frozen=True, slots=True)
class RoleBlueprint:
    title: str
    area: str
    purpose: str
    responsibilities: tuple[str, ...]
    vacancy_plan: str


def _role(
    title: str,
    area: str,
    purpose: str,
    responsibilities: tuple[str, ...],
    vacancy_plan: str,
) -> RoleBlueprint:
    return RoleBlueprint(title, area, purpose, responsibilities, vacancy_plan)


_ES_LEAN = (
    _role(
        "Dirección de campaña",
        "Dirección de campaña",
        (
            "Convertir las decisiones humanas aprobadas en prioridades coordinadas, "
            "responsables visibles y una cadencia operativa verificable."
        ),
        (
            "Mantener prioridades y resultados semanales",
            "Coordinar decisiones entre áreas",
            "Escalar aprobaciones y bloqueos humanos",
            "Proteger los límites legales, éticos y de autoridad",
        ),
        (
            "Definir experiencia de dirección, disponibilidad y conflictos de interés; "
            "entrevistar y aprobar humanamente antes de asignar identidad o acceso."
        ),
    ),
    _role(
        "Investigación y evidencia",
        "Investigación electoral",
        (
            "Mantener un registro verificable de fuentes, hallazgos, contradicciones e "
            "incógnitas que permita decidir sin presentar hipótesis como hechos."
        ),
        (
            "Registrar fuentes y procedencia",
            "Verificar citas y fechas",
            "Mantener contradicciones e incógnitas visibles",
            "Preparar síntesis para revisión humana",
        ),
        (
            "Seleccionar un perfil con criterio de evidencia y manejo responsable de datos; "
            "validar experiencia y aprobar su incorporación humanamente."
        ),
    ),
    _role(
        "Territorio y organización",
        "Territorio",
        (
            "Convertir los objetivos territoriales aprobados en cobertura agregada, "
            "coordinación local y logística observable sin perfilar preferencias "
            "individuales."
        ),
        (
            "Diseñar capas de coordinación territorial",
            "Mantener cobertura agregada y responsables",
            "Coordinar necesidades logísticas",
            "Escalar riesgos y vacíos de organización",
        ),
        (
            "Definir experiencia territorial, límites de datos y cobertura requerida; "
            "completar selección y autorización humana antes de cualquier operación."
        ),
    ),
    _role(
        "Comunicación y narrativa",
        "Comunicación",
        (
            "Transformar estrategia aprobada y evidencia revisada en planes de comunicación "
            "coherentes, trazables y sujetos a aprobación humana antes de publicar."
        ),
        (
            "Mantener calendario y prioridades editoriales",
            "Coordinar prensa y vocerías autorizadas",
            "Preparar materiales para revisión",
            "Verificar fuentes, tono y aprobaciones",
        ),
        (
            "Evaluar criterio editorial, experiencia y límites de publicación; aprobar "
            "persona, alcance y accesos mediante procesos separados."
        ),
    ),
    _role(
        "Administración, legal y finanzas",
        "Legal y finanzas",
        (
            "Mantener presupuesto, obligaciones, compras y evidencia financiera o legal "
            "disponibles para control humano y revisión independiente."
        ),
        (
            "Mantener presupuesto y compromisos documentados",
            "Coordinar revisión legal y financiera",
            "Registrar evidencia de gastos y proveedores",
            "Escalar decisiones que requieren aprobación",
        ),
        (
            "Definir credenciales, independencia y separación de funciones; realizar "
            "validación y aprobación humana antes de otorgar responsabilidades."
        ),
    ),
)

_EN_LEAN = (
    _role(
        "Campaign Direction",
        "Campaign leadership",
        (
            "Turn approved human decisions into coordinated priorities, visible ownership, "
            "and a verifiable operating cadence."
        ),
        (
            "Maintain weekly priorities and outcomes",
            "Coordinate cross-functional decisions",
            "Escalate human approvals and blockers",
            "Protect legal, ethical, and authority boundaries",
        ),
        (
            "Define leadership experience, availability, and conflicts; interview and "
            "approve a person before assigning identity or access."
        ),
    ),
    _role(
        "Research and Evidence",
        "Electoral research",
        (
            "Maintain a verifiable register of sources, findings, contradictions, and "
            "unknowns so hypotheses are not presented as facts."
        ),
        (
            "Register source provenance",
            "Verify citations and dates",
            "Keep contradictions and unknowns visible",
            "Prepare evidence briefs for human review",
        ),
        (
            "Select for evidence discipline and responsible data handling; validate "
            "experience and approve onboarding through a separate human process."
        ),
    ),
    _role(
        "Territory and Organization",
        "Territory",
        (
            "Turn approved territorial objectives into aggregate coverage, accountable "
            "local coordination, and observable logistics without individual profiling."
        ),
        (
            "Design territorial coordination layers",
            "Maintain aggregate coverage and owners",
            "Coordinate logistics requirements",
            "Escalate safety and organization gaps",
        ),
        (
            "Define field experience, data boundaries, and required coverage; complete "
            "human selection and authorization before operations."
        ),
    ),
    _role(
        "Communications and Narrative",
        "Communications",
        (
            "Turn approved strategy and reviewed evidence into coherent, traceable "
            "communications plans that remain human-gated before publication."
        ),
        (
            "Maintain editorial priorities and calendar",
            "Coordinate press and authorized spokespeople",
            "Prepare materials for review",
            "Verify sources, tone, and approvals",
        ),
        (
            "Evaluate editorial judgment, experience, and publishing boundaries; approve "
            "the person, scope, and access through separate processes."
        ),
    ),
    _role(
        "Administration, Legal, and Finance",
        "Legal and finance",
        (
            "Keep budgets, obligations, purchases, and financial or legal evidence "
            "available for human control and independent review."
        ),
        (
            "Maintain documented budgets and commitments",
            "Coordinate legal and financial review",
            "Register expense and vendor evidence",
            "Escalate decisions that require approval",
        ),
        (
            "Define credentials, independence, and separation of duties; complete human "
            "validation and approval before granting responsibility."
        ),
    ),
)

_EN_FULL = (
    _role(
        "Campaign Chief",
        "Campaign leadership",
        (
            "Coordinate approved human decisions, priorities, accountability, and "
            "cross-functional execution."
        ),
        (
            "Maintain weekly priorities and outcomes",
            "Coordinate cross-functional decisions",
            "Escalate approvals and blockers",
            "Protect legal, ethical, and authority boundaries",
        ),
        (
            "Validate leadership experience, availability, and conflicts; require human "
            "approval before identity or access assignment."
        ),
    ),
    _role(
        "Electoral Research",
        "Research",
        (
            "Maintain verifiable sources, findings, contradictions, and unknowns for human "
            "decision-making."
        ),
        (
            "Register source provenance",
            "Verify citations and dates",
            "Maintain contradictions and unknowns",
            "Prepare evidence briefs for review",
        ),
        (
            "Select for evidence discipline and responsible data handling; approve "
            "onboarding through a separate human process."
        ),
    ),
    _role(
        "Digital Strategy",
        "Digital",
        (
            "Translate approved strategy into governed digital plans, measurable "
            "hypotheses, and reviewable execution requirements."
        ),
        (
            "Maintain digital objectives and hypotheses",
            "Define measurable conversion events",
            "Coordinate owned-channel plans",
            "Escalate privacy, platform, and approval risks",
        ),
        (
            "Validate digital, privacy, and measurement experience; assign no platform "
            "access until separately authorized."
        ),
    ),
    _role(
        "Territory and Mobilization",
        "Territory",
        (
            "Turn approved field objectives into aggregate coverage, accountable local "
            "coordination, and safe logistics."
        ),
        (
            "Design field coordination layers",
            "Track aggregate coverage and owners",
            "Coordinate logistics and readiness",
            "Escalate safety and organization gaps",
        ),
        (
            "Validate field experience and safety boundaries; require human approval before "
            "any operational responsibility."
        ),
    ),
    _role(
        "Political Content",
        "Content",
        (
            "Prepare evidence-grounded content proposals that remain blocked until "
            "objective, audience, message, and human review are satisfied."
        ),
        (
            "Maintain content briefs and sources",
            "Coordinate review status",
            "Resolve evidence gaps",
            "Prevent unapproved publication",
        ),
        (
            "Evaluate writing, evidence, and review discipline; publication authority "
            "remains separate and human-gated."
        ),
    ),
    _role(
        "Paid Media and Distribution",
        "Distribution",
        (
            "Prepare reviewable distribution plans only after segment, territory, "
            "conversion event, budget, and legal gates are satisfied."
        ),
        (
            "Document channel and budget assumptions",
            "Maintain approval and compliance requirements",
            "Coordinate measurement plans",
            "Block spend without exact authorization",
        ),
        (
            "Validate media, finance, and compliance experience; grant no spend or platform "
            "authority automatically."
        ),
    ),
    _role(
        "Storytelling, Speech, and Media Training",
        "Storytelling and training",
        (
            "Prepare the candidate and authorized spokespeople for truthful, "
            "evidence-grounded communication and reviewed public appearances."
        ),
        (
            "Design rehearsal and training plans",
            "Maintain approved talking-point evidence",
            "Document feedback and development needs",
            "Coordinate authorized spokesperson readiness",
        ),
        (
            "Validate coaching and media-training experience; require human approval and "
            "confidentiality review."
        ),
    ),
    _role(
        "Tracking, Risks, and Learning",
        "War Room",
        (
            "Maintain campaign health, decisions, blockers, risks, and learning without "
            "converting internal signals into automatic external action."
        ),
        (
            "Maintain operating indicators and definitions",
            "Track decisions and blockers",
            "Coordinate risk reviews",
            "Produce learning loops for human governance",
        ),
        (
            "Select for analytical rigor and operational judgment; all recommendations and "
            "access remain separately reviewed."
        ),
    ),
)


def _spanish_full() -> tuple[RoleBlueprint, ...]:
    translations = (
        ("Jefatura de campaña", "Dirección de campaña"),
        ("Investigación electoral", "Investigación"),
        ("Estrategia digital", "Digital"),
        ("Territorio y movilización", "Territorio"),
        ("Contenido político", "Contenido"),
        ("Medios pagados y distribución", "Distribución"),
        ("Narrativa, discurso y formación de medios", "Narrativa y formación"),
        ("Seguimiento, riesgos y aprendizaje", "War Room"),
    )
    purposes = (
        (
            "Coordinar decisiones humanas aprobadas, prioridades, responsabilidad y "
            "ejecución entre áreas."
        ),
        (
            "Mantener fuentes, hallazgos, contradicciones e incógnitas verificables para la "
            "decisión humana."
        ),
        (
            "Traducir estrategia aprobada en planes digitales gobernados, hipótesis "
            "medibles y requisitos revisables."
        ),
        (
            "Convertir objetivos de campo aprobados en cobertura agregada, coordinación "
            "local responsable y logística segura."
        ),
        (
            "Preparar propuestas de contenido con evidencia que permanezcan bloqueadas "
            "hasta completar objetivo, audiencia, mensaje y revisión humana."
        ),
        (
            "Preparar planes revisables de distribución sólo cuando segmento, territorio, "
            "conversión, presupuesto y legal estén completos."
        ),
        (
            "Preparar a candidatura y vocerías autorizadas para comunicación veraz, "
            "documentada y revisada."
        ),
        (
            "Mantener salud de campaña, decisiones, bloqueos, riesgos y aprendizaje sin "
            "acciones externas automáticas."
        ),
    )
    responsibilities = (
        (
            "Mantener prioridades semanales",
            "Coordinar decisiones entre áreas",
            "Escalar aprobaciones",
            "Proteger límites de autoridad",
        ),
        ("Registrar procedencia", "Verificar citas", "Mantener incógnitas", "Preparar síntesis"),
        (
            "Mantener objetivos digitales",
            "Definir medición",
            "Coordinar canales propios",
            "Escalar riesgos de privacidad",
        ),
        (
            "Diseñar coordinación territorial",
            "Monitorear cobertura agregada",
            "Coordinar logística",
            "Escalar riesgos",
        ),
        (
            "Mantener briefs y fuentes",
            "Coordinar revisiones",
            "Resolver vacíos",
            "Impedir publicación no aprobada",
        ),
        (
            "Documentar canales y presupuesto",
            "Mantener requisitos legales",
            "Coordinar medición",
            "Bloquear gasto sin autorización",
        ),
        (
            "Diseñar ensayos",
            "Mantener evidencia de mensajes",
            "Documentar retroalimentación",
            "Coordinar preparación",
        ),
        (
            "Mantener indicadores",
            "Rastrear decisiones",
            "Coordinar revisión de riesgos",
            "Producir ciclos de aprendizaje",
        ),
    )
    return tuple(
        _role(
            title,
            area,
            purposes[index],
            responsibilities[index],
            (
                "Definir el perfil, validar experiencia y aprobar humanamente antes de asignar "
                "identidad, responsabilidad o acceso."
            ),
        )
        for index, (title, area) in enumerate(translations)
    )


def build_role_blueprints(
    organization_template: OrganizationTemplate,
    locale: BlueprintLocale,
) -> tuple[TeamRoleCard, ...] | None:
    if organization_template == "CUSTOM":
        return None
    blueprints = (
        (_ES_LEAN if locale == "es" else _EN_LEAN)
        if organization_template == "LEAN_CAMPAIGN"
        else (_spanish_full() if locale == "es" else _EN_FULL)
    )
    return tuple(
        TeamRoleCard(
            id=uuid4(),
            title=item.title,
            area=item.area,
            purpose=item.purpose,
            responsibilities=item.responsibilities,
            status="VACANT",
            principal_id=None,
            availability_status="UNASSESSED",
            weekly_capacity_hours=None,
            onboarding_status="NOT_STARTED",
            vacancy_plan=item.vacancy_plan,
        )
        for item in blueprints
    )
