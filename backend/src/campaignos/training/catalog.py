"""Repository-owned bilingual Training Academy catalog."""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass

from campaignos.data.audit import canonical_hash
from campaignos.training.contracts import (
    Locale,
    TrainingAnswerSubmission,
    TrainingAssessmentOutcome,
    TrainingCatalog,
    TrainingCatalogLessonProjection,
    TrainingCatalogModuleProjection,
    TrainingCatalogOptionProjection,
    TrainingCatalogPathProjection,
    TrainingCatalogProjection,
    TrainingCatalogQuestionProjection,
    TrainingLearningPath,
    TrainingLesson,
    TrainingLocalizedModule,
    TrainingModule,
    TrainingObjective,
    TrainingOption,
    TrainingPathModule,
    TrainingQuestion,
    TrainingQuestionFeedback,
)

MODULE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class LocalizedSpec:
    title: str
    summary: str
    objective: str
    lesson_title: str
    lesson_body: str
    question: str
    correct_label: str
    incorrect_label: str
    explanation: str


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    module_id: str
    sources: tuple[str, ...]
    roles: tuple[str, ...]
    es: LocalizedSpec
    en: LocalizedSpec


SPECS = (
    ModuleSpec(
        module_id="research_foundations",
        sources=(
            "docs/product/product-boundaries.md",
            "docs/testing/c3-front-011-campol-consultant-evaluation.md",
        ),
        roles=("electoral_research", "campaign_leadership", "digital_strategy"),
        es=LocalizedSpec(
            title="Investigar antes de actuar",
            summary="Convierte preguntas abiertas en evidencia verificable antes de comunicar o gastar.",
            objective="Distinguir investigación, estrategia y ejecución con límites agregados y legales.",
            lesson_title="Primero entender",
            lesson_body="Una campaña comienza aclarando territorio, candidatura, actores y preguntas. CampaignOS admite evidencia agregada y con propósito; no crea preferencias individuales, puntuaciones de persuasión ni listas para contacto.",
            question="¿Qué debe ocurrir antes de comunicar o gastar?",
            correct_label="Investigar y documentar evidencia",
            incorrect_label="Publicar o perfilar personas de inmediato",
            explanation="La investigación y la evidencia reducen decisiones improvisadas y preservan límites de privacidad.",
        ),
        en=LocalizedSpec(
            title="Research before action",
            summary="Turn open questions into verifiable evidence before communication or spending.",
            objective="Distinguish research, strategy, and execution under aggregate and lawful limits.",
            lesson_title="Understand first",
            lesson_body="A campaign starts by clarifying territory, candidacy, actors, and questions. CampaignOS supports aggregate, purpose-limited evidence; it does not create individual preferences, persuasion scores, or contact lists.",
            question="What should happen before communication or spending?",
            correct_label="Research and document evidence",
            incorrect_label="Publish or profile people immediately",
            explanation="Research and evidence reduce improvised decisions and preserve privacy limits.",
        ),
    ),
    ModuleSpec(
        module_id="candidate_evidence_and_risk",
        sources=("docs/product/product-boundaries.md", "docs/api/candidate-workspace.md"),
        roles=("campaign_leadership", "electoral_research", "tracking_risks_learning"),
        es=LocalizedSpec(
            title="Perfil, evidencia y riesgos",
            summary="Separa hechos confirmados, contradicciones, desarrollo pendiente y riesgo reputacional.",
            objective="Diferenciar declaraciones de evidencia independiente antes de una decisión pública.",
            lesson_title="No mezclar afirmaciones y prueba",
            lesson_body="Una declaración de la candidatura no reemplaza una fuente independiente. Las contradicciones y los riesgos requieren documentación y revisión humana autorizada.",
            question="¿Qué confirma una declaración de candidatura?",
            correct_label="Una fuente independiente y atribuible",
            incorrect_label="Repetir la declaración o asignar una puntuación",
            explanation="La evidencia independiente debe poder atribuirse y revisarse.",
        ),
        en=LocalizedSpec(
            title="Profile, evidence, and risks",
            summary="Separate confirmed facts, contradictions, pending development, and reputation risk.",
            objective="Distinguish claims from independent evidence before a public decision.",
            lesson_title="Keep claims and proof separate",
            lesson_body="A candidacy claim does not replace an independent source. Contradictions and risks require documentation and authorized human review.",
            question="What confirms a candidacy claim?",
            correct_label="An attributable independent source",
            incorrect_label="Repeating the claim or assigning a score",
            explanation="Independent evidence must be attributable and reviewable.",
        ),
    ),
    ModuleSpec(
        module_id="team_accountability",
        sources=("docs/product/team-workspace.md", "docs/design/team-role-operations-board.md"),
        roles=("campaign_leadership", "tracking_risks_learning"),
        es=LocalizedSpec(
            title="Equipo y responsabilidad clara",
            summary="Conecta propósito, roles, RACI, capacidad y escalamiento sin convertir etiquetas en permisos.",
            objective="Separar organización, responsabilidad y autoridad de aplicación.",
            lesson_title="Un rol explica trabajo, no acceso",
            lesson_body="Cada función necesita propósito, responsables y entregables. Vacantes, bloqueos y capacidad deben ser visibles, pero una etiqueta de rol o una formación nunca concede permisos.",
            question="¿Una etiqueta de rol concede acceso?",
            correct_label="No, requiere una autorización exacta",
            incorrect_label="Sí, automáticamente",
            explanation="La organización del equipo no sustituye la autorización del servidor.",
        ),
        en=LocalizedSpec(
            title="Team accountability",
            summary="Connect purpose, roles, RACI, capacity, and escalation without turning labels into permissions.",
            objective="Separate organization, accountability, and application authority.",
            lesson_title="A role explains work, not access",
            lesson_body="Each function needs purpose, owners, and deliverables. Vacancies, blockers, and capacity should be visible, but a role label or training completion never grants permissions.",
            question="Does a role label grant access?",
            correct_label="No, an exact authorization is required",
            incorrect_label="Yes, automatically",
            explanation="Team organization does not replace server-owned authorization.",
        ),
    ),
    ModuleSpec(
        module_id="strategy_and_decisions",
        sources=("docs/product/product-boundaries.md", "docs/security/threat-model.md"),
        roles=("campaign_leadership", "digital_strategy", "electoral_research"),
        es=LocalizedSpec(
            title="Estrategia y decisiones humanas",
            summary="Compara hipótesis y opciones con evidencia, indicadores y revisión crítica.",
            objective="Reservar la decisión final a una persona autorizada.",
            lesson_title="Comparar antes de decidir",
            lesson_body="Una estrategia gobernada registra problema, hipótesis, opciones, evidencia, contradicciones e indicadores. La IA puede ordenar evidencia; una persona autorizada decide.",
            question="¿Quién toma la decisión final?",
            correct_label="Una persona autorizada",
            incorrect_label="El modelo o el indicador más alto",
            explanation="CampaignOS preserva autoridad y recibos humanos.",
        ),
        en=LocalizedSpec(
            title="Strategy and human decisions",
            summary="Compare hypotheses and options with evidence, indicators, and critical review.",
            objective="Reserve the final decision for an authorized human.",
            lesson_title="Compare before deciding",
            lesson_body="A governed strategy records the problem, hypotheses, options, evidence, contradictions, and indicators. AI can organize evidence; an authorized human decides.",
            question="Who makes the final decision?",
            correct_label="An authorized human",
            incorrect_label="The model or highest indicator",
            explanation="CampaignOS preserves human authority and attributable receipts.",
        ),
    ),
    ModuleSpec(
        module_id="war_room_and_measurement",
        sources=("docs/product/campaign-launch-roadmap.md", "docs/operations/release-readiness.md"),
        roles=("campaign_leadership", "tracking_risks_learning", "territory_mobilization"),
        es=LocalizedSpec(
            title="Operar, medir y aprender",
            summary="Usa un breve diario e indicadores para ajustar trabajo sin confundir actividad con impacto.",
            objective="Convertir resultados en aprendizaje y ajuste humano.",
            lesson_title="Una foto diaria, no una verdad eterna",
            lesson_body="El War Room registra prioridades, bloqueos y decisiones para una fecha exacta. Una desviación genera revisión y ajuste humano, no publicación ni sanción automática.",
            question="¿Qué hacer cuando un indicador se desvía?",
            correct_label="Revisar evidencia y ajustar el plan",
            incorrect_label="Ocultarlo o sancionar automáticamente",
            explanation="La medición debe producir aprendizaje y decisión humana.",
        ),
        en=LocalizedSpec(
            title="Operate, measure, and learn",
            summary="Use a daily brief and indicators to adjust work without confusing activity with impact.",
            objective="Turn results into learning and human adjustment.",
            lesson_title="A daily snapshot, not an eternal truth",
            lesson_body="The War Room records priorities, blockers, and decisions for an exact date. A deviation produces human review and adjustment, not automatic publication or punishment.",
            question="What should happen when an indicator drifts?",
            correct_label="Review evidence and adjust the plan",
            incorrect_label="Hide it or apply an automatic penalty",
            explanation="Measurement should produce learning and human judgment.",
        ),
    ),
    ModuleSpec(
        module_id="safety_privacy_and_authority",
        sources=("docs/product/product-boundaries.md", "docs/security/threat-model.md"),
        roles=(
            "campaign_leadership",
            "political_content",
            "paid_media_distribution",
            "territory_mobilization",
        ),
        es=LocalizedSpec(
            title="Seguridad, privacidad y autoridad",
            summary="Protege datos, permisos y decisiones antes de cualquier efecto externo.",
            objective="Reconocer datos mínimos y acciones que exigen aprobación humana separada.",
            lesson_title="Los efectos externos están bloqueados",
            lesson_body="Cada registro necesita propósito y alcance. Publicar, gastar, contactar o movilizar requiere controles y aprobación separada; completar un curso nunca concede esa autoridad.",
            question="¿Completar un módulo concede permisos?",
            correct_label="No, no tiene efecto de autoridad",
            incorrect_label="Sí, concede acceso operativo",
            explanation="La formación aporta evidencia educativa, no permisos ni acreditación profesional.",
        ),
        en=LocalizedSpec(
            title="Safety, privacy, and authority",
            summary="Protect data, permissions, and decisions before any external effect.",
            objective="Recognize minimal data and actions requiring separate human approval.",
            lesson_title="External effects remain blocked",
            lesson_body="Every record needs a purpose and scope. Publishing, spending, contacting, or mobilizing requires separate controls and approval; course completion never grants that authority.",
            question="Does module completion grant permissions?",
            correct_label="No, it has no authority effect",
            incorrect_label="Yes, it grants operational access",
            explanation="Training provides educational evidence, not permissions or professional accreditation.",
        ),
    ),
)


