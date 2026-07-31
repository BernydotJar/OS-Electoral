from __future__ import annotations

from dataclasses import dataclass, field

from campaignos.performance import WorkloadCatalog, default_workload_catalog
from campaignos.performance import supervisor as supervisor_module
from campaignos.performance.supervisor import ProcessIsolatedLoadSupervisor


@dataclass
class HangingProcess:
    target: object
    args: tuple[object, ...]
    name: str
    alive: bool = False
    exitcode: int | None = None
    join_timeouts: list[float | None] = field(default_factory=list)

    def start(self) -> None:
        self.alive = True

    def join(self, timeout: float | None = None) -> None:
        self.join_timeouts.append(timeout)

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.alive = False
        self.exitcode = -15

    def kill(self) -> None:
        self.alive = False
        self.exitcode = -9


class FakeContext:
    def __init__(self) -> None:
        self.processes: list[HangingProcess] = []

    def Process(self, *, target, args, name):  # type: ignore[no-untyped-def,override]
        process = HangingProcess(target=target, args=args, name=name)
        self.processes.append(process)
        return process


def test_supervisor_terminates_hung_scenario_at_hard_deadline(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    configured = default_workload_catalog().scenarios[0]
    scenario = configured.model_copy(
        update={"request_count": 1, "concurrency": 1, "timeout_seconds": 0.05}
    )
    catalog = WorkloadCatalog(catalog_version="1.0", scenarios=(scenario,))
    context = FakeContext()
    cleaned: list[str] = []
    monkeypatch.setattr(supervisor_module, "_postgresql_version", lambda url: "18.3")
    monkeypatch.setattr(supervisor_module.multiprocessing, "get_context", lambda mode: context)
    monkeypatch.setattr(
        supervisor_module,
        "cleanup_verification_role",
        lambda url, role: cleaned.append(role),
    )

    receipt = ProcessIsolatedLoadSupervisor(
        database_url="postgresql+psycopg://local/performance_test",
        source_revision="f" * 40,
        catalog=catalog,
    ).run()

    assert receipt.overall_decision == "FAIL"
    assert receipt.scenarios[0].timed_out == 1
    assert receipt.scenarios[0].invariant_failures == ("SCENARIO_PROCESS_TIMEOUT",)
    assert len(context.processes) == 1
    assert context.processes[0].exitcode == -15
    assert context.processes[0].join_timeouts[0] <= scenario.timeout_seconds
    assert len(cleaned) == 1


def passing_scenario_receipt(scenario):  # type: ignore[no-untyped-def]
    from campaignos.performance.contracts import (
        LatencySummary,
        PoolEvidence,
        PoolSnapshot,
        RateLimitOutcomeCounts,
        ResponseClassCounts,
        ScenarioReceipt,
    )

    snapshot = PoolSnapshot()
    return ScenarioReceipt(
        scenario_id=scenario.scenario_id,
        policy_class=scenario.policy_class,
        configured_requests=scenario.request_count,
        configured_concurrency=scenario.concurrency,
        configured_timeout_seconds=scenario.timeout_seconds,
        completed=scenario.request_count,
        expected_errors=0,
        unexpected_errors=0,
        timed_out=0,
        response_classes=ResponseClassCounts(
            success_2xx=scenario.request_count,
            redirect_3xx=0,
            client_error_4xx=0,
            server_error_5xx=0,
            transport_error=0,
        ),
        rate_limit_outcomes=RateLimitOutcomeCounts(
            allowed=scenario.request_count,
            denied=0,
            unavailable=0,
            not_applicable=0,
        ),
        latency=LatencySummary(
            minimum_ms=1,
            median_ms=1,
            p95_ms=1,
            p99_ms=1,
            maximum_ms=1,
        ),
        pool=PoolEvidence(before=snapshot, peak=snapshot, after=snapshot),
        invariant_failures=(),
        invariant_decision="PASS",
        threshold_decision="PASS",
        cleanup_decision="PASS",
        cleanup_duration_ms=0,
        overall_decision="PASS",
    )


@dataclass
class ImmediateProcess:
    target: object
    args: tuple[object, ...]
    name: str
    mode: str = "success"
    alive: bool = False
    exitcode: int | None = None

    def start(self) -> None:
        from pathlib import Path

        from campaignos.performance import WorkloadScenario

        self.alive = False
        output = Path(str(self.args[-1]))
        scenario = WorkloadScenario.model_validate(self.args[-2])
        if self.mode == "success":
            output.write_text(
                passing_scenario_receipt(scenario).model_dump_json(),
                encoding="utf-8",
            )
            self.exitcode = 0
        elif self.mode == "invalid":
            output.write_text("not-json", encoding="utf-8")
            self.exitcode = 0
        elif self.mode == "drift":
            other = default_workload_catalog().scenarios[1]
            output.write_text(
                passing_scenario_receipt(other).model_dump_json(),
                encoding="utf-8",
            )
            self.exitcode = 0
        else:
            self.exitcode = 1

    def join(self, timeout: float | None = None) -> None:
        del timeout

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.alive = False

    def kill(self) -> None:
        self.alive = False


class ImmediateContext:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode

    def Process(self, *, target, args, name):  # type: ignore[no-untyped-def,override]
        return ImmediateProcess(target=target, args=args, name=name, mode=self.mode)


def one_scenario_catalog() -> WorkloadCatalog:
    return WorkloadCatalog(
        catalog_version="1.0",
        scenarios=(default_workload_catalog().scenarios[0],),
    )


def test_supervisor_builds_complete_pass_receipt_from_child(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(supervisor_module, "_postgresql_version", lambda url: "18.3")
    monkeypatch.setattr(
        supervisor_module.multiprocessing,
        "get_context",
        lambda mode: ImmediateContext(),
    )
    monkeypatch.setattr(supervisor_module, "cleanup_verification_role", lambda url, role: None)

    receipt = ProcessIsolatedLoadSupervisor(
        database_url="postgresql+psycopg://local/performance_test",
        source_revision="1" * 40,
        catalog=one_scenario_catalog(),
    ).run()

    assert receipt.overall_decision == "PASS"
    assert receipt.postgresql_version == "18.3"
    assert len(receipt.scenarios) == 1


def test_supervisor_records_process_cleanup_and_receipt_failures(
    monkeypatch,
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    scenario = one_scenario_catalog().scenarios[0]
    supervisor = ProcessIsolatedLoadSupervisor(
        database_url="postgresql+psycopg://local/performance_test",
        source_revision="2" * 40,
        catalog=one_scenario_catalog(),
    )

    monkeypatch.setattr(supervisor_module, "cleanup_verification_role", lambda url, role: None)
    for mode, expected in (
        ("failure", "SCENARIO_PROCESS_FAILURE"),
        ("invalid", "SCENARIO_RECEIPT_INVALID"),
        ("drift", "SCENARIO_RECEIPT_ID_DRIFT"),
    ):
        result = supervisor._run_process_scenario(  # type: ignore[attr-defined]
            context=ImmediateContext(mode),
            scenario=scenario,
            directory=tmp_path,
            timeout_seconds=1,
        )
        assert result.invariant_failures == (expected,)
        for child in tmp_path.iterdir():
            child.unlink()

    def fail_cleanup(url, role):  # type: ignore[no-untyped-def]
        del url, role
        raise RuntimeError("cleanup unavailable")

    monkeypatch.setattr(supervisor_module, "cleanup_verification_role", fail_cleanup)
    result = supervisor._run_process_scenario(  # type: ignore[attr-defined]
        context=ImmediateContext("success"),
        scenario=scenario,
        directory=tmp_path,
        timeout_seconds=1,
    )
    assert result.invariant_failures == ("SUPERVISOR_ROLE_CLEANUP_FAILURE",)


def test_supervisor_validates_database_revision_and_limits() -> None:
    import pytest

    from campaignos.performance import RunnerLimits

    with pytest.raises(ValueError, match="PostgreSQL"):
        ProcessIsolatedLoadSupervisor(
            database_url="sqlite:///local.db",
            source_revision="3" * 40,
        )
    with pytest.raises(ValueError, match="Git SHA"):
        ProcessIsolatedLoadSupervisor(
            database_url="postgresql+psycopg://local/performance_test",
            source_revision="short",
        )

    scenario = default_workload_catalog().scenarios[0]
    catalog = WorkloadCatalog(catalog_version="1.0", scenarios=(scenario,))
    with pytest.raises(ValueError, match="concurrency"):
        ProcessIsolatedLoadSupervisor(
            database_url="postgresql+psycopg://local/performance_test",
            source_revision="4" * 40,
            catalog=catalog,
            limits=RunnerLimits(max_concurrency=1),
        )
    with pytest.raises(ValueError, match="requests"):
        ProcessIsolatedLoadSupervisor(
            database_url="postgresql+psycopg://local/performance_test",
            source_revision="4" * 40,
            catalog=catalog,
            limits=RunnerLimits(max_requests_per_scenario=1),
        )
    with pytest.raises(ValueError, match="scenario timeout"):
        ProcessIsolatedLoadSupervisor(
            database_url="postgresql+psycopg://local/performance_test",
            source_revision="4" * 40,
            catalog=catalog,
            limits=RunnerLimits(max_scenario_seconds=1),
        )
    with pytest.raises(ValueError, match="catalog timeout"):
        ProcessIsolatedLoadSupervisor(
            database_url="postgresql+psycopg://local/performance_test",
            source_revision="4" * 40,
            catalog=catalog,
            limits=RunnerLimits(max_harness_seconds=1),
        )


def test_postgresql_version_is_normalized_and_engine_disposed(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    class Connection:
        def scalar(self, statement):  # type: ignore[no-untyped-def]
            del statement
            return "18.3 (test build)"

    class Engine:
        disposed = False

        def connect(self):  # type: ignore[no-untyped-def]
            class Context:
                def __enter__(self):  # type: ignore[no-untyped-def]
                    return Connection()

                def __exit__(self, exc_type, exc, traceback):  # type: ignore[no-untyped-def]
                    del exc_type, exc, traceback
                    return False

            return Context()

        def dispose(self) -> None:
            self.disposed = True

    engine = Engine()
    monkeypatch.setattr(supervisor_module, "create_engine", lambda *args, **kwargs: engine)
    assert (
        supervisor_module._postgresql_version(  # type: ignore[attr-defined]
            "postgresql+psycopg://local/performance_test"
        )
        == "18.3"
    )
    assert engine.disposed is True
