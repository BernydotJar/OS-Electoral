import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { isLocale } from "@/lib/i18n";

function preferredLocale(request: NextRequest): "es" | "en" {
  const language = request.headers.get("accept-language")?.toLowerCase() ?? "";
  return language.startsWith("en") ? "en" : "es";
}

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (pathname === "/") {
    return NextResponse.redirect(new URL(`/${preferredLocale(request)}`, request.url));
  }
  const segment = pathname.split("/").filter(Boolean)[0];
  if (!segment || !isLocale(segment)) {
    return NextResponse.redirect(new URL(`/${preferredLocale(request)}`, request.url));
  }
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-campaignos-locale", segment);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
