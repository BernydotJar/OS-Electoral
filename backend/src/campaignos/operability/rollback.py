"""Fail-closed release rollback policy and constrained rehearsal evidence.

This module is deliberately a decision boundary, not a deployment controller.
It never executes migrations, restores a database, changes configuration, or
promotes an application artifact.
"""

from __future__ import annotations

import ast
import json
import os
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SHA_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
MIGRATION_REVISION_PATTERN: Final = re.compile(r"^[0-9]{8}_[0-9]{4}$")
UNKNOWN_MIGRATION_PATTERN: Final = re.compile(r"^[a-z0-9_]{3,64}$")
REQUIRED_PROTECTED_CONTROLS: Final = {
    "authentication",
    "authorization",
    "row_level_security",
    "append_only_audit",
    "rate_limiting",
    "safety_gates",
}
REQUIRED_PROHIBITED_COMMAND_FRAGMENTS: Final = {
    "alembic downgrade",
    "drop database",
    "drop table",
    "truncate table",
    "pg_restore --clean",
    "terraform apply",
    "docker push",
    "automatic replay",
}
SENSITIVE_RECEIPT_PATTERNS: Final = (
    re.compile(r"(?i)postgres(?:ql)?(?:\+psycopg)?://"),
    re.compile(r"(?i)\b(?:bearer|password|cookie|secret)\b\s*[:=]"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)https?://"),
    re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
)


class MigrationClassification(StrEnum):
    EXPAND_BACKWARD_COMPATIBLE = "EXPAND_BACKWARD_COMPATIBLE"
    REVERSIBLE_TESTED_NO_DATA_LOSS = "REVERSIBLE_TESTED_NO_DATA_LOSS"
    FORWARD_FIX_ONLY = "FORWARD_FIX_ONLY"
    RESTORE_REQUIRED_FOR_DATA_RECOVERY = "RESTORE_REQUIRED_FOR_DATA_RECOVERY"


class RollbackResponse(StrEnum):
    ABORT_BEFORE_CHANGE = "ABORT_BEFORE_CHANGE"
    ROLL_BACK_APPLICATION_ARTIFACT = "ROLL_BACK_APPLICATION_ARTIFACT"
    REVERSE_CONFIGURATION = "REVERSE_CONFIGURATION"
    FORWARD_FIX_SCHEMA_OR_APPLICATION = "FORWARD_FIX_SCHEMA_OR_APPLICATION"
    ISOLATED_RESTORE_FOR_INVESTIGATION = "ISOLATED_RESTORE_FOR_INVESTIGATION"
    CONTAIN_AND_ESCALATE = "CONTAIN_AND_ESCALATE"
    REFUSE_UNSAFE_ROLLBACK = "REFUSE_UNSAFE_ROLLBACK"


