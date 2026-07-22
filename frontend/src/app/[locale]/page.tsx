import { notFound } from "next/navigation";

import { CampaignShell } from "@/components/shell";
import { dictionaryFor, isLocale } from "@/lib/i18n";
import { loadShellViewModel } from "@/lib/shell-view-model";
import { parseUiNotice } from "@/lib/ui-notices";

export const dynamic = "force-dynamic";

export default async function LocalePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ notice?: string | string[] }>;
}) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  if (!isLocale(locale)) notFound();
  const model = await loadShellViewModel();
  return (
    <CampaignShell
      locale={locale}
      dictionary={dictionaryFor(locale)}
      model={model}
      notice={parseUiNotice(query.notice)}
    />
  );
}
