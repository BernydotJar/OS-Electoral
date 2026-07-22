#!/usr/bin/env python3
"""Exercise the real API-backed campaign onboarding journey in Chromium."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).resolve().parents[2]
AXE_SOURCE = ROOT / "frontend" / "node_modules" / "axe-core" / "axe.min.js"
BASE_URL = os.environ["CAMPAIGNOS_FRONTEND_URL"].rstrip("/")
ARTIFACT_DIR = Path(
    os.environ.get(
        "CAMPAIGNOS_FRONTEND_ARTIFACT_DIR",
        str(ROOT / "artifacts" / "c3-front-002"),
    )
)
BASE_PARSED = urlparse(BASE_URL)
EXPECTED_HOST = BASE_PARSED.netloc
ALLOWED_HOSTS = {EXPECTED_HOST}
if BASE_PARSED.hostname in {"127.0.0.1", "localhost"}:
    alias = "localhost" if BASE_PARSED.hostname == "127.0.0.1" else "127.0.0.1"
    ALLOWED_HOSTS.add(f"{alias}:{BASE_PARSED.port}")


class ReviewFailure(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewFailure(message)


async def assert_no_overflow(page: Page, label: str) -> None:
    widths = await page.evaluate(
        """() => ({
          viewport: window.innerWidth,
          document: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
        })"""
    )
    require(
        widths["document"] <= widths["viewport"] + 1,
        f"{label}: document overflow: {widths}",
    )
    require(
        widths["body"] <= widths["viewport"] + 1,
        f"{label}: body overflow: {widths}",
    )


async def assert_accessible(page: Page, label: str) -> None:
    require(AXE_SOURCE.is_file(), f"axe-core runtime missing: {AXE_SOURCE}")
    await page.add_script_tag(path=str(AXE_SOURCE))
    violations = await page.evaluate(
        """async () => {
          const result = await axe.run(document, {
            runOnly: {
              type: 'tag',
              values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
            },
          });
          return result.violations.map((item) => ({
            id: item.id,
            impact: item.impact,
            targets: item.nodes.flatMap((node) => node.target),
          }));
        }"""
    )
    require(not violations, f"{label}: WCAG violations: {violations}")


async def review() -> dict[str, object]:
    await asyncio.to_thread(ARTIFACT_DIR.mkdir, parents=True, exist_ok=True)
    console_errors: list[str] = []
    page_errors: list[str] = []
    unexpected_hosts: set[str] = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="es-GT",
        )
        page = await context.new_page()
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                unexpected_hosts.add(urlparse(request.url).netloc)
                if urlparse(request.url).netloc
                and urlparse(request.url).netloc not in ALLOWED_HOSTS
                else None
            ),
        )

        response = await page.goto(f"{BASE_URL}/es", wait_until="networkidle")
        require(response is not None and response.ok, "live shell did not load")
        require(
            await page.get_by_text("SESIÓN VERIFICADA", exact=True).count() >= 1,
            "live session badge missing",
        )
        require(
            await page.get_by_text("DEMO SINTÉTICO", exact=True).count() == 0,
            "demo badge leaked into live journey",
        )
        require(
            await page.get_by_role("link", name="Administración").count() == 0,
            "non-functional Administration navigation is still visible",
        )
        require(
            await page.get_by_role("link", name="Candidatura").count() == 0,
            "ungranted candidate module is visible",
        )
        require(
            await page.get_by_label("Campaña autorizada").input_value()
            == "22222222-2222-4222-8222-222222222222",
            "seeded campaign was not selected",
        )
        require(
            await page.get_by_role("button", name="Iniciar intake").count() == 1,
            "authorized intake start control missing",
        )
        html = await page.content()
        require(
            "campaignos-local-development-token" not in html,
            "development token leaked into HTML",
        )
        storage = await page.evaluate(
            "() => ({local: Object.keys(localStorage), session: Object.keys(sessionStorage)})"
        )
        require(storage == {"local": [], "session": []}, f"browser storage used: {storage}")

        await page.get_by_role("button", name="Iniciar intake").click()
        await page.wait_for_url("**notice=intake_started**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text("Intake iniciado y guardado en PostgreSQL.", exact=True).count()
            == 1,
            "start success notice missing",
        )
        require(
            await page.get_by_role("button", name="Guardar cambios").count() == 1,
            "authorized intake editor missing after start",
        )

        await page.get_by_label("Cargo objetivo").fill("Alcaldía Municipal")
        await page.get_by_label("Evidencia presupuestaria").select_option("ROUGH_RANGE")
        await page.get_by_label("Proyecto de candidatura").fill(
            "Proyecto municipal interno sujeto a evidencia y revisión humana."
        )
        await page.get_by_label("Equipo actual").fill(
            "Dirección de campaña\nCoordinación financiera"
        )
        await page.get_by_label("Activos actuales").fill("Archivo documental\nAgenda operativa")
        await page.get_by_label("Preguntas conocidas").fill(
            "Calendario electoral\nRequisitos de inscripción"
        )
        await page.get_by_label("Evidencia requerida").fill(
            "Resolución oficial\nDocumento de identidad"
        )
        await page.get_by_role("button", name="Guardar cambios").click()
        await page.wait_for_url("**notice=intake_saved**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text("Cambios guardados con nueva versión.", exact=True).count() == 1,
            "save success notice missing",
        )
        require(
            await page.get_by_label("Cargo objetivo").input_value() == "Alcaldía Municipal",
            "saved office was not projected",
        )
        require(
            await page.get_by_label("Evidencia presupuestaria").input_value() == "ROUGH_RANGE",
            "saved budget was not projected",
        )

        await page.reload(wait_until="networkidle")
        require(
            await page.get_by_label("Cargo objetivo").input_value() == "Alcaldía Municipal",
            "intake did not persist after reload",
        )
        require(
            await page.get_by_text("Alcaldía Municipal", exact=True).count() >= 1,
            "persisted value is absent from read projection",
        )
        await assert_no_overflow(page, "functional-desktop-es")
        await assert_accessible(page, "functional-desktop-es")
        await page.screenshot(path=ARTIFACT_DIR / "functional-desktop-es.png", full_page=True)

        english = await browser.new_page(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        await english.goto(f"{BASE_URL}/en", wait_until="networkidle")
        require(
            await english.get_by_role("button", name="Save changes").count() == 1,
            "English live editor is unavailable",
        )
        require(
            await english.get_by_label("Target office").input_value() == "Alcaldía Municipal",
            "English live projection did not preserve the saved intake",
        )
        require(
            await english.get_by_role("link", name="Administration").count() == 0,
            "Administration placeholder is visible in English",
        )
        await assert_no_overflow(english, "functional-desktop-en")
        await assert_accessible(english, "functional-desktop-en")
        await english.screenshot(path=ARTIFACT_DIR / "functional-desktop-en.png", full_page=True)

        mobile = await browser.new_page(
            viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        await mobile.goto(f"{BASE_URL}/es", wait_until="networkidle")
        await assert_no_overflow(mobile, "functional-mobile-es")
        await assert_accessible(mobile, "functional-mobile-es")
        require(
            await mobile.get_by_role("button", name="Guardar cambios").count() == 1,
            "mobile editor is not functional",
        )
        await mobile.screenshot(path=ARTIFACT_DIR / "functional-mobile-es.png", full_page=True)
        await browser.close()

    require(not console_errors, f"browser console errors: {console_errors}")
    require(not page_errors, f"browser page errors: {page_errors}")
    require(not unexpected_hosts, f"unexpected outbound hosts: {unexpected_hosts}")
    result: dict[str, object] = {
        "status": "PASS",
        "journey": "campaign_select_start_and_update_guided_intake",
        "persistence_after_reload": "PASS",
        "exact_authorization_controls": "PASS",
        "administration_placeholder": "ABSENT",
        "desktop_spanish": "PASS",
        "desktop_english": "PASS",
        "mobile_spanish": "PASS",
        "wcag_2_2_aa": "PASS_ZERO_AXE_VIOLATIONS",
        "horizontal_overflow": "NONE",
        "browser_storage": "EMPTY",
        "unexpected_outbound_hosts": [],
        "console_errors": [],
        "page_errors": [],
        "external_effects": "NONE",
    }
    await asyncio.to_thread(
        (ARTIFACT_DIR / "review.json").write_text,
        json.dumps(result, indent=2) + "\n",
    )
    return result


def main() -> int:
    print(json.dumps(asyncio.run(review()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
