from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier, Lock
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
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError

from campaignos.agents import (
    AgentRunCreateEvidence,
    AgentRunRequest,
    AgentRuntime,
    ProviderGenerationRequest,
    ProviderGenerationResponse,
    SqlAlchemyAgentRunService,
)
from campaignos.data import Database
from campaignos.data.models import (
    AgentRun,
    AuditEvent,
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    StrategyWorkspace,
    TeamWorkspace,
    Tenant,
)
from campaignos.strategy import (
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
)

TENANT_ID = UUID("91111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("91212121-2121-4212-8212-121212121212")
CAMPAIGN_ID = UUID("92222222-2222-4222-8222-222222222222")
OTHER_CAMPAIGN_ID = UUID("92323232-3232-4232-8232-232323232323")
PRINCIPAL_ID = UUID("93333333-3333-4333-8333-333333333333")
GRANT_ID = UUID("94444444-4444-4444-8444-444444444444")
ROLE_ID = UUID("95555555-5555-4555-8555-555555555555")
EVIDENCE_ID = UUID("96666666-6666-4666-8666-666666666666")
HYPOTHESIS_A = UUID("97777777-7777-4777-8777-777777777771")
HYPOTHESIS_B = UUID("97777777-7777-4777-8777-777777777772")
OPTION_A = UUID("98888888-8888-4888-8888-888888888881")
OPTION_B = UUID("98888888-8888-4888-8888-888888888882")
OBJECTIVE_ID = UUID("99999999-9999-4999-8999-999999999990")
STRATEGY_ID = UUID("9aaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OTHER_STRATEGY_ID = UUID("9bbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
NOW = datetime(2026, 7, 21, 23, 50, tzinfo=UTC)
CREATE_PURPOSE = "Create internal governed recommendation run"


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


def _drop_role(engine: Engine, role_name: str) -> None:
    with engine.begin() as connection:
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
        "display_name": "Synthetic candidate",
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


def _strategy_documents() -> dict[str, object]:
    evidence = StrategyEvidence(
        id=EVIDENCE_ID,
        classification="VERIFIED",
        statement="A public record establishes the current internal planning context.",
        source_reference="https://example.test/public-record",
        authority="Public authority",
        jurisdiction="Guatemala",
        status="ACCEPTED",
        collected_at=NOW,
    )
    hypotheses = (
        StrategyHypothesis(
            id=HYPOTHESIS_A,
            title="Evidence consolidation",
            statement="Evidence consolidation improves internal review quality.",
            evidence_refs=(EVIDENCE_ID,),
            invalidation_signals=("Review quality does not improve",),
            status="IN_REVIEW",
        ),
        StrategyHypothesis(
            id=HYPOTHESIS_B,
            title="Capacity sequencing",
            statement="Capacity sequencing reduces unresolved internal blockers.",
            evidence_refs=(EVIDENCE_ID,),
            invalidation_signals=("Unresolved blockers increase",),
            status="IN_REVIEW",
        ),
    )
    options = (
        StrategyOption(
            id=OPTION_A,
            title="Option A",
            summary="Consolidate accepted evidence before downstream planning.",
            hypothesis_refs=(HYPOTHESIS_A,),
            evidence_refs=(EVIDENCE_ID,),
            benefits=("Preserves provenance",),
            risks=("Requires review time",),
            tradeoffs=("Delays downstream planning",),
        ),
        StrategyOption(
            id=OPTION_B,
            title="Option B",
            summary="Sequence planning by verified internal capacity.",
            hypothesis_refs=(HYPOTHESIS_B,),
            evidence_refs=(EVIDENCE_ID,),
            benefits=("Surfaces constraints",),
            risks=("May defer evidence work",),
            tradeoffs=("Prioritizes capacity",),
        ),
    )
    objective = StrategyObjective(
        id=OBJECTIVE_ID,
        outcome="Complete accepted internal evidence review.",
        metric="Accepted evidence records",
        baseline="1 accepted record",
        target="10 accepted records",
        deadline=date(2026, 8, 15),
        owner_role_id=ROLE_ID,
        evidence_refs=(EVIDENCE_ID,),
    )
    return {
        "evidence": [evidence.model_dump(mode="json")],
        "hypotheses": [item.model_dump(mode="json") for item in hypotheses],
        "options": [item.model_dump(mode="json") for item in options],
        "objectives": [objective.model_dump(mode="json")],
    }


class CountingProvider:
    provider_name = "fixture-provider"
    model_name = "fixture-model"

    def __init__(self) -> None:
        self._lock = Lock()
        self.calls = 0

    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResponse:
        with self._lock:
            self.calls += 1
        return ProviderGenerationResponse(
            provider=self.provider_name,
            model=self.model_name,
            content={
                "summary": "The options differ in sequencing and internal review burden.",
                "claims": [
                    {
                        "statement": "Both options use the same accepted public record.",
                        "classification": "SUPPORTED",
                        "evidence_refs": [str(EVIDENCE_ID)],
                    }
                ],
                "option_refs": [str(OPTION_A), str(OPTION_B)],
                "risks": ["Internal review capacity may constrain either option."],
                "uncertainties": ["The current evidence does not guarantee outcomes."],
                "human_review_required": True,
                "authority_effect": "NONE",
                "external_effects": "NONE",
            },
            prompt_tokens=100,
            output_tokens=120,
            latency_ms=50,
            cost_micros=25,
        )


def _request() -> AgentRunRequest:
    return AgentRunRequest(
        strategy_workspace_version=3,
        purpose="OPTION_COMPARISON",
        instruction="Compare documented options for internal human review.",
        output_token_limit=400,
        timeout_ms=1000,
        cost_ceiling_micros=100,
    )


@pytest.mark.postgres
def test_postgresql_agent_run_replay_and_rls(monkeypatch: pytest.MonkeyPatch) -> None:
    admin_url = _postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = "campaignos_agent_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role(admin_engine, role_name)
    with admin_engine.begin() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "20260721_0011"
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
        app_url.render_as_string(hide_password=False), pool_size=6, max_overflow=0
    )
    try:
        with database.tenant_transaction(TENANT_ID) as session:
            session.add_all(
                [
                    Tenant(id=TENANT_ID, slug="agent-tenant", name="Agent Tenant"),
                    Principal(
                        id=PRINCIPAL_ID,
                        issuer="https://identity.example.test/",
                        subject=f"agent-{PRINCIPAL_ID}",
                    ),
                ]
            )
            session.flush()
            session.add(
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="agent-campaign",
                    name="Agent Campaign",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=4,
                )
            )
            session.flush()
            session.add(_candidate(TENANT_ID, CAMPAIGN_ID))
            session.flush()
            session.add(_team(TENANT_ID, CAMPAIGN_ID))
            session.flush()
            documents = _strategy_documents()
            session.add(
                StrategyWorkspace(
                    id=STRATEGY_ID,
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    campaign_version=4,
                    candidate_workspace_version=1,
                    team_workspace_version=1,
                    known_role_ids=[str(ROLE_ID)],
                    title="Evidence-first strategy room",
                    evidence=documents["evidence"],
                    assumptions=[],
                    hypotheses=documents["hypotheses"],
                    options=documents["options"],
                    objectives=documents["objectives"],
                    contradictions=[],
                    red_team_findings=[],
                    version=3,
                )
            )
        with database.tenant_transaction(OTHER_TENANT_ID) as session:
            session.add(Tenant(id=OTHER_TENANT_ID, slug="foreign-agent", name="Foreign Agent"))
            session.flush()
            session.add(
                Campaign(
                    id=OTHER_CAMPAIGN_ID,
                    tenant_id=OTHER_TENANT_ID,
                    slug="foreign-agent-campaign",
                    name="Foreign Agent Campaign",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add(_candidate(OTHER_TENANT_ID, OTHER_CAMPAIGN_ID))
            session.flush()
            session.add(_team(OTHER_TENANT_ID, OTHER_CAMPAIGN_ID))
            session.flush()
            documents = _strategy_documents()
            session.add(
                StrategyWorkspace(
                    id=OTHER_STRATEGY_ID,
                    tenant_id=OTHER_TENANT_ID,
                    campaign_id=OTHER_CAMPAIGN_ID,
                    campaign_version=1,
                    candidate_workspace_version=1,
                    team_workspace_version=1,
                    known_role_ids=[str(ROLE_ID)],
                    title="Foreign evidence-first strategy room",
                    evidence=documents["evidence"],
                    assumptions=[],
                    hypotheses=documents["hypotheses"],
                    options=documents["options"],
                    objectives=documents["objectives"],
                    contradictions=[],
                    red_team_findings=[],
                    version=3,
                )
            )

        provider = CountingProvider()
        service = SqlAlchemyAgentRunService(database, AgentRuntime(provider))
        barrier = Barrier(2)

        def same_key(_: int) -> AgentRunCreateEvidence:
            barrier.wait()
            return service.create(
                TENANT_ID,
                CAMPAIGN_ID,
                request=_request(),
                principal_id=PRINCIPAL_ID,
                authorization_grant_id=GRANT_ID,
                approval_receipt_id="approval-agent-run",
                authorization_purpose=CREATE_PURPOSE,
                correlation_id="agent-same-key",
                idempotency_key="agent-same-key",
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            created = list(executor.map(same_key, (1, 2)))
        assert created[0] == created[1]
        assert provider.calls == 1
        run_id = created[0].run.id

        with database.tenant_transaction(TENANT_ID) as session:
            assert set(session.scalars(select(AgentRun.id))) == {run_id}
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
            row = session.get(AgentRun, run_id)
            assert row is not None
            assert row.status == "COMPLETED"
            assert row.human_disposition == "PENDING"
            assert row.authority_effect == row.external_effects == "NONE"
        with database.tenant_transaction(OTHER_TENANT_ID) as session:
            assert session.get(AgentRun, run_id) is None
            assert session.scalar(select(func.count()).select_from(AgentRun)) == 0

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(TENANT_ID) as session:
                session.add(
                    AgentRun(
                        tenant_id=OTHER_TENANT_ID,
                        campaign_id=OTHER_CAMPAIGN_ID,
                        strategy_workspace_id=OTHER_STRATEGY_ID,
                        strategy_workspace_version=3,
                        principal_id=PRINCIPAL_ID,
                        purpose="OPTION_COMPARISON",
                        instruction_digest="a" * 64,
                        policy_id="campaignos.agent.internal-recommendation",
                        policy_version="1.0",
                        prompt_template_id="agent.option-comparison",
                        prompt_template_version="1.0",
                        output_schema_version="1.0",
                        prompt_digest="b" * 64,
                        provider="fixture-provider",
                        model="fixture-model",
                        status="COMPLETED",
                        recommendation={},
                        evidence_refs=[str(EVIDENCE_ID)],
                        option_refs=[str(OPTION_A)],
                        prompt_tokens=1,
                        output_tokens=1,
                        latency_ms=1,
                        cost_micros=1,
                        human_disposition="PENDING",
                        authority_effect="NONE",
                        external_effects="NONE",
                    )
                )
    finally:
        database.dispose()
        _drop_role(admin_engine, role_name)
        admin_engine.dispose()
