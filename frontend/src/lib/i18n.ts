export const locales = ["es", "en"] as const;
export type Locale = (typeof locales)[number];

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}

const es = {
  metadata: {
    title: "CampaignOS · Command Center",
    description:
      "Shell operativo gobernado para campañas con autoridad humana y evidencia trazable.",
  },
  common: {
    skip: "Saltar al contenido",
    product: "CampaignOS",
    readOnly: "SOLO LECTURA",
    demo: "DEMO SINTÉTICO",
    live: "SESIÓN VERIFICADA",
    notApproval:
      "No constituye aprobación política, legal, financiera, de publicación ni de producción.",
    localeLabel: "Idioma",
    spanish: "ES",
    english: "EN",
  },
  shell: {
    eyebrow: "SISTEMA OPERATIVO DE CAMPAÑA",
    title: "Convierte tu campaña en un sistema que avanza",
    subtitle:
      "CampaignOS te muestra qué decidir, qué evidencia falta y cuál es el siguiente movimiento seguro.",
    authority:
      "La IA recomienda; la evidencia sustenta; la persona autorizada decide.",
    syntheticContext: "DATOS SINTÉTICOS · SIN CAMPAÑA REAL",
    verifiedContext: "CONTEXTO VERIFICADO POR EL SERVIDOR",
    humanAuthority: "DECISIÓN HUMANA",
    authorizationContext: "CONTEXTO DE AUTORIZACIÓN",
    currentContext: "Contexto actual",
    tenant: "Organización",
    campaign: "Campaña",
    principal: "Sesión",
    roles: "Responsabilidades visibles",
    authorizationFresh: "Permisos verificados",
    modules: "Módulos",
    reference:
      "Referencia visual estática preservada hasta revisión de paridad.",
  },
  states: {
    unauthenticatedTitle: "Se requiere una sesión verificada",
    unauthenticatedBody:
      "El shell no expone un login simulado. La integración OIDC y el ciclo de sesión permanecen detrás de C3-IAM-002.",
    contextTitle: "Selecciona un contexto autorizado",
    contextBody:
      "El selector de tenant no crea autoridad. CampaignOS requiere un tenant preseleccionado y vuelve a validar permisos en el servidor.",
    unavailableTitle: "Dependencia temporalmente no disponible",
    unavailableBody:
      "No se muestran datos parciales ni cachés cruzados. Conserva el correlation ID para soporte.",
    emptyTitle: "No hay campañas autorizadas",
    emptyBody:
      "La sesión es válida, pero no existe una campaña visible bajo permisos exactos vigentes.",
  },
  dashboard: {
    readinessEyebrow: "BASE OPERATIVA",
    readinessTitle: "Preparación operativa",
    readinessBody:
      "Confirma que la campaña tiene el contexto mínimo para comenzar una ruta guiada.",
    checks: "pasos básicos completos",
    nextAction: "Siguiente paso del sistema",
    authorityEyebrow: "PERMISOS EXACTOS",
    authorityTitle: "Permisos y responsabilidades",
    authorityBody:
      "Las responsabilidades orientan el trabajo, pero cada acción vuelve a validar el permiso, el recurso y el propósito exactos.",
    grantCountLabel: "permisos exactos administrados por el servidor",
    evidenceEyebrow: "TRAZABILIDAD",
    evidenceTitle: "Evidencia y auditoría",
    evidenceBody:
      "Las lecturas sensibles y los cambios guardados producen comprobantes trazables.",
    auditReceipt: "Comprobante de lectura",
    noExternal: "Sin efectos externos",
    confirmed: "Confirmado",
    operationsEyebrow: "SECUENCIA GUIADA",
    operationsTitle: "Cómo avanza CampaignOS",
    operationsBody:
      "Primero ordena la base; después habilita evidencia, equipo, estrategia y operación diaria.",
    campaignStatus: "Estado de campaña",
    version: "Versión",
    workspaceCount: "Espacios de trabajo activos",
    limitationsEyebrow: "LÍMITES OBLIGATORIOS",
    limitations: "Controles que siguen vigentes",
    readinessCheckLabels: {
      campaign_name: "Nombre de campaña definido",
      jurisdiction: "Territorio definido",
      campaign_stage: "Etapa de campaña definida",
      active_workspace: "Espacio de trabajo activo",
    },
    readinessNextActionLabels: {
      COMPLETE_CAMPAIGN_METADATA: "Completar nombre, territorio y etapa",
      CREATE_CAMPAIGN_WORKSPACE: "Crear el espacio de trabajo inicial",
      BEGIN_GUIDED_INTAKE: "Comenzar la ruta guiada",
    },
    sequence: {
      context: "Definir contexto y propósito",
      workspace: "Organizar el espacio de trabajo",
      intake: "Completar la información de arranque",
      evidence: "Construir evidencia antes de decidir estrategia",
    },
    limitationLabels: {
      NOT_A_HUMAN_APPROVAL: "Requiere decisión de una persona autorizada",
      NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT:
        "Aún no existe evidencia suficiente para decidir estrategia",
      NOT_A_STRATEGY: "Esta etapa todavía no constituye una estrategia",
      NO_CITIZEN_CONTACT_OR_PROFILING:
        "No habilita contacto ciudadano ni perfiles individuales",
      NO_EXTERNAL_EFFECTS: "No produce acciones fuera de CampaignOS",
      NOT_PUBLIC_POSITIONING_APPROVAL:
        "No autoriza posicionamiento ni mensajes públicos",
      NO_VOTER_PROFILING: "No habilita perfiles individuales de electores",
      HUMAN_REVIEW_REQUIRED: "Requiere revisión humana antes de avanzar",
      ROLE_LABELS_ARE_NOT_PERMISSIONS:
        "Los nombres de puesto no conceden permisos",
      ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION:
        "Los accesos requieren autorización humana separada",
      HUMAN_DECISIONS_REQUIRED: "Las decisiones críticas pertenecen al equipo humano",
      NO_AUTONOMOUS_TASK_EXECUTION:
        "CampaignOS no ejecuta tareas de campaña de forma autónoma",
      NO_CITIZEN_CONTACT: "No habilita contacto ciudadano",
      NOT_PUBLIC_POSITIONING: "No constituye posicionamiento público",
      NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING:
        "No habilita perfiles ni segmentación individual",
      NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS:
        "No contacta personas ni produce efectos externos",
    },
  },
  journey: {
    eyebrow: "RUTA MAESTRA DE CAMPAÑA",
    title: "Tu campaña, paso a paso",
    body:
      "Desde la idea inicial hasta la operación diaria, CampaignOS ordena decisiones, evidencia, equipo y seguimiento sin saltarse los controles humanos.",
    progressLabel: "Progreso de la ruta de campaña",
    stageLabel: "Etapa actual",
    completedLabel: "etapas completadas",
    missionLabel: "Tu misión ahora",
    openPhase: "Ver etapa",
    blockedAction: "Requiere habilitación o acceso adicional",
    boundary:
      "La ruta orienta y organiza. No autoriza publicaciones, contacto ciudadano, gasto, movilización ni producción.",
    statusLabels: {
      COMPLETE: "Completada",
      ACTIVE: "En curso",
      AVAILABLE: "Siguiente",
      BLOCKED: "Bloqueada por acceso o configuración",
      LOCKED: "Se habilita después",
    },
    phaseLabels: {
      foundation: "Aterrizar la campaña",
      evidence: "Conocer la candidatura y el territorio",
      team: "Organizar el equipo",
      strategy: "Decidir la estrategia",
      operations: "Operar y aprender cada día",
    },
    phaseDescriptions: {
      foundation:
        "Define cargo, territorio, propósito, equipo, activos y capacidad presupuestaria.",
      evidence:
        "Reúne padrón, resultados históricos, fichas comunitarias, fuentes públicas y evidencia verificable.",
      team:
        "Diseña coordinaciones, secretarías, responsables, capacidad y vacíos que debes cubrir.",
      strategy:
        "Construye FODA, objetivos, hipótesis y el equilibrio entre trabajo territorial, comunicación y digital.",
      operations:
        "Da seguimiento a metas, comunidades, responsables, tareas, bloqueos y aprendizajes del War Room.",
    },
    phaseOutcomes: {
      foundation: "Resultado: una campaña entendible y lista para investigar.",
      evidence: "Resultado: decisiones basadas en evidencia, no intuición.",
      team: "Resultado: cada función tiene responsable y capacidad visible.",
      strategy: "Resultado: una dirección humana, medible y revisable.",
      operations: "Resultado: seguimiento diario con trazabilidad y aprendizaje.",
    },
    phaseActions: {
      foundation: "Continuar información de arranque",
      evidence: "Revisar candidatura y evidencia",
      team: "Revisar equipo y responsabilidades",
      strategy: "Abrir sala de estrategia",
      operations: "Abrir operación diaria",
    },
  },
  campaigns: {
    eyebrow: "CONTEXTO DE CAMPAÑA",
    title: "Elige la campaña de trabajo",
    body:
      "La selección cambia únicamente el contexto visible. El servidor vuelve a validar cada permiso y alcance.",
    current: "Campaña actual",
    selectLabel: "Campaña autorizada",
    apply: "Usar esta campaña",
    help: "Sólo aparecen campañas visibles para la sesión verificada.",
  },
  notices: {
    campaign_selected: "Contexto de campaña actualizado.",
    intake_started: "Ruta guiada creada y guardada en PostgreSQL.",
    intake_saved: "Cambios guardados con nueva versión.",
    authorization_denied: "La sesión no tiene autorización exacta para esta acción.",
    conflict: "El registro cambió o la solicitud ya fue utilizada. Recarga y revisa la versión.",
    validation_error: "Revisa los campos señalados y vuelve a intentar.",
    dependency_failure: "Una dependencia no está disponible. No se guardaron cambios parciales.",
    unauthenticated: "La sesión ya no es válida.",
    not_found: "El recurso solicitado no está disponible en este contexto.",
    request_failed: "La solicitud no pudo completarse de forma segura.",
  },
  intake: {
    eyebrow: "INICIO GUIADO · EVIDENCIA PRIMERO",
    title: "Construye la base de tu campaña",
    body:
      "Responde preguntas claras para que CampaignOS pueda indicarte qué sigue, qué evidencia falta y qué trabajo debe organizarse.",
    startTitle: "Comenzar la ruta guiada",
    startBody:
      "Crea el registro interno y su evidencia de auditoría. No inicia estrategia, contacto ni ejecución externa.",
    startAction: "Comenzar ruta",
    editEyebrow: "EDICIÓN AUTORIZADA",
    editTitle: "Cuéntanos con qué estás comenzando",
    editBody:
      "Puedes completar esta información por etapas. CampaignOS conserva la versión correcta y nunca reemplaza cambios en silencio.",
    onePerLine: "Un elemento por línea. Máximo 30.",
    officeHelp: "Indica el cargo que buscas y confirma que corresponde al territorio de la campaña.",
    officePlaceholder: "Ej. Alcaldía Municipal",
    budgetHelp: "Selecciona el nivel de evidencia disponible; no necesitas tener el presupuesto cerrado para comenzar.",
    candidateProjectHelp:
      "Explica por qué nace la candidatura, qué cambio busca y a quién desea servir.",
    candidateProjectPlaceholder:
      "Ej. Queremos construir una candidatura municipal basada en evidencia, organización comunitaria y resultados medibles.",
    currentTeamHelp:
      "Una persona o función por línea. Incluye coordinaciones, secretarías y roles todavía vacantes.",
    currentTeamPlaceholder:
      "Coordinación general — confirmada\nTerritorio — por definir",
    currentAssetsHelp:
      "Registra recursos existentes: archivos, redes, herramientas, oficina, vehículos, voluntariado o alianzas autorizadas.",
    currentAssetsPlaceholder:
      "Archivo documental\nCanales digitales\nHerramienta de datos territoriales",
    knownUnknownsHelp:
      "Anota preguntas que deben resolverse antes de decidir estrategia o ejecutar trabajo.",
    knownUnknownsPlaceholder:
      "¿Cuántos votos se requieren?\n¿Qué comunidades necesitan mayor investigación?",
    evidenceRequirementsHelp:
      "Lista los datos y documentos que harán falta para responder esas preguntas.",
    evidenceRequirementsPlaceholder:
      "Padrón electoral\nResultados históricos\nFichas comunitarias\nPresupuesto preliminar",
    checkComplete: "Completado",
    checkPending: "Pendiente",
    saveBoundary:
      "Guardar actualiza sólo esta preparación interna; no aprueba estrategia ni activa trabajo externo.",
    saveAction: "Guardar cambios",
    status: "Estado de la preparación",
    statusLabels: {
      BLOCKED_BY_CAMPAIGN_SETUP: "Bloqueado por configuración de campaña",
      IN_PROGRESS: "Preparación en progreso",
      READY_FOR_RESEARCH: "Listo para comenzar investigación",
    },
    progress: "pasos completos",
    nextAction: "Siguiente paso",
    checks: "Pasos de esta etapa",
    researchActions: "Lo que se desbloquea después",
    notStarted:
      "La ruta guiada todavía no ha sido iniciada por una persona autorizada.",
    notAuthorized:
      "La sesión no tiene el permiso exacto para revisar esta ruta guiada.",
    unavailable:
      "La ruta guiada no está disponible temporalmente. No se muestran datos parciales.",
    noItems: "Evaluado: no se registraron elementos.",
    notAssessed: "Pendiente de evaluación",
    office: "Cargo objetivo",
    candidateProject: "Proyecto de candidatura",
    currentTeam: "Equipo actual",
    currentAssets: "Activos actuales",
    budgetStatus: "Estado del presupuesto",
    knownUnknowns: "Preguntas que debemos resolver",
    evidenceRequirements: "Datos y documentos necesarios",
    readReceipt: "Comprobante de lectura",
    updatedAt: "Actualizado",
    budgetStatusLabels: {
      NOT_ASSESSED: "No evaluado",
      NO_DOCUMENT: "Sin documento",
      ROUGH_RANGE: "Rango preliminar",
      DOCUMENTED: "Documentado",
    },
    checkLabels: {
      campaign_operational_setup: "Completar configuración operativa",
      office: "Definir el cargo objetivo",
      candidate_project: "Describir el proyecto de candidatura",
      current_team: "Evaluar el equipo actual",
      current_assets: "Inventariar activos actuales",
      budget_status: "Evaluar evidencia presupuestaria",
      known_unknowns: "Registrar preguntas conocidas",
      evidence_requirements: "Definir evidencia necesaria",
    },
    nextActionLabels: {
      COMPLETE_CAMPAIGN_SETUP:
        "Completar la configuración operativa de la campaña",
      DEFINE_TARGET_OFFICE: "Definir el cargo y la jurisdicción objetivo",
      DESCRIBE_CANDIDATE_PROJECT: "Describir el proyecto de candidatura",
      ASSESS_CURRENT_TEAM: "Evaluar capacidades y vacíos del equipo",
      ASSESS_CURRENT_ASSETS: "Inventariar activos y su procedencia",
      ASSESS_BUDGET_EVIDENCE: "Documentar el estado real del presupuesto",
      RECORD_KNOWN_UNKNOWNS: "Registrar lo que aún debe resolverse",
      DEFINE_EVIDENCE_REQUIREMENTS: "Definir qué evidencia debe recopilarse",
      BEGIN_RESEARCH: "Comenzar investigación verificable",
    },
    researchActionLabels: {
      VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE:
        "Verificar cargo y jurisdicción con evidencia",
      VALIDATE_CANDIDATE_PROJECT_EVIDENCE: "Validar el proyecto de candidatura",
      ASSESS_TEAM_CAPACITY_GAPS: "Investigar vacíos de capacidad del equipo",
      INVENTORY_ASSET_PROVENANCE: "Verificar procedencia de los activos",
      DOCUMENT_BUDGET_ASSUMPTIONS: "Documentar supuestos presupuestarios",
      RESEARCH_KNOWN_UNKNOWNS: "Resolver las preguntas conocidas",
      COLLECT_REQUIRED_EVIDENCE: "Recopilar la evidencia requerida",
    },
  },
  candidate: {
    eyebrow: "CANDIDATURA · EVIDENCIA Y REVISIÓN HUMANA",
    title: "Workspace ejecutivo de candidatura",
    body: "Separa declaraciones, evidencia independiente, contradicciones, desarrollo y riesgos antes de cualquier decisión pública.",
    status: "Estado interno",
    progress: "pasos completos",
    nextAction: "Siguiente acción humana",
    sections: "Secciones de evidencia",
    identity: "Identidad",
    biography: "Biografía",
    purpose: "Propósito",
    values: "Valores",
    attributes: "Atributos",
    contradictions: "Contradicciones",
    developmentGoals: "Objetivos de desarrollo",
    reputationRisks: "Riesgos reputacionales",
    evidenceInventory: "Inventario de evidencia",
    approvedSections: "Secciones aprobadas",
    pendingApprovals: "Aprobaciones pendientes",
    criticalHighRisks: "Riesgos críticos/altos abiertos",
    publicBoundary: "Uso público bloqueado",
    publicBoundaryBody:
      "La aprobación interna no autoriza posicionamiento público, estrategia, contenido, contacto, gasto ni movilización.",
    notStarted:
      "El espacio de trabajo de candidatura todavía no ha sido creado por una persona autorizada.",
    notAuthorized:
      "La sesión no tiene autorización exacta para revisar esta candidatura.",
    unavailable:
      "El espacio de trabajo de candidatura no está disponible temporalmente. No se muestran datos parciales.",
    notAssessed: "Pendiente de evidencia y revisión",
    noItems: "Revisado: no se registraron elementos.",
    readReceipt: "Comprobante de lectura",
    updatedAt: "Actualizado",
    statusLabels: {
      SETUP_REQUIRED: "Configuración y evidencia inicial requeridas",
      UNDER_REVIEW: "Evidencia bajo revisión",
      AWAITING_APPROVAL: "Esperando aprobaciones por sección",
      INTERNALLY_APPROVED: "Aprobación interna completa",
    },
    checkLabels: {
      identity: "Verificar identidad",
      biography: "Documentar biografía verificable",
      purpose: "Definir propósito con evidencia",
      values: "Verificar valores declarados",
      attributes: "Contrastar atributos",
      contradictions: "Resolver contradicciones",
      development_goals: "Definir desarrollo necesario",
      reputation: "Revisar riesgos reputacionales",
      approvals: "Obtener aprobaciones vigentes",
    },
    nextActionLabels: {
      DEFINE_IDENTITY: "Definir y verificar identidad",
      DOCUMENT_BIOGRAPHY: "Documentar la biografía",
      DEFINE_PURPOSE: "Definir propósito y evidencia",
      VERIFY_VALUES: "Verificar valores",
      VERIFY_ATTRIBUTES: "Contrastar atributos",
      REVIEW_CONTRADICTIONS: "Revisar contradicciones",
      DEFINE_DEVELOPMENT_GOALS: "Definir objetivos de desarrollo",
      REVIEW_REPUTATION_RISKS: "Revisar riesgos reputacionales",
      OBTAIN_SECTION_APPROVALS: "Obtener aprobaciones humanas por sección",
      CONTINUE_HUMAN_GOVERNANCE: "Continuar gobierno y decisiones humanas",
    },
    sectionLabels: {
      identity: "Identidad",
      biography: "Biografía",
      purpose: "Propósito",
      values: "Valores",
      attributes: "Atributos",
      contradictions: "Contradicciones",
      development_goals: "Desarrollo",
      reputation: "Reputación",
    },
  },
  teamWorkspace: {
    eyebrow: "EQUIPO · RESPONSABILIDAD Y CAPACIDAD",
    title: "Mapa de equipo y responsabilidades",
    body: "Hace visibles roles, vacantes, capacidad, RACI, incorporación, formación y recomendaciones de acceso sin convertir etiquetas en permisos.",
    status: "Estado organizacional",
    progress: "pasos completos",
    nextAction: "Siguiente acción humana",
    authorityBoundary: "Las etiquetas de rol no son permisos",
    authorityBody:
      "Las recomendaciones de acceso requieren una autorización humana exacta y separada. Este espacio de trabajo no crea membresías, roles ni permisos.",
    roles: "Roles",
    filledRoles: "Roles cubiertos",
    vacantRoles: "Vacantes",
    capacity: "Capacidad semanal",
    workItems: "Responsabilidades RACI",
    training: "Formación",
    accessRecommendations: "Recomendaciones de acceso",
    notStarted:
      "El espacio de trabajo de equipo todavía no ha sido creado por una persona autorizada.",
    notAuthorized:
      "La sesión no tiene autorización exacta para revisar este equipo.",
    unavailable:
      "El espacio de trabajo de equipo no está disponible temporalmente. No se muestran datos parciales.",
    noItems: "Evaluado: no se registraron elementos.",
    notAssessed: "Pendiente de evaluación",
    readReceipt: "Comprobante de lectura",
    updatedAt: "Actualizado",
    hours: "horas",
    statusLabels: {
      SETUP_REQUIRED: "Estructura inicial requerida",
      STRUCTURE_IN_PROGRESS: "Estructura y capacidades en progreso",
      READY_FOR_HUMAN_REVIEW: "Listo para revisión humana",
    },
    checkLabels: {
      organization_template: "Seleccionar estructura",
      role_cards: "Definir tarjetas de rol",
      accountability: "Asignar responsabilidad RACI",
      availability: "Evaluar disponibilidad",
      vacancies: "Identificar vacantes",
      onboarding: "Completar incorporación",
      training: "Completar formación",
      access_review: "Revisar recomendaciones de acceso",
    },
    nextActionLabels: {
      SELECT_ORGANIZATION_TEMPLATE: "Seleccionar estructura organizacional",
      DEFINE_ROLE_CARDS: "Definir roles y responsabilidades",
      ASSIGN_ACCOUNTABILITY: "Asignar accountable y responsables",
      ASSESS_AVAILABILITY: "Evaluar disponibilidad y capacidad",
      PLAN_VACANCIES: "Crear planes para vacantes",
      COMPLETE_ONBOARDING: "Completar incorporación",
      COMPLETE_TRAINING: "Completar formación",
      REVIEW_ACCESS_RECOMMENDATIONS: "Revisar recomendaciones de acceso",
      CONTINUE_HUMAN_GOVERNANCE: "Continuar gobierno humano del equipo",
    },
    responsibilityLabels: {
      RESPONSIBLE: "Responsable",
      ACCOUNTABLE: "Accountable",
      CONSULTED: "Consultado",
      INFORMED: "Informado",
    },
  },
  strategyRoom: {
    eyebrow: "EVIDENCIA · HIPÓTESIS · DECISIÓN HUMANA",
    title: "Sala de estrategia y decisión",
    body: "Compara evidencia, supuestos, hipótesis, opciones y riesgos internos. No crea posicionamiento público, targeting, mensajes ni aprobación automática.",
    status: "Estado de preparación",
    nextAction: "Siguiente acción humana",
    evidence: "Evidencia",
    verified: "Verificada",
    inferred: "Inferida",
    unknown: "Desconocida",
    options: "Opciones comparables",
    objectives: "Objetivos medibles",
    contradictions: "Contradicciones abiertas",
    findings: "Hallazgos críticos/altos",
    decision: "Decisión interna",
    humanDecision: "La decisión pertenece a una persona autorizada",
    notStarted: "La sala de estrategia todavía no ha sido creada.",
    notAuthorized:
      "La sesión no tiene autorización exacta para revisar esta sala.",
    unavailable:
      "La sala de estrategia no está disponible temporalmente. No se muestran datos parciales.",
    noItems: "No hay elementos registrados en este estado.",
    authorityBoundary: "La evidencia informa; la persona autorizada decide",
    authorityBody:
      "Las opciones son internas y comparables. Ninguna recomendación autoriza contacto, publicación, gasto, movilización o efectos externos.",
    benefits: "Beneficios",
    risks: "Riesgos",
    tradeoffs: "Tradeoffs",
    metric: "Métrica",
    target: "Meta",
    deadline: "Fecha objetivo",
    readReceipt: "Comprobante de lectura",
    version: "Versión",
    statusLabels: {
      EVIDENCE_REQUIRED: "Se requiere evidencia verificada",
      CONTRADICTIONS_OPEN: "Contradicciones pendientes",
      RED_TEAM_BLOCKED: "Bloqueado por revisión adversarial",
      OPTIONS_INCOMPLETE: "Faltan opciones comparables",
      OBJECTIVES_INCOMPLETE: "Faltan objetivos medibles",
      READY_FOR_HUMAN_DECISION: "Listo para decisión humana",
      DECIDED_INTERNAL: "Decisión interna registrada",
    },
    nextActionLabels: {
      ADD_VERIFIED_EVIDENCE: "Agregar o validar evidencia",
      RESOLVE_CONTRADICTIONS: "Resolver contradicciones",
      ADDRESS_RED_TEAM_FINDINGS: "Cerrar hallazgos de red team",
      COMPLETE_COMPARABLE_OPTIONS: "Completar opciones comparables",
      DEFINE_MEASURABLE_OBJECTIVES: "Definir objetivos medibles",
      MAKE_HUMAN_DECISION: "Tomar decisión humana",
      REVALIDATE_DECISION: "Revalidar la decisión ante nueva evidencia",
    },
  },
  operations: {
    eyebrow: "ROADMAP · WAR ROOM DIARIO",
    title: "Ruta operativa y decisiones de hoy",
    body: "Ordena fases, dependencias, tareas, blockers y decisiones humanas. No ejecuta trabajo, no contacta personas y no sustituye a la dirección de campaña.",
    status: "Estado del roadmap",
    nextAction: "Siguiente acción humana",
    readyTasks: "Tareas listas",
    blockedTasks: "Tareas bloqueadas",
    criticalPath: "Ruta crítica",
    decisions: "Decisiones requeridas",
    blockers: "Blockers abiertos",
    priorities: "Prioridades de hoy",
    followUp: "Seguimiento",
    snapshot: "Último War Room",
    roadmapVersion: "Versión del roadmap",
    snapshotDate: "Fecha del snapshot",
    readReceipt: "Comprobante de lectura",
    authorityBoundary: "El roadmap coordina; no autoriza ni ejecuta",
    authorityBody:
      "Cada tarea sigue bajo responsabilidad humana. El snapshot es evidencia interna inmutable y no produce efectos externos.",
    notStarted:
      "El roadmap operativo todavía no ha sido creado por una persona autorizada.",
    notAuthorized:
      "La sesión no tiene autorización exacta para revisar este roadmap.",
    unavailable:
      "El roadmap no está disponible temporalmente. No se muestran datos parciales.",
    snapshotNotStarted:
      "Todavía no existe un snapshot diario para este roadmap.",
    snapshotNotAuthorized: "La sesión no puede revisar snapshots del War Room.",
    snapshotUnavailable: "El último snapshot no está disponible temporalmente.",
    noItems: "No hay elementos en este estado.",
    statusLabels: {
      SETUP_REQUIRED: "Roadmap inicial requerido",
      IN_PROGRESS: "Roadmap en progreso",
      READY_FOR_DAILY_OPERATION: "Listo para operación diaria humana",
      COMPLETE: "Roadmap completado; requiere revisión humana",
    },
    nextActionLabels: {
      DEFINE_ROADMAP: "Definir fases, workstreams y tareas",
      RESOLVE_BLOCKERS: "Resolver blockers abiertos",
      MAKE_HUMAN_DECISIONS: "Tomar decisiones humanas pendientes",
      START_READY_TASKS: "Asignar inicio a las tareas listas",
      CONTINUE_ACTIVE_WORK: "Continuar trabajo activo",
      REVIEW_COMPLETION: "Revisar evidencia de cierre",
    },
  },
  nav: {
    overview: "Resumen",
    campaigns: "Campañas",
    readiness: "Preparación",
    intake: "Ruta de inicio",
    candidate: "Candidatura",
    team: "Equipo",
    strategy: "Estrategia",
    warRoom: "War Room",
    evidence: "Evidencia",
    administration: "Administración",
  },
} as const;

