from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}: found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


shell = ROOT / "frontend/src/components/shell.tsx"
replace_once(
    shell,
    'import { TeamWorkspaceEditor } from "@/components/team-workspace-editor";\n',
    'import { TeamWorkspaceEditor } from "@/components/team-workspace-editor";\n'
    'import { TrainingAcademyPanel } from "@/components/training-academy-panel";\n',
)
replace_once(
    shell,
    "  deriveGuidedIntakeCapabilities,\n  deriveTeamWorkspaceCapabilities,\n",
    "  deriveGuidedIntakeCapabilities,\n"
    "  deriveTeamWorkspaceCapabilities,\n"
    "  deriveTrainingCapabilities,\n",
)
replace_once(
    shell,
    "  const teamCapabilities = deriveTeamWorkspaceCapabilities(\n"
    "    model.memberships,\n"
    "    model.campaign.id,\n"
    "  );\n",
    "  const teamCapabilities = deriveTeamWorkspaceCapabilities(\n"
    "    model.memberships,\n"
    "    model.campaign.id,\n"
    "  );\n"
    "  const trainingCapabilities = deriveTrainingCapabilities(\n"
    "    model.memberships,\n"
    "    model.campaign.id,\n"
    "  );\n",
)
replace_once(
    shell,
    '                    <details className="governance-metadata">\n',
    "                    <TrainingAcademyPanel\n"
    "                      locale={locale}\n"
    "                      dictionary={dictionary}\n"
    "                      catalog={model.trainingCatalog}\n"
    "                      assignments={model.trainingAssignments}\n"
    "                      receipts={model.trainingReceipts}\n"
    "                      availability={model.trainingAvailability}\n"
    "                      capabilities={trainingCapabilities}\n"
    "                      demo={model.demo}\n"
    "                    />\n\n"
    '                    <details className="governance-metadata">\n',
)

postgres_test = ROOT / "backend/tests/test_training_postgres.py"
replace_once(
    postgres_test,
    '"INSERT INTO tenants (id, slug, name, status) VALUES "\n'
    '                "(:tenant_a, :slug_a, \'Training A\', \'ACTIVE\'), "\n'
    '                "(:tenant_b, :slug_b, \'Training B\', \'ACTIVE\')"',
    '"INSERT INTO tenants (id, slug, name, status, version) VALUES "\n'
    '                "(:tenant_a, :slug_a, \'Training A\', \'ACTIVE\', 1), "\n'
    '                "(:tenant_b, :slug_b, \'Training B\', \'ACTIVE\', 1)"',
)

