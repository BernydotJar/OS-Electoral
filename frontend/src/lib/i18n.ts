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
  nav: {
    overview: "Resumen",
    campaigns: "Campañas",
    readiness: "Readiness",
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
  nav: {
    overview: "Overview",
    campaigns: "Campaigns",
    readiness: "Readiness",
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
