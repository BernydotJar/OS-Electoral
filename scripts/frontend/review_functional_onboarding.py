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


async def wait_for_chapter(page: Page, url_pattern: str, selector: str) -> None:
    await page.wait_for_url(url_pattern)
    await page.locator(selector).wait_for(state="visible")


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

        def attach_page_guards(target: Page) -> None:
            target.on(
                "console",
                lambda message: (
                    console_errors.append(message.text) if message.type == "error" else None
                ),
            )
            target.on("pageerror", lambda error: page_errors.append(str(error)))
            target.on(
                "request",
                lambda request: (
                    unexpected_hosts.add(urlparse(request.url).netloc)
                    if urlparse(request.url).netloc
                    and urlparse(request.url).netloc not in ALLOWED_HOSTS
                    else None
                ),
            )

        page = await context.new_page()
        attach_page_guards(page)

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
            await page.get_by_role("link", name="Candidatura").count() == 1,
            "granted candidate module is not visible",
        )
        require(
            await page.get_by_role("heading", level=1).inner_text()
            == "Convierte una idea política en una campaña que sabe avanzar",
            "first-use campaign welcome is missing",
        )
        require(
            await page.get_by_role("button", name="Crear expediente").count() == 0,
            "candidate dossier was exposed before the foundation gate",
        )
        require(
            await page.get_by_role("heading", name="Tu campaña, paso a paso").count() == 1,
            "campaign master path missing from live journey",
        )
        visible_text = await page.locator("body").inner_text()
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
            await page.get_by_label("Campaña autorizada").input_value()
            == "22222222-2222-4222-8222-222222222222",
            "seeded campaign was not selected",
        )
        require(
            await page.get_by_role("link", name="Comenzar la ruta", exact=True).count() == 1,
            "foundation chapter entry link missing",
        )
        require(
            await page.get_by_role("button", name="Comenzar la ruta", exact=True).count() == 0,
            "foundation mutation leaked into the command overview",
        )
        for chapter_id in (
            "guided-intake",
            "candidate-workspace",
            "team-workspace",
            "strategy-room",
            "war-room",
        ):
            require(
                await page.locator(f"#{chapter_id}").count() == 0,
                f"chapter surface leaked into overview: {chapter_id}",
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

        await page.get_by_role("link", name="Comenzar la ruta", exact=True).click()
        await wait_for_chapter(page, "**/es/campaign/foundation**", "#guided-intake")
        require(
            await page.locator("#guided-intake").count() == 1,
            "foundation chapter did not render its mission",
        )
        require(
            await page.locator(
                "#candidate-workspace, #team-workspace, #strategy-room, #war-room"
            ).count()
            == 0,
            "non-foundation missions leaked into the foundation chapter",
        )
        require(
            await page.get_by_role("button", name="Comenzar ruta").count() == 1,
            "authorized intake start control missing in foundation chapter",
        )
        await page.get_by_role("button", name="Comenzar ruta").click()
        await page.wait_for_url("**notice=intake_started**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Ruta guiada creada y guardada en PostgreSQL.", exact=True
            ).count()
            == 1,
            "start success notice missing",
        )
        require(
            await page.get_by_role("button", name="Guardar cambios").count() == 1,
            "authorized intake editor missing after start",
        )

        await page.get_by_label("Cargo objetivo").fill("Alcaldía Municipal")
        await page.get_by_label("Estado del presupuesto").select_option("ROUGH_RANGE")
        await page.get_by_label("Proyecto de candidatura").fill(
            "Proyecto municipal interno sujeto a evidencia y revisión humana."
        )
        await page.get_by_label("Equipo actual").fill(
            "Dirección de campaña\nCoordinación financiera"
        )
        await page.get_by_label("Activos actuales").fill("Archivo documental\nAgenda operativa")
        await page.get_by_label("Preguntas que debemos resolver").fill(
            "Calendario electoral\nRequisitos de inscripción"
        )
        await page.get_by_label("Datos y documentos necesarios").fill(
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
            await page.get_by_label("Estado del presupuesto").input_value() == "ROUGH_RANGE",
            "saved budget was not projected",
        )
        require(
            await page.get_by_role("heading", level=1).inner_text() == "Aterrizar la campaña",
            "foundation chapter lost its stable chapter identity after save",
        )
        await page.locator(
            '.chapter-navigation-track a[href="/es/campaign/evidence#candidate-workspace"]'
        ).click()
        await wait_for_chapter(page, "**/es/campaign/evidence**", "#candidate-workspace")
        require(
            await page.locator("#candidate-workspace").count() == 1,
            "evidence chapter did not render its mission",
        )
        require(
            await page.locator("#guided-intake, #team-workspace, #strategy-room, #war-room").count()
            == 0,
            "non-evidence missions leaked into the evidence chapter",
        )
        require(
            await page.get_by_role("button", name="Crear expediente").count() == 1,
            "candidate dossier start control did not unlock",
        )
        await page.go_back(wait_until="networkidle")
        await wait_for_chapter(page, "**/es/campaign/foundation**", "#guided-intake")
        require(
            "/es/campaign/foundation" in page.url,
            "browser back did not return to the foundation chapter",
        )
        await page.go_forward(wait_until="networkidle")
        await wait_for_chapter(page, "**/es/campaign/evidence**", "#candidate-workspace")
        require(
            "/es/campaign/evidence" in page.url,
            "browser forward did not restore the evidence chapter",
        )

        await page.get_by_label("Nombre público de la candidatura").fill("Ana Pérez")
        await page.get_by_role("button", name="Crear expediente").click()
        await page.wait_for_url("**notice=candidate_started**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Expediente de candidatura creado y listo para documentar.", exact=True
            ).count()
            == 1,
            "candidate start success notice missing",
        )
        require(
            await page.get_by_role("button", name="Agregar fuente").count() == 1,
            "candidate evidence editor missing after dossier creation",
        )

        await page.get_by_label("Tipo de fuente").select_option("OFFICIAL_SOURCE")
        await page.get_by_label("Título de la fuente").fill("Acuerdo de convocatoria electoral")
        await page.get_by_label("Enlace verificable").fill(
            "https://example.test/convocatoria-electoral"
        )
        await page.get_by_label("Autoridad o institución").fill("Tribunal Electoral")
        await page.get_by_label("Jurisdicción").fill("Guatemala")
        await page.get_by_label("Fecha observada").fill("2026-07-24")
        await page.get_by_label("Nota de relevancia").fill(
            "Confirma el calendario oficial; todavía requiere contraste jurídico."
        )
        await page.get_by_role("button", name="Agregar fuente").click()
        await page.wait_for_url("**notice=candidate_evidence_saved**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Fuente incorporada al expediente con una nueva versión.", exact=True
            ).count()
            == 1,
            "candidate evidence success notice missing",
        )
        require(
            await page.get_by_text("Acuerdo de convocatoria electoral", exact=True).count() >= 1,
            "candidate evidence was not projected",
        )
        await page.locator(
            '.chapter-navigation-track a[href="/es/campaign/team#team-workspace"]'
        ).click()
        await wait_for_chapter(page, "**/es/campaign/team**", "#team-workspace")
        require(
            await page.locator("#team-workspace").count() == 1,
            "team chapter did not render its mission",
        )
        require(
            await page.locator(
                "#guided-intake, #candidate-workspace, #strategy-room, #war-room"
            ).count()
            == 0,
            "non-team missions leaked into the team chapter",
        )
        require(
            await page.get_by_role("button", name="Crear mapa de equipo").count() == 1,
            "parallel team preparation did not unlock",
        )
        template_guide = page.locator(".team-template-guide")
        template_summary = template_guide.locator("summary")
        await template_summary.focus()
        require(
            await page.evaluate(
                "document.activeElement?.matches('.team-template-guide > summary')"
            ),
            "team template guide is not keyboard focusable",
        )
        await page.keyboard.press("Enter")
        require(
            await template_guide.evaluate("element => element.open"), "template guide did not open"
        )
        await page.keyboard.press("Enter")
        require(
            not await template_guide.evaluate("element => element.open"),
            "template guide did not close",
        )

        await page.get_by_label("Modelo organizativo").select_option("LEAN_CAMPAIGN")
        await page.get_by_role("button", name="Crear mapa de equipo").click()
        await page.wait_for_url("**notice=team_started**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Mapa de equipo creado con funciones iniciales listas para revisión.",
                exact=True,
            ).count()
            == 1,
            "team start success notice missing",
        )
        require(
            await page.locator(".team-role-grid article").count() == 5,
            "lean campaign did not seed five role blueprints",
        )
        for seeded_title in (
            "Dirección de campaña",
            "Investigación y evidencia",
            "Territorio y organización",
            "Comunicación y narrativa",
            "Administración, legal y finanzas",
        ):
            require(
                await page.get_by_role("heading", name=seeded_title, exact=True).count() == 1,
                f"seeded job description missing: {seeded_title}",
            )
        require(
            await page.get_by_text("Responsabilidades del puesto", exact=True).count() == 5,
            "seeded job responsibilities are not visible",
        )
        require(
            await page.get_by_text("Plan humano de cobertura", exact=True).count() == 5,
            "seeded human vacancy plans are not visible",
        )
        seeded_dossier = page.locator(".team-role-grid .team-role-dossier").first
        seeded_summary = seeded_dossier.locator("summary")
        await seeded_summary.focus()
        await page.keyboard.press("Enter")
        require(
            await seeded_dossier.evaluate("element => element.open"),
            "seeded consultant dossier did not open from keyboard",
        )
        for heading in (
            "Decisiones que prepara o eleva",
            "Entregables verificables",
            "Interacciones clave",
            "Señales de funcionamiento",
        ):
            require(
                await seeded_dossier.get_by_role("heading", name=heading, exact=True).count() == 1,
                f"seeded consultant dossier missing section: {heading}",
            )
        await page.keyboard.press("Enter")
        require(
            await page.get_by_role("button", name="Agregar función").count() == 1,
            "team role editor missing after map creation",
        )

        await page.get_by_label("Modelo organizativo").select_option("FULL_CAMPAIGN")
        await page.get_by_role("button", name="Previsualizar cambios").click()
        await page.wait_for_url("**team_template=FULL_CAMPAIGN**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.locator(".team-template-role-card").count() == 5,
            "full template preview did not propose exactly five missing functions",
        )
        require(
            await page.locator(".team-template-skipped-list > li").count() == 3,
            "full template preview did not preserve the three equivalent functions",
        )
        for proposed_title in (
            "Estrategia digital",
            "Contenido político",
            "Medios pagados y distribución",
            "Narrativa, discurso y formación de medios",
            "Seguimiento, riesgos y aprendizaje",
        ):
            require(
                await page.get_by_role("heading", name=proposed_title, exact=True).count() == 1,
                f"template preview missing proposed job description: {proposed_title}",
            )
        require(
            await page.get_by_text(
                "La misma función ya existe en otra variante de idioma", exact=True
            ).count()
            == 3,
            "bilingual canonical deduplication is not explained",
        )
        require(
            await page.locator(".team-template-role-card .team-role-dossier").count() == 5,
            "proposed functions do not expose consultant dossiers",
        )
        require(
            await page.locator(".team-template-skipped-list .team-role-dossier").count() == 3,
            "preserved functions do not explain their consultant dossiers",
        )
        proposed_dossier = page.locator(".team-template-role-card .team-role-dossier").first
        await proposed_dossier.locator("summary").click()
        require(
            await proposed_dossier.get_by_text("Plan digital", exact=True).count() == 1,
            "proposed function dossier does not include a verifiable deliverable",
        )
        await page.set_viewport_size({"width": 390, "height": 844})
        preview_columns = await page.locator(".team-template-role-grid").evaluate(
            "element => getComputedStyle(element).gridTemplateColumns.split(' ').length"
        )
        require(
            preview_columns == 1,
            f"mobile template preview is not a single column: {preview_columns}",
        )
        await assert_no_overflow(page, "team-template-preview-mobile")
        await page.set_viewport_size({"width": 1440, "height": 1000})
        await assert_accessible(page, "team-template-preview-desktop")

        await page.get_by_role("button", name="Aplicar funciones nuevas").click()
        await page.wait_for_url("**notice=team_template_applied**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                (
                    "Plantilla aplicada: se conservaron las funciones existentes "
                    "y se agregaron sólo las ausentes."
                ),
                exact=True,
            ).count()
            == 1,
            "template application success notice missing",
        )
        require(
            await page.locator(".team-role-grid article").count() == 10,
            "confirmed full template did not persist ten total functions",
        )

        await page.get_by_label("Nombre de la función").fill("Coordinación de voluntariado")
        await page.get_by_label("Área").fill("Logística y apoyo")
        await page.get_by_label("Resultado que debe producir").fill(
            "Convertir necesidades operativas aprobadas en turnos y cobertura verificables."
        )
        await page.get_by_label("Responsabilidades principales").fill(
            "Mantener necesidades de voluntariado\n"
            "Coordinar turnos autorizados\n"
            "Escalar brechas de cobertura"
        )
        await page.get_by_label("Decisiones que prepara o eleva").fill(
            "Preparar escenarios de cobertura para decisión humana\n"
            "Elevar brechas que requieren aprobación"
        )
        await page.get_by_label("Entregables verificables").fill(
            "Plan de turnos\nRegistro de cobertura\nMapa de brechas"
        )
        await page.get_by_label("Interacciones clave").fill(
            "Territorio y organización\nDirección y legal"
        )
        await page.get_by_label("Señales de funcionamiento").fill(
            "Turnos con responsable\nBrechas visibles\nSin asignación automática"
        )
        await page.get_by_label("Plan para cubrir la función").fill(
            "Definir perfil, entrevistar responsables y aprobar la asignación humana."
        )
        await page.get_by_role("button", name="Agregar función").click()
        await page.wait_for_url("**notice=team_role_saved**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Función incorporada al mapa de equipo con una nueva versión.",
                exact=True,
            ).count()
            == 1,
            "team role success notice missing",
        )
        require(
            await page.get_by_text("Coordinación de voluntariado", exact=True).count() >= 1,
            "team role was not projected",
        )
        require(
            await page.get_by_text("Vacante", exact=True).count() >= 1,
            "team role vacancy state is missing",
        )

        await page.reload(wait_until="networkidle")
        require(
            await page.get_by_text("Coordinación de voluntariado", exact=True).count() >= 1,
            "team role did not persist after reload",
        )
        manual_dossier = (
            page.get_by_text("Coordinación de voluntariado", exact=True)
            .locator("xpath=ancestor::article[1]")
            .locator(".team-role-dossier")
        )
        await manual_dossier.locator("summary").click()
        require(
            await manual_dossier.get_by_text("Plan de turnos", exact=True).count() == 1,
            "manual role consultant dossier did not persist",
        )

        await page.locator(
            '.chapter-navigation-track a[href="/es/campaign/evidence#candidate-workspace"]'
        ).click()
        await wait_for_chapter(page, "**/es/campaign/evidence**", "#candidate-workspace")
        require(
            await page.get_by_text("Acuerdo de convocatoria electoral", exact=True).count() >= 1,
            "candidate evidence did not persist on its chapter route",
        )
        await page.locator(
            '.chapter-navigation-track a[href="/es/campaign/foundation#guided-intake"]'
        ).click()
        await wait_for_chapter(page, "**/es/campaign/foundation**", "#guided-intake")
        require(
            await page.get_by_label("Cargo objetivo").input_value() == "Alcaldía Municipal",
            "intake did not persist on its chapter route",
        )
        require(
            await page.get_by_text("Alcaldía Municipal", exact=True).count() >= 1,
            "persisted intake value is absent from its read projection",
        )
        await page.locator(
            '.chapter-navigation-track a[href="/es/campaign/team#team-workspace"]'
        ).click()
        await wait_for_chapter(page, "**/es/campaign/team**", "#team-workspace")
        require(
            await page.get_by_text("Coordinación de voluntariado", exact=True).count() >= 1,
            "team chapter did not restore after chapter-to-chapter navigation",
        )
        await assert_no_overflow(page, "functional-desktop-es-team")
        await assert_accessible(page, "functional-desktop-es-team")
        await page.screenshot(path=ARTIFACT_DIR / "functional-desktop-es.png", full_page=True)

        english = await browser.new_page(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        attach_page_guards(english)
        await english.goto(f"{BASE_URL}/en/campaign/foundation", wait_until="networkidle")
        require(
            await english.get_by_role("button", name="Save changes").count() == 1,
            "English foundation editor is unavailable",
        )
        require(
            await english.get_by_label("Target office").input_value() == "Alcaldía Municipal",
            "English foundation projection did not preserve the saved intake",
        )
        require(
            await english.get_by_role("link", name="Administration").count() == 0,
            "Administration placeholder is visible in English",
        )
        await english.goto(f"{BASE_URL}/en/campaign/evidence", wait_until="networkidle")
        require(
            await english.get_by_role("button", name="Add source").count() == 1,
            "English candidate evidence editor is unavailable",
        )
        await english.goto(f"{BASE_URL}/en/campaign/team", wait_until="networkidle")
        require(
            await english.get_by_role("button", name="Add function").count() == 1,
            "English team function editor is unavailable",
        )
        english_dossier = english.locator(".team-role-grid .team-role-dossier").first
        await english_dossier.locator("summary").click()
        require(
            await english_dossier.get_by_role(
                "heading", name="Verifiable deliverables", exact=True
            ).count()
            == 1,
            "English consultant dossier is unavailable",
        )
        await assert_no_overflow(english, "functional-desktop-en-team")
        await assert_accessible(english, "functional-desktop-en-team")
        await english.screenshot(path=ARTIFACT_DIR / "functional-desktop-en.png", full_page=True)

        mobile = await browser.new_page(
            viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        attach_page_guards(mobile)
        await mobile.goto(f"{BASE_URL}/es/campaign/team", wait_until="networkidle")
        await assert_no_overflow(mobile, "functional-mobile-es-team")
        await assert_accessible(mobile, "functional-mobile-es-team")
        require(
            await mobile.get_by_role("button", name="Agregar función").count() == 1,
            "mobile team function editor is not functional",
        )
        require(
            await mobile.locator(
                "#guided-intake, #candidate-workspace, #strategy-room, #war-room"
            ).count()
            == 0,
            "mobile chapter route contains unrelated missions",
        )
        mobile_role_columns = await mobile.locator(".team-role-grid").evaluate(
            "element => getComputedStyle(element).gridTemplateColumns.split(' ').length"
        )
        require(
            mobile_role_columns == 1,
            f"mobile role blueprints are not a single responsive column: {mobile_role_columns}",
        )
        reduced_motion_state = await mobile.locator(".experience-mission-pulse i").first.evaluate(
            "element => getComputedStyle(element).animationName"
        )
        require(
            reduced_motion_state == "none",
            f"mission cadence still animates under reduced motion: {reduced_motion_state}",
        )
        require(
            await mobile.get_by_text("Evidencia", exact=True).count() >= 1
            and await mobile.get_by_text("Decisión humana", exact=True).count() >= 1
            and await mobile.get_by_text("Ejecución gobernada", exact=True).count() >= 1,
            "reduced-motion hero lost its static mission cadence",
        )
        await mobile.screenshot(path=ARTIFACT_DIR / "functional-mobile-es.png", full_page=True)
        await browser.close()

    require(not console_errors, f"browser console errors: {console_errors}")
    require(not page_errors, f"browser page errors: {page_errors}")
    require(not unexpected_hosts, f"unexpected outbound hosts: {unexpected_hosts}")
    result: dict[str, object] = {
        "status": "PASS",
        "journey": "command_center_to_isolated_campaign_chapters",
        "chapter_navigation": "PASS_URL_HISTORY_BACK_FORWARD_ISOLATION",
        "role_blueprints": "PASS_LEAN_5_TO_FULL_10_PLUS_CUSTOM_ROLE",
        "consultant_role_dossiers": "PASS_PROPOSED_PRESERVED_APPLIED_MANUAL",
        "keyboard_progressive_disclosure": "PASS",
        "template_application": "PASS_PREVIEW_DEDUP_CONFIRM",
        "reduced_motion_cadence": "PASS_STATIC_EQUIVALENT",
        "mobile_template_preview": "PASS_SINGLE_COLUMN",
        "mobile_role_layout": "PASS_SINGLE_COLUMN",
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
