import { notFound } from "next/navigation";

import { CampaignShell } from "@/components/shell";
import { dictionaryFor, isLocale } from "@/lib/i18n";
import { loadShellViewModel } from "@/lib/shell-view-model";

export const dynamic = "force-dynamic";

export default async function LocalePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const model = await loadShellViewModel();
  return <CampaignShell locale={locale} dictionary={dictionaryFor(locale)} model={model} />;
}