def _localized(
    locale: Locale, spec: LocalizedSpec, sources: tuple[str, ...]
) -> TrainingLocalizedModule:
    return TrainingLocalizedModule(
        locale=locale,
        title=spec.title,
        summary=spec.summary,
        objectives=(TrainingObjective(id="objective", text=spec.objective),),
        lessons=(
            TrainingLesson(
                id="lesson",
                title=spec.lesson_title,
                body=spec.lesson_body,
                source_refs=sources,
            ),
        ),
        questions=(
            TrainingQuestion(
                id="knowledge_check",
                prompt=spec.question,
                options=(
                    TrainingOption(id="correct", label=spec.correct_label),
                    TrainingOption(id="incorrect", label=spec.incorrect_label),
                ),
                correct_option_ids=("correct",),
                explanation=spec.explanation,
            ),
        ),
    )


def _build_catalog() -> TrainingCatalog:
    modules = tuple(
        TrainingModule(
            module_id=spec.module_id,
            version=MODULE_VERSION,
            status="APPROVED",
            owner="CampaignOS product governance",
            reviewer="Authorized human training reviewer",
            passing_percent=100,
            sources=spec.sources,
            locales=(
                _localized("es", spec.es, spec.sources),
                _localized("en", spec.en, spec.sources),
            ),
        )
        for spec in SPECS
    )
    paths = tuple(
        TrainingLearningPath(
            path_id=f"{spec.module_id}_path",
            version=MODULE_VERSION,
            role_slugs=spec.roles,
            modules=(TrainingPathModule(module_id=spec.module_id, version=MODULE_VERSION),),
        )
        for spec in SPECS
    )
    return TrainingCatalog(modules=modules, paths=paths)


