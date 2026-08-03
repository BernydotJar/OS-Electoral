from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
    Campaign,
    IdempotencyRecord,
    Membership,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    TrainingAssignment,
    TrainingCompletionReceipt,
    TrainingModuleProgress,
)
from campaignos.training.catalog import CATALOG_DIGEST, module_by_ref
from campaignos.training.contracts import (
    TrainingAnswerSubmission,
    TrainingAssignmentCreate,
    TrainingAttemptRequest,
    TrainingModuleStartRequest,
)
from campaignos.training.service import (
    SqlAlchemyTrainingService,
    TrainingAccessConflict,
    TrainingIdempotencyConflict,
    TrainingNotFound,
    TrainingUnavailable,
    TrainingVersionConflict,
    UnavailableTrainingService,
    _assignment,
    _assignment_projection,
    _campaign,
    _guard,
    _progress,
    _require_active_learner,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
MANAGER_ID = UUID("33333333-3333-4333-8333-333333333333")
LEARNER_ID = UUID("44444444-4444-4444-8444-444444444444")
OTHER_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        expire_on_commit=False,
    )
    runtime = Database(engine=engine, _sessions=sessions)
    now = datetime(2026, 8, 1, 5, 30, tzinfo=UTC)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Principal(
                    id=MANAGER_ID,
                    issuer="https://identity.example.test/",
                    subject="training-manager",
                ),
                Principal(
                    id=LEARNER_ID,
                    issuer="https://identity.example.test/",
                    subject="training-learner",
                ),
                Principal(
                    id=OTHER_ID,
                    issuer="https://identity.example.test/",
                    subject="other-learner",
                ),
            ]
        )
        session.flush()
        session.add(
            Campaign(
                id=CAMPAIGN_ID,
                tenant_id=TENANT_ID,
                slug="campaign",
                name="Campaign",
                jurisdiction="Antigua Guatemala",
                stage="PRECAMPAIGN",
                status="ACTIVE",
                version=1,
            )
        )
        session.flush()
        session.add_all(
            [
                Membership(
                    tenant_id=TENANT_ID,
                    principal_id=MANAGER_ID,
                    campaign_id=CAMPAIGN_ID,
                    status="ACTIVE",
                    valid_from=now,
                    version=1,
                ),
                Membership(
                    tenant_id=TENANT_ID,
                    principal_id=LEARNER_ID,
                    campaign_id=CAMPAIGN_ID,
                    status="ACTIVE",
                    valid_from=now,
                    version=1,
                ),
            ]
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def create_assignment(database: Database, *, key: str = "training-create-1"):
    return SqlAlchemyTrainingService(database).create_assignment(
        TENANT_ID,
        CAMPAIGN_ID,
        request=TrainingAssignmentCreate(
            principal_id=LEARNER_ID,
            path_id="research_foundations_path",
            path_version="1.0.0",
            catalog_digest=CATALOG_DIGEST,
            role_slug="electoral_research",
        ),
        principal_id=MANAGER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-manage",
        authorization_purpose="Assign campaign learning path",
        correlation_id="training-create",
        idempotency_key=key,
    )


def correct_answers() -> tuple[TrainingAnswerSubmission, ...]:
    module = module_by_ref("research_foundations", "1.0.0")
    return tuple(
        TrainingAnswerSubmission(
            question_id=question.id,
            option_ids=question.correct_option_ids,
        )
        for question in module.localized("es").questions
    )


def test_assignment_start_and_completion_are_idempotent_and_create_no_authority(
    database: Database,
) -> None:
    service = SqlAlchemyTrainingService(database)
    created = create_assignment(database)
    assert create_assignment(database) == created
    assert created.assignment.status == "ASSIGNED"
    assert created.assignment.next_module_id == "research_foundations"
    progress = created.assignment.modules[0]

    started = service.start_module(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingModuleStartRequest(
            expected_assignment_version=1,
            expected_progress_version=1,
            catalog_digest=CATALOG_DIGEST,
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-start",
        idempotency_key="training-start-1",
    )
    assert started.assignment.status == "IN_PROGRESS"
    assert started.assignment.version == 2
    assert started.assignment.modules[0].version == 2

    completed = service.submit_attempt(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingAttemptRequest(
            locale="es",
            expected_assignment_version=2,
            expected_progress_version=2,
            catalog_digest=CATALOG_DIGEST,
            answers=correct_answers(),
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-attempt",
        idempotency_key="training-attempt-1",
    )
    assert completed.outcome.result == "PASS"
    assert completed.assignment.status == "COMPLETED"
    assert completed.assignment.authority_effect == "NONE"
    assert completed.receipt is not None
    assert completed.receipt.authority_effect == "NONE"
    replay = service.submit_attempt(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingAttemptRequest(
            locale="es",
            expected_assignment_version=2,
            expected_progress_version=2,
            catalog_digest=CATALOG_DIGEST,
            answers=correct_answers(),
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="ignored-on-replay",
        idempotency_key="training-attempt-1",
    )
    assert replay == completed

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(TrainingAssignment)) == 1
        assert session.scalar(select(func.count()).select_from(TrainingModuleProgress)) == 1
        assert session.scalar(select(func.count()).select_from(TrainingCompletionReceipt)) == 1
        assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 0
        assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 3
        audits = tuple(session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)))
        assert [item.event_type for item in audits] == [
            "training.assignment.created",
            "training.module.started",
            "training.module.attempted",
        ]
        assert "answers" not in str(audits[-1].payload).lower()


def test_failed_attempt_is_bounded_and_does_not_create_receipt(database: Database) -> None:
    service = SqlAlchemyTrainingService(database)
    created = create_assignment(database)
    progress = created.assignment.modules[0]
    started = service.start_module(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingModuleStartRequest(
            expected_assignment_version=1,
            expected_progress_version=1,
            catalog_digest=CATALOG_DIGEST,
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-start",
        idempotency_key="training-start-fail",
    )
    failed = service.submit_attempt(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingAttemptRequest(
            locale="es",
            expected_assignment_version=started.assignment.version,
            expected_progress_version=started.assignment.modules[0].version,
            catalog_digest=CATALOG_DIGEST,
            answers=(
                TrainingAnswerSubmission(
                    question_id="knowledge_check",
                    option_ids=("incorrect",),
                ),
            ),
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-fail",
        idempotency_key="training-attempt-fail",
    )
    assert failed.outcome.result == "FAIL"
    assert failed.receipt is None
    assert failed.assignment.status == "IN_PROGRESS"
    assert failed.assignment.modules[0].attempt_count == 1


def test_stale_catalog_versions_and_foreign_learner_fail_closed(database: Database) -> None:
    service = SqlAlchemyTrainingService(database)
    created = create_assignment(database)
    progress = created.assignment.modules[0]
    with pytest.raises(TrainingVersionConflict):
        service.start_module(
            TENANT_ID,
            CAMPAIGN_ID,
            created.assignment.id,
            progress.module_id,
            request=TrainingModuleStartRequest(
                expected_assignment_version=99,
                expected_progress_version=1,
                catalog_digest=CATALOG_DIGEST,
            ),
            principal_id=LEARNER_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-training-self",
            authorization_purpose="Complete assigned campaign training",
            correlation_id="training-stale",
            idempotency_key="training-stale",
        )
    with pytest.raises(TrainingAccessConflict):
        service.start_module(
            TENANT_ID,
            CAMPAIGN_ID,
            created.assignment.id,
            progress.module_id,
            request=TrainingModuleStartRequest(
                expected_assignment_version=1,
                expected_progress_version=1,
                catalog_digest=CATALOG_DIGEST,
            ),
            principal_id=OTHER_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-training-self",
            authorization_purpose="Complete assigned campaign training",
            correlation_id="training-other",
            idempotency_key="training-other",
        )
    with pytest.raises(TrainingIdempotencyConflict):
        SqlAlchemyTrainingService(database).create_assignment(
            TENANT_ID,
            CAMPAIGN_ID,
            request=TrainingAssignmentCreate(
                principal_id=LEARNER_ID,
                path_id="research_foundations_path",
                path_version="1.0.0",
                catalog_digest=CATALOG_DIGEST,
                role_slug="campaign_leadership",
            ),
            principal_id=MANAGER_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-training-manage",
            authorization_purpose="Assign campaign learning path",
            correlation_id="training-conflict",
            idempotency_key="training-create-1",
        )


def test_audited_training_reads_preserve_learner_scope_and_receipts(
    database: Database,
) -> None:
    service = SqlAlchemyTrainingService(database)
    created = create_assignment(database, key="training-read-create")

    assignments = service.list_self(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self-read",
        authorization_purpose="Review own campaign training",
        correlation_id="training-list-self",
    )
    assert [item.id for item in assignments.assignments] == [created.assignment.id]
    assert assignments.assignments[0].principal_id == LEARNER_ID

    detail = service.get_assignment(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        principal_id=MANAGER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-admin-read",
        authorization_purpose="Review campaign training assignment",
        correlation_id="training-get-assignment",
    )
    assert detail.assignment.id == created.assignment.id
    assert detail.assignment.authority_effect == "NONE"

    empty_receipts = service.list_receipts(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-receipt-read",
        authorization_purpose="Review own campaign training",
        correlation_id="training-receipts-empty",
    )
    assert empty_receipts.receipts == ()
    with pytest.raises(TrainingAccessConflict):
        service.list_receipts(
            TENANT_ID,
            CAMPAIGN_ID,
            created.assignment.id,
            principal_id=OTHER_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-training-receipt-read",
            authorization_purpose="Review own campaign training",
            correlation_id="training-receipts-foreign",
        )

    progress = created.assignment.modules[0]
    started = service.start_module(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingModuleStartRequest(
            expected_assignment_version=created.assignment.version,
            expected_progress_version=progress.version,
            catalog_digest=CATALOG_DIGEST,
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-read-start",
        idempotency_key="training-read-start",
    )
    with pytest.raises(TrainingAccessConflict):
        service.submit_attempt(
            TENANT_ID,
            CAMPAIGN_ID,
            created.assignment.id,
            progress.module_id,
            request=TrainingAttemptRequest(
                locale="es",
                expected_assignment_version=started.assignment.version,
                expected_progress_version=started.assignment.modules[0].version,
                catalog_digest=CATALOG_DIGEST,
                answers=correct_answers(),
            ),
            principal_id=OTHER_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-training-self",
            authorization_purpose="Complete assigned campaign training",
            correlation_id="training-read-foreign-attempt",
            idempotency_key="training-read-foreign-attempt",
        )

    completed = service.submit_attempt(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        progress.module_id,
        request=TrainingAttemptRequest(
            locale="es",
            expected_assignment_version=started.assignment.version,
            expected_progress_version=started.assignment.modules[0].version,
            catalog_digest=CATALOG_DIGEST,
            answers=correct_answers(),
        ),
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-self",
        authorization_purpose="Complete assigned campaign training",
        correlation_id="training-read-complete",
        idempotency_key="training-read-complete",
    )
    assert completed.receipt is not None

    receipts = service.list_receipts(
        TENANT_ID,
        CAMPAIGN_ID,
        created.assignment.id,
        principal_id=LEARNER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-training-receipt-read",
        authorization_purpose="Review own campaign training",
        correlation_id="training-receipts-complete",
    )
    assert [item.id for item in receipts.receipts] == [completed.receipt.id]
    assert receipts.receipts[0].principal_id == LEARNER_ID
    assert receipts.receipts[0].authority_effect == "NONE"

    with database.tenant_transaction(TENANT_ID) as session:
        read_events = tuple(
            session.scalars(
                select(AuditEvent)
                .where(AuditEvent.event_type.like("training.%read"))
                .order_by(AuditEvent.occurred_at)
            )
        )
    assert [item.event_type for item in read_events] == [
        "training.assignments.read",
        "training.assignment.read",
        "training.receipts.read",
        "training.receipts.read",
    ]
    assert all(item.payload["authority_effect"] == "NONE" for item in read_events)


def test_unavailable_adapter_and_guard_preserve_fail_closed_errors() -> None:
    unavailable = UnavailableTrainingService()
    with pytest.raises(TrainingUnavailable):
        unavailable.catalog("es")
    with pytest.raises(TrainingUnavailable):
        _missing_operation = unavailable.list_self

    assert _guard(lambda: "available") == "available"
    known = TrainingNotFound("known training absence")
    with pytest.raises(TrainingNotFound) as known_error:
        _guard(lambda: (_ for _ in ()).throw(known))
    assert known_error.value is known

    with pytest.raises(TrainingUnavailable) as unexpected_error:
        _guard(lambda: (_ for _ in ()).throw(ValueError("sensitive backend detail")))
    assert "sensitive backend detail" not in str(unexpected_error.value)
    assert isinstance(unexpected_error.value.__cause__, ValueError)


def test_training_repository_helpers_fail_closed_on_missing_or_corrupt_state(
    database: Database,
) -> None:
    service = SqlAlchemyTrainingService(database)
    assert service.catalog("es").locale == "es"
    created = create_assignment(database, key="training-helper-create")

    with database.tenant_transaction(TENANT_ID) as session:
        with pytest.raises(TrainingNotFound):
            _campaign(session, TENANT_ID, UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
        with pytest.raises(TrainingNotFound):
            _require_active_learner(
                session,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                principal_id=OTHER_ID,
            )
        with pytest.raises(TrainingNotFound):
            _assignment(
                session,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                assignment_id=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
                lock=True,
            )
        with pytest.raises(TrainingNotFound):
            _progress(
                session,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                assignment_id=created.assignment.id,
                module_id="missing_module",
                lock=True,
            )
        row = session.get(TrainingAssignment, created.assignment.id)
        assert row is not None
        with pytest.raises(TrainingUnavailable):
            _assignment_projection(row, ())