boundary_test = ROOT / "backend/tests/test_training_api_boundaries.py"
boundary_test.write_text(
    '''from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from campaignos.api.errors import ProblemException
from campaignos.api.routes.training import (
    _correlation_id,
    _idempotency_key,
    _raise_training_error,
    _verify_assignment_scope,
    training_service,
)
from campaignos.training.service import (
    TrainingAccessConflict,
    TrainingConflict,
    TrainingIdempotencyConflict,
    TrainingLimitConflict,
    TrainingNotFound,
    TrainingUnavailable,
    TrainingVersionConflict,
)


def request(*headers: tuple[bytes, bytes]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/training",
            "raw_path": b"/training",
            "query_string": b"",
            "headers": list(headers),
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "app": SimpleNamespace(
                state=SimpleNamespace(training_service="training-service")
            ),
        }
    )


def evidence(
    *,
    tenant_id=None,
    campaign_id=None,
    principal_id=None,
    authority_effect: str = "NONE",
    external_effects: str = "NONE",
):
    return SimpleNamespace(
        assignment=SimpleNamespace(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            principal_id=principal_id,
            authority_effect=authority_effect,
            external_effects=external_effects,
        )
    )


def test_training_service_and_correlation_id_are_request_scoped() -> None:
    req = request()
    assert training_service(req) == "training-service"
    assert _correlation_id(req) == "unknown"
    req.state.correlation_id = "training-correlation"
    assert _correlation_id(req) == "training-correlation"


def test_idempotency_key_accepts_one_trimmed_header() -> None:
    req = request((b"idempotency-key", b"  stable-key  "))
    assert _idempotency_key(req, "  stable-key  ") == "stable-key"


@pytest.mark.parametrize(
    ("headers", "value"),
    [
        ((), None),
        ((), ""),
        (((b"idempotency-key", b"one"), (b"idempotency-key", b"two")), "one"),
    ],
)
def test_idempotency_key_rejects_missing_blank_or_duplicate_headers(
    headers: tuple[tuple[bytes, bytes], ...], value: str | None
) -> None:
    with pytest.raises(HTTPException) as error:
        _idempotency_key(request(*headers), value)
    assert error.value.status_code == 428


def test_idempotency_key_rejects_oversized_value() -> None:
    value = "x" * 256
    with pytest.raises(HTTPException) as error:
        _idempotency_key(request((b"idempotency-key", value.encode())), value)
    assert error.value.status_code == 400


@pytest.mark.parametrize(
    ("exception", "status_code"),
    [
        (TrainingIdempotencyConflict("secret-idempotency-detail-409"), 409),
        (TrainingVersionConflict("secret-version-detail-412"), 412),
        (TrainingNotFound("secret-not-found-detail-404"), 404),
        (TrainingUnavailable("secret-unavailable-detail-503"), 503),
    ],
)
def test_training_errors_map_to_sanitized_http_statuses(
    exception: Exception, status_code: int
) -> None:
    with pytest.raises(HTTPException) as error:
        _raise_training_error(exception)
    assert error.value.status_code == status_code
    assert str(exception) not in str(error.value.detail)


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (TrainingLimitConflict("limit details"), "TRAINING_LIMIT_REACHED"),
        (TrainingConflict("state details"), "TRAINING_STATE_CONFLICT"),
        (TrainingAccessConflict("access details"), "TRAINING_STATE_CONFLICT"),
    ],
)
def test_training_conflicts_map_to_sanitized_problem_codes(
    exception: Exception, code: str
) -> None:
    with pytest.raises(ProblemException) as error:
        _raise_training_error(exception)
    assert error.value.status == 409
    assert error.value.code == code
    assert str(exception) not in error.value.detail


def test_unknown_training_error_is_not_hidden() -> None:
    exception = RuntimeError("unexpected")
    with pytest.raises(RuntimeError) as error:
        _raise_training_error(exception)
    assert error.value is exception


def test_assignment_scope_accepts_exact_non_effecting_projection() -> None:
    tenant_id = uuid4()
    campaign_id = uuid4()
    principal_id = uuid4()
    _verify_assignment_scope(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        evidence=evidence(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            principal_id=principal_id,
        ),
        expected_principal_id=principal_id,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "tenant",
        "campaign",
        "principal",
        "authority",
        "external",
    ],
)
def test_assignment_scope_fails_closed_on_scope_or_effect_drift(mutation: str) -> None:
    tenant_id = uuid4()
    campaign_id = uuid4()
    principal_id = uuid4()
    values = {
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
        "principal_id": principal_id,
        "authority_effect": "NONE",
        "external_effects": "NONE",
    }
    if mutation == "tenant":
        values["tenant_id"] = uuid4()
    elif mutation == "campaign":
        values["campaign_id"] = uuid4()
    elif mutation == "principal":
        values["principal_id"] = uuid4()
    elif mutation == "authority":
        values["authority_effect"] = "GRANT"
    else:
        values["external_effects"] = "CONTACT"

    with pytest.raises(HTTPException) as error:
        _verify_assignment_scope(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            evidence=evidence(**values),
            expected_principal_id=principal_id,
        )
    assert error.value.status_code == 503
''',
    encoding="utf-8",
)
