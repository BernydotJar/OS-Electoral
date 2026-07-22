import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { proxy } from "@/proxy";

describe("locale proxy", () => {
  it("never redirects internal API mutation routes", () => {
    const response = proxy(
      new NextRequest("http://127.0.0.1:3000/api/ui/guided-intake/start", {
        method: "POST",
        headers: { origin: "http://127.0.0.1:3000" },
      }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });

  it("still localizes browser pages", () => {
    const response = proxy(
      new NextRequest("http://127.0.0.1:3000/", {
        headers: { "accept-language": "en-US" },
      }),
    );

    expect(response.status).toBe(307);
    const location = response.headers.get("location");
    expect(location).not.toBeNull();
    expect(new URL(location!).pathname).toBe("/en");
  });
});
