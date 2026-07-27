import { NextResponse } from "next/server";

import {
  campaignChapterKeyForAnchor,
  campaignChapterPath,
} from "@/lib/campaign-chapters";
import type { UiNotice } from "@/lib/ui-notices";

export function noticeRedirect(
  request: Request,
  locale: "es" | "en",
  notice: UiNotice,
  hash: string,
): NextResponse {
  const chapter = campaignChapterKeyForAnchor(hash);
  const pathname = chapter
    ? campaignChapterPath(locale, chapter)
    : `/${locale}`;
  const destination = new URL(pathname, request.url);
  destination.searchParams.set("notice", notice);
  destination.hash = hash;
  return NextResponse.redirect(destination, 303);
}
