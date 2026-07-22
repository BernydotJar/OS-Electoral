import { NextResponse } from "next/server";

import type { UiNotice } from "@/lib/ui-notices";

export function noticeRedirect(
  request: Request,
  locale: "es" | "en",
  notice: UiNotice,
  hash: string,
): NextResponse {
  const destination = new URL(`/${locale}`, request.url);
  destination.searchParams.set("notice", notice);
  destination.hash = hash;
  return NextResponse.redirect(destination, 303);
}
