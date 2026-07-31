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
            await desktop.get_by_role("heading", level=1).inner_text() == "Tu campaña, paso a paso",
            "Spanish command-overview heading mismatch",
        )
        require(
            await desktop.get_by_text("DEMO SINTÉTICO", exact=True).count() >= 1,
            "demo classification missing",
        )
        require(
            await desktop.get_by_text(
                "Requiere decisión de una persona autorizada", exact=True
            ).count()
            == 1,
            "human-decision boundary missing",
        )
        require(
            await desktop.get_by_text(
                "Aún no existe evidencia suficiente para decidir estrategia", exact=True
            ).count()
            == 1,
            "strategy/evidence boundary missing",
        )
        require(
            await desktop.locator(".campaign-command-overview").count() == 1,
            "campaign command overview missing",
        )
        require(
            await desktop.locator(".campaign-experience").count() == 0,
            "retired mission hero remains visible on the command overview",
        )
        require(
            await desktop.get_by_role("progressbar", name="Progreso de la ruta de campaña").count()
            == 1,
            "campaign progress semantics missing",
        )
        require(
            await desktop.locator(".command-priority").count() == 1,
            "current decision focus is missing",
        )
        require(
            await desktop.get_by_role(
                "heading", name="Conocer la candidatura y el territorio", exact=True
            ).count()
            == 1,
            "current evidence focus is missing",
        )
        require(
            await desktop.locator('.command-stage-navigation [aria-current="step"]').count() == 1,
            "current stage semantics missing",
        )
        require(
            await desktop.locator(
                "#guided-intake, #candidate-workspace, #team-workspace, #strategy-room, #war-room"
            ).count()
            == 0,
            "chapter workspaces leaked into the command overview",
        )
        path_disclosure = desktop.locator(".command-path-disclosure")
        require(await path_disclosure.count() == 1, "complete path disclosure missing")
        require(
            not await path_disclosure.evaluate("element => element.open"),
            "complete path disclosure must start closed",
        )
        require(
            await desktop.locator("video, source[src*='sceneai.art']").count() == 0,
            "third-party cinematic media leaked into the product",
        )
        visible_text = await desktop.locator("body").inner_text()
        for internal_code in (
            "OPERATIONAL SETUP ONLY",
            "BEGIN_GUIDED_INTAKE",
            "CAMPAIGN_NAME_PRESENT",
            "IDENTITY_NOT_VERIFIED",
            "BIOGRAPHY_NOT_VERIFIED",
            "ROLE_CARDS_MISSING",
            "VACANCIES_UNASSESSED",
        ):
            require(internal_code not in visible_text, f"internal code leaked: {internal_code}")

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

        path_summary = desktop.locator(".command-path-disclosure > summary")
        await path_summary.focus()
        require(
            await desktop.evaluate(
                "document.activeElement?.matches('.command-path-disclosure > summary')"
            ),
            "complete path summary is not keyboard focusable",
        )
        await desktop.keyboard.press("Enter")
        require(
            await path_disclosure.evaluate("element => element.open"),
            "Enter did not open the complete path",
        )
        await desktop.keyboard.press("Enter")
        require(
            not await path_disclosure.evaluate("element => element.open"),
            "Enter did not close the complete path",
        )

        await desktop.locator(
            '.command-priority a[href="/es/campaign/evidence#candidate-workspace"]'
        ).click()
        await desktop.wait_for_url("**/es/campaign/evidence**")
        await desktop.locator("#candidate-workspace").wait_for(state="visible")
        await desktop.locator(".chapter-command-bar").wait_for(state="visible")
        require(
            await desktop.locator(".chapter-command-bar").count() == 1,
            "chapter navigation missing after mission entry",
        )
        require(
            await desktop.locator("#candidate-workspace").count() == 1,
            "selected evidence chapter is absent",
        )
        require(
            await desktop.locator(".campaign-experience").count() == 0,
            "mission hero leaked into the evidence chapter",
        )
        action_tab = desktop.get_by_role("tab", name="Qué hacer ahora")
        require(await action_tab.count() == 1, "candidate action tab missing")
        require(
            await desktop.get_by_text("Qué debemos resolver ahora", exact=True).count() == 1,
            "candidate action brief missing",
        )
        await action_tab.focus()
        await desktop.keyboard.press("ArrowRight")
        require(
            await desktop.get_by_role("tab", name="Perfil y riesgos").get_attribute("aria-selected")
            == "true",
            "candidate profile tab did not activate with ArrowRight",
        )
        require(
            await desktop.locator(".candidate-profile-view").count() == 1,
            "candidate profile view did not activate",
        )
        await desktop.keyboard.press("ArrowRight")
        require(
            await desktop.get_by_role("tab", name="Fuentes y evidencia").get_attribute(
                "aria-selected"
            )
            == "true",
            "candidate evidence tab did not activate with ArrowRight",
        )
        require(
            await desktop.locator("#candidate-evidence-panel:not([hidden])").count() == 1,
            "candidate evidence view did not activate",
        )
        require(
            await desktop.locator(
                "#guided-intake, #team-workspace, #strategy-room, #war-room"
            ).count()
            == 0,
            "unselected missions leaked into evidence chapter",
        )
        require(
            await desktop.locator('[aria-current="step"][data-current="true"]').count() == 1,
            "chapter navigation lacks one current step",
        )
        await assert_no_overflow(desktop, "desktop-es-evidence")
        await assert_accessible(desktop, "desktop-es-evidence")

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

        await desktop.locator(".chapter-command-map > summary").click()
        await desktop.locator(
            '.chapter-command-track a[href="/es/campaign/team#team-workspace"]'
        ).click()
        await desktop.wait_for_url("**/es/campaign/team**")
        await desktop.locator("#team-workspace").wait_for(state="visible")
        compact_topbar = desktop.locator(".topbar-compact")
        require(await compact_topbar.count() == 1, "team chapter lacks compact command chrome")
        compact_height = await compact_topbar.evaluate("element => element.getBoundingClientRect().height")
        require(compact_height <= 80, f"compact command chrome is too tall: {compact_height}")
        require(
            await desktop.locator(".context-strip").count() == 0,
            "technical context strip still occupies chapter space",
        )
        session_menu = desktop.locator(".session-context-menu")
        require(
            await session_menu.count() == 1
            and not await session_menu.evaluate("element => element.open"),
            "session context is not collapsed by default",
        )
        await session_menu.locator("summary").click()
        require(
            await session_menu.evaluate("element => element.open")
            and await session_menu.get_by_text("Campaña", exact=True).count() == 1,
            "compact session context did not reveal technical details",
        )
        await session_menu.locator("summary").click()
        require(
            await desktop.locator(".campaign-experience").count() == 0,
            "mission hero leaked into the team chapter",
        )
        operation_layers = desktop.locator(".team-operations-layer")
        require(
            await operation_layers.count() == 2,
            "team operation cards are not both retained in the visual stack",
        )
        create_layer = desktop.locator('[data-layer="create"]')
        board_layer = desktop.locator('[data-layer="board"]')
        require(
            await create_layer.get_attribute("data-active") == "true"
            and await board_layer.get_attribute("data-active") == "false",
            "empty demo operation stack does not begin with creation in front",
        )
        layer_visibility = await desktop.locator(".team-operations-stack").evaluate(
            """stack => {
              const active = stack.querySelector('[data-active="true"]');
              const inactive = stack.querySelector('[data-active="false"]');
              return {
                activeDisplay: getComputedStyle(active).display,
                activeVisibility: getComputedStyle(active).visibility,
                inactiveDisplay: getComputedStyle(inactive).display,
                inactiveVisibility: getComputedStyle(inactive).visibility,
              };
            }"""
        )
        require(
            layer_visibility["activeDisplay"] != "none"
            and layer_visibility["activeVisibility"] == "visible"
            and layer_visibility["inactiveDisplay"] == "none",
            f"inactive operation card still distracts or occupies layout: {layer_visibility}",
        )
        create_tab = desktop.get_by_role("tab", name="Crear seguimiento")
        board_tab = desktop.get_by_role("tab", name="Tablero operativo")
        await create_tab.focus()
        await desktop.keyboard.press("ArrowLeft")
        require(
            await board_tab.get_attribute("aria-selected") == "true"
            and await board_layer.get_attribute("data-active") == "true"
            and await create_layer.get_attribute("data-active") == "false",
            "keyboard navigation did not exchange the operation cards",
        )
        await desktop.keyboard.press("ArrowRight")
        require(
            await create_tab.get_attribute("aria-selected") == "true"
            and await create_layer.get_attribute("data-active") == "true",
            "keyboard navigation did not restore the creation card to the front",
        )
        await assert_no_overflow(desktop, "desktop-es-team")
        await assert_accessible(desktop, "desktop-es-team")
        await desktop.screenshot(path=ARTIFACT_DIR / "desktop-es-team.png", full_page=True)

        await desktop.locator(".chapter-command-map > summary").click()
        await desktop.locator(
            '.chapter-command-track a[href="/es/campaign/evidence#candidate-workspace"]'
        ).click()
        await desktop.wait_for_url("**/es/campaign/evidence**")
        await desktop.locator("#candidate-workspace").wait_for(state="visible")
        await desktop.get_by_role("button", name="EN", exact=True).click()
        await desktop.wait_for_url("**/en/campaign/evidence**")
        await desktop.wait_for_load_state("networkidle")
        require(
            "/en/campaign/evidence" in desktop.url,
            f"English locale did not preserve the chapter path: {desktop.url}",
        )
        require(
            await desktop.locator("html").get_attribute("lang") == "en",
            "English document lang missing",
        )
        require(
            await desktop.get_by_role(
                "heading", name="Candidate executive workspace", exact=True
            ).count()
            == 1,
            "English candidate chapter heading mismatch",
        )
        require(
            await desktop.locator(".campaign-experience").count() == 0,
            "mission hero leaked into the English candidate chapter",
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
        await mobile.goto(f"{BASE_URL}/es/campaign/evidence", wait_until="networkidle")
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
        require(
            await mobile.locator("#candidate-workspace").count() == 1,
            "mobile chapter route did not preserve its selected mission",
        )
        require(
            await mobile.locator(".campaign-experience, .experience-mission-pulse").count() == 0,
            "mission hero leaked into the mobile candidate chapter",
        )
        reduced_transition = await mobile.locator(".candidate-workspace-layer").first.evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )

        def transition_seconds(value: str) -> float:
            token = value.strip()
            if token.endswith("ms"):
                return float(token[:-2]) / 1000
            if token.endswith("s"):
                return float(token[:-1])
            raise ReviewFailure(f"unexpected transition duration token: {token}")

        require(
            all(transition_seconds(part) <= 0.0001 for part in reduced_transition.split(",")),
            f"candidate workspace still transitions under reduced motion: {reduced_transition}",
        )
        mobile_session_menu = mobile.locator(".session-context-menu")
        await mobile_session_menu.locator("summary").click()
        session_bounds = await mobile_session_menu.locator("dl").evaluate(
            """element => {
              const rect = element.getBoundingClientRect();
              return {left: rect.left, right: rect.right, viewport: window.innerWidth};
            }"""
        )
        require(
            session_bounds["left"] >= 0
            and session_bounds["right"] <= session_bounds["viewport"],
            f"mobile session disclosure escapes viewport: {session_bounds}",
        )
        await mobile_session_menu.locator("summary").click()
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
        "chapter_navigation": "PASS_ROUTE_ISOLATION_LOCALE_PRESERVATION",
        "command_overview": "PASS_CURRENT_FOCUS_PROGRESSIVE_PATH",
        "reduced_motion": "PASS_STATIC_EQUIVALENT",
        "horizontal_overflow": "NONE",
        "wcag_2_2_aa": "PASS_ZERO_AXE_VIOLATIONS",
        "browser_storage": "EMPTY",
        "unexpected_outbound_hosts": [],
        "console_errors": [],
        "page_errors": [],
        "screenshots": [
            str(ARTIFACT_DIR / "desktop-es.png"),
            str(ARTIFACT_DIR / "desktop-es-team.png"),
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
