import { notFound } from "next/navigation";

import { CampaignShell } from "@/components/shell";
import type { TeamBlueprintTemplate } from "@/lib/contracts";
import { dictionaryFor, isLocale } from "@/lib/i18n";
import { loadShellViewModel } from "@/lib/shell-view-model";
import { parseUiNotice } from "@/lib/ui-notices";

export const dynamic = "force-dynamic";

export default async function LocalePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    notice?: string | string[];
    team_template?: string | string[];
  }>;
}) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  if (!isLocale(locale)) notFound();
  const requestedTemplate = Array.isArray(query.team_template)
    ? query.team_template[0]
    : query.team_template;
  const teamTemplate = (
    requestedTemplate === "LEAN_CAMPAIGN" ||
    requestedTemplate === "FULL_CAMPAIGN"
      ? requestedTemplate
      : null
  ) as TeamBlueprintTemplate | null;
  const model = await loadShellViewModel({
    locale,
    teamTemplatePreview: teamTemplate
      ? { organization_template: teamTemplate, blueprint_locale: locale }
      : null,
  });
  return (
    <CampaignShell
      locale={locale}
      dictionary={dictionaryFor(locale)}
      model={model}
      notice={parseUiNotice(query.notice)}
    />
  );
}
