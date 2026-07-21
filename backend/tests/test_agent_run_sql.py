from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from campaignos.agents import (
    AgentRunCreateEvidence,
    AgentRunIdempotencyConflict,
    AgentRunNotFound,
    AgentRunRequest,
    AgentRunStrategyConflict,
    AgentRuntime,
    ProviderGenerationRequest,
    ProviderGenerationResponse,
    SqlAlchemyAgentRunService,
    UnavailableStructuredGenerationProvider,
)
from campaignos.data import Base, Database
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
from campaignos.workers import InternalCampaignUpdatedHandler, OutboxWorker

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
GRANT_ID = UUID("44444444-4444-4444-8444-444444444444")
ROLE_ID = UUID("55555555-5555-4555-8555-555555555555")
EVIDENCE_ID = UUID("66666666-6666-4666-8666-666666666666")
HYPOTHESIS_A = UUID("77777777-7777-4777-8777-777777777771")
HYPOTHESIS_B = UUID("77777777-7777-4777-8777-777777777772")
OPTION_A = UUID("88888888-8888-4888-8888-888888888881")
OPTION_B = UUID("88888888-8888-4888-8888-888888888882")
OBJECTIVE_ID = UUID("99999999-9999-4999-8999-999999999999")
STRATEGY_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NOW = datetime(2026, 7, 21, 23, 30, tzinfo=UTC)
CREATE_PURPOSE = "Create internal governed recommendation run"
READ_PURPOSE = "Review internal governed recommendation run"


def strategy_documents() -> dict[str, object]:
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


