#!/usr/bin/env python3
"""Review the production-built CampaignOS dynamic shell in explicit demo mode."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from playwright.async_api import Browser, Page, async_playwright

ROOT = Path(__file__).resolve().parents[2]
AXE_SOURCE = ROOT / "frontend" / "node_modules" / "axe-core" / "axe.min.js"
BASE_URL = os.environ.get("CAMPAIGNOS_FRONTEND_URL", "http://127.0.0.1:4174").rstrip("/")
ARTIFACT_DIR = Path(
    os.environ.get(
        "CAMPAIGNOS_FRONTEND_ARTIFACT_DIR",
        str(Path.cwd() / "artifacts" / "c3-front-001"),
    )
)
EXPECTED_HOST = urlparse(BASE_URL).netloc


class ReviewFailure(AssertionError):
    """The runtime shell violated a required visual or security invariant."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewFailure(message)


async def assert_no_overflow(page: Page, label: str) -> None:
    dimensions = await page.evaluate(
        """() => ({
          viewport: window.innerWidth,
          document: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
        })"""
    )
    require(
        dimensions["document"] <= dimensions["viewport"] + 1,
        f"{label}: document overflows horizontally: {dimensions}",
    )
    require(
        dimensions["body"] <= dimensions["viewport"] + 1,
        f"{label}: body overflows horizontally: {dimensions}",
    )


async def assert_accessible(page: Page, label: str) -> None:
    if not AXE_SOURCE.is_file():
        raise ReviewFailure(f"axe-core runtime is missing: {AXE_SOURCE}")
    await page.add_script_tag(path=str(AXE_SOURCE))
    violations = await page.evaluate(
        """async () => {
          const result = await axe.run(document, {
            runOnly: {
              type: 'tag',
              values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
            },
          });
          return result.violations.map((violation) => ({
            id: violation.id,
            impact: violation.impact,
            nodes: violation.nodes.length,
            targets: violation.nodes.flatMap((node) => node.target),
          }));
        }"""
    )
    require(not violations, f"{label}: WCAG violations: {violations}")


async def open_page(
    browser: Browser,
    *,
    width: int,
    height: int,
    reduced_motion: Literal["no-preference", "reduce"],
) -> Page:
    context = await browser.new_context(
        viewport={"width": width, "height": height},
        reduced_motion=reduced_motion,
        locale="es-GT",
    )
    return await context.new_page()


