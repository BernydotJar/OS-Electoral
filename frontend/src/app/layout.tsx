import type { Metadata } from "next";
import { headers } from "next/headers";

import "./globals.css";
import { dictionaries, isLocale } from "@/lib/i18n";

export async function generateMetadata(): Promise<Metadata> {
  const value = (await headers()).get("x-campaignos-locale") ?? "es";
  const locale = isLocale(value) ? value : "es";
  return dictionaries[locale].metadata;
}

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const value = (await headers()).get("x-campaignos-locale") ?? "es";
  const locale = isLocale(value) ? value : "es";
  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  );
}
