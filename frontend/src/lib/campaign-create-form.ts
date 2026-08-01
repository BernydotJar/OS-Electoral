import type { CampaignCreateInput } from "@/lib/contracts";

export class CampaignCreateFormError extends Error {}

export type ParsedCampaignCreateForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: CampaignCreateInput;
}>;

const IDEMPOTENCY_PATTERN =
  /^campaign-create:([0-9a-f]{8}-[0-9a-f]{4})-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function requiredText(
  form: FormData,
  key: string,
  maximum: number,
): string {
  const value = form.get(key);
  if (typeof value !== "string") {
    throw new CampaignCreateFormError(`${key} is required`);
  }
  const normalized = value.trim().replace(/\s+/g, " ");
  if (!normalized || normalized.length > maximum) {
    throw new CampaignCreateFormError(`${key} is invalid`);
  }
  return normalized;
}

function slugBase(name: string): string {
  const normalized = name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80)
    .replace(/-+$/g, "");
  return normalized || "campaign";
}

export function parseCampaignCreateForm(
  form: FormData,
): ParsedCampaignCreateForm {
  const locale = form.get("locale");
  if (locale !== "es" && locale !== "en") {
    throw new CampaignCreateFormError("locale is invalid");
  }
  const idempotencyKey = form.get("idempotency_key");
  if (typeof idempotencyKey !== "string") {
    throw new CampaignCreateFormError("idempotency key is required");
  }
  const idempotencyMatch = IDEMPOTENCY_PATTERN.exec(idempotencyKey);
  if (idempotencyMatch === null) {
    throw new CampaignCreateFormError("idempotency key is invalid");
  }
  const rawSlugSuffix = idempotencyMatch[1];
  if (rawSlugSuffix === undefined) {
    throw new CampaignCreateFormError("idempotency key is invalid");
  }
  const slugSuffix = rawSlugSuffix.replace("-", "");
  const name = requiredText(form, "name", 255);
  const jurisdiction = requiredText(form, "jurisdiction", 255);
  return {
    locale,
    idempotencyKey,
    create: {
      slug: `${slugBase(name)}-${slugSuffix}`,
      name,
      jurisdiction,
      stage: "PREPARATION",
    },
  };
}