async def review() -> dict[str, object]:
    await asyncio.to_thread(ARTIFACT_DIR.mkdir, parents=True, exist_ok=True)
    console_errors: list[str] = []
    page_errors: list[str] = []
    unexpected_hosts: set[str] = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        desktop = await open_page(browser, width=1440, height=1000, reduced_motion="no-preference")
        desktop.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        desktop.on("pageerror", lambda error: page_errors.append(str(error)))
        desktop.on(
            "request",
            lambda request: (
                unexpected_hosts.add(urlparse(request.url).netloc)
                if urlparse(request.url).netloc and urlparse(request.url).netloc != EXPECTED_HOST
                else None
            ),
        )

        response = await desktop.goto(f"{BASE_URL}/", wait_until="networkidle")
        if response is None or not response.ok:
            raise ReviewFailure("root route did not return a successful response")
        require(desktop.url == f"{BASE_URL}/es", f"root did not resolve to Spanish: {desktop.url}")
        require(
            await desktop.locator("html").get_attribute("lang") == "es",
            "Spanish document lang missing",
        )
        require(
            await desktop.get_by_role("heading", level=1).inner_text()
            == "Centro de mando gobernado",
            "Spanish heading mismatch",
        )
        require(
            await desktop.get_by_text("DEMO SINTÉTICO", exact=True).count() >= 1,
            "demo classification missing",
        )
        require(
            await desktop.get_by_text("SYNTHETIC DATA · NO REAL CAMPAIGN", exact=True).count() == 1,
            "synthetic-data banner missing",
        )
        require(
            await desktop.get_by_text("NOT_A_HUMAN_APPROVAL", exact=True).count() == 1,
            "approval limitation missing",
        )
        require(
            await desktop.get_by_text(
                "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT", exact=True
            ).count()
            == 1,
            "strategy/evidence limitation missing",
        )
        require(
            await desktop.locator("form").count() == 0,
            "read-only shell unexpectedly contains a form",
        )
        require(
            await desktop.locator("button:not([data-locale-switch])").count() == 0,
            "read-only shell unexpectedly contains a domain action button",
        )
        await assert_no_overflow(desktop, "desktop-es")
        await assert_accessible(desktop, "desktop-es")

        await desktop.keyboard.press("Tab")
        active_text = await desktop.evaluate("document.activeElement?.textContent?.trim()")
        require(
            active_text == "Saltar al contenido",
            f"skip link is not first focus target: {active_text}",
        )
        await desktop.keyboard.press("Enter")
        active_id = await desktop.evaluate("document.activeElement?.id")
        require(active_id == "main", f"skip link did not focus main content: {active_id}")

        html = await desktop.content()
        require(
            "campaignos_access_token" not in html,
            "server-only cookie name leaked into rendered HTML",
        )
        require("Bearer " not in html, "bearer token marker leaked into rendered HTML")
        storage = await desktop.evaluate(
            """() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) })"""
        )
        require(storage == {"local": [], "session": []}, f"browser storage is not empty: {storage}")
        headers = response.headers
        require(headers.get("x-content-type-options") == "nosniff", "nosniff header missing")
        require(headers.get("x-frame-options") == "DENY", "frame denial header missing")
        require(
            headers.get("referrer-policy") == "strict-origin-when-cross-origin",
            "referrer policy header missing",
        )
        await desktop.screenshot(path=ARTIFACT_DIR / "desktop-es.png", full_page=True)

        await desktop.get_by_role("button", name="EN", exact=True).click()
        await desktop.wait_for_url(f"{BASE_URL}/en")
        await desktop.wait_for_load_state("networkidle")
        require(desktop.url == f"{BASE_URL}/en", f"English locale navigation failed: {desktop.url}")
        require(
            await desktop.locator("html").get_attribute("lang") == "en",
            "English document lang missing",
        )
        require(
            await desktop.get_by_role("heading", level=1).inner_text() == "Governed command center",
            "English heading mismatch",
        )
        await assert_no_overflow(desktop, "desktop-en")
        await assert_accessible(desktop, "desktop-en")
        await desktop.screenshot(path=ARTIFACT_DIR / "desktop-en.png", full_page=True)

        mobile = await open_page(browser, width=390, height=844, reduced_motion="reduce")
        mobile.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        mobile.on("pageerror", lambda error: page_errors.append(str(error)))
        await mobile.goto(f"{BASE_URL}/es", wait_until="networkidle")
        require(
            await mobile.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"),
            "reduced-motion context was not active",
        )
        await assert_no_overflow(mobile, "mobile-es")
        await assert_accessible(mobile, "mobile-es")
        require(
            await mobile.get_by_text("DEMO SINTÉTICO", exact=True).count() >= 1,
            "mobile demo badge missing",
        )
        await mobile.screenshot(path=ARTIFACT_DIR / "mobile-es.png", full_page=True)

        await browser.close()

    require(not console_errors, f"browser console errors: {console_errors}")
    require(not page_errors, f"browser page errors: {page_errors}")
    require(not unexpected_hosts, f"unexpected outbound browser hosts: {sorted(unexpected_hosts)}")
    result: dict[str, object] = {
        "status": "PASS",
        "base_url": BASE_URL,
        "desktop_spanish": "PASS",
        "desktop_english": "PASS",
        "mobile_spanish": "PASS",
        "keyboard_skip_link": "PASS",
        "reduced_motion": "PASS",
        "horizontal_overflow": "NONE",
        "wcag_2_2_aa": "PASS_ZERO_AXE_VIOLATIONS",
        "browser_storage": "EMPTY",
        "unexpected_outbound_hosts": [],
        "console_errors": [],
        "page_errors": [],
        "screenshots": [
            str(ARTIFACT_DIR / "desktop-es.png"),
            str(ARTIFACT_DIR / "desktop-en.png"),
            str(ARTIFACT_DIR / "mobile-es.png"),
        ],
    }
    await asyncio.to_thread(
        (ARTIFACT_DIR / "review.json").write_text,
        json.dumps(result, indent=2) + "\n",
    )
    return result


def main() -> int:
    result = asyncio.run(review())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
