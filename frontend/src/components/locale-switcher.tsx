"use client";

import type { Dictionary, Locale } from "@/lib/i18n";

function changeDocumentLocale(locale: Locale): void {
  window.location.assign(`/${locale}`);
}

export function LocaleSwitcher({
  locale,
  dictionary,
}: {
  locale: Locale;
  dictionary: Dictionary;
}) {
  return (
    <div className="locale-switcher" role="group" aria-label={dictionary.common.localeLabel}>
      <button
        type="button"
        lang="es"
        data-locale-switch
        aria-pressed={locale === "es"}
        onClick={() => changeDocumentLocale("es")}
      >
        {dictionary.common.spanish}
      </button>
      <button
        type="button"
        lang="en"
        data-locale-switch
        aria-pressed={locale === "en"}
        onClick={() => changeDocumentLocale("en")}
      >
        {dictionary.common.english}
      </button>
    </div>
  );
}
