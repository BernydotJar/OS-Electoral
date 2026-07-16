#!/usr/bin/env python3
"""Runtime and visual review for C1-FRONT-002-V1."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = os.environ.get("CAMPAIGNOS_URL", "http://127.0.0.1:4173")
ARTIFACT_DIR = Path(os.environ.get("CAMPAIGNOS_ARTIFACT_DIR", "artifacts/c1-front-002-v1"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_horizontal_overflow(page: Page, label: str) -> None:
    dimensions = page.evaluate(
        """() => ({
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth
        })"""
    )
    require(
        dimensions["scrollWidth"] <= dimensions["clientWidth"] + 1,
        f"{label}: horizontal overflow {dimensions}",
    )


def collect_runtime_errors(page: Page, bucket: list[str]) -> None:
    page.on(
        "console",
        lambda message: bucket.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: bucket.append(f"pageerror:{error}"))


def wait_for_application(page: Page) -> None:
    page.goto(BASE_URL, wait_until="networkidle")
    page.locator("#teamGrid .department-card").first.wait_for(state="visible")
    require(page.locator("#teamGrid .department-card").count() == 10, "expected ten department buttons")


def review_desktop(browser, results: dict) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors: list[str] = []
    collect_runtime_errors(page, errors)
    wait_for_application(page)

    require(page.locator("#candidateTitle").is_visible(), "candidate authority node is not visible")
    require(page.locator("#chiefTitle").is_visible(), "AI Chief of Staff node is not visible")
    require(page.locator("#teamGrid [role=listitem]").count() == 10, "semantic list must contain ten list items")
    require(page.locator("#teamGrid button.department-card").count() == 10, "cards must retain native button semantics")
    require(page.locator("#teamGrid button.department-card[role]").count() == 0, "department buttons must not override native role")
    assert_no_horizontal_overflow(page, "desktop-team")
    page.screenshot(path=ARTIFACT_DIR / "desktop-team.png", full_page=True)

    first_card = page.locator("#teamGrid button.department-card").first
    first_card.focus()
    first_card.click()
    drawer = page.locator("#agentDrawer")
    require(drawer.is_visible(), "drawer did not open")
    require(page.locator("#drawerBackdrop").get_attribute("tabindex") == "-1", "backdrop must be excluded from tab order")
    require(page.evaluate("document.activeElement?.id") == "drawerClose", "drawer close button must receive focus")
    page.screenshot(path=ARTIFACT_DIR / "desktop-drawer.png", full_page=True)

    page.keyboard.press("Tab")
    require(page.evaluate("document.activeElement?.id") == "drawerClose", "focus must remain trapped inside drawer")
    page.keyboard.press("Escape")
    require(drawer.is_hidden(), "Escape did not close drawer")
    require(
        page.evaluate("document.activeElement?.classList.contains('department-card')") is True,
        "focus did not return to invoking department card",
    )

    evidence_tab = page.locator('[data-module="evidence"]')
    evidence_tab.click()
    require(page.locator("#evidenceModule").is_visible(), "evidence module did not become visible")
    require(page.locator("#teamModule").is_hidden(), "team module did not hide")
    require(page.evaluate("document.activeElement?.id") == "overview-title", "evidence title did not receive focus")
    assert_no_horizontal_overflow(page, "desktop-evidence")
    page.screenshot(path=ARTIFACT_DIR / "desktop-evidence.png", full_page=True)

    page.locator('[data-module="team"]').click()
    require(page.evaluate("document.activeElement?.id") == "team-title", "team title did not receive focus")

    cdp = context.new_cdp_session(page)
    cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 2})
    require(page.locator("#teamModule").is_visible(), "team module failed at 200 percent page scale")
    cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})

    require(not errors, f"runtime errors detected: {errors}")
    results["desktop"] = {"status": "PASS", "errors": errors}
    context.close()


def review_mobile(browser, results: dict) -> None:
    context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = context.new_page()
    errors: list[str] = []
    collect_runtime_errors(page, errors)
    wait_for_application(page)
    assert_no_horizontal_overflow(page, "mobile-team")
    require(page.locator("#teamGrid button.department-card").count() == 10, "mobile lost department cards")
    page.screenshot(path=ARTIFACT_DIR / "mobile-team.png", full_page=True)

    page.locator("#teamGrid button.department-card").first.click()
    require(page.locator("#agentDrawer").is_visible(), "mobile drawer did not open")
    page.screenshot(path=ARTIFACT_DIR / "mobile-drawer.png", full_page=True)
    page.keyboard.press("Escape")
    require(page.locator("#agentDrawer").is_hidden(), "mobile Escape did not close drawer")
    require(not errors, f"mobile runtime errors detected: {errors}")
    results["mobile"] = {"status": "PASS", "errors": errors}
    context.close()


def review_reduced_motion(browser, results: dict) -> None:
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        reduced_motion="reduce",
    )
    page = context.new_page()
    wait_for_application(page)
    require(page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"), "reduced-motion emulation failed")
    page.locator('[data-module="evidence"]').click()
    require(page.locator("#evidenceModule").is_visible(), "module switching failed with reduced motion")
    results["reduced_motion"] = {"status": "PASS"}
    context.close()


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {"base_url": BASE_URL}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            review_desktop(browser, results)
            review_mobile(browser, results)
            review_reduced_motion(browser, results)
        finally:
            browser.close()

    results["overall"] = "PASS"
    (ARTIFACT_DIR / "runtime-review.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("[OK] desktop runtime and screenshots")
    print("[OK] accessible drawer focus lifecycle")
    print("[OK] Team/Evidence module switching")
    print("[OK] mobile layout and drawer")
    print("[OK] reduced-motion behavior")
    print("[OK] no page-level horizontal overflow")


if __name__ == "__main__":
    main()