@pytest.fixture
def database() -> Iterator[Database]:
    runtime = Database.from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(runtime.engine)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="agent", name="Agent"),
                Tenant(id=OTHER_TENANT_ID, slug="other-agent", name="Other Agent"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="agent-operator",
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
        session.add_all(
            [
                CandidateWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    candidate_id=uuid4(),
                    display_name="Synthetic candidate",
                    evidence=[],
                    version=2,
                    created_at=NOW,
                    updated_at=NOW,
                ),
                TeamWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
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
                    version=3,
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.flush()
        documents = strategy_documents()
        session.add(
            StrategyWorkspace(
                id=STRATEGY_ID,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                campaign_version=4,
                candidate_workspace_version=2,
                team_workspace_version=3,
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
                created_at=NOW,
                updated_at=NOW,
            )
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def recommendation() -> dict[str, object]:
    return {
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
    }


class Provider:
    provider_name = "fixture-provider"
    model_name = "fixture-model"

    def __init__(self) -> None:
        self.calls: list[ProviderGenerationRequest] = []

    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResponse:
        self.calls.append(request)
        return ProviderGenerationResponse(
            provider=self.provider_name,
            model=self.model_name,
            content=recommendation(),
            prompt_tokens=100,
            output_tokens=120,
            latency_ms=50,
            cost_micros=25,
        )


def run_request(**changes: object) -> AgentRunRequest:
    values: dict[str, object] = {
        "strategy_workspace_version": 3,
        "purpose": "OPTION_COMPARISON",
        "instruction": "Compare documented options for internal human review.",
        "output_token_limit": 400,
        "timeout_ms": 1000,
        "cost_ceiling_micros": 100,
    }
    values.update(changes)
    return AgentRunRequest.model_validate(values)


def create_run(
    service: SqlAlchemyAgentRunService,
    *,
    key: str = "agent-run-create",
    value: AgentRunRequest | None = None,
    grant_id: UUID = GRANT_ID,
) -> AgentRunCreateEvidence:
    return service.create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=value or run_request(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=grant_id,
        approval_receipt_id="approval-agent-run",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id=key,
        idempotency_key=key,
    )


def test_sql_agent_run_replays_without_second_provider_call(database: Database) -> None:
    provider = Provider()
    service = SqlAlchemyAgentRunService(database, AgentRuntime(provider))

    created = create_run(service)
    replay = create_run(service)
    read = service.get(
        TENANT_ID,
        CAMPAIGN_ID,
        created.run.id,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-agent-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="agent-run-read",
    )

    assert replay == created
    assert len(provider.calls) == 1
    assert created.run.status == "COMPLETED"
    assert created.run.human_disposition == "PENDING"
    assert created.run.authority_effect == created.run.external_effects == "NONE"
    assert created.run.provider == "fixture-provider"
    assert created.run.prompt_digest is not None
    assert read.run == created.run

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
        row = session.scalar(select(AgentRun))
        assert row is not None
        assert row.recommendation is not None
        assert row.evidence_refs == [str(EVIDENCE_ID)]
        outbox = session.scalar(select(OutboxEvent))
        assert outbox is not None
        assert outbox.topic == "agent.run.recorded"
        assert outbox.payload["external_effects"] == "NONE"
        serialized = " ".join(
            [
                str(row.recommendation),
                str(outbox.payload),
                *(str(item.payload) for item in session.scalars(select(AuditEvent))),
                *(
                    str(item.response_payload)
                    for item in session.scalars(select(IdempotencyRecord))
                ),
            ]
        )
        assert "Compare documented options for internal human review" not in serialized


def test_sql_agent_run_changed_request_or_authority_conflicts(database: Database) -> None:
    provider = Provider()
    service = SqlAlchemyAgentRunService(database, AgentRuntime(provider))
    create_run(service)

    with pytest.raises(AgentRunIdempotencyConflict):
        create_run(
            service,
            value=run_request(instruction="Compare only the documented evidence."),
        )
    with pytest.raises(AgentRunIdempotencyConflict):
        create_run(service, grant_id=uuid4())

    assert len(provider.calls) == 1
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_sql_agent_run_persists_provider_unavailable_refusal(database: Database) -> None:
    service = SqlAlchemyAgentRunService(
        database,
        AgentRuntime(UnavailableStructuredGenerationProvider()),
    )
    created = create_run(service)

    assert created.run.status == "REFUSED"
    assert created.run.refusal_code == "PROVIDER_UNAVAILABLE"
    assert created.run.recommendation is None
    assert created.run.prompt_digest is not None
    assert created.run.provider is None
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(AgentRun, created.run.id)
        assert row is not None and row.status == "REFUSED"
        assert row.refusal_code == "PROVIDER_UNAVAILABLE"


def test_sql_agent_run_stale_strategy_rolls_back_without_provider(database: Database) -> None:
    provider = Provider()
    service = SqlAlchemyAgentRunService(database, AgentRuntime(provider))

    with pytest.raises(AgentRunStrategyConflict):
        create_run(service, value=run_request(strategy_workspace_version=2))

    assert provider.calls == []
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(AgentRun)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_sql_agent_run_scope_and_not_found_fail_closed(database: Database) -> None:
    service = SqlAlchemyAgentRunService(database, AgentRuntime(Provider()))
    created = create_run(service)

    with pytest.raises(AgentRunNotFound):
        service.get(
            OTHER_TENANT_ID,
            CAMPAIGN_ID,
            created.run.id,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-agent-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="cross-tenant-agent-read",
        )
    with pytest.raises(AgentRunNotFound):
        service.get(
            TENANT_ID,
            CAMPAIGN_ID,
            uuid4(),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-agent-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="missing-agent-read",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_agent_run_internal_outbox_is_delivered_without_external_effect(
    database: Database,
) -> None:
    service = SqlAlchemyAgentRunService(database, AgentRuntime(Provider()))
    created = create_run(service)

    with database.tenant_transaction(TENANT_ID) as session:
        pending = session.get(OutboxEvent, created.outbox_event_id)
        assert pending is not None
        available_at = pending.available_at
        if available_at.utcoffset() is None:
            available_at = available_at.replace(tzinfo=UTC)
        else:
            available_at = available_at.astimezone(UTC)
        worker_now = available_at + timedelta(seconds=1)

    result = OutboxWorker(
        database,
        "agent-worker",
        InternalCampaignUpdatedHandler(),
    ).run_once(TENANT_ID, now=worker_now)

    assert result.claimed == result.delivered == 1
    assert result.retried == result.dead_lettered == 0
    with database.tenant_transaction(TENANT_ID) as session:
        event = session.get(OutboxEvent, created.outbox_event_id)
        assert event is not None
        assert event.status == "DELIVERED"
        assert event.payload["authority_effect"] == "NONE"
        assert event.payload["external_effects"] == "NONE"
