from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Uuid,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from campaignos.data import Database
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    StrategyDecisionReceipt,
    StrategyWorkspace,
    TeamWorkspace,
    Tenant,
)
from campaignos.strategy import (
    SqlAlchemyStrategyWorkspaceService,
    StrategyAssumption,
    StrategyDecisionRequest,
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
    StrategyWorkspaceConflict,
    StrategyWorkspaceCreate,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceVersionConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
GRANT_ID = UUID("44444444-4444-4444-8444-444444444444")
ROLE_ID = UUID("55555555-5555-4555-8555-555555555555")
EVIDENCE_ID = UUID("66666666-6666-4666-8666-666666666666")
ASSUMPTION_ID = UUID("77777777-7777-4777-8777-777777777777")
HYPOTHESIS_A = UUID("88888888-8888-4888-8888-888888888881")
HYPOTHESIS_B = UUID("88888888-8888-4888-8888-888888888882")
OPTION_A = UUID("99999999-9999-4999-8999-999999999991")
OPTION_B = UUID("99999999-9999-4999-8999-999999999992")
OBJECTIVE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)
CREATE_PURPOSE = "Create campaign strategy workspace"
READ_PURPOSE = "Review campaign strategy workspace"
UPDATE_PURPOSE = "Maintain campaign strategy workspace"
DECIDE_PURPOSE = "Approve internal campaign strategy option"


def _postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("PostgreSQL integration tests require an isolated *_test database")
    return value


def _drop_role(engine: object, role_name: str) -> None:
    with engine.begin() as connection:  # type: ignore[union-attr]
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


def _candidate(tenant_id: UUID, campaign_id: UUID) -> CandidateWorkspace:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
        "candidate_id": uuid4(),
        "title": "Synthetic candidate workspace",
        "name": "Synthetic candidate",
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    for column in CandidateWorkspace.__table__.columns:
        if column.name in values or column.primary_key or column.default or column.server_default:
            continue
        if column.nullable:
            values[column.name] = None
        elif isinstance(column.type, Uuid):
            values[column.name] = uuid4()
        elif isinstance(column.type, Integer):
            values[column.name] = 1
        elif isinstance(column.type, Boolean):
            values[column.name] = False
        elif isinstance(column.type, DateTime):
            values[column.name] = now
        elif isinstance(column.type, JSON):
            values[column.name] = []
        elif isinstance(column.type, String):
            values[column.name] = "synthetic"
        else:
            raise AssertionError(f"Unsupported CandidateWorkspace column {column.name}")
    return CandidateWorkspace(**values)


def _team(tenant_id: UUID, campaign_id: UUID) -> TeamWorkspace:
    return TeamWorkspace(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        organization_template="LEAN_CAMPAIGN",
        roles=[
            {
                "id": str(ROLE_ID),
                "title": "Campaign direction",
                "area": "Direction",
                "purpose": "Own accountable human decisions.",
                "responsibilities": ["Decide"],
                "status": "FILLED",
                "principal_id": str(PRINCIPAL_ID),
                "availability_status": "AVAILABLE",
                "weekly_capacity_hours": 40,
                "onboarding_status": "COMPLETE",
                "vacancy_plan": None,
            }
        ],
        work_items=[],
        training_requirements=[],
        access_recommendations=[],
        version=1,
    )


