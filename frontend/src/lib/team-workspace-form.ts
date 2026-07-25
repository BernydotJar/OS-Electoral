import type {
  TeamOrganizationTemplate,
  TeamRoleCard,
  TeamWorkspaceCreateInput,
} from "@/lib/contracts";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TEMPLATES = new Set<TeamOrganizationTemplate>([
  "LEAN_CAMPAIGN",
  "FULL_CAMPAIGN",
  "CUSTOM",
]);

export class TeamWorkspaceFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new TeamWorkspaceFormError(`${name} is required`);
  }
  return value;
}

function locale(form: FormData): "es" | "en" {
  const value = field(form, "locale");
  if (value !== "es" && value !== "en") {
    throw new TeamWorkspaceFormError("Locale is invalid");
  }
  return value;
}

function requiredText(form: FormData, name: string, maximum: number): string {
  const value = field(form, name).trim().replace(/\s+/g, " ");
  if (!value || value.length > maximum) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function idempotencyKey(form: FormData): string {
  const value = field(form, "idempotency_key").trim();
  if (!validIdempotencyKey(value)) {
    throw new TeamWorkspaceFormError("Idempotency key is invalid");
  }
  return value;
}

function expectedVersion(form: FormData): number {
  const value = Number(field(form, "version"));
  if (!Number.isInteger(value) || value < 1) {
    throw new TeamWorkspaceFormError("Version is invalid");
  }
  return value;
}

function responsibilities(form: FormData): readonly string[] {
  const values = field(form, "responsibilities")
    .split(/\r?\n/)
    .map((value) => value.trim().replace(/\s+/g, " "))
    .filter(Boolean);
  if (values.length < 1 || values.length > 20) {
    throw new TeamWorkspaceFormError("Responsibilities are invalid");
  }
  if (values.some((value) => value.length > 500)) {
    throw new TeamWorkspaceFormError("Responsibility is too long");
  }
  if (new Set(values.map((value) => value.toLocaleLowerCase())).size !== values.length) {
    throw new TeamWorkspaceFormError("Responsibilities contain duplicates");
  }
  return values;
}

export type ParsedTeamWorkspaceStartForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: TeamWorkspaceCreateInput;
}>;

export function parseTeamWorkspaceStartForm(
  form: FormData,
): ParsedTeamWorkspaceStartForm {
  const organizationTemplate = field(
    form,
    "organization_template",
  ) as TeamOrganizationTemplate;
  if (!TEMPLATES.has(organizationTemplate)) {
    throw new TeamWorkspaceFormError("Organization template is invalid");
  }
  return {
    locale: locale(form),
    idempotencyKey: idempotencyKey(form),
    create: { organization_template: organizationTemplate },
  };
}

export type ParsedTeamRoleForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  role: TeamRoleCard;
}>;

export function parseTeamRoleForm(
  form: FormData,
  roleId: string,
): ParsedTeamRoleForm {
  if (!UUID_PATTERN.test(roleId)) {
    throw new TeamWorkspaceFormError("Role ID is invalid");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    role: {
      id: roleId,
      title: requiredText(form, "title", 160),
      area: requiredText(form, "area", 160),
      purpose: requiredText(form, "purpose", 1000),
      responsibilities: responsibilities(form),
      status: "VACANT",
      principal_id: null,
      availability_status: "UNASSESSED",
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED",
      vacancy_plan: requiredText(form, "vacancy_plan", 1000),
    },
  };
}
