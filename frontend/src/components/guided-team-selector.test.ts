import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { GuidedTeamSelector } from "@/components/guided-team-selector";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");

describe("GuidedTeamSelector", () => {
  it("renders guided role options, persisted chips, and the canonical current_team field", () => {
    const html = renderToStaticMarkup(
      createElement(GuidedTeamSelector, {
        dictionary,
        defaultValues: ["Dirección de campaña", "Territorio"],
      }),
    );

    expect(html).toContain('name="current_team"');
    expect(html).toContain("Dirección de campaña");
    expect(html).toContain("Territorio");
    expect(html).toContain("Agregar función");
    expect(html).toContain('data-team-chip="true"');
    expect(html).not.toContain("Una persona o función por línea");
  });
});