type WidenStrings<T> = T extends string
  ? string
  : T extends object
    ? { [Key in keyof T]: WidenStrings<T[Key]> }
    : T;

export type Dictionary = WidenStrings<typeof es>;

const en: Dictionary = {
  metadata: {
    title: "CampaignOS · Command Center",
    description:
      "Governed campaign operations shell with human authority and traceable evidence.",
  },
  common: {
    skip: "Skip to content",
    product: "CampaignOS",
    readOnly: "READ ONLY",
    demo: "SYNTHETIC DEMO",
    live: "VERIFIED SESSION",
    notApproval:
      "This is not political, legal, financial, publication, or production approval.",
    localeLabel: "Language",
    spanish: "ES",
    english: "EN",
  },
  shell: {
    eyebrow: "CAMPAIGN OPERATING SYSTEM",
    title: "Turn your campaign into a system that moves",
    subtitle:
      "CampaignOS shows what to decide, what evidence is missing, and the next safe move.",
    authority:
      "AI recommends; evidence supports; the authorized person decides.",
    syntheticContext: "SYNTHETIC DATA · NO REAL CAMPAIGN",
    verifiedContext: "SERVER-VERIFIED CONTEXT",
    humanAuthority: "HUMAN DECISION",
    authorizationContext: "AUTHORIZATION CONTEXT",
    currentContext: "Current context",
    tenant: "Organization",
    campaign: "Campaign",
    principal: "Session",
    roles: "Visible responsibilities",
    authorizationFresh: "Permissions verified",
    modules: "Modules",
    reference: "Static visual reference preserved until parity review.",
  },
  states: {
    unauthenticatedTitle: "A verified session is required",
    unauthenticatedBody:
      "The shell does not expose a simulated login. OIDC integration and session lifecycle remain behind C3-IAM-002.",
    contextTitle: "Select an authorized context",
    contextBody:
      "A tenant selector does not create authority. CampaignOS requires a preselected tenant and revalidates permissions in the backend.",
    unavailableTitle: "A dependency is temporarily unavailable",
    unavailableBody:
      "No partial data or cross-tenant cache is shown. Keep the correlation ID for support.",
    emptyTitle: "No authorized campaigns",
    emptyBody:
      "The session is valid, but no campaign is visible under current exact grants.",
  },
  dashboard: {
    readinessEyebrow: "OPERATING FOUNDATION",
    readinessTitle: "Operational preparation",
    readinessBody:
      "Confirms that the campaign has the minimum context required to begin a guided path.",
    checks: "foundation steps complete",
    nextAction: "Next system step",
    authorityEyebrow: "EXACT PERMISSIONS",
    authorityTitle: "Permissions and responsibilities",
    authorityBody:
      "Responsibilities guide the work, but every action revalidates the exact permission, resource, and purpose.",
    grantCountLabel: "server-managed exact permissions",
    evidenceEyebrow: "TRACEABILITY",
    evidenceTitle: "Evidence and audit",
    evidenceBody:
      "Sensitive reads and saved changes produce traceable receipts.",
    auditReceipt: "Read receipt",
    noExternal: "No external effects",
    confirmed: "Confirmed",
    operationsEyebrow: "GUIDED SEQUENCE",
    operationsTitle: "How CampaignOS advances",
    operationsBody:
      "First establish the foundation; then enable evidence, team, strategy, and daily operations.",
    campaignStatus: "Campaign status",
    version: "Version",
    workspaceCount: "Active workspaces",
    limitationsEyebrow: "MANDATORY LIMITS",
    limitations: "Controls that remain in force",
    readinessCheckLabels: {
      campaign_name: "Campaign name defined",
      jurisdiction: "Territory defined",
      campaign_stage: "Campaign stage defined",
      active_workspace: "Active workspace",
    },
    readinessNextActionLabels: {
      COMPLETE_CAMPAIGN_METADATA: "Complete name, territory, and stage",
      CREATE_CAMPAIGN_WORKSPACE: "Create the initial workspace",
      BEGIN_GUIDED_INTAKE: "Begin the guided path",
    },
    sequence: {
      context: "Define context and purpose",
      workspace: "Organize the workspace",
      intake: "Complete campaign starting information",
      evidence: "Build evidence before strategy decisions",
    },
    limitationLabels: {
      NOT_A_HUMAN_APPROVAL: "Requires a decision by an authorized person",
      NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT:
        "There is not yet enough evidence for a strategy decision",
      NOT_A_STRATEGY: "This stage does not yet constitute a strategy",
      NO_CITIZEN_CONTACT_OR_PROFILING:
        "Does not enable citizen contact or individual profiles",
      NO_EXTERNAL_EFFECTS: "Produces no actions outside CampaignOS",
      NOT_PUBLIC_POSITIONING_APPROVAL:
        "Does not authorize public positioning or messages",
      NO_VOTER_PROFILING: "Does not enable individual voter profiles",
      HUMAN_REVIEW_REQUIRED: "Requires human review before advancing",
      ROLE_LABELS_ARE_NOT_PERMISSIONS: "Job labels do not grant permissions",
      ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION:
        "Access requires separate human authorization",
      HUMAN_DECISIONS_REQUIRED: "Critical decisions belong to the human team",
      NO_AUTONOMOUS_TASK_EXECUTION:
        "CampaignOS does not autonomously execute campaign tasks",
      NO_CITIZEN_CONTACT: "Does not enable citizen contact",
      NOT_PUBLIC_POSITIONING: "Does not constitute public positioning",
      NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING:
        "Does not enable individual profiling or targeting",
      NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS:
        "Does not contact people or produce external effects",
    },
  },
  journey: {
    eyebrow: "CAMPAIGN MASTER PATH",
    title: "Your campaign, step by step",
    body:
      "From the initial idea to daily operations, CampaignOS orders decisions, evidence, team, and follow-up without bypassing human controls.",
    progressLabel: "Campaign path progress",
    stageLabel: "Current stage",
    completedLabel: "stages complete",
    missionLabel: "Your mission now",
    openPhase: "View stage",
    blockedAction: "Requires additional access or enablement",
    boundary:
      "The path guides and organizes. It does not authorize publication, citizen contact, spending, mobilization, or production.",
    statusLabels: {
      COMPLETE: "Complete",
      ACTIVE: "In progress",
      AVAILABLE: "Next",
      BLOCKED: "Blocked by access or configuration",
      LOCKED: "Unlocks later",
    },
    phaseLabels: {
      foundation: "Ground the campaign",
      evidence: "Understand the candidacy and territory",
      team: "Organize the team",
      strategy: "Decide the strategy",
      operations: "Operate and learn every day",
    },
    phaseDescriptions: {
      foundation:
        "Define office, territory, purpose, team, assets, and budget capacity.",
      evidence:
        "Gather the electoral roll, historical results, community profiles, public sources, and verifiable evidence.",
      team:
        "Design coordinations, departments, owners, capacity, and the gaps that must be filled.",
      strategy:
        "Build a SWOT, objectives, hypotheses, and the balance between field, communications, and digital work.",
      operations:
        "Track goals, communities, owners, tasks, blockers, and War Room learning.",
    },
    phaseOutcomes: {
      foundation: "Outcome: a campaign that is understood and ready for research.",
      evidence: "Outcome: decisions based on evidence rather than intuition.",
      team: "Outcome: every function has an owner and visible capacity.",
      strategy: "Outcome: a human, measurable, reviewable direction.",
      operations: "Outcome: traceable daily follow-up and learning.",
    },
    phaseActions: {
      foundation: "Continue starting information",
      evidence: "Review candidacy and evidence",
      team: "Review team and responsibilities",
      strategy: "Open the strategy room",
      operations: "Open daily operations",
    },
  },
  campaigns: {
    eyebrow: "CAMPAIGN CONTEXT",
    title: "Choose the working campaign",
    body:
      "Selection changes only the visible context. The backend revalidates every grant and scope.",
    current: "Current campaign",
    selectLabel: "Authorized campaign",
    apply: "Use this campaign",
    help: "Only campaigns visible to the verified session are listed.",
  },
  notices: {
    campaign_selected: "Campaign context updated.",
    intake_started: "Intake started and persisted in PostgreSQL.",
    intake_saved: "Changes saved with a new version.",
    authorization_denied: "This session lacks exact authorization for the action.",
    conflict: "The record changed or the request key was reused. Reload and review the version.",
    validation_error: "Review the fields and try again.",
    dependency_failure: "A dependency is unavailable. No partial changes were saved.",
    unauthenticated: "The session is no longer valid.",
    not_found: "The requested resource is unavailable in this context.",
    request_failed: "The request could not be completed safely.",
  },
  intake: {
    eyebrow: "GUIDED START · EVIDENCE FIRST",
    title: "Build your campaign foundation",
    body:
      "Answer clear questions so CampaignOS can show what comes next, what evidence is missing, and what work must be organized.",
    startTitle: "Start the verifiable intake",
    startBody:
      "Creates the internal record and audit evidence. It does not start strategy, contact, or external execution.",
    startAction: "Start intake",
    editEyebrow: "AUTHORIZED EDITING",
    editTitle: "Tell us what you are starting with",
    editBody:
      "You can complete this information in stages. CampaignOS preserves the correct version and never overwrites changes silently.",
    onePerLine: "One item per line. Maximum 30.",
    officeHelp: "State the office you seek and confirm that it matches the campaign territory.",
    officePlaceholder: "Example: Municipal Mayor",
    budgetHelp: "Choose the evidence level currently available; the budget does not need to be final to begin.",
    candidateProjectHelp:
      "Explain why the candidacy exists, what change it seeks, and whom it intends to serve.",
    candidateProjectPlaceholder:
      "Example: Build a municipal candidacy based on evidence, community organization, and measurable results.",
    currentTeamHelp:
      "One person or function per line. Include coordinations, departments, and roles that remain vacant.",
    currentTeamPlaceholder:
      "General coordination — confirmed\nTerritory — to be defined",
    currentAssetsHelp:
      "Record current resources: files, channels, tools, office, vehicles, volunteers, or authorized alliances.",
    currentAssetsPlaceholder:
      "Document archive\nDigital channels\nTerritorial data tool",
    knownUnknownsHelp:
      "Record questions that must be answered before strategy decisions or execution.",
    knownUnknownsPlaceholder:
      "How many votes are required?\nWhich communities need more research?",
    evidenceRequirementsHelp:
      "List the data and documents required to answer those questions.",
    evidenceRequirementsPlaceholder:
      "Electoral roll\nHistorical results\nCommunity profiles\nPreliminary budget",
    checkComplete: "Complete",
    checkPending: "Pending",
    saveBoundary:
      "Saving updates only the internal intake; it does not approve strategy or activate external work.",
    saveAction: "Save changes",
    status: "Intake status",
    statusLabels: {
      BLOCKED_BY_CAMPAIGN_SETUP: "Blocked by campaign setup",
      IN_PROGRESS: "Preparation in progress",
      READY_FOR_RESEARCH: "Ready to begin research",
    },
    progress: "steps complete",
    nextAction: "Next step",
    checks: "Steps in this stage",
    researchActions: "What unlocks next",
    notStarted: "The intake has not yet been started by an authorized person.",
    notAuthorized:
      "This session lacks the exact authorization required to review this intake.",
    unavailable:
      "The intake is temporarily unavailable. Partial data is not displayed.",
    noItems: "Assessed: no items were recorded.",
    notAssessed: "Pending assessment",
    office: "Target office",
    candidateProject: "Candidate project",
    currentTeam: "Current team",
    currentAssets: "Current assets",
    budgetStatus: "Budget status",
    knownUnknowns: "Questions we must answer",
    evidenceRequirements: "Required data and documents",
    readReceipt: "Read receipt",
    updatedAt: "Updated",
    budgetStatusLabels: {
      NOT_ASSESSED: "Not assessed",
      NO_DOCUMENT: "No document",
      ROUGH_RANGE: "Preliminary range",
      DOCUMENTED: "Documented",
    },
    checkLabels: {
      campaign_operational_setup: "Complete operational setup",
      office: "Define the target office",
      candidate_project: "Describe the candidate project",
      current_team: "Assess the current team",
      current_assets: "Inventory current assets",
      budget_status: "Assess budget evidence",
      known_unknowns: "Record known questions",
      evidence_requirements: "Define required evidence",
    },
    nextActionLabels: {
      COMPLETE_CAMPAIGN_SETUP: "Complete campaign operational setup",
      DEFINE_TARGET_OFFICE: "Define the target office and jurisdiction",
      DESCRIBE_CANDIDATE_PROJECT: "Describe the candidate project",
      ASSESS_CURRENT_TEAM: "Assess team capacity and gaps",
      ASSESS_CURRENT_ASSETS: "Inventory assets and provenance",
      ASSESS_BUDGET_EVIDENCE: "Document the actual budget evidence",
      RECORD_KNOWN_UNKNOWNS: "Record what still needs to be resolved",
      DEFINE_EVIDENCE_REQUIREMENTS:
        "Define the evidence that must be collected",
      BEGIN_RESEARCH: "Begin verifiable research",
    },
    researchActionLabels: {
      VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE:
        "Verify office and jurisdiction evidence",
      VALIDATE_CANDIDATE_PROJECT_EVIDENCE: "Validate the candidate project",
      ASSESS_TEAM_CAPACITY_GAPS: "Research team capacity gaps",
      INVENTORY_ASSET_PROVENANCE: "Verify asset provenance",
      DOCUMENT_BUDGET_ASSUMPTIONS: "Document budget assumptions",
      RESEARCH_KNOWN_UNKNOWNS: "Research the known questions",
      COLLECT_REQUIRED_EVIDENCE: "Collect the required evidence",
    },
  },
  candidate: {
    eyebrow: "CANDIDATE · EVIDENCE AND HUMAN REVIEW",
    title: "Candidate executive workspace",
    body: "Separates claims, independent evidence, contradictions, development, and risk before any public decision.",
    status: "Internal status",
    progress: "checks complete",
    nextAction: "Next human action",
    sections: "Evidence sections",
    identity: "Identity",
    biography: "Biography",
    purpose: "Purpose",
    values: "Values",
    attributes: "Attributes",
    contradictions: "Contradictions",
    developmentGoals: "Development goals",
    reputationRisks: "Reputation risks",
    evidenceInventory: "Evidence inventory",
    approvedSections: "Approved sections",
    pendingApprovals: "Pending approvals",
    criticalHighRisks: "Open critical/high risks",
    publicBoundary: "Public use blocked",
    publicBoundaryBody:
      "Internal approval does not authorize public positioning, strategy, content, contact, spending, or mobilization.",
    notStarted:
      "The candidate workspace has not yet been created by an authorized person.",
    notAuthorized:
      "This session lacks the exact authorization required to review this candidate.",
    unavailable:
      "The candidate workspace is temporarily unavailable. Partial data is not displayed.",
    notAssessed: "Pending evidence and review",
    noItems: "Reviewed: no items were recorded.",
    readReceipt: "Read receipt",
    updatedAt: "Updated",
    statusLabels: {
      SETUP_REQUIRED: "Initial setup and evidence required",
      UNDER_REVIEW: "Evidence under review",
      AWAITING_APPROVAL: "Awaiting section approvals",
      INTERNALLY_APPROVED: "Internal approval complete",
    },
    checkLabels: {
      identity: "Verify identity",
      biography: "Document a verifiable biography",
      purpose: "Define purpose with evidence",
      values: "Verify declared values",
      attributes: "Corroborate attributes",
      contradictions: "Resolve contradictions",
      development_goals: "Define development needs",
      reputation: "Review reputation risks",
      approvals: "Obtain current approvals",
    },
    nextActionLabels: {
      DEFINE_IDENTITY: "Define and verify identity",
      DOCUMENT_BIOGRAPHY: "Document the biography",
      DEFINE_PURPOSE: "Define purpose and evidence",
      VERIFY_VALUES: "Verify values",
      VERIFY_ATTRIBUTES: "Corroborate attributes",
      REVIEW_CONTRADICTIONS: "Review contradictions",
      DEFINE_DEVELOPMENT_GOALS: "Define development goals",
      REVIEW_REPUTATION_RISKS: "Review reputation risks",
      OBTAIN_SECTION_APPROVALS: "Obtain human section approvals",
      CONTINUE_HUMAN_GOVERNANCE: "Continue human governance and decisions",
    },
    sectionLabels: {
      identity: "Identity",
      biography: "Biography",
      purpose: "Purpose",
      values: "Values",
      attributes: "Attributes",
      contradictions: "Contradictions",
      development_goals: "Development",
      reputation: "Reputation",
    },
  },
  teamWorkspace: {
    eyebrow: "TEAM · ACCOUNTABILITY AND CAPACITY",
    title: "Team and accountability map",
    body: "Makes roles, vacancies, capacity, RACI, onboarding, training, and access recommendations visible without turning labels into permissions.",
    status: "Organizational status",
    progress: "checks complete",
    nextAction: "Next human action",
    authorityBoundary: "Role labels are not permissions",
    authorityBody:
      "Access recommendations require a separate exact human authorization. This workspace creates no memberships, roles, or grants.",
    roles: "Roles",
    filledRoles: "Filled roles",
    vacantRoles: "Vacancies",
    capacity: "Weekly capacity",
    workItems: "RACI responsibilities",
    training: "Training",
    accessRecommendations: "Access recommendations",
    notStarted:
      "The team workspace has not yet been created by an authorized person.",
    notAuthorized:
      "This session lacks the exact authorization required to review this team.",
    unavailable:
      "The team workspace is temporarily unavailable. Partial data is not displayed.",
    noItems: "Assessed: no items were recorded.",
    notAssessed: "Pending assessment",
    readReceipt: "Read receipt",
    updatedAt: "Updated",
    hours: "hours",
    statusLabels: {
      SETUP_REQUIRED: "Initial structure required",
      STRUCTURE_IN_PROGRESS: "Structure and capacity in progress",
      READY_FOR_HUMAN_REVIEW: "Ready for human review",
    },
    checkLabels: {
      organization_template: "Select organization structure",
      role_cards: "Define role cards",
      accountability: "Assign RACI accountability",
      availability: "Assess availability",
      vacancies: "Identify vacancies",
      onboarding: "Complete onboarding",
      training: "Complete training",
      access_review: "Review access recommendations",
    },
    nextActionLabels: {
      SELECT_ORGANIZATION_TEMPLATE: "Select organization structure",
      DEFINE_ROLE_CARDS: "Define roles and responsibilities",
      ASSIGN_ACCOUNTABILITY: "Assign accountable and responsible roles",
      ASSESS_AVAILABILITY: "Assess availability and capacity",
      PLAN_VACANCIES: "Create vacancy plans",
      COMPLETE_ONBOARDING: "Complete onboarding",
      COMPLETE_TRAINING: "Complete training",
      REVIEW_ACCESS_RECOMMENDATIONS: "Review access recommendations",
      CONTINUE_HUMAN_GOVERNANCE: "Continue human team governance",
    },
    responsibilityLabels: {
      RESPONSIBLE: "Responsible",
      ACCOUNTABLE: "Accountable",
      CONSULTED: "Consulted",
      INFORMED: "Informed",
    },
  },
  strategyRoom: {
    eyebrow: "EVIDENCE · HYPOTHESES · HUMAN DECISION",
    title: "Strategy and decision room",
    body: "Compares internal evidence, assumptions, hypotheses, options, and risks. It does not create public positioning, targeting, messages, or automatic approval.",
    status: "Readiness status",
    nextAction: "Next human action",
    evidence: "Evidence",
    verified: "Verified",
    inferred: "Inferred",
    unknown: "Unknown",
    options: "Comparable options",
    objectives: "Measurable objectives",
    contradictions: "Open contradictions",
    findings: "Critical/high findings",
    decision: "Internal decision",
    humanDecision: "The decision belongs to an authorized person",
    notStarted: "The strategy room has not been created yet.",
    notAuthorized:
      "This session lacks exact authorization to review this room.",
    unavailable:
      "The strategy room is temporarily unavailable. Partial data is not displayed.",
    noItems: "No items are recorded in this state.",
    authorityBoundary: "Evidence informs; the authorized person decides",
    authorityBody:
      "Options are internal and comparable. No recommendation authorizes contact, publication, spending, mobilization, or external effects.",
    benefits: "Benefits",
    risks: "Risks",
    tradeoffs: "Tradeoffs",
    metric: "Metric",
    target: "Target",
    deadline: "Target date",
    readReceipt: "Read receipt",
    version: "Version",
    statusLabels: {
      EVIDENCE_REQUIRED: "Verified evidence required",
      CONTRADICTIONS_OPEN: "Contradictions remain open",
      RED_TEAM_BLOCKED: "Blocked by adversarial review",
      OPTIONS_INCOMPLETE: "Comparable options are incomplete",
      OBJECTIVES_INCOMPLETE: "Measurable objectives are incomplete",
      READY_FOR_HUMAN_DECISION: "Ready for human decision",
      DECIDED_INTERNAL: "Internal decision recorded",
    },
    nextActionLabels: {
      ADD_VERIFIED_EVIDENCE: "Add or validate evidence",
      RESOLVE_CONTRADICTIONS: "Resolve contradictions",
      ADDRESS_RED_TEAM_FINDINGS: "Close red-team findings",
      COMPLETE_COMPARABLE_OPTIONS: "Complete comparable options",
      DEFINE_MEASURABLE_OBJECTIVES: "Define measurable objectives",
      MAKE_HUMAN_DECISION: "Make the human decision",
      REVALIDATE_DECISION: "Revalidate the decision against new evidence",
    },
  },
  operations: {
    eyebrow: "ROADMAP · DAILY WAR ROOM",
    title: "Operating path and today's decisions",
    body: "Orders phases, dependencies, tasks, blockers, and human decisions. It does not execute work, contact people, or replace campaign leadership.",
    status: "Roadmap status",
    nextAction: "Next human action",
    readyTasks: "Ready tasks",
    blockedTasks: "Blocked tasks",
    criticalPath: "Critical path",
    decisions: "Required decisions",
    blockers: "Open blockers",
    priorities: "Today's priorities",
    followUp: "Follow-up",
    snapshot: "Latest War Room",
    roadmapVersion: "Roadmap version",
    snapshotDate: "Snapshot date",
    readReceipt: "Read receipt",
    authorityBoundary:
      "The roadmap coordinates; it does not authorize or execute",
    authorityBody:
      "Every task remains under human responsibility. The snapshot is immutable internal evidence and produces no external effects.",
    notStarted:
      "The operations roadmap has not yet been created by an authorized person.",
    notAuthorized:
      "This session lacks the exact authorization required to review this roadmap.",
    unavailable:
      "The roadmap is temporarily unavailable. Partial data is not displayed.",
    snapshotNotStarted: "No daily snapshot exists for this roadmap yet.",
    snapshotNotAuthorized: "This session cannot review War Room snapshots.",
    snapshotUnavailable: "The latest snapshot is temporarily unavailable.",
    noItems: "There are no items in this state.",
    statusLabels: {
      SETUP_REQUIRED: "Initial roadmap required",
      IN_PROGRESS: "Roadmap in progress",
      READY_FOR_DAILY_OPERATION: "Ready for human daily operation",
      COMPLETE: "Roadmap complete; human review required",
    },
    nextActionLabels: {
      DEFINE_ROADMAP: "Define phases, workstreams, and tasks",
      RESOLVE_BLOCKERS: "Resolve open blockers",
      MAKE_HUMAN_DECISIONS: "Make pending human decisions",
      START_READY_TASKS: "Assign the start of ready tasks",
      CONTINUE_ACTIVE_WORK: "Continue active work",
      REVIEW_COMPLETION: "Review completion evidence",
    },
  },
  nav: {
    overview: "Overview",
    campaigns: "Campaigns",
    readiness: "Preparation",
    intake: "Starting path",
    candidate: "Candidate",
    team: "Team",
    strategy: "Strategy",
    warRoom: "War Room",
    evidence: "Evidence",
    administration: "Administration",
  },
};

export const dictionaries: Readonly<Record<Locale, Dictionary>> = { es, en };

export function dictionaryFor(locale: Locale): Dictionary {
  return dictionaries[locale];
}
