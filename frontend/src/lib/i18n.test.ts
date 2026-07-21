import { describe, expect, it } from "vitest";

import { dictionaries, isLocale, locales } from "@/lib/i18n";

function shape(value: unknown): unknown {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return typeof value;
  return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, shape(child)]));
}

describe("i18n", () => {
  it("accepts only supported locales", () => {
    expect(locales).toEqual(["es", "en"]);
    expect(isLocale("es")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("fr")).toBe(false);
  });

  it("keeps Spanish and English dictionary structure in parity", () => {
    expect(shape(dictionaries.en)).toEqual(shape(dictionaries.es));
  });
});