CATALOG = _build_catalog()
CATALOG_DIGEST = canonical_hash(CATALOG.model_dump(mode="json"))


def module_by_ref(module_id: str, module_version: str) -> TrainingModule:
    try:
        return next(
            item
            for item in CATALOG.modules
            if item.module_id == module_id and item.version == module_version
        )
    except StopIteration as exc:
        raise KeyError("unknown training module version") from exc


def path_by_ref(path_id: str, path_version: str) -> TrainingLearningPath:
    try:
        return next(
            item
            for item in CATALOG.paths
            if item.path_id == path_id and item.version == path_version
        )
    except StopIteration as exc:
        raise KeyError("unknown training learning path version") from exc


def project_catalog(locale: Locale) -> TrainingCatalogProjection:
    modules: list[TrainingCatalogModuleProjection] = []
    for module in CATALOG.modules:
        localized = module.localized(locale)
        modules.append(
            TrainingCatalogModuleProjection(
                module_id=module.module_id,
                version=module.version,
                status=module.status,
                title=localized.title,
                summary=localized.summary,
                objectives=localized.objectives,
                lessons=tuple(
                    TrainingCatalogLessonProjection.model_validate(item.model_dump())
                    for item in localized.lessons
                ),
                questions=tuple(
                    TrainingCatalogQuestionProjection(
                        id=question.id,
                        prompt=question.prompt,
                        options=tuple(
                            TrainingCatalogOptionProjection.model_validate(option.model_dump())
                            for option in question.options
                        ),
                    )
                    for question in localized.questions
                ),
                passing_percent=module.passing_percent,
                sources=module.sources,
            )
        )
    return TrainingCatalogProjection(
        locale=locale,
        catalog_digest=CATALOG_DIGEST,
        modules=tuple(modules),
        paths=tuple(
            TrainingCatalogPathProjection.model_validate(item.model_dump())
            for item in CATALOG.paths
        ),
    )


