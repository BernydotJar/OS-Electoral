"""Deterministic preview and append-only application of campaign role blueprints."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from uuid import UUID, uuid5

from campaignos.teams.blueprints import (
    ROLE_BLUEPRINT_VERSION,
    blueprint_entries,
    canonical_blueprint_key,
)
from campaignos.teams.consulting_profiles import consulting_profile
from campaignos.teams.contracts import (
    TeamRoleCard,
    TeamWorkspaceProjection,
    TeamWorkspaceTemplatePreview,
    TeamWorkspaceTemplatePreviewRequest,
    TeamWorkspaceTemplateSkip,
)

_SPACE = re.compile(r"\s+")


def _identity(title: str, area: str) -> tuple[str, str]:
    return (_SPACE.sub(" ", title).strip().casefold(), _SPACE.sub(" ", area).strip().casefold())


def _role_id(workspace_id: UUID, version: int, template: str, key: str) -> UUID:
    return uuid5(
        workspace_id,
        f"{ROLE_BLUEPRINT_VERSION}:{version}:{template}:{key}",
    )


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def build_team_template_preview(
    workspace: TeamWorkspaceProjection,
    request: TeamWorkspaceTemplatePreviewRequest,
) -> TeamWorkspaceTemplatePreview:
    existing = tuple(workspace.roles or ())
    existing_pairs = {_identity(role.title, role.area): role for role in existing}
    existing_keys = {
        key: role
        for role in existing
        if (key := canonical_blueprint_key(role.title, role.area)) is not None
    }
    additions: list[TeamRoleCard] = []
    skipped: list[TeamWorkspaceTemplateSkip] = []
    for key, item in blueprint_entries(request.organization_template, request.blueprint_locale):
        profile = consulting_profile(key, request.blueprint_locale)
        exact = existing_pairs.get(_identity(item.title, item.area))
        canonical = existing_keys.get(key)
        matched = canonical or exact
        if matched is not None:
            skipped.append(
                TeamWorkspaceTemplateSkip(
                    blueprint_key=key,
                    title=item.title,
                    area=item.area,
                    matched_role_id=matched.id,
                    reason=("CANONICAL_BLUEPRINT_MATCH" if canonical else "EXACT_TITLE_AREA_MATCH"),
                    decision_scope=profile.decision_scope,
                    deliverables=profile.deliverables,
                    collaboration_points=profile.collaboration_points,
                    success_signals=profile.success_signals,
                )
            )
            continue
        additions.append(
            TeamRoleCard(
                id=_role_id(workspace.id, workspace.version, request.organization_template, key),
                title=item.title,
                area=item.area,
                purpose=item.purpose,
                responsibilities=item.responsibilities,
                decision_scope=profile.decision_scope,
                deliverables=profile.deliverables,
                collaboration_points=profile.collaboration_points,
                success_signals=profile.success_signals,
                status="VACANT",
                principal_id=None,
                availability_status="UNASSESSED",
                weekly_capacity_hours=None,
                onboarding_status="NOT_STARTED",
                vacancy_plan=item.vacancy_plan,
            )
        )
    digest_payload = {
        "workspace_id": str(workspace.id),
        "workspace_version": workspace.version,
        "organization_template": request.organization_template,
        "blueprint_locale": request.blueprint_locale,
        "blueprint_version": ROLE_BLUEPRINT_VERSION,
        "existing_roles": [
            {"id": str(role.id), "title": role.title, "area": role.area} for role in existing
        ],
        "additions": [role.model_dump(mode="json") for role in additions],
        "skipped": [item.model_dump(mode="json") for item in skipped],
    }
    return TeamWorkspaceTemplatePreview(
        workspace_id=workspace.id,
        tenant_id=workspace.tenant_id,
        campaign_id=workspace.campaign_id,
        workspace_version=workspace.version,
        organization_template=request.organization_template,
        blueprint_locale=request.blueprint_locale,
        blueprint_version=ROLE_BLUEPRINT_VERSION,
        additions=tuple(additions),
        skipped=tuple(skipped),
        preview_digest=_digest(digest_payload),
    )
