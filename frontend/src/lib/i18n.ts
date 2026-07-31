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
    technicalDetails: "Ver detalles técnicos y permisos",
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
      HUMAN_DECISIONS_REQUIRED:
        "Las decisiones críticas pertenecen al equipo humano",
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
    body: "Desde la idea inicial hasta la operación diaria, CampaignOS ordena decisiones, evidencia, equipo y seguimiento sin saltarse los controles humanos.",
    firstUseEyebrow: "TU CAMPAÑA EMPIEZA AQUÍ",
    firstUseTitle:
      "Convierte una idea política en una campaña que sabe avanzar",
    firstUseBody:
      "Define la base una vez. Después CampaignOS conservará el contexto y te mostrará la misión, la evidencia y la decisión que siguen.",
    firstUseAction: "Comenzar la ruta",
    activeEyebrow: "MISIÓN ACTIVA",
    activeBody:
      "No vuelves a empezar. Continúa desde el punto exacto donde quedó la campaña y cierra el siguiente gate con evidencia.",
    resumeAction: "Continuar misión",
    completeEyebrow: "RUTA OPERATIVA COMPLETA",
    completeTitle: "La campaña ya tiene un sistema de trabajo verificable",
    completeBody:
      "La ruta está completa, pero las decisiones, revisiones y efectos externos continúan bajo autoridad humana.",
    commandCenterLabel: "CENTRO DE MANDO",
    commandCenterAction: "Abrir operación diaria",
    commandPriorityLabel: "FOCO DE DECISIÓN ACTUAL",
    statusLabel: "Estado",
    outcomeLabel: "Resultado esperado",
    stageNavigationLabel: "Atajos de las etapas de campaña",
    explorePathLabel: "Explorar la ruta completa",
    explorePathBody:
      "Revisa cada etapa, su resultado esperado y el espacio de trabajo que la sostiene.",
    chapterMapLabel: "Ver mapa de la campaña",
    chapterMapBody:
      "Abre la navegación completa sin desplazar el espacio de trabajo principal.",
    progressLabel: "Progreso de la ruta de campaña",
    contextHintLabel: "Por qué importa",
    chapterNavigationLabel: "Navegación por capítulos",
    backToOverview: "Volver al centro de mando",
    previousChapter: "Capítulo anterior",
    nextChapter: "Siguiente capítulo",
    currentChapter: "Capítulo actual",
    chapterUnavailable:
      "El capítulo solicitado todavía está bloqueado. Mostramos la misión disponible más cercana.",
    stageLabel: "Etapa actual",
    completedLabel: "etapas completadas",
    missionLabel: "Tu misión ahora",
    chapterLabel: "CAPÍTULO",
    openPhase: "Ver etapa",
    blockedAction: "Requiere habilitación o acceso adicional",
    blockedTitle: "Esta etapa todavía no está disponible",
    blockedBody:
      "Completa el paso anterior o solicita a tu consultor el permiso exacto para continuar.",
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
      team: "Diseña coordinaciones, secretarías, responsables, capacidad y vacíos que debes cubrir.",
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
      operations:
        "Resultado: seguimiento diario con trazabilidad y aprendizaje.",
    },
    phaseActions: {
      foundation: "Continuar información de arranque",
      evidence: "Revisar candidatura y evidencia",
      team: "Revisar equipo y responsabilidades",
      strategy: "Abrir sala de estrategia",
      operations: "Abrir operación diaria",
    },
    sceneLabels: {
      foundation: "Territorio",
      evidence: "Evidencia",
      team: "Equipo",
      strategy: "Estrategia",
      operations: "Operación",
    },
    missionPulseLabel: "Cadencia de misión",
    missionPulseStages: {
      evidence: "Evidencia",
      decision: "Decisión humana",
      execution: "Ejecución gobernada",
    },
  },
  campaigns: {
    eyebrow: "CONTEXTO DE CAMPAÑA",
    title: "Elige la campaña de trabajo",
    body: "La selección cambia únicamente el contexto visible. El servidor vuelve a validar cada permiso y alcance.",
    current: "Campaña actual",
    selectLabel: "Campaña autorizada",
    apply: "Usar esta campaña",
    help: "Sólo aparecen campañas visibles para la sesión verificada.",
  },
  notices: {
    campaign_selected: "Contexto de campaña actualizado.",
    intake_started: "Ruta guiada creada y guardada en PostgreSQL.",
    intake_saved: "Cambios guardados con nueva versión.",
    candidate_started:
      "Expediente de candidatura creado y listo para documentar.",
    candidate_evidence_saved:
      "Fuente incorporada al expediente con una nueva versión.",
    team_started:
      "Mapa de equipo creado con funciones iniciales listas para revisión.",
    team_role_saved:
      "Función incorporada al mapa de equipo con una nueva versión.",
    team_work_item_saved:
      "Seguimiento operativo agregado al tablero con una nueva versión.",
    team_work_item_updated:
      "Check-in operativo guardado con estado, salud y siguiente acción actualizados.",
    team_template_applied:
      "Plantilla aplicada: se conservaron las funciones existentes y se agregaron sólo las ausentes.",
    authorization_denied:
      "La sesión no tiene autorización exacta para esta acción.",
    conflict:
      "El registro cambió o la solicitud ya fue utilizada. Recarga y revisa la versión.",
    validation_error: "Revisa los campos señalados y vuelve a intentar.",
    dependency_failure:
      "Una dependencia no está disponible. No se guardaron cambios parciales.",
    unauthenticated: "La sesión ya no es válida.",
    not_found: "El recurso solicitado no está disponible en este contexto.",
    request_failed: "La solicitud no pudo completarse de forma segura.",
  },
  intake: {
    eyebrow: "INICIO GUIADO · EVIDENCIA PRIMERO",
    title: "Construye la base de tu campaña",
    body: "Responde preguntas claras para que CampaignOS pueda indicarte qué sigue, qué evidencia falta y qué trabajo debe organizarse.",
    completedTitle: "Ver la configuración registrada",
    completedBody:
      "Consulta aquí lo que ingresaste y abre la edición cuando necesites actualizarlo.",
    startTitle: "Comenzar la ruta guiada",
    startBody:
      "Crea el registro interno y su evidencia de auditoría. No inicia estrategia, contacto ni ejecución externa.",
    startAction: "Comenzar ruta",
    editEyebrow: "EDICIÓN AUTORIZADA",
    editTitle: "Cuéntanos con qué estás comenzando",
    editBody:
      "Puedes completar esta información por etapas. CampaignOS conserva la versión correcta y nunca reemplaza cambios en silencio.",
    onePerLine: "Un elemento por línea. Máximo 30.",
    officeHelp:
      "Indica el cargo que buscas y confirma que corresponde al territorio de la campaña.",
    officePlaceholder: "Ej. Alcaldía Municipal",
    budgetHelp:
      "Selecciona el nivel de evidencia disponible; no necesitas tener el presupuesto cerrado para comenzar.",
    candidateProjectHelp:
      "Explica por qué nace la candidatura, qué cambio busca y a quién desea servir.",
    candidateProjectPlaceholder:
      "Ej. Queremos construir una candidatura municipal basada en evidencia, organización comunitaria y resultados medibles.",
    currentTeamHelp:
      "Selecciona las funciones que ya existen y agrega cualquier coordinación o vacante que todavía no aparezca.",
    currentTeamPlaceholder:
      "Coordinación general — confirmada\nTerritorio — por definir",
    currentTeamPresetLabel: "Función sugerida",
    currentTeamCustomLabel: "Otra función o coordinación",
    currentTeamCustomPlaceholder: "Ej. Coordinación jurídica",
    currentTeamAddAction: "Agregar función",
    currentTeamSelectedLabel: "Equipo registrado",
    currentTeamRemoveAction: "Quitar",
    currentTeamEmpty: "Todavía no registraste funciones del equipo.",
    currentTeamBoundary:
      "Estas selecciones describen capacidad existente; no asignan identidad, autoridad ni permisos.",
    currentTeamOptions: {
      campaignChief: "Dirección de campaña",
      research: "Investigación electoral",
      territory: "Territorio y movilización",
      communication: "Comunicación y narrativa",
      digital: "Estrategia digital",
      legalFinance: "Legal, administración y finanzas",
      logistics: "Logística y agenda",
      warRoom: "Seguimiento, riesgos y aprendizaje",
    },
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
    startEyebrow: "ABRIR EXPEDIENTE",
    startTitle: "Crea el expediente verificable de la candidatura",
    startBody:
      "Este espacio organiza identidad, trayectoria, propósito, fuentes, contradicciones y riesgos. Crear el expediente no aprueba posicionamiento público.",
    displayName: "Nombre público de la candidatura",
    displayNamePlaceholder: "Ej. Ana Pérez",
    displayNameHelp:
      "Usa el nombre que permita identificar el expediente; todavía no constituye una marca aprobada.",
    startAction: "Crear expediente",
    evidenceEditorEyebrow: "INVESTIGACIÓN CON PROCEDENCIA",
    evidenceEditorTitle: "Incorpora una fuente verificable",
    evidenceEditorBody:
      "Agrega una fuente por vez. CampaignOS conserva su clasificación, procedencia, jurisdicción y versión para que el equipo pueda revisarla.",
    evidenceClassification: "Tipo de fuente",
    evidenceClassificationLabels: {
      OFFICIAL_SOURCE: "Fuente oficial",
      CAMPAIGN_RESEARCH: "Investigación de campaña",
      PERCEPTION: "Percepción",
      HYPOTHESIS: "Hipótesis",
      UNKNOWN: "Clasificación pendiente",
    },
    evidenceTitle: "Título de la fuente",
    evidenceTitlePlaceholder: "Ej. Acuerdo de convocatoria electoral",
    sourceReference: "Enlace verificable",
    sourceReferenceHelp:
      "Debe usar HTTPS y apuntar a la fuente original cuando exista.",
    sourceAuthority: "Autoridad o institución",
    sourceAuthorityPlaceholder: "Ej. Tribunal Electoral",
    sourceAuthorityUnknown: "Autoridad pendiente",
    evidenceJurisdiction: "Jurisdicción",
    evidenceJurisdictionPlaceholder: "Ej. Municipio, departamento o país",
    observedAt: "Fecha observada",
    evidenceExcerpt: "Nota de relevancia",
    evidenceExcerptPlaceholder:
      "Explica qué confirma esta fuente y qué todavía no demuestra.",
    evidenceBoundary:
      "Registrar una fuente no la convierte en verdad ni autoriza estrategia. El equipo debe contrastarla y resolver contradicciones.",
    addEvidenceAction: "Agregar fuente",
    sourceRegister: "Fuentes registradas",
    openSource: "Abrir fuente",
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
    publicBoundary: "Preparación interna activa",
    publicBoundaryBody:
      "La aprobación interna no autoriza posicionamiento público, estrategia, contenido, contacto, gasto ni movilización.",
    notStarted:
      "El espacio de trabajo de candidatura todavía no ha sido creado por una persona autorizada.",
    prerequisitePending:
      "Completa primero la base de campaña. El expediente se habilita cuando la ruta queda lista para investigación.",
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
    workspaceViewLabel: "Vistas del expediente de candidatura",
    actionViewLabel: "Qué hacer ahora",
    profileViewLabel: "Perfil y riesgos",
    evidenceViewLabel: "Fuentes y evidencia",
    actionBriefEyebrow: "INSIGHTS · SIGUIENTE DECISIÓN",
    actionBriefTitle: "Qué debemos resolver ahora",
    actionBriefBody:
      "CampaignOS convierte vacíos, riesgos y revisiones pendientes en trabajo preparatorio trazable. No decide estrategia ni autoriza uso público.",
    actionBriefBoundary:
      "Puedes probar, documentar y organizar esta sección. Las publicaciones y demás efectos externos conservan revisión separada.",
    zeroVerifiedSources: "0 fuentes verificables",
    actionInsightLabels: {
      NEXT_ACTION: "Siguiente acción humana",
      EVIDENCE_GAP: "Falta evidencia verificable",
      CONTRADICTIONS_OPEN: "Contradicciones abiertas",
      RISK_DECISION_REQUIRED: "Riesgos que requieren decisión",
      DEVELOPMENT_ACTIVE: "Desarrollo pendiente",
      APPROVALS_PENDING: "Aprobaciones pendientes",
    },
    actionInsightBodies: {
      NEXT_ACTION:
        "Avanza el siguiente gate sin saltar evidencia ni aprobación.",
      EVIDENCE_GAP:
        "Agrega fuentes oficiales o investigación de campaña con procedencia.",
      CONTRADICTIONS_OPEN:
        "Contrasta las versiones y documenta la resolución antes de usar la declaración.",
      RISK_DECISION_REQUIRED:
        "Eleva el riesgo a revisión humana con evidencia y responsable.",
      DEVELOPMENT_ACTIVE:
        "Convierte el objetivo de desarrollo en preparación, responsable y evidencia.",
      APPROVALS_PENDING:
        "Obtén aprobaciones vigentes por sección antes de avanzar.",
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
    prerequisitePending:
      "Abre primero el expediente de candidatura. La preparación del equipo se habilita en paralelo con la investigación.",
    startEyebrow: "PREPARACIÓN PARALELA",
    startTitle: "Elige una estructura para empezar a organizar la campaña",
    startBody:
      "Comienza con una estructura proporcional al tamaño real de la campaña. Después documenta funciones, vacantes, responsables y capacidad sin confundir cargos con permisos.",
    organizationTemplate: "Modelo organizativo",
    organizationTemplateHelp:
      "Puedes ampliarlo después. Elegir una estructura no crea personas, cargos formales ni accesos.",
    templateGuideTitle: "Qué incluye cada estructura",
    templateDescriptions: {
      LEAN_CAMPAIGN:
        "Incluye 5 funciones esenciales con propósito, responsabilidades y plan humano para cubrir cada vacante.",
      FULL_CAMPAIGN:
        "Incluye las 8 estaciones operativas de CampaignOS como descripciones de puesto vacantes y editables.",
      CUSTOM:
        "Inicia sin funciones predeterminadas para que la organización sea definida completamente por el equipo.",
    },
    templateLabels: {
      LEAN_CAMPAIGN: "Campaña compacta",
      FULL_CAMPAIGN: "Campaña completa",
      CUSTOM: "Estructura personalizada",
    },
    startAction: "Crear mapa de equipo",
    templateApplyEyebrow: "AMPLIAR SIN SOBRESCRIBIR",
    templateApplyTitle: "Aplica una estructura al mapa existente",
    templateApplyBody:
      "Previsualiza qué funciones faltan. CampaignOS conservará las existentes y sólo agregará vacantes nuevas después de tu confirmación.",
    templatePreviewAction: "Previsualizar cambios",
    templatePreviewUnavailable:
      "El preview no está disponible con la versión actual. Recarga antes de confirmar cambios.",
    templateAdditionsTitle: "Funciones nuevas propuestas",
    templateSkippedTitle: "Funciones existentes que se conservarán",
    templateAddedCount: "funciones nuevas",
    templateSkippedCount: "funciones conservadas",
    templatePreviewVersion: "Versión del catálogo",
    templateConfirmAction: "Aplicar funciones nuevas",
    templateConfirmBoundary:
      "Esta confirmación agrega únicamente funciones vacantes. No asigna personas, capacidad, membresías, permisos ni accesos.",
    templateNoChanges:
      "El mapa ya contiene todas las funciones reconocidas de esta plantilla. No hay cambios que aplicar.",
    templateExactMatch: "Coincidencia exacta de nombre y área",
    templateCanonicalMatch:
      "La misma función ya existe en otra variante de idioma",
    roleEditorEyebrow: "FUNCIÓN Y RESULTADO",
    roleEditorTitle: "Documenta la siguiente función que necesita la campaña",
    roleEditorBody:
      "Define qué debe lograr esta función y cómo sabremos que está cubierta. La persona responsable se asignará después mediante identidad gobernada.",
    roleTitle: "Nombre de la función",
    roleTitlePlaceholder: "Ej. Coordinación territorial",
    roleArea: "Área",
    roleAreaPlaceholder: "Ej. Territorio",
    areaOptions: {
      direction: "Dirección de campaña",
      communication: "Comunicación",
      territory: "Territorio",
      legalFinance: "Legal y finanzas",
      support: "Logística y apoyo",
      warRoom: "War Room",
    },
    rolePurpose: "Resultado que debe producir",
    rolePurposePlaceholder:
      "Ej. Convertir el objetivo territorial en cobertura organizada y verificable.",
    roleResponsibilities: "Responsabilidades principales",
    roleResponsibilitiesPlaceholder:
      "Diseñar coordinaciones\nDar seguimiento a cobertura\nEscalar bloqueos",
    oneResponsibilityPerLine: "Una responsabilidad por línea. Máximo 20.",
    vacancyPlan: "Plan para cubrir la función",
    vacancyPlanPlaceholder:
      "Define el perfil, el proceso de selección y la aprobación humana requerida.",
    roleBoundary:
      "Registrar una función no asigna a una persona, no crea membresías y no concede permisos. La vacante permanece visible hasta una asignación gobernada.",
    addRoleAction: "Agregar función",
    roleStatusLabels: {
      FILLED: "Cubierta",
      VACANT: "Vacante",
    },
    status: "Estado organizacional",
    progress: "pasos completos",
    progressGuidanceTitle: "Qué falta para completar esta etapa",
    progressGuidanceBody: "El indicador resume preparación del equipo. Completa estos puntos para llegar al siguiente estado:",
    progressDetailsAction: "Ver los 8 pasos y su estado",
    nextAction: "Siguiente acción humana",
    authorityBoundary: "Las etiquetas de rol no son permisos",
    authorityBody:
      "Las recomendaciones de acceso requieren una autorización humana exacta y separada. Este espacio de trabajo no crea membresías, roles ni permisos.",
    roles: "Funciones y descripciones de puesto",
    roleResponsibilitiesLabel: "Responsabilidades del puesto",
    consultingReadout: "LECTURA CONSULTIVA",
    roleDossierAction: "Abrir expediente operativo",
    roleDossierMissing:
      "Esta función histórica aún no tiene expediente consultivo. Complétalo antes de asignar responsabilidad.",
    decisionScopeLabel: "Decisiones que prepara o eleva",
    deliverablesLabel: "Entregables verificables",
    collaborationPointsLabel: "Interacciones clave",
    successSignalsLabel: "Señales de funcionamiento",
    decisionScopePlaceholder:
      "Preparar prioridades para decisión humana\nElevar cambios que requieren aprobación",
    deliverablesPlaceholder:
      "Agenda semanal\nRegistro de decisiones\nMapa de bloqueos",
    collaborationPointsPlaceholder:
      "Investigación y estrategia\nLegal, finanzas y operación",
    successSignalsPlaceholder:
      "Prioridades con responsable y fecha\nDecisiones pendientes visibles\nSin autoridad implícita",
    consultingListHelp: "Una entrada por línea. Entre 1 y 12 entradas.",
    vacancyPlanLabel: "Plan humano de cobertura",
    filledRoles: "Roles cubiertos",
    vacantRoles: "Vacantes",
    capacity: "Capacidad semanal",
    workItems: "Responsabilidades RACI",
    operationsEyebrow: "SEGUIMIENTO · BLOQUEOS · PRÓXIMA ACCIÓN",
    operationsTitle: "Operación del equipo",
    operationsBody:
      "Convierte cada función en trabajo verificable. Revisa qué avanza, qué requiere decisión y qué debe ocurrir después.",
    operationsViewLabel: "Vista de operación del equipo",
    boardViewAction: "Tablero operativo",
    createViewAction: "Crear seguimiento",
    commandViewLabel: "Vista de mando",
    commandViewBoundary:
      "Esta vista amplia requiere autorización de mando. La vista individual por función se habilitará sólo con asignaciones de identidad y permisos gobernados.",
    workPulse: "Pulso operativo del equipo",
    attention: "Requieren atención",
    filterRole: "Filtrar por función",
    allRoles: "Todas las funciones",
    filterStatus: "Filtrar por estado",
    allStatuses: "Todos los estados",
    noWorkItems:
      "Aún no hay seguimiento operativo. Crea la primera tarea o entregable desde una función.",
    createWorkItem: "Crear seguimiento operativo",
    plannedBoundary:
      "El trabajo nace planificado. Para activarlo, las funciones accountable y responsables deben estar cubiertas por personas autorizadas.",
    workRole: "Función accountable y responsable",
    workType: "Tipo de trabajo",
    workTypeLabels: {
      TASK: "Tarea",
      DELIVERABLE: "Entregable",
      CHECK_IN: "Revisión periódica",
      DECISION_PREP: "Preparación de decisión",
    },
    priority: "Prioridad",
    priorityLabels: {
      CRITICAL: "Crítica",
      HIGH: "Alta",
      MEDIUM: "Media",
      LOW: "Baja",
    },
    cadence: "Cadencia",
    cadenceLabels: {
      AD_HOC: "Sin recurrencia",
      DAILY: "Diaria",
      WEEKLY: "Semanal",
      BIWEEKLY: "Quincenal",
      MONTHLY: "Mensual",
    },
    workName: "Nombre del seguimiento",
    workDescription: "Resultado y alcance",
    targetDate: "Fecha objetivo",
    workNextAction: "Siguiente acción concreta",
    workEvidence: "Evidencia o comprobantes esperados",
    workEvidenceHelp:
      "Una referencia por línea. No incluyas datos personales sensibles.",
    addWorkItem: "Agregar al tablero",
    workStatus: "Estado del trabajo",
    workStatusLabels: {
      PLANNED: "Planificado",
      ACTIVE: "En curso",
      BLOCKED: "Bloqueado",
      COMPLETE: "Completado",
    },
    health: "Salud reportada",
    healthLabels: {
      NOT_REPORTED: "Sin reporte",
      ON_TRACK: "En curso normal",
      AT_RISK: "En riesgo",
      OFF_TRACK: "Fuera de rumbo",
    },
    assignedFunction: "Función accountable",
    blocker: "Bloqueo",
    operationalDetails: "Ver evidencia, RACI y check-in",
    checkInNote: "Nota del check-in humano",
    lastCheckIn: "Último check-in",
    updateWorkItem: "Actualizar estado y salud",
    activateRequiresFilledRole:
      "Para activar, bloquear o completar trabajo, las funciones accountable y responsables deben estar cubiertas.",
    saveCheckIn: "Guardar check-in",
    roleDetailAction: "Ver función y expediente",
    roleWorkCount: "seguimientos",
    roleAttentionCount: "requieren atención",
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
    intake: "Preparación inicial",
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
    technicalDetails: "View technical details and permissions",
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
    body: "From the initial idea to daily operations, CampaignOS orders decisions, evidence, team, and follow-up without bypassing human controls.",
    firstUseEyebrow: "YOUR CAMPAIGN STARTS HERE",
    firstUseTitle:
      "Turn a political idea into a campaign that knows how to move",
    firstUseBody:
      "Define the foundation once. CampaignOS will then preserve context and show the next mission, evidence, and decision.",
    firstUseAction: "Start the path",
    activeEyebrow: "ACTIVE MISSION",
    activeBody:
      "You do not start over. Continue from the campaign's exact position and close the next gate with evidence.",
    resumeAction: "Continue mission",
    completeEyebrow: "OPERATING PATH COMPLETE",
    completeTitle: "The campaign now has a verifiable operating system",
    completeBody:
      "The path is complete, while decisions, reviews, and external effects remain under human authority.",
    commandCenterLabel: "COMMAND CENTER",
    commandCenterAction: "Open daily operations",
    commandPriorityLabel: "CURRENT DECISION FOCUS",
    statusLabel: "Status",
    outcomeLabel: "Expected outcome",
    stageNavigationLabel: "Campaign stage shortcuts",
    explorePathLabel: "Explore the complete path",
    explorePathBody:
      "Review every stage, its expected outcome, and the workspace that supports it.",
    chapterMapLabel: "View campaign map",
    chapterMapBody:
      "Open the complete navigation without pushing the primary workspace below the fold.",
    progressLabel: "Campaign path progress",
    contextHintLabel: "Why this matters",
    chapterNavigationLabel: "Chapter navigation",
    backToOverview: "Back to command center",
    previousChapter: "Previous chapter",
    nextChapter: "Next chapter",
    currentChapter: "Current chapter",
    chapterUnavailable:
      "The requested chapter is still locked. The nearest available mission is shown instead.",
    stageLabel: "Current stage",
    completedLabel: "stages complete",
    missionLabel: "Your mission now",
    chapterLabel: "CHAPTER",
    openPhase: "View stage",
    blockedAction: "Requires additional access or enablement",
    blockedTitle: "This stage is not available yet",
    blockedBody:
      "Complete the previous step or ask your consultant for the exact permission required to continue.",
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
      team: "Design coordinations, departments, owners, capacity, and the gaps that must be filled.",
      strategy:
        "Build a SWOT, objectives, hypotheses, and the balance between field, communications, and digital work.",
      operations:
        "Track goals, communities, owners, tasks, blockers, and War Room learning.",
    },
    phaseOutcomes: {
      foundation:
        "Outcome: a campaign that is understood and ready for research.",
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
    sceneLabels: {
      foundation: "Territory",
      evidence: "Evidence",
      team: "Team",
      strategy: "Strategy",
      operations: "Operations",
    },
    missionPulseLabel: "Mission cadence",
    missionPulseStages: {
      evidence: "Evidence",
      decision: "Human decision",
      execution: "Governed execution",
    },
  },
  campaigns: {
    eyebrow: "CAMPAIGN CONTEXT",
    title: "Choose the working campaign",
    body: "Selection changes only the visible context. The backend revalidates every grant and scope.",
    current: "Current campaign",
    selectLabel: "Authorized campaign",
    apply: "Use this campaign",
    help: "Only campaigns visible to the verified session are listed.",
  },
  notices: {
    campaign_selected: "Campaign context updated.",
    intake_started: "Intake started and persisted in PostgreSQL.",
    intake_saved: "Changes saved with a new version.",
    candidate_started: "Candidate dossier created and ready for evidence.",
    candidate_evidence_saved: "Source added to the dossier with a new version.",
    team_started: "Team map created with initial functions ready for review.",
    team_role_saved: "Function added to the team map with a new version.",
    team_work_item_saved:
      "Operational follow-up added to the board with a new version.",
    team_work_item_updated:
      "Operational check-in saved with updated status, health, and next action.",
    team_template_applied:
      "Template applied: existing functions were preserved and only missing roles were added.",
    authorization_denied:
      "This session lacks exact authorization for the action.",
    conflict:
      "The record changed or the request key was reused. Reload and review the version.",
    validation_error: "Review the fields and try again.",
    dependency_failure:
      "A dependency is unavailable. No partial changes were saved.",
    unauthenticated: "The session is no longer valid.",
    not_found: "The requested resource is unavailable in this context.",
    request_failed: "The request could not be completed safely.",
  },
  intake: {
    eyebrow: "GUIDED START · EVIDENCE FIRST",
    title: "Build your campaign foundation",
    body: "Answer clear questions so CampaignOS can show what comes next, what evidence is missing, and what work must be organized.",
    completedTitle: "View saved setup",
    completedBody:
      "The foundation is already recorded. Open it only when you need to review or update the starting configuration.",
    startTitle: "Start the verifiable intake",
    startBody:
      "Creates the internal record and audit evidence. It does not start strategy, contact, or external execution.",
    startAction: "Start intake",
    editEyebrow: "AUTHORIZED EDITING",
    editTitle: "Tell us what you are starting with",
    editBody:
      "You can complete this information in stages. CampaignOS preserves the correct version and never overwrites changes silently.",
    onePerLine: "One item per line. Maximum 30.",
    officeHelp:
      "State the office you seek and confirm that it matches the campaign territory.",
    officePlaceholder: "Example: Municipal Mayor",
    budgetHelp:
      "Choose the evidence level currently available; the budget does not need to be final to begin.",
    candidateProjectHelp:
      "Explain why the candidacy exists, what change it seeks, and whom it intends to serve.",
    candidateProjectPlaceholder:
      "Example: Build a municipal candidacy based on evidence, community organization, and measurable results.",
    currentTeamHelp:
      "Select the functions already present and add any coordination or vacancy that is still missing.",
    currentTeamPlaceholder:
      "General coordination — confirmed\nTerritory — to be defined",
    currentTeamPresetLabel: "Suggested function",
    currentTeamCustomLabel: "Another function or coordination",
    currentTeamCustomPlaceholder: "E.g. Legal coordination",
    currentTeamAddAction: "Add function",
    currentTeamSelectedLabel: "Registered team",
    currentTeamRemoveAction: "Remove",
    currentTeamEmpty: "No team functions have been registered yet.",
    currentTeamBoundary:
      "These selections describe existing capacity; they assign no identity, authority, or permission.",
    currentTeamOptions: {
      campaignChief: "Campaign direction",
      research: "Electoral research",
      territory: "Territory and mobilization",
      communication: "Communication and narrative",
      digital: "Digital strategy",
      legalFinance: "Legal, administration, and finance",
      logistics: "Logistics and agenda",
      warRoom: "Tracking, risks, and learning",
    },
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
    startEyebrow: "OPEN DOSSIER",
    startTitle: "Create the candidate's verifiable dossier",
    startBody:
      "This workspace organizes identity, history, purpose, sources, contradictions, and risks. Creating it does not approve public positioning.",
    displayName: "Candidate public name",
    displayNamePlaceholder: "Example: Ana Perez",
    displayNameHelp:
      "Use a name that identifies the dossier; it is not yet an approved brand.",
    startAction: "Create dossier",
    evidenceEditorEyebrow: "RESEARCH WITH PROVENANCE",
    evidenceEditorTitle: "Add a verifiable source",
    evidenceEditorBody:
      "Add one source at a time. CampaignOS preserves classification, provenance, jurisdiction, and version for team review.",
    evidenceClassification: "Source type",
    evidenceClassificationLabels: {
      OFFICIAL_SOURCE: "Official source",
      CAMPAIGN_RESEARCH: "Campaign research",
      PERCEPTION: "Perception",
      HYPOTHESIS: "Hypothesis",
      UNKNOWN: "Pending classification",
    },
    evidenceTitle: "Source title",
    evidenceTitlePlaceholder: "Example: Electoral call resolution",
    sourceReference: "Verifiable link",
    sourceReferenceHelp:
      "Must use HTTPS and point to the original source when available.",
    sourceAuthority: "Authority or institution",
    sourceAuthorityPlaceholder: "Example: Electoral Tribunal",
    sourceAuthorityUnknown: "Authority pending",
    evidenceJurisdiction: "Jurisdiction",
    evidenceJurisdictionPlaceholder:
      "Example: Municipality, region, or country",
    observedAt: "Observed date",
    evidenceExcerpt: "Relevance note",
    evidenceExcerptPlaceholder:
      "Explain what this source confirms and what it still does not prove.",
    evidenceBoundary:
      "Registering a source does not make it true or authorize strategy. The team must contrast it and resolve contradictions.",
    addEvidenceAction: "Add source",
    sourceRegister: "Registered sources",
    openSource: "Open source",
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
    publicBoundary: "Internal preparation active",
    publicBoundaryBody:
      "Internal approval does not authorize public positioning, strategy, content, contact, spending, or mobilization.",
    notStarted:
      "The candidate workspace has not yet been created by an authorized person.",
    prerequisitePending:
      "Complete the campaign foundation first. The dossier unlocks when the path is ready for research.",
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
    workspaceViewLabel: "Candidate workspace views",
    actionViewLabel: "What to do now",
    profileViewLabel: "Profile and risks",
    evidenceViewLabel: "Sources and evidence",
    actionBriefEyebrow: "INSIGHTS · NEXT DECISION",
    actionBriefTitle: "What we need to resolve now",
    actionBriefBody:
      "CampaignOS turns gaps, risks, and pending reviews into traceable preparation work. It does not decide strategy or authorize public use.",
    actionBriefBoundary:
      "You can test, document, and organize this section. Publishing and other external effects retain a separate review gate.",
    zeroVerifiedSources: "0 verified sources",
    actionInsightLabels: {
      NEXT_ACTION: "Next human action",
      EVIDENCE_GAP: "Verifiable evidence is missing",
      CONTRADICTIONS_OPEN: "Open contradictions",
      RISK_DECISION_REQUIRED: "Risks requiring a decision",
      DEVELOPMENT_ACTIVE: "Development work pending",
      APPROVALS_PENDING: "Approvals pending",
    },
    actionInsightBodies: {
      NEXT_ACTION:
        "Advance the next gate without skipping evidence or approval.",
      EVIDENCE_GAP:
        "Add official sources or campaign research with provenance.",
      CONTRADICTIONS_OPEN:
        "Compare versions and document resolution before using the claim.",
      RISK_DECISION_REQUIRED:
        "Escalate the risk for human review with evidence and an owner.",
      DEVELOPMENT_ACTIVE:
        "Turn the development goal into preparation, ownership, and evidence.",
      APPROVALS_PENDING: "Obtain current section approvals before proceeding.",
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
    prerequisitePending:
      "Open the candidate dossier first. Team preparation then becomes available in parallel with research.",
    startEyebrow: "PARALLEL PREPARATION",
    startTitle: "Choose a structure to begin organizing the campaign",
    startBody:
      "Start with a structure proportional to the real campaign. Then document functions, vacancies, accountability, and capacity without confusing titles with permissions.",
    organizationTemplate: "Organization model",
    organizationTemplateHelp:
      "You can expand it later. Selecting a structure creates no people, formal positions, or access.",
    templateGuideTitle: "What each structure includes",
    templateDescriptions: {
      LEAN_CAMPAIGN:
        "Includes 5 essential functions with purpose, responsibilities, and a human plan for each vacancy.",
      FULL_CAMPAIGN:
        "Includes the 8 CampaignOS operating stations as vacant, editable job descriptions.",
      CUSTOM:
        "Starts without predefined functions so the team can define the organization completely.",
    },
    templateLabels: {
      LEAN_CAMPAIGN: "Lean campaign",
      FULL_CAMPAIGN: "Full campaign",
      CUSTOM: "Custom structure",
    },
    startAction: "Create team map",
    templateApplyEyebrow: "EXPAND WITHOUT OVERWRITING",
    templateApplyTitle: "Apply a structure to the existing map",
    templateApplyBody:
      "Preview which functions are missing. CampaignOS preserves existing roles and adds only new vacancies after your confirmation.",
    templatePreviewAction: "Preview changes",
    templatePreviewUnavailable:
      "The preview is unavailable for the current version. Reload before confirming changes.",
    templateAdditionsTitle: "Proposed new functions",
    templateSkippedTitle: "Existing functions that will be preserved",
    templateAddedCount: "new functions",
    templateSkippedCount: "preserved functions",
    templatePreviewVersion: "Catalog version",
    templateConfirmAction: "Apply new functions",
    templateConfirmBoundary:
      "This confirmation adds vacant functions only. It assigns no people, capacity, memberships, permissions, or access.",
    templateNoChanges:
      "The map already contains every recognized function in this template. There are no changes to apply.",
    templateExactMatch: "Exact title and area match",
    templateCanonicalMatch:
      "The same function already exists in another language variant",
    roleEditorEyebrow: "FUNCTION AND OUTCOME",
    roleEditorTitle: "Document the next function the campaign needs",
    roleEditorBody:
      "Define what this function must achieve and how coverage will be recognized. A person is assigned later through governed identity.",
    roleTitle: "Function name",
    roleTitlePlaceholder: "Example: Field coordination",
    roleArea: "Area",
    roleAreaPlaceholder: "Example: Field",
    areaOptions: {
      direction: "Campaign leadership",
      communication: "Communications",
      territory: "Field",
      legalFinance: "Legal and finance",
      support: "Logistics and support",
      warRoom: "War Room",
    },
    rolePurpose: "Outcome this function must produce",
    rolePurposePlaceholder:
      "Example: Turn the field objective into organized, verifiable coverage.",
    roleResponsibilities: "Core responsibilities",
    roleResponsibilitiesPlaceholder:
      "Design coordination layers\nTrack coverage\nEscalate blockers",
    oneResponsibilityPerLine: "One responsibility per line. Maximum 20.",
    vacancyPlan: "Plan to fill the function",
    vacancyPlanPlaceholder:
      "Define the profile, selection process, and required human approval.",
    roleBoundary:
      "Registering a function assigns no person, creates no membership, and grants no permission. The vacancy remains visible until governed assignment.",
    addRoleAction: "Add function",
    roleStatusLabels: {
      FILLED: "Filled",
      VACANT: "Vacant",
    },
    status: "Organizational status",
    progress: "checks complete",
    progressGuidanceTitle: "What remains to complete this stage",
    progressGuidanceBody: "The indicator summarizes team readiness. Complete these points to reach the next state:",
    progressDetailsAction: "View all 8 steps and their status",
    nextAction: "Next human action",
    authorityBoundary: "Role labels are not permissions",
    authorityBody:
      "Access recommendations require a separate exact human authorization. This workspace creates no memberships, roles, or grants.",
    roles: "Functions and job descriptions",
    roleResponsibilitiesLabel: "Job responsibilities",
    consultingReadout: "CONSULTING READOUT",
    roleDossierAction: "Open operating dossier",
    roleDossierMissing:
      "This historical function has no consulting dossier yet. Complete it before assigning responsibility.",
    decisionScopeLabel: "Decisions prepared or escalated",
    deliverablesLabel: "Verifiable deliverables",
    collaborationPointsLabel: "Key interactions",
    successSignalsLabel: "Operating signals",
    decisionScopePlaceholder:
      "Prepare priorities for human decision\nElevate changes requiring approval",
    deliverablesPlaceholder: "Weekly agenda\nDecision register\nBlocker map",
    collaborationPointsPlaceholder:
      "Research and strategy\nLegal, finance, and operations",
    successSignalsPlaceholder:
      "Priorities have owner and date\nPending decisions are visible\nNo implicit authority",
    consultingListHelp: "One entry per line. Between 1 and 12 entries.",
    vacancyPlanLabel: "Human coverage plan",
    filledRoles: "Filled roles",
    vacantRoles: "Vacancies",
    capacity: "Weekly capacity",
    workItems: "RACI responsibilities",
    operationsEyebrow: "FOLLOW-UP · BLOCKERS · NEXT ACTION",
    operationsTitle: "Team operations",
    operationsBody:
      "Turn every function into verifiable work. Review what is moving, what requires a decision, and what must happen next.",
    operationsViewLabel: "Team operations view",
    boardViewAction: "Operations board",
    createViewAction: "Create follow-up",
    commandViewLabel: "Command view",
    commandViewBoundary:
      "This broad view requires command authorization. Per-function views will be enabled only through governed identity assignments and permissions.",
    workPulse: "Team operating pulse",
    attention: "Need attention",
    filterRole: "Filter by function",
    allRoles: "All functions",
    filterStatus: "Filter by status",
    allStatuses: "All statuses",
    noWorkItems:
      "No operational follow-up exists yet. Create the first task or deliverable from a function.",
    createWorkItem: "Create operational follow-up",
    plannedBoundary:
      "Work starts as planned. To activate it, accountable and responsible functions must be filled by authorized people.",
    workRole: "Accountable and responsible function",
    workType: "Work type",
    workTypeLabels: {
      TASK: "Task",
      DELIVERABLE: "Deliverable",
      CHECK_IN: "Recurring review",
      DECISION_PREP: "Decision preparation",
    },
    priority: "Priority",
    priorityLabels: {
      CRITICAL: "Critical",
      HIGH: "High",
      MEDIUM: "Medium",
      LOW: "Low",
    },
    cadence: "Cadence",
    cadenceLabels: {
      AD_HOC: "No recurrence",
      DAILY: "Daily",
      WEEKLY: "Weekly",
      BIWEEKLY: "Biweekly",
      MONTHLY: "Monthly",
    },
    workName: "Follow-up name",
    workDescription: "Outcome and scope",
    targetDate: "Target date",
    workNextAction: "Concrete next action",
    workEvidence: "Expected evidence or receipts",
    workEvidenceHelp:
      "One reference per line. Do not include sensitive personal data.",
    addWorkItem: "Add to board",
    workStatus: "Work status",
    workStatusLabels: {
      PLANNED: "Planned",
      ACTIVE: "In progress",
      BLOCKED: "Blocked",
      COMPLETE: "Complete",
    },
    health: "Reported health",
    healthLabels: {
      NOT_REPORTED: "Not reported",
      ON_TRACK: "On track",
      AT_RISK: "At risk",
      OFF_TRACK: "Off track",
    },
    assignedFunction: "Accountable function",
    blocker: "Blocker",
    operationalDetails: "View evidence, RACI, and check-in",
    checkInNote: "Human check-in note",
    lastCheckIn: "Last check-in",
    updateWorkItem: "Update status and health",
    activateRequiresFilledRole:
      "To activate, block, or complete work, accountable and responsible functions must be filled.",
    saveCheckIn: "Save check-in",
    roleDetailAction: "View function and dossier",
    roleWorkCount: "follow-ups",
    roleAttentionCount: "need attention",
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
    intake: "Initial preparation",
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