def grade_attempt(
    module: TrainingModule,
    *,
    locale: Locale,
    answers: tuple[TrainingAnswerSubmission, ...],
) -> TrainingAssessmentOutcome:
    localized = module.localized(locale)
    submitted = {item.question_id: item for item in answers}
    expected = {item.id for item in localized.questions}
    if set(submitted) != expected or len(submitted) != len(answers):
        raise ValueError("answers must cover every catalog question exactly once")
    feedback: list[TrainingQuestionFeedback] = []
    correct_count = 0
    for question in localized.questions:
        answer = submitted[question.id]
        valid_options = {item.id for item in question.options}
        if not set(answer.option_ids) <= valid_options:
            raise ValueError("answer references an unknown option")
        correct = set(answer.option_ids) == set(question.correct_option_ids)
        correct_count += int(correct)
        feedback.append(
            TrainingQuestionFeedback(
                question_id=question.id,
                correct=correct,
                explanation=question.explanation,
            )
        )
    total = len(localized.questions)
    percent = (correct_count * 100) // total
    return TrainingAssessmentOutcome(
        result="PASS" if percent >= module.passing_percent else "FAIL",
        correct_count=correct_count,
        total_questions=total,
        passing_percent=module.passing_percent,
        feedback=tuple(feedback),
    )