EXPECTED_SCENARIOS: Final[dict[str, RollbackResponse]] = {
    "release_stopped_before_migration": RollbackResponse.ABORT_BEFORE_CHANGE,
    "application_health_failure_backward_compatible": (
        RollbackResponse.ROLL_BACK_APPLICATION_ARTIFACT
    ),
    "application_health_failure_unknown_schema": RollbackResponse.REFUSE_UNSAFE_ROLLBACK,
    "stale_or_failed_migration_no_writes": RollbackResponse.FORWARD_FIX_SCHEMA_OR_APPLICATION,
    "suspected_data_integrity_after_writes": RollbackResponse.CONTAIN_AND_ESCALATE,
    "identity_or_database_dependency_outage": RollbackResponse.CONTAIN_AND_ESCALATE,
    "worker_retry_or_dead_letter_growth": RollbackResponse.CONTAIN_AND_ESCALATE,
    "configuration_regression": RollbackResponse.REVERSE_CONFIGURATION,
    "verified_backup_isolated_restore": RollbackResponse.ISOLATED_RESTORE_FOR_INVESTIGATION,
    "missing_authority_or_evidence": RollbackResponse.REFUSE_UNSAFE_ROLLBACK,
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MigrationPolicy(StrictModel):
    revision: str
    down_revision: str | None
    classification: MigrationClassification
    compatibility_window: str = Field(min_length=1, max_length=160)
    data_loss_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL_CONTROL_LOSS"]
    default_response: RollbackResponse
    reason: str = Field(min_length=1, max_length=400)

    @field_validator("revision")
    @classmethod
    def validate_revision(cls, value: str) -> str:
        if not MIGRATION_REVISION_PATTERN.fullmatch(value):
            raise ValueError("migration revision must use YYYYMMDD_NNNN")
        return value

    @field_validator("down_revision")
    @classmethod
    def validate_down_revision(cls, value: str | None) -> str | None:
        if value is not None and not MIGRATION_REVISION_PATTERN.fullmatch(value):
            raise ValueError("down revision must use YYYYMMDD_NNNN")
        return value


class RollbackScenario(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_]{3,80}$")
    trigger: str = Field(min_length=1, max_length=300)
    owner: str = Field(min_length=1, max_length=120)
    prerequisites: tuple[str, ...] = Field(min_length=1)
    evidence_requirements: tuple[str, ...] = Field(min_length=1)
    prohibited_actions: tuple[str, ...] = Field(min_length=1)
    stop_conditions: tuple[str, ...] = Field(min_length=1)
    escalation: str = Field(min_length=1, max_length=300)
    expected_response: RollbackResponse


class RollbackPolicy(StrictModel):
    schema_version: Literal["1.0"]
    increment: Literal["C3-OPS-002"]
    environment_classification: Literal["CONSTRAINED_NON_PRODUCTION"]
    production_status: Literal["BLOCKED"]
    release_decision: Literal["DENY_RELEASE"]
    external_effects: Literal["NONE"]
    production_rollback_claim: Literal[False]
    current_migration_head: str
    allowed_responses: tuple[RollbackResponse, ...]
    prohibited_command_fragments: tuple[str, ...] = Field(min_length=1)
    protected_controls: tuple[str, ...] = Field(min_length=1)
    migrations: tuple[MigrationPolicy, ...] = Field(min_length=1)
    scenarios: tuple[RollbackScenario, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)

    @field_validator("current_migration_head")
    @classmethod
    def validate_current_migration_head(cls, value: str) -> str:
        if not MIGRATION_REVISION_PATTERN.fullmatch(value):
            raise ValueError("current migration head must use YYYYMMDD_NNNN")
        return value

    @model_validator(mode="after")
    def validate_catalog(self) -> RollbackPolicy:
        if len(self.allowed_responses) != len(set(self.allowed_responses)):
            raise ValueError("allowed response inventory contains duplicates")
        if set(self.allowed_responses) != set(RollbackResponse):
            raise ValueError("allowed response inventory is incomplete")
        if len(self.protected_controls) != len(set(self.protected_controls)):
            raise ValueError("protected control inventory contains duplicates")
        if set(self.protected_controls) != REQUIRED_PROTECTED_CONTROLS:
            raise ValueError("protected control inventory drift")
        if len(self.prohibited_command_fragments) != len(set(self.prohibited_command_fragments)):
            raise ValueError("prohibited command inventory contains duplicates")
        if not REQUIRED_PROHIBITED_COMMAND_FRAGMENTS <= set(self.prohibited_command_fragments):
            raise ValueError("required prohibited command fragment is missing")
        migration_ids = [item.revision for item in self.migrations]
        if len(migration_ids) != len(set(migration_ids)):
            raise ValueError("migration catalog contains duplicate revisions")
        if self.current_migration_head not in set(migration_ids):
            raise ValueError("current migration head is absent from the catalog")
        scenario_ids = [item.id for item in self.scenarios]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("rollback scenario inventory contains duplicates")
        scenario_map = {item.id: item.expected_response for item in self.scenarios}
        if scenario_map != EXPECTED_SCENARIOS:
            raise ValueError("rollback scenario inventory or expected response drift")
        return self


class AuthorityCheck(StrictModel):
    granted: bool
    scope: str = Field(min_length=1, max_length=120)


class ArtifactCheck(StrictModel):
    reference: str = Field(min_length=1, max_length=80)
    immutable: bool
    provenance_present: bool


class HealthCheck(StrictModel):
    name: Literal["liveness", "readiness", "identity", "database", "worker"]
    passed: bool


class RehearsalContext(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    scenario_id: str = Field(pattern=r"^[a-z0-9_]{3,80}$")
    source_revision: str
    candidate_revision: str
    previous_known_good_revision: str
    environment_classification: Literal["CONSTRAINED_NON_PRODUCTION"]
    authority: AuthorityCheck
    artifact: ArtifactCheck
    migration_head: str
    committed_writes_observed: bool
    health_checks: tuple[HealthCheck, ...] = Field(min_length=1)
    configuration_snapshot_present: bool
    protected_controls_preserved: bool
    verified_backup_present: bool
    isolated_restore_target: bool
    automatic_worker_replay_requested: bool
    production_target: bool
    requested_operation: str = Field(min_length=1, max_length=160)

    @field_validator("source_revision", "candidate_revision", "previous_known_good_revision")
    @classmethod
    def validate_sha(cls, value: str) -> str:
        if not SHA_PATTERN.fullmatch(value):
            raise ValueError("revisions must be full lowercase Git SHAs")
        return value

    @field_validator("migration_head")
    @classmethod
    def validate_migration_head(cls, value: str) -> str:
        if not (
            MIGRATION_REVISION_PATTERN.fullmatch(value)
            or UNKNOWN_MIGRATION_PATTERN.fullmatch(value)
        ):
            raise ValueError("invalid migration head")
        return value

    @model_validator(mode="after")
    def validate_health_inventory(self) -> RehearsalContext:
        names = [item.name for item in self.health_checks]
        if len(names) != len(set(names)):
            raise ValueError("health check names must be unique")
        return self


class ReceiptEvidenceCheck(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_]{3,80}$")
    passed: bool


class ReceiptCleanup(StrictModel):
    temporary_files_removed: bool
    restore_target_state: Literal["NOT_CREATED", "REMOVED", "RETAINED_AUTHORIZED"]
    source_mutation: Literal["NONE"]


class RollbackReceipt(StrictModel):
    schema_version: Literal["1.0"]
    generated_at: str
    source_revision: str
    environment_classification: Literal["CONSTRAINED_NON_PRODUCTION"]
    scenario_id: str
    candidate_revision: str
    previous_known_good_revision: str
    migration_head: str
    migration_classification: str
    committed_writes_observed: bool
    authority_check: Literal["PASS", "FAIL"]
    artifact_provenance_check: Literal["PASS", "FAIL", "NOT_APPLICABLE"]
    health_checks: tuple[HealthCheck, ...]
    evidence_checks: tuple[ReceiptEvidenceCheck, ...]
    selected_response: RollbackResponse
    expected_response: RollbackResponse
    decision: Literal["PASS", "FAIL"]
    decision_reason: str = Field(pattern=r"^[A-Z0-9_]{3,100}$")
    cleanup: ReceiptCleanup
    limitations: tuple[str, ...]
    production_rollback_claim: Literal[False]
    external_effects: Literal["NONE"]

    @field_validator("source_revision", "candidate_revision", "previous_known_good_revision")
    @classmethod
    def validate_sha(cls, value: str) -> str:
        if not SHA_PATTERN.fullmatch(value):
            raise ValueError("receipt revisions must be full lowercase Git SHAs")
        return value


class RollbackFailureReceipt(StrictModel):
    schema_version: Literal["1.0"]
    generated_at: str
    environment_classification: Literal["CONSTRAINED_NON_PRODUCTION"]
    status: Literal["FAIL"]
    failure_class: str = Field(pattern=r"^[A-Z0-9_]{3,100}$")
    selected_response: Literal[RollbackResponse.REFUSE_UNSAFE_ROLLBACK]
    decision: Literal["FAIL"]
    production_rollback_claim: Literal[False]
    external_effects: Literal["NONE"]


def discover_migration_chain(migrations_directory: Path) -> tuple[tuple[str, str | None], ...]:
    revisions: list[tuple[str, str | None]] = []
    for path in sorted(migrations_directory.glob("*.py")):
        values: dict[str, str | None] = {}
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if not isinstance(target, ast.Name) or target.id not in {
                    "revision",
                    "down_revision",
                }:
                    continue
                if node.value is None:
                    continue
                value = ast.literal_eval(node.value)
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"unsupported migration revision in {path}")
                values[target.id] = value
        revision = values.get("revision")
        if not isinstance(revision, str):
            raise ValueError(f"migration lacks revision: {path}")
        revisions.append((revision, values.get("down_revision")))
    if not revisions:
        raise ValueError("migration directory is empty")
    return tuple(revisions)


def load_policy(path: Path) -> RollbackPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RollbackPolicy.model_validate(payload)


def validate_policy_against_repository(policy: RollbackPolicy, repository_root: Path) -> None:
    discovered = discover_migration_chain(repository_root / "backend/migrations/versions")
    catalog = tuple((item.revision, item.down_revision) for item in policy.migrations)
    if catalog != discovered:
        raise ValueError("migration policy does not match the repository migration chain")
    for index, (revision, down_revision) in enumerate(discovered):
        expected_down = None if index == 0 else discovered[index - 1][0]
        if down_revision != expected_down:
            raise ValueError(
                f"migration chain is not linear at {revision}; expected {expected_down}"
            )
    if discovered[-1][0] != policy.current_migration_head:
        raise ValueError("current migration head does not match the repository")


def _operation_is_prohibited(policy: RollbackPolicy, requested_operation: str) -> bool:
    normalized = " ".join(requested_operation.lower().split())
    return any(fragment.lower() in normalized for fragment in policy.prohibited_command_fragments)


def _migration_by_revision(policy: RollbackPolicy, revision: str) -> MigrationPolicy | None:
    return next((item for item in policy.migrations if item.revision == revision), None)


def select_response(
    policy: RollbackPolicy, context: RehearsalContext
) -> tuple[RollbackResponse, str, tuple[ReceiptEvidenceCheck, ...]]:
    scenario = next((item for item in policy.scenarios if item.id == context.scenario_id), None)
    if scenario is None:
        raise ValueError("unknown rollback scenario")
    migration = _migration_by_revision(policy, context.migration_head)
    source_matches = context.source_revision == context.candidate_revision
    previous_is_distinct = context.previous_known_good_revision != context.candidate_revision
    authority_valid = context.authority.granted and (
        context.authority.scope == "CONSTRAINED_NON_PRODUCTION_REHEARSAL"
    )
    artifact_valid = (
        context.artifact.immutable
        and context.artifact.provenance_present
        and context.artifact.reference == context.previous_known_good_revision
    )
    operation_safe = not _operation_is_prohibited(policy, context.requested_operation)
    checks = (
        ReceiptEvidenceCheck(id="source_matches_candidate", passed=source_matches),
        ReceiptEvidenceCheck(id="previous_revision_is_distinct", passed=previous_is_distinct),
        ReceiptEvidenceCheck(id="authority_scope_valid", passed=authority_valid),
        ReceiptEvidenceCheck(id="artifact_is_immutable_and_provenanced", passed=artifact_valid),
        ReceiptEvidenceCheck(id="migration_is_cataloged", passed=migration is not None),
        ReceiptEvidenceCheck(id="requested_operation_is_safe", passed=operation_safe),
        ReceiptEvidenceCheck(
            id="protected_controls_preserved", passed=context.protected_controls_preserved
        ),
        ReceiptEvidenceCheck(
            id="automatic_worker_replay_absent",
            passed=not context.automatic_worker_replay_requested,
        ),
        ReceiptEvidenceCheck(id="production_target_absent", passed=not context.production_target),
    )

    if context.production_target:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "PRODUCTION_TARGET_FORBIDDEN", checks
    if not source_matches or not previous_is_distinct:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "REVISION_EVIDENCE_INVALID", checks
    if not authority_valid:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "AUTHORITY_MISSING", checks
    if not operation_safe:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "DESTRUCTIVE_OPERATION_REFUSED", checks
    if context.automatic_worker_replay_requested:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "AUTOMATIC_REPLAY_REFUSED", checks
    if not context.protected_controls_preserved:
        return (
            RollbackResponse.REFUSE_UNSAFE_ROLLBACK,
            "PROTECTED_CONTROL_WEAKENING_REFUSED",
            checks,
        )
    if migration is None:
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "UNKNOWN_MIGRATION_REFUSED", checks

    expected = scenario.expected_response
    if expected == RollbackResponse.ROLL_BACK_APPLICATION_ARTIFACT:
        health_failure_observed = any(not item.passed for item in context.health_checks)
        if migration.classification != MigrationClassification.EXPAND_BACKWARD_COMPATIBLE:
            return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "SCHEMA_NOT_BACKWARD_COMPATIBLE", checks
        if not artifact_valid:
            return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "ARTIFACT_EVIDENCE_INVALID", checks
        if not health_failure_observed:
            return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "ROLLBACK_TRIGGER_NOT_PROVEN", checks
    if expected == RollbackResponse.REVERSE_CONFIGURATION and not (
        context.configuration_snapshot_present and context.protected_controls_preserved
    ):
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "CONFIGURATION_SNAPSHOT_INVALID", checks
    if expected == RollbackResponse.ISOLATED_RESTORE_FOR_INVESTIGATION and not (
        context.verified_backup_present and context.isolated_restore_target
    ):
        return RollbackResponse.REFUSE_UNSAFE_ROLLBACK, "RESTORE_EVIDENCE_INVALID", checks
    if (
        expected == RollbackResponse.FORWARD_FIX_SCHEMA_OR_APPLICATION
        and context.committed_writes_observed
    ):
        return RollbackResponse.CONTAIN_AND_ESCALATE, "WRITES_REQUIRE_CONTAINMENT", checks
    return expected, "POLICY_RESPONSE_SELECTED", checks


def build_receipt(policy: RollbackPolicy, context: RehearsalContext) -> RollbackReceipt:
    scenario = next((item for item in policy.scenarios if item.id == context.scenario_id), None)
    if scenario is None:
        raise ValueError("unknown rollback scenario")
    selected, reason, checks = select_response(policy, context)
    migration = _migration_by_revision(policy, context.migration_head)
    receipt = RollbackReceipt(
        schema_version="1.0",
        generated_at=datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        source_revision=context.source_revision,
        environment_classification="CONSTRAINED_NON_PRODUCTION",
        scenario_id=context.scenario_id,
        candidate_revision=context.candidate_revision,
        previous_known_good_revision=context.previous_known_good_revision,
        migration_head=context.migration_head,
        migration_classification=(
            migration.classification.value if migration is not None else "UNKNOWN"
        ),
        committed_writes_observed=context.committed_writes_observed,
        authority_check=(
            "PASS"
            if context.authority.granted
            and context.authority.scope == "CONSTRAINED_NON_PRODUCTION_REHEARSAL"
            else "FAIL"
        ),
        artifact_provenance_check=(
            "PASS"
            if context.artifact.immutable
            and context.artifact.provenance_present
            and context.artifact.reference == context.previous_known_good_revision
            else "FAIL"
        ),
        health_checks=context.health_checks,
        evidence_checks=checks,
        selected_response=selected,
        expected_response=scenario.expected_response,
        decision="PASS" if selected == scenario.expected_response else "FAIL",
        decision_reason=reason,
        cleanup=ReceiptCleanup(
            temporary_files_removed=True,
            restore_target_state="NOT_CREATED",
            source_mutation="NONE",
        ),
        limitations=policy.limitations,
        production_rollback_claim=False,
        external_effects="NONE",
    )
    assert_sanitized_receipt(receipt)
    return receipt


def assert_sanitized_receipt(receipt: RollbackReceipt) -> None:
    serialized = json.dumps(receipt.model_dump(mode="json"), sort_keys=True)
    for pattern in SENSITIVE_RECEIPT_PATTERNS:
        if pattern.search(serialized):
            raise ValueError("rollback receipt contains prohibited sensitive content")


def _write_strict_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    os.chmod(path, 0o600)


def write_receipt(path: Path, receipt: RollbackReceipt) -> None:
    assert_sanitized_receipt(receipt)
    _write_strict_json(path, receipt.model_dump(mode="json"))


def build_failure_receipt(failure_class: str) -> RollbackFailureReceipt:
    receipt = RollbackFailureReceipt(
        schema_version="1.0",
        generated_at=datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        environment_classification="CONSTRAINED_NON_PRODUCTION",
        status="FAIL",
        failure_class=failure_class,
        selected_response=RollbackResponse.REFUSE_UNSAFE_ROLLBACK,
        decision="FAIL",
        production_rollback_claim=False,
        external_effects="NONE",
    )
    serialized = json.dumps(receipt.model_dump(mode="json"), sort_keys=True)
    for pattern in SENSITIVE_RECEIPT_PATTERNS:
        if pattern.search(serialized):
            raise ValueError("rollback failure receipt contains prohibited sensitive content")
    return receipt


def write_failure_receipt(path: Path, receipt: RollbackFailureReceipt) -> None:
    _write_strict_json(path, receipt.model_dump(mode="json"))
