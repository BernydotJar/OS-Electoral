export const locales = ["es", "en"] as const;
export type Locale = (typeof locales)[number];

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}

const es = {
  metadata: {
    title: "CampaignOS · Command Center",
    description: "Shell operativo gobernado para campañas con autoridad humana y evidencia trazable.",
  },
  common: {
    skip: "Saltar al contenido",
    product: "CampaignOS",
    readOnly: "SOLO LECTURA",
    demo: "DEMO SINTÉTICO",
    live: "SESIÓN VERIFICADA",
    notApproval: "No constituye aprobación política, legal, financiera, de publicación ni de producción.",
    localeLabel: "Idioma",
    spanish: "ES",
    english: "EN",
  },
  shell: {
    eyebrow: "CAMPAIGN OPERATING SYSTEM",
    title: "Centro de mando gobernado",
    subtitle: "Contexto, evidencia y próximos pasos internos sin sustituir a la autoridad humana.",
    authority: "La IA recomienda; la evidencia sustenta; la persona autorizada decide.",
    currentContext: "Contexto actual",
    tenant: "Tenant",
    campaign: "Campaña",
    principal: "Sesión",
    roles: "Roles informativos",
    authorizationFresh: "Autorización evaluada",
    modules: "Módulos",
    reference: "Referencia visual estática preservada hasta revisión de paridad.",
  },
  states: {
    unauthenticatedTitle: "Se requiere una sesión verificada",
    unauthenticatedBody:
      "El shell no expone un login simulado. La integración OIDC y el ciclo de sesión permanecen detrás de C3-IAM-002.",
    contextTitle: "Selecciona un contexto autorizado",
    contextBody:
      "El selector de tenant no crea autoridad. CampaignOS requiere un tenant preseleccionado y vuelve a validar permisos en el backend.",
    unavailableTitle: "Dependencia temporalmente no disponible",
    unavailableBody:
      "No se muestran datos parciales ni cachés cruzados. Conserva el correlation ID para soporte.",
    emptyTitle: "No hay campañas autorizadas",
    emptyBody: "La sesión es válida, pero no existe una campaña visible bajo grants exactos vigentes.",
  },
  dashboard: {
    readinessTitle: "Readiness operativo",
    readinessBody: "Mide únicamente setup mínimo para iniciar intake guiado.",
    checks: "checks completos",
    nextAction: "Siguiente acción interna",
    authorityTitle: "Límite de autoridad",
    authorityBody:
      "Roles ayudan a orientar la navegación; nunca conceden permisos. Cada operación debe coincidir exactamente con grant, recurso, propósito y scope.",
    evidenceTitle: "Evidencia y auditoría",
    evidenceBody: "Las lecturas sensibles y escrituras exitosas producen receipts trazables en el backend.",
    auditReceipt: "Receipt de lectura",
    noExternal: "Sin efectos externos",
    operationsTitle: "Ruta operativa",
    operationsBody: "Completa metadatos, configura workspace y comienza intake antes de estrategia o comunicación.",
    campaignStatus: "Estado de campaña",
    version: "Versión",
    workspaceCount: "Workspaces activos",
    limitations: "Limitaciones obligatorias",
  },
  intake: {
    eyebrow: "INTAKE GUIADO · INVESTIGACIÓN PRIMERO",
    title: "Hoja de ruta para comenzar la campaña",
    body:
      "Ordena la información mínima antes de investigar, decidir estrategia o activar trabajo externo.",
    status: "Estado del intake",
    statusLabels: {
      BLOCKED_BY_CAMPAIGN_SETUP: "Bloqueado por configuración de campaña",
      IN_PROGRESS: "Preparación en progreso",
      READY_FOR_RESEARCH: "Listo para comenzar investigación",
    },
    progress: "pasos completos",
    nextAction: "Siguiente paso",
    checks: "Ruta de preparación",
    researchActions: "Investigación habilitada",
    notStarted: "El intake todavía no ha sido iniciado por una persona autorizada.",
    notAuthorized: "La sesión no tiene autorización exacta para revisar este intake.",
    unavailable: "El intake no está disponible temporalmente. No se muestran datos parciales.",
    noItems: "Evaluado: no se registraron elementos.",
    notAssessed: "Pendiente de evaluación",
    office: "Cargo objetivo",
    candidateProject: "Proyecto de candidatura",
    currentTeam: "Equipo actual",
    currentAssets: "Activos actuales",
    budgetStatus: "Evidencia presupuestaria",
    knownUnknowns: "Preguntas conocidas",
    evidenceRequirements: "Evidencia requerida",
    readReceipt: "Receipt de lectura",
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
      COMPLETE_CAMPAIGN_SETUP: "Completar la configuración operativa de la campaña",
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
      VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE: "Verificar cargo y jurisdicción con evidencia",
      VALIDATE_CANDIDATE_PROJECT_EVIDENCE: "Validar el proyecto de candidatura",
      ASSESS_TEAM_CAPACITY_GAPS: "Investigar vacíos de capacidad del equipo",
      INVENTORY_ASSET_PROVENANCE: "Verificar procedencia de los activos",
      DOCUMENT_BUDGET_ASSUMPTIONS: "Documentar supuestos presupuestarios",
      RESEARCH_KNOWN_UNKNOWNS: "Resolver las preguntas conocidas",
      COLLECT_REQUIRED_EVIDENCE: "Recopilar la evidencia requerida",
    },
  },
  nav: {
    overview: "Resumen",
    campaigns: "Campañas",
    readiness: "Readiness",
    intake: "Comenzar campaña",
    team: "Equipo",
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
    description: "Governed campaign operations shell with human authority and traceable evidence.",
  },
  common: {
    skip: "Skip to content",
    product: "CampaignOS",
    readOnly: "READ ONLY",
    demo: "SYNTHETIC DEMO",
    live: "VERIFIED SESSION",
    notApproval: "This is not political, legal, financial, publication, or production approval.",
    localeLabel: "Language",
    spanish: "ES",
    english: "EN",
  },
  shell: {
    eyebrow: "CAMPAIGN OPERATING SYSTEM",
    title: "Governed command center",
    subtitle: "Context, evidence, and internal next steps without replacing human authority.",
    authority: "AI recommends; evidence supports; the authorized person decides.",
    currentContext: "Current context",
    tenant: "Tenant",
    campaign: "Campaign",
    principal: "Session",
    roles: "Informational roles",
    authorizationFresh: "Authorization evaluated",
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
    emptyBody: "The session is valid, but no campaign is visible under current exact grants.",
  },
  dashboard: {
    readinessTitle: "Operational readiness",
    readinessBody: "Measures only the minimum setup required to begin guided intake.",
    checks: "checks complete",
    nextAction: "Next internal action",
    authorityTitle: "Authority boundary",
    authorityBody:
      "Roles orient navigation but never grant permission. Every operation must match the exact grant, resource, purpose, and scope.",
    evidenceTitle: "Evidence and audit",
    evidenceBody: "Sensitive reads and successful writes produce traceable backend receipts.",
    auditReceipt: "Read receipt",
    noExternal: "No external effects",
    operationsTitle: "Operating path",
    operationsBody: "Complete metadata, configure a workspace, and begin intake before strategy or communications.",
    campaignStatus: "Campaign status",
    version: "Version",
    workspaceCount: "Active workspaces",
    limitations: "Mandatory limitations",
  },
  intake: {
    eyebrow: "GUIDED INTAKE · RESEARCH FIRST",
    title: "Campaign starting roadmap",
    body:
      "Structures the minimum information before research, strategy decisions, or external work begins.",
    status: "Intake status",
    statusLabels: {
      BLOCKED_BY_CAMPAIGN_SETUP: "Blocked by campaign setup",
      IN_PROGRESS: "Preparation in progress",
      READY_FOR_RESEARCH: "Ready to begin research",
    },
    progress: "steps complete",
    nextAction: "Next step",
    checks: "Preparation path",
    researchActions: "Enabled research",
    notStarted: "The intake has not yet been started by an authorized person.",
    notAuthorized: "This session lacks the exact authorization required to review this intake.",
    unavailable: "The intake is temporarily unavailable. Partial data is not displayed.",
    noItems: "Assessed: no items were recorded.",
    notAssessed: "Pending assessment",
    office: "Target office",
    candidateProject: "Candidate project",
    currentTeam: "Current team",
    currentAssets: "Current assets",
    budgetStatus: "Budget evidence",
    knownUnknowns: "Known questions",
    evidenceRequirements: "Required evidence",
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
      DEFINE_EVIDENCE_REQUIREMENTS: "Define the evidence that must be collected",
      BEGIN_RESEARCH: "Begin verifiable research",
    },
    researchActionLabels: {
      VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE: "Verify office and jurisdiction evidence",
      VALIDATE_CANDIDATE_PROJECT_EVIDENCE: "Validate the candidate project",
      ASSESS_TEAM_CAPACITY_GAPS: "Research team capacity gaps",
      INVENTORY_ASSET_PROVENANCE: "Verify asset provenance",
      DOCUMENT_BUDGET_ASSUMPTIONS: "Document budget assumptions",
      RESEARCH_KNOWN_UNKNOWNS: "Research the known questions",
      COLLECT_REQUIRED_EVIDENCE: "Collect the required evidence",
    },
  },
  nav: {
    overview: "Overview",
    campaigns: "Campaigns",
    readiness: "Readiness",
    intake: "Start campaign",
    team: "Team",
    warRoom: "War Room",
    evidence: "Evidence",
    administration: "Administration",
  },
};

export const dictionaries: Readonly<Record<Locale, Dictionary>> = { es, en };

export function dictionaryFor(locale: Locale): Dictionary {
  return dictionaries[locale];
}
