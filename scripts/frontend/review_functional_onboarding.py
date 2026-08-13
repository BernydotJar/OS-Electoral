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


def transition_seconds(value: str) -> float:
    token = value.strip()
    if token.endswith("ms"):
        return float(token[:-2]) / 1000
    if token.endswith("s"):
        return float(token[:-1])
    raise ReviewFailure(f"unexpected transition duration token: {token}")


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


async def navigate_from_chapter(page: Page, href: str) -> None:
    chapter_map = page.locator(".chapter-command-map")
    require(await chapter_map.count() == 1, "chapter map disclosure is missing")
    if not await chapter_map.evaluate("element => element.open"):
        await chapter_map.locator(":scope > summary").click()
    await page.locator(f'.chapter-command-track a[href="{href}"]').click()


async def open_details(page: Page, selector: str):
    details = page.locator(selector)
    require(await details.count() == 1, f"missing disclosure: {selector}")
    if not await details.evaluate("element => element.open"):
        await details.locator(":scope > summary").click()
    return details


async def save_candidate_claim(
    page: Page, section: str, claim: str, *, label: str | None = None
) -> None:
    details = await open_details(page, f"#candidate-edit-{section}")
    form = details.locator("form").first
    if label is not None:
        await form.get_by_label("Etiqueta").fill(label)
    await form.get_by_label("Afirmación verificable").fill(claim)
    await form.get_by_label("Estado de verificación").select_option("VERIFIED")
    await form.get_by_label("Clasificación").select_option("OFFICIAL_SOURCE")
    evidence = form.locator('input[name="evidence_refs"]').first
    require(await evidence.count() == 1, f"{section}: evidence reference control missing")
    await evidence.check()
    await form.get_by_role("button", name="Guardar sección").click()
    await page.wait_for_load_state("networkidle")
    require(
        "notice=candidate_section_saved" in page.url,
        f"{section}: candidate section save notice missing: {page.url}",
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

        readiness_response = await context.request.get(f"{BASE_URL}/api/v1/ready")
        require(
            readiness_response.status == 200,
            "same-origin frontend readiness did not return HTTP 200",
        )
        readiness_payload = await readiness_response.json()
        require(
            isinstance(readiness_payload, dict) and readiness_payload.get("status") == "READY",
            "same-origin frontend readiness did not proxy the backend contract",
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
            await page.get_by_role("link", name="Candidatura").count() == 1,
            "granted candidate module is not visible",
        )
        require(
            await page.get_by_role("heading", level=1).inner_text() == "Tu campaña, paso a paso",
            "campaign command overview heading is missing",
        )
        require(
            await page.locator(".campaign-command-overview").count() == 1,
            "campaign command overview is missing",
        )
        require(
            await page.locator(".campaign-experience").count() == 0,
            "retired first-use hero remains visible",
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
        campaign_create = page.locator(".campaign-create-disclosure")
        require(
            await campaign_create.count() == 1,
            "exact campaign-create authority did not expose the governed draft flow",
        )
        await campaign_create.locator(":scope > summary").click()
        await page.get_by_label("Nombre de la candidatura", exact=True).fill(
            "Candidatura funcional"
        )
        await page.get_by_label("Territorio", exact=True).fill("Municipio funcional")
        await page.get_by_role("button", name="Crear borrador", exact=True).click()
        await page.wait_for_url("**notice=campaign_created**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Borrador de candidatura creado. El acceso y la selección siguen separados.",
                exact=True,
            ).count()
            == 1,
            "campaign draft success notice is missing",
        )
        campaign_select = page.get_by_label("Campaña autorizada")
        require(
            await campaign_select.input_value() == "22222222-2222-4222-8222-222222222222",
            "draft creation changed the active campaign context",
        )
        require(
            await campaign_select.locator("option").count() == 1,
            "new draft became visible without a separate campaign read grant",
        )
        require(
            await campaign_select.locator("option", has_text="Candidatura funcional").count() == 0,
            "new draft was implicitly authorized after creation",
        )
        await page.get_by_role("link", name="Cerrar aviso", exact=True).click()
        await page.wait_for_url("**/es#campaigns")
        require(
            await page.get_by_role(
                "link", name="Continuar información de arranque", exact=True
            ).count()
            == 1,
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

        await page.get_by_role("link", name="Continuar información de arranque", exact=True).click()
        await wait_for_chapter(page, "**/es/campaign/foundation**", "#guided-intake")
        require(
            await page.locator("#guided-intake").count() == 1,
            "foundation chapter did not render its mission",
        )
        require(
            await page.locator(".campaign-experience").count() == 0,
            "mission hero leaked into the foundation chapter",
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
        team_selector = page.locator(".guided-team-selector")
        await team_selector.get_by_label("Función sugerida").select_option(
            label="Dirección de campaña"
        )
        await (
            team_selector.locator(".guided-team-selector-controls")
            .get_by_role("button", name="Agregar función")
            .click()
        )
        await team_selector.get_by_label("Otra función o coordinación").fill(
            "Coordinación financiera"
        )
        await (
            team_selector.locator(".guided-team-custom-row")
            .get_by_role("button", name="Agregar función")
            .click()
        )
        require(
            await team_selector.locator('[data-team-chip="true"]').count() == 2,
            "guided team selector did not create two chips",
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
        guided_review = page.locator(".guided-intake-review")
        require(
            not await guided_review.evaluate("element => element.open"),
            "completed guided intake did not collapse into one-time setup",
        )
        await guided_review.locator("summary").click()
        require(
            await page.get_by_label("Cargo objetivo").input_value() == "Alcaldía Municipal",
            "saved office was not projected",
        )
        require(
            await page.get_by_label("Estado del presupuesto").input_value() == "ROUGH_RANGE",
            "saved budget was not projected",
        )
        require(
            await page.get_by_role(
                "heading", name="Construye la base de tu campaña", exact=True
            ).count()
            == 1,
            "foundation route lost its setup identity after save",
        )
        await navigate_from_chapter(page, "/es/campaign/evidence#candidate-workspace")
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
            await page.get_by_role("heading", name="Perfil y riesgos", exact=True).count() == 1,
            "candidate profile heading missing after dossier creation",
        )
        require(
            await page.locator(".candidate-profile-view").count() == 1,
            "candidate profile is not visible after dossier creation",
        )
        require(
            await page.get_by_text("Qué hacer ahora", exact=True).count() == 0,
            "candidate next-action guidance leaked into the candidacy chapter",
        )
        require(
            await page.get_by_role("tab").count() == 0,
            "retired candidate tabs remain visible after dossier creation",
        )
        evidence_disclosure = page.locator(".candidate-evidence-disclosure")
        require(await evidence_disclosure.count() == 1, "candidate evidence disclosure missing")
        await evidence_disclosure.locator(":scope > summary").click()
        require(
            await page.get_by_role("button", name="Agregar fuente").count() == 1,
            "candidate evidence editor missing after opening evidence details",
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
        evidence_disclosure = page.locator(".candidate-evidence-disclosure")
        if not await evidence_disclosure.evaluate("element => element.open"):
            await evidence_disclosure.locator(":scope > summary").click()
        require(
            await page.get_by_text("Acuerdo de convocatoria electoral", exact=True).count() >= 1,
            "candidate evidence was not projected",
        )
        require(
            await page.get_by_role(
                "heading", name="Completa el expediente sin salir de CampaignOS", exact=True
            ).count()
            == 1,
            "candidate completion workspace is missing",
        )

        await save_candidate_claim(
            page,
            "identity",
            "Ana Pérez es la identidad pública vinculada al expediente verificado.",
        )
        await save_candidate_claim(
            page,
            "biography",
            "La biografía usada en este ejercicio está respaldada por la fuente registrada.",
        )
        await save_candidate_claim(
            page,
            "purpose",
            "El propósito interno de la candidatura queda documentado con evidencia revisable.",
        )

        values = await open_details(page, "#candidate-edit-values")
        value_form = values.locator("form").last
        await value_form.get_by_label("Etiqueta").fill("Servicio público")
        await value_form.get_by_label("Afirmación verificable").fill(
            "El expediente documenta servicio público como valor declarado sujeto a evidencia."
        )
        await value_form.get_by_label("Estado de verificación").select_option("VERIFIED")
        await value_form.get_by_label("Clasificación").select_option("OFFICIAL_SOURCE")
        await value_form.locator('input[name="evidence_refs"]').first.check()
        await value_form.get_by_role("button", name="Guardar sección").click()
        await page.wait_for_load_state("networkidle")
        require("notice=candidate_section_saved" in page.url, "candidate value did not persist")

        attributes = await open_details(page, "#candidate-edit-attributes")
        attribute_form = attributes.locator("form").last
        await attribute_form.get_by_label("Nombre del atributo").fill("Capacidad de organización")
        await attribute_form.get_by_label("Afirmación verificable").fill(
            "La evidencia registrada permite revisar una afirmación acotada de capacidad organizativa."
        )
        await attribute_form.get_by_label("Estado de verificación").select_option("VERIFIED")
        await attribute_form.get_by_label("Autoevaluación de la candidatura").select_option("YES")
        await attribute_form.get_by_label("Evaluación del equipo").select_option("YES")
        await attribute_form.get_by_label("Evidencia agregada de percepción").select_option(
            "UNRESOLVED"
        )
        await attribute_form.get_by_label("Riesgo de sobreinterpretación").fill(
            "No extrapolar este atributo fuera del alcance de la evidencia."
        )
        await attribute_form.locator('input[name="evidence_refs"]').first.check()
        await attribute_form.get_by_role("button", name="Guardar sección").click()
        await page.wait_for_load_state("networkidle")
        require("notice=candidate_section_saved" in page.url, "candidate attribute did not persist")

        contradictions = await open_details(page, "#candidate-edit-contradictions")
        await contradictions.get_by_role(
            "button", name="Registrar revisión sin contradicciones abiertas", exact=True
        ).click()
        await page.wait_for_load_state("networkidle")
        require(
            "notice=candidate_section_saved" in page.url,
            "empty contradiction review did not persist",
        )

        development = await open_details(page, "#candidate-edit-development_goals")
        development_form = development.locator("form").last
        await development_form.get_by_label("Área de desarrollo").fill("Media training")
        await development_form.get_by_label("Objetivo de preparación").fill(
            "Practicar respuestas breves y verificables antes de una entrevista pública."
        )
        await development_form.get_by_label("Estado").select_option("OPEN")
        await development_form.locator('input[name="evidence_refs"]').first.check()
        await development_form.get_by_role("button", name="Guardar sección").click()
        await page.wait_for_load_state("networkidle")
        require(
            "notice=candidate_section_saved" in page.url,
            "candidate development goal did not persist",
        )

        reputation = await open_details(page, "#candidate-edit-reputation")
        await reputation.get_by_role(
            "button", name="Registrar revisión sin riesgos reputacionales abiertos", exact=True
        ).click()
        await page.wait_for_load_state("networkidle")
        require(
            "notice=candidate_section_saved" in page.url,
            "empty reputation review did not persist",
        )

        approvals = await open_details(page, "#candidate-approvals")
        require(
            await approvals.locator('.candidate-approval-list form').count() == 8,
            "all eight candidate sections were not ready for current-version approval",
        )
        approved_count = 0
        while True:
            approvals = await open_details(page, "#candidate-approvals")
            forms = approvals.locator('.candidate-approval-list form')
            if await forms.count() == 0:
                break
            form = forms.first
            await form.get_by_label("Motivo de aprobación").fill(
                "Evidencia, alcance y contradicciones revisados para esta versión interna."
            )
            await form.get_by_role("button", name="Aprobar sección", exact=True).click()
            await page.wait_for_load_state("networkidle")
            require(
                "notice=candidate_section_approved" in page.url,
                "candidate approval notice missing",
            )
            approved_count += 1
            require(approved_count <= 8, "candidate approval loop exceeded expected sections")
        require(approved_count == 8, f"candidate approvals recorded: {approved_count}")
        require(
            await page.get_by_text("Aprobación interna completa", exact=True).count() >= 1,
            "candidate workspace did not reach internally approved status",
        )
        require(
            await page.locator(
                '.candidate-profile-view .intake-checks li[data-complete="true"]'
            ).count()
            == 9,
            "candidate workspace did not complete all nine governed checks",
        )

        await navigate_from_chapter(page, "/es/campaign/team#team-workspace")
        await wait_for_chapter(page, "**/es/campaign/team**", "#team-workspace")
        compact_topbar = page.locator(".topbar-compact")
        require(await compact_topbar.count() == 1, "team chapter lacks compact command chrome")
        compact_height = await compact_topbar.evaluate(
            "element => element.getBoundingClientRect().height"
        )
        require(compact_height <= 80, f"compact command chrome is too tall: {compact_height}")
        require(
            await page.locator(".context-strip").count() == 0,
            "chapter still exposes the full technical context strip",
        )
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
        seeded_role = page.locator(".team-role-grid article").first
        seeded_role_details = seeded_role.locator(".team-role-card-details")
        seeded_role_summary = seeded_role_details.locator(":scope > summary")
        await seeded_role_summary.focus()
        await page.keyboard.press("Enter")
        require(
            await seeded_role_details.evaluate("element => element.open"),
            "seeded role details did not open from keyboard",
        )
        require(
            await seeded_role.get_by_text("Responsabilidades del puesto", exact=True).count() == 1,
            "seeded job responsibilities are not available on demand",
        )
        require(
            await seeded_role.get_by_text("Plan humano de cobertura", exact=True).count() == 1,
            "seeded human vacancy plan is not available on demand",
        )
        seeded_dossier = seeded_role.locator(".team-role-dossier")
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
        require(
            await page.get_by_role("tab", name="Crear seguimiento").get_attribute("aria-selected")
            == "true",
            "empty team operations deck did not begin on creation",
        )
        operation_layers = page.locator(".team-operations-layer")
        require(
            await operation_layers.count() == 2,
            "team operations deck must retain two accessible tab panels",
        )
        create_layer = page.locator('[data-layer="create"]')
        board_layer = page.locator('[data-layer="board"]')
        require(
            await create_layer.get_attribute("data-active") == "true",
            "creation card is not in front for an empty board",
        )
        require(
            await board_layer.get_attribute("data-active") == "false"
            and await board_layer.get_attribute("inert") is not None
            and await board_layer.get_attribute("aria-hidden") == "true",
            "inactive board panel is not inert and hidden from assistive technology",
        )
        layer_visibility = await page.locator(".team-operations-stack").evaluate(
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
            f"inactive operation panel still distracts or occupies layout: {layer_visibility}",
        )
        work_creator = page.locator(".team-work-item-creator")
        await work_creator.get_by_label("Tipo de trabajo").select_option("DELIVERABLE")
        await work_creator.get_by_label("Prioridad").select_option("HIGH")
        await work_creator.locator('select[name="cadence"]').select_option("WEEKLY")
        await work_creator.get_by_label("Nombre del seguimiento").fill(
            "Agenda semanal de dirección"
        )
        await work_creator.get_by_label("Resultado y alcance").fill(
            "Consolidar prioridades, decisiones pendientes y bloqueos del equipo."
        )
        await work_creator.get_by_label("Fecha objetivo").fill("2026-08-05")
        await work_creator.get_by_label("Siguiente acción concreta").fill(
            "Validar el alcance y los entregables con la jefatura de campaña."
        )
        await work_creator.get_by_label("Evidencia o comprobantes esperados").fill(
            "Registro de decisiones\nMapa de bloqueos"
        )
        await work_creator.get_by_role("button", name="Agregar al tablero").click()
        await page.wait_for_url("**notice=team_work_item_saved**")
        await page.wait_for_load_state("networkidle")
        require(
            await page.get_by_text(
                "Seguimiento operativo agregado al tablero con una nueva versión.",
                exact=True,
            ).count()
            == 1,
            "operational work success notice missing",
        )
        board_tab = page.get_by_role("tab", name="Tablero operativo")
        require(
            await board_tab.get_attribute("aria-selected") == "true",
            "team operations deck did not return to the board after saving work",
        )
        require(
            await board_layer.get_attribute("data-active") == "true"
            and await create_layer.get_attribute("data-active") == "false"
            and await create_layer.get_attribute("inert") is not None,
            "operation cards did not exchange front and back positions after save",
        )
        await board_tab.focus()
        await page.keyboard.press("ArrowRight")
        require(
            await page.get_by_role("tab", name="Crear seguimiento").get_attribute("aria-selected")
            == "true",
            "team creation tab did not activate with ArrowRight",
        )
        await page.keyboard.press("ArrowLeft")
        require(
            await board_tab.get_attribute("aria-selected") == "true",
            "team board tab did not reactivate with ArrowLeft",
        )
        planned_column = page.locator('.team-work-columns > section[data-status="PLANNED"]')
        await planned_column.wait_for(state="visible")
        require(
            await planned_column.get_by_role("heading", name="Planificado", exact=True).count()
            == 1,
            "planned work column is missing",
        )
        work_card = planned_column.locator(".team-work-card").filter(
            has_text="Agenda semanal de dirección"
        )
        await work_card.wait_for(state="visible")
        require(
            await work_card.count() == 1,
            "planned operational work was not projected",
        )
        card_style = await work_card.evaluate(
            """element => {
              const style = getComputedStyle(element);
              const nextAction = element.querySelector('.team-work-next-action');
              const nextStyle = nextAction ? getComputedStyle(nextAction) : null;
              return {
                borderRadius: parseFloat(style.borderRadius),
                backdropFilter: style.backdropFilter || style.webkitBackdropFilter,
                backgroundImage: style.backgroundImage,
                backgroundColor: style.backgroundColor,
                borderColor: style.borderColor,
                boxShadow: style.boxShadow,
                nextActionBackground: nextStyle?.backgroundImage ?? 'none',
                structuredBadges: element.querySelectorAll('[data-kind]').length,
              };
            }"""
        )
        glass_enhancement = "blur" in card_style["backdropFilter"]
        glass_fallback = (
            card_style["backgroundImage"] != "none"
            and card_style["borderColor"] != "rgba(0, 0, 0, 0)"
            and "inset" in card_style["boxShadow"]
        )
        require(
            card_style["borderRadius"] >= 18
            and (glass_enhancement or glass_fallback)
            and card_style["boxShadow"] != "none"
            and card_style["nextActionBackground"] != "none"
            and card_style["structuredBadges"] == 3,
            f"work card lacks restrained liquid-glass hierarchy or fallback: {card_style}",
        )
        work_details = work_card.locator(".team-work-details")
        await work_details.locator("summary").focus()
        await page.keyboard.press("Enter")
        require(
            await work_details.get_by_text("Registro de decisiones", exact=True).count() == 1,
            "operational evidence did not persist",
        )
        status_select = work_card.locator('.team-work-check-in select[name="status"]')
        for executed_status in ("ACTIVE", "BLOCKED", "COMPLETE"):
            option = status_select.locator(f'option[value="{executed_status}"]')
            require(
                await option.get_attribute("disabled") is not None,
                (
                    "vacant organizational function exposed executable status "
                    f"{executed_status} without a human owner"
                ),
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
            await proposed_dossier.locator(".team-role-dossier-grid > section").count() == 4,
            "proposed function dossier does not expose four consulting sections",
        )
        require(
            await proposed_dossier.locator(
                ".team-role-dossier-grid > section:nth-child(2) li"
            ).count()
            == 3,
            "proposed function dossier does not expose three deliverables",
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

        apply_template = page.get_by_role("button", name="Aplicar funciones nuevas · 5", exact=True)
        require(
            await apply_template.count() == 1,
            "template apply action is not visible next to the preview summary",
        )
        confirmation_top = await apply_template.evaluate(
            "element => element.closest('.team-template-confirm-form').getBoundingClientRect().top"
        )
        catalog_top = await page.locator(".team-template-role-grid").evaluate(
            "element => element.getBoundingClientRect().top"
        )
        require(
            confirmation_top < catalog_top,
            "template confirmation remains buried below the detailed catalog",
        )
        await apply_template.click()
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
        require(
            await page.get_by_text("Agenda semanal de dirección", exact=True).count() == 1,
            "operational work item did not persist after reload",
        )
        manual_role_card = page.get_by_text("Coordinación de voluntariado", exact=True).locator(
            "xpath=ancestor::article[1]"
        )
        manual_role_details = manual_role_card.locator(".team-role-card-details")
        await manual_role_details.locator(":scope > summary").click()
        manual_dossier = manual_role_details.locator(".team-role-dossier")
        await manual_dossier.locator("summary").click()
        require(
            await manual_dossier.get_by_text("Plan de turnos", exact=True).count() == 1,
            "manual role consultant dossier did not persist",
        )

        await navigate_from_chapter(page, "/es/campaign/evidence#candidate-workspace")
        await wait_for_chapter(page, "**/es/campaign/evidence**", "#candidate-workspace")
        persisted_evidence = page.locator(".candidate-evidence-disclosure")
        require(
            await persisted_evidence.count() == 1,
            "candidate evidence disclosure is missing after chapter navigation",
        )
        if not await persisted_evidence.evaluate("element => element.open"):
            await persisted_evidence.locator(":scope > summary").click()
        require(
            await page.get_by_text("Acuerdo de convocatoria electoral", exact=True).count() >= 1,
            "candidate evidence did not persist on its chapter route",
        )
        await navigate_from_chapter(page, "/es/campaign/foundation#guided-intake")
        await wait_for_chapter(page, "**/es/campaign/foundation**", "#guided-intake")
        require(
            await page.locator(".campaign-experience").count() == 0,
            "mission hero leaked back into the completed foundation route",
        )
        guided_review = page.locator(".guided-intake-review")
        require(
            not await guided_review.evaluate("element => element.open"),
            "completed setup did not remain collapsed after chapter navigation",
        )
        await guided_review.locator("summary").click()
        require(
            await page.get_by_label("Cargo objetivo").input_value() == "Alcaldía Municipal",
            "intake did not persist on its chapter route",
        )
        require(
            await page.get_by_text("Alcaldía Municipal", exact=True).count() >= 1,
            "persisted intake value is absent from its read projection",
        )
        await navigate_from_chapter(page, "/es/campaign/team#team-workspace")
        await wait_for_chapter(page, "**/es/campaign/team**", "#team-workspace")
        require(
            await page.get_by_text("Coordinación de voluntariado", exact=True).count() >= 1,
            "team chapter did not restore after chapter-to-chapter navigation",
        )
        await assert_no_overflow(page, "functional-desktop-es-team")
        await assert_accessible(page, "functional-desktop-es-team")
        await page.screenshot(path=ARTIFACT_DIR / "functional-desktop-es.png", full_page=True)

        await page.goto(f"{BASE_URL}/es", wait_until="networkidle")
        require(
            await page.get_by_role("heading", name="Resumen de candidatura", exact=True).count()
            == 1,
            "candidate summary is unavailable from the Spanish overview",
        )
        require(
            await page.get_by_text("Qué hacer ahora", exact=True).count() == 1,
            "candidate next-action guidance is missing from the Spanish overview",
        )

        english = await browser.new_page(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        attach_page_guards(english)
        await english.goto(f"{BASE_URL}/en/campaign/foundation", wait_until="networkidle")
        require(
            await english.locator(".campaign-experience").count() == 0,
            "mission hero leaked into the English foundation chapter",
        )
        english_guided_review = english.locator(".guided-intake-review")
        require(
            await english_guided_review.count() == 1
            and not await english_guided_review.evaluate("element => element.open"),
            "completed English setup did not start collapsed",
        )
        require(
            await english.get_by_role("button", name="Save changes").count() == 0,
            "completed English setup exposed its editor before review",
        )
        await english_guided_review.get_by_text("View saved setup", exact=True).click()
        require(
            await english.get_by_role("button", name="Save changes").count() == 1,
            "English foundation editor is unavailable after opening setup review",
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
            await english.get_by_role("heading", name="Profile and risks", exact=True).count() == 1,
            "English candidate profile is unavailable",
        )
        require(
            await english.get_by_text("What to do now", exact=True).count() == 0,
            "English candidate next-action guidance leaked into the candidacy chapter",
        )
        require(
            await english.get_by_role("tab").count() == 0,
            "retired candidate tabs remain visible in English",
        )
        english_evidence = english.locator(".candidate-evidence-disclosure")
        await english_evidence.locator(":scope > summary").click()
        require(
            await english.get_by_role("button", name="Add source").count() == 1,
            "English candidate evidence editor is unavailable",
        )
        await english.goto(f"{BASE_URL}/en", wait_until="networkidle")
        require(
            await english.get_by_role("heading", name="Candidacy summary", exact=True).count() == 1,
            "English candidacy summary is unavailable from the overview",
        )
        require(
            await english.get_by_text("What to do now", exact=True).count() == 1,
            "English candidate next-action guidance is missing from the overview",
        )
        await english.goto(f"{BASE_URL}/en/campaign/team", wait_until="networkidle")
        require(
            await english.get_by_role("button", name="Add function").count() == 1,
            "English team function editor is unavailable",
        )
        english_role_details = english.locator(".team-role-grid .team-role-card-details").first
        await english_role_details.locator(":scope > summary").click()
        english_dossier = english_role_details.locator(".team-role-dossier")
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
        mobile_work_columns = await mobile.locator(".team-work-columns").evaluate(
            "element => getComputedStyle(element).gridTemplateColumns.split(' ').length"
        )
        require(
            mobile_work_columns == 1,
            f"mobile operations board is not a single responsive column: {mobile_work_columns}",
        )
        require(
            await mobile.locator(".campaign-experience, .experience-mission-pulse").count() == 0,
            "mission hero leaked into the mobile team chapter",
        )
        require(
            await mobile.locator(".team-operations-layer").count() == 2,
            "mobile team chapter lost one of its operation tab panels",
        )
        reduced_transition = await mobile.locator(".team-operations-layer").first.evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )
        require(
            all(transition_seconds(part) <= 0.0001 for part in reduced_transition.split(",")),
            f"team operation cards still transition under reduced motion: {reduced_transition}",
        )
        await mobile.screenshot(path=ARTIFACT_DIR / "functional-mobile-es.png", full_page=True)
        # training academy functional journey
        await page.goto(f"{BASE_URL}/es/campaign/team", wait_until="networkidle")
        require(
            await page.get_by_role("heading", name="Academia de campaña", exact=True).count() == 1,
            "authenticated Training Academy is missing",
        )
        require(
            await page.get_by_text("Investigar antes de actuar", exact=True).count() >= 1,
            "training path is missing",
        )
        assign_button = page.get_by_role("button", name="Asignarme esta ruta", exact=True).first
        if await assign_button.count() == 1:
            await assign_button.click()
            await page.wait_for_load_state("networkidle")
            require(
                "/es/campaign/team" in page.url,
                f"training assignment left the Team chapter: {page.url}",
            )
        start_button = page.get_by_role("button", name="Comenzar lección", exact=True)
        require(
            await start_button.count() == 1,
            "assigned training module cannot be started",
        )
        await start_button.click()
        await page.wait_for_load_state("networkidle")
        require(
            "/es/campaign/team" in page.url,
            f"training start left the Team chapter: {page.url}",
        )
        require(
            await page.get_by_role(
                "heading", name="Comprobación de aprendizaje", exact=True
            ).count()
            == 1,
            "training assessment is unavailable after module start",
        )
        await page.get_by_label("Investigar y documentar evidencia", exact=True).check()
        await page.get_by_role("button", name="Enviar respuesta", exact=True).click()
        await page.wait_for_load_state("networkidle")
        require(
            "/es/campaign/team" in page.url,
            f"training assessment left the Team chapter: {page.url}",
        )
        require(
            await page.get_by_text("Módulo aprobado", exact=True).count() == 1,
            "passing training result is missing",
        )
        require(
            await page.get_by_text("Finalización interna", exact=False).count() >= 1,
            "append-only training completion receipt is missing",
        )
        require(
            await page.get_by_text(
                (
                    "La formación no concede permisos, no evalúa desempeño laboral "
                    "y no es una acreditación profesional."
                ),
                exact=True,
            ).count()
            == 1,
            "training authority boundary is missing",
        )
        await page.goto(f"{BASE_URL}/en/campaign/team", wait_until="networkidle")
        require(
            await page.get_by_role("heading", name="Campaign academy", exact=True).count() == 1,
            "English Training Academy is unavailable after completion",
        )
        require(
            await page.get_by_text("Internal completion", exact=False).count() >= 1,
            "English training completion receipt is unavailable",
        )

        await browser.close()

    require(not console_errors, f"browser console errors: {console_errors}")
    require(not page_errors, f"browser page errors: {page_errors}")
    require(not unexpected_hosts, f"unexpected outbound hosts: {unexpected_hosts}")
    result: dict[str, object] = {
        "status": "PASS",
        "journey": "command_center_to_isolated_campaign_chapters",
        "same_origin_readiness": "PASS_FRONTEND_PROXY_TO_BACKEND_READY",
        "governed_campaign_draft": "PASS_DRAFT_PERSISTED_CONTEXT_AND_ACCESS_UNCHANGED",
        "chapter_navigation": "PASS_URL_HISTORY_BACK_FORWARD_ISOLATION",
        "role_blueprints": "PASS_LEAN_5_TO_FULL_10_PLUS_CUSTOM_ROLE",
        "consultant_role_dossiers": "PASS_PROPOSED_PRESERVED_APPLIED_MANUAL",
        "role_operations_board": "PASS_PLANNED_RACI_EVIDENCE_PERSISTENCE_VACANT_ACTIVATION_BLOCKED",
        "keyboard_progressive_disclosure": "PASS",
        "template_application": "PASS_PREVIEW_DEDUP_CONFIRM",
        "reduced_motion_cadence": "PASS_STATIC_EQUIVALENT",
        "mobile_template_preview": "PASS_SINGLE_COLUMN",
        "mobile_role_layout": "PASS_SINGLE_COLUMN",
        "persistence_after_reload": "PASS",
        "candidate_dossier_completion": "PASS_9_OF_9_CURRENT_VERSION_APPROVED",
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
