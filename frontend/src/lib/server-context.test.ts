import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("next/headers", () => ({ cookies: vi.fn() }));

import { UiContextError, requireSameOrigin } from "@/lib/server-context";

function request(
  origin: string | null,
  host = "127.0.0.1:3000",
  forwardedProtocol?: string,
): Request {
  const headers = new Headers({ host });
  if (origin !== null) headers.set("origin", origin);
  if (forwardedProtocol) headers.set("x-forwarded-proto", forwardedProtocol);
  return new Request("http://localhost:3000/api/ui/guided-intake/start", {
    method: "POST",
    headers,
  });
}

describe("requireSameOrigin", () => {
  it("accepts the browser origin matching the received Host header", () => {
    expect(() =>
      requireSameOrigin(request("http://127.0.0.1:3000")),
    ).not.toThrow();
    expect(() =>
      requireSameOrigin(
        request("https://app.example.test", "app.example.test", "https"),
      ),
    ).not.toThrow();
  });

  it("rejects missing, malformed, cross-host, and cross-protocol origins", () => {
    for (const candidate of [
      request(null),
      request("not-a-url"),
      request("http://attacker.example"),
      request("https://127.0.0.1:3000"),
      request("http://127.0.0.1:3000", "a.example,b.example"),
    ]) {
      expect(() => requireSameOrigin(candidate)).toThrow(UiContextError);
    }
  });
});
