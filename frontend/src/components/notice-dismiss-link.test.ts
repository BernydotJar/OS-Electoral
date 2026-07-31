import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

import { NoticeDismissLink } from "@/components/notice-dismiss-link";

describe("NoticeDismissLink", () => {
  it("renders a safe server fallback while client dismissal preserves the live hash", () => {
    const html = renderToStaticMarkup(
      createElement(NoticeDismissLink, {
        fallbackHref: "/es/campaign/team#team-workspace",
        label: "Cerrar aviso",
      }),
    );

    expect(html).toContain('href="/es/campaign/team#team-workspace"');
    expect(html).toContain("Cerrar aviso");
  });
});