def ready_update() -> StrategyWorkspaceUpdate:
    evidence = StrategyEvidence(
        id=EVIDENCE_ID,
        classification="VERIFIED",
        statement="A public record establishes the current campaign context.",
        source_reference="https://example.test/public-record",
        authority="Public authority",
        jurisdiction="Guatemala",
        status="ACCEPTED",
        collected_at=NOW,
    )
    assumption = StrategyAssumption(
        id=ASSUMPTION_ID,
        statement="The team can maintain the documented operating cadence.",
        evidence_refs=(EVIDENCE_ID,),
        invalidation_signals=("Available capacity falls below the documented threshold",),
    )
    return StrategyWorkspaceUpdate(
        evidence=(evidence,),
        assumptions=(assumption,),
        hypotheses=(
            StrategyHypothesis(
                id=HYPOTHESIS_A,
                title="Evidence consolidation",
                statement="Evidence consolidation improves internal decision quality.",
                evidence_refs=(EVIDENCE_ID,),
                assumption_refs=(ASSUMPTION_ID,),
                invalidation_signals=("Decision quality does not improve",),
                status="IN_REVIEW",
            ),
            StrategyHypothesis(
                id=HYPOTHESIS_B,
                title="Capacity-first sequencing",
                statement="Capacity-first sequencing reduces internal blockers.",
                evidence_refs=(EVIDENCE_ID,),
                assumption_refs=(ASSUMPTION_ID,),
                invalidation_signals=("Unresolved blockers increase",),
                status="IN_REVIEW",
            ),
        ),
        options=(
            StrategyOption(
                id=OPTION_A,
                title="Option A",
                summary="Consolidate evidence before downstream planning.",
                hypothesis_refs=(HYPOTHESIS_A,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Preserves provenance",),
                risks=("Requires review time",),
                tradeoffs=("Delays downstream planning",),
            ),
            StrategyOption(
                id=OPTION_B,
                title="Option B",
                summary="Sequence internal planning by verified capacity.",
                hypothesis_refs=(HYPOTHESIS_B,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Surfaces capacity constraints",),
                risks=("May defer evidence collection",),
                tradeoffs=("Prioritizes capacity over speed",),
            ),
        ),
        objectives=(
            StrategyObjective(
                id=OBJECTIVE_ID,
                outcome="Complete the accepted internal evidence review.",
                metric="Accepted evidence records",
                baseline="1 accepted record",
                target="10 accepted records",
                deadline=date(2026, 8, 15),
                owner_role_id=ROLE_ID,
                evidence_refs=(EVIDENCE_ID,),
            ),
        ),
        contradictions=(),
        red_team_findings=(),
    )


def _create(service: SqlAlchemyStrategyWorkspaceService, key: str):
    return service.create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=StrategyWorkspaceCreate(title="Evidence-first strategy room"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-create",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id=key,
        idempotency_key=key,
    )


@pytest.mark.postgres
def test_postgresql_strategy_replay_decision_versioning_and_rls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = _postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = "campaignos_strategy_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role(admin_engine, role_name)
    with admin_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        assert connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = :name"),
            {"name": role_name},
        ).one() == (False, False)
        connection.execute(text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{role_name}"'))
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role_name}"'))
        connection.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
                f'TO "{role_name}"'
            )
        )

    app_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(
        app_url.render_as_string(hide_password=False), pool_size=8, max_overflow=0
    )
    foreign_campaign_id = uuid4()
    foreign_role_id = uuid4()
    try:
        with database.tenant_transaction(TENANT_ID) as session:
            session.add_all(
                [
                    Tenant(id=TENANT_ID, slug="strategy-tenant", name="Strategy Tenant"),
                    Principal(
                        id=PRINCIPAL_ID,
                        issuer="https://identity.example.test/",
                        subject=f"strategy-{PRINCIPAL_ID}",
                    ),
                ]
            )
            session.flush()
            session.add(
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="strategy-campaign",
                    name="Strategy Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=5,
                )
            )
            session.flush()
            session.add(_candidate(TENANT_ID, CAMPAIGN_ID))
            session.flush()
            session.add(_team(TENANT_ID, CAMPAIGN_ID))
        with database.tenant_transaction(OTHER_TENANT_ID) as session:
            session.add(
                Tenant(id=OTHER_TENANT_ID, slug="foreign-strategy", name="Foreign Strategy")
            )
            session.flush()
            session.add(
                Campaign(
                    id=foreign_campaign_id,
                    tenant_id=OTHER_TENANT_ID,
                    slug="foreign-strategy-campaign",
                    name="Foreign Strategy Campaign",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add(_candidate(OTHER_TENANT_ID, foreign_campaign_id))
            session.flush()
            foreign_team = _team(OTHER_TENANT_ID, foreign_campaign_id)
            foreign_team.roles[0]["id"] = str(foreign_role_id)  # type: ignore[index]
            session.add(foreign_team)

        service = SqlAlchemyStrategyWorkspaceService(database)
        barrier = Barrier(2)

        def same_key(_: int):
            barrier.wait()
            return _create(service, "strategy-same-key")

        with ThreadPoolExecutor(max_workers=2) as executor:
            created = list(executor.map(same_key, (1, 2)))
        assert created[0] == created[1]
        workspace_id = created[0].workspace.id

        update = service.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=ready_update(),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-strategy-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="strategy-update",
            idempotency_key="strategy-update",
        )
        assert update.workspace.status == "READY_FOR_HUMAN_DECISION"
        assert update.workspace.version == 2

        update_barrier = Barrier(2)

        def stale_race(index: int) -> str:
            update_barrier.wait()
            try:
                service.update(
                    TENANT_ID,
                    CAMPAIGN_ID,
                    expected_version=2,
                    changes=StrategyWorkspaceUpdate(title=f"Strategy title {index}"),
                    principal_id=PRINCIPAL_ID,
                    authorization_grant_id=GRANT_ID,
                    approval_receipt_id="approval-strategy-race",
                    authorization_purpose=UPDATE_PURPOSE,
                    correlation_id=f"strategy-race-{index}",
                    idempotency_key=f"strategy-race-{index}",
                )
            except StrategyWorkspaceVersionConflict:
                return "VERSION_CONFLICT"
            return "UPDATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(stale_race, (1, 2))) == ["UPDATED", "VERSION_CONFLICT"]

        current = service.get(
            TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-strategy-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="strategy-read",
        )
        assert current.workspace.version == 3
        decision = service.decide(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=3,
            request=StrategyDecisionRequest(
                selected_option_id=current.workspace.options[0].id,  # type: ignore[index]
                reason="Authorized human decision after evidence and red-team review.",
                human_role_id=ROLE_ID,
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-strategy-v3",
            authorization_purpose=DECIDE_PURPOSE,
            correlation_id="strategy-decide",
            idempotency_key="strategy-decide",
        )
        replay = service.decide(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=3,
            request=StrategyDecisionRequest(
                selected_option_id=decision.decision.selected_option_id,
                reason="Authorized human decision after evidence and red-team review.",
                human_role_id=ROLE_ID,
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-strategy-v3",
            authorization_purpose=DECIDE_PURPOSE,
            correlation_id="strategy-decide-replay",
            idempotency_key="strategy-decide",
        )
        assert replay == decision
        assert decision.workspace.status == "DECIDED_INTERNAL"

        with database.tenant_transaction(TENANT_ID) as session:
            campaign_row = session.get(Campaign, CAMPAIGN_ID)
            assert campaign_row is not None
            campaign_row.version = 6
            team_row = session.scalar(
                select(TeamWorkspace).where(
                    TeamWorkspace.tenant_id == TENANT_ID,
                    TeamWorkspace.campaign_id == CAMPAIGN_ID,
                )
            )
            assert team_row is not None
            team_row.version = 2
            team_row.roles = [
                {
                    **team_row.roles[0],
                    "id": str(uuid4()),
                    "principal_id": str(uuid4()),
                }
            ]

        historical = service.get(
            TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-strategy-historical-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="strategy-historical-read",
        )
        assert historical.workspace.campaign_version == 5
        assert historical.workspace.team_workspace_version == 1
        assert historical.workspace.decision is not None
        assert historical.workspace.decision.human_role_id == ROLE_ID

        with database.tenant_transaction(TENANT_ID) as session:
            assert set(session.scalars(select(StrategyWorkspace.id))) == {workspace_id}
            assert session.scalar(select(func.count()).select_from(StrategyDecisionReceipt)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 6
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 4
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 4
        with database.tenant_transaction(OTHER_TENANT_ID) as session:
            assert session.scalar(select(func.count()).select_from(StrategyWorkspace)) == 0

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(TENANT_ID) as session:
                session.add(
                    StrategyWorkspace(
                        tenant_id=OTHER_TENANT_ID,
                        campaign_id=foreign_campaign_id,
                        campaign_version=1,
                        candidate_workspace_version=1,
                        team_workspace_version=1,
                        known_role_ids=[str(foreign_role_id)],
                        title="Cross-tenant strategy",
                        evidence=None,
                        assumptions=None,
                        hypotheses=None,
                        options=None,
                        objectives=None,
                        contradictions=None,
                        red_team_findings=None,
                        version=1,
                    )
                )

        with pytest.raises(StrategyWorkspaceConflict):
            _create(service, "strategy-distinct-key")
    finally:
        database.dispose()
        _drop_role(admin_engine, role_name)
        admin_engine.dispose()
