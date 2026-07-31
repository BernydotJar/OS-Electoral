"""Bounded authenticated load-verification contracts."""

from campaignos.performance.catalog import (
    CATALOG_VERSION,
    assert_complete_catalog,
    default_workload_catalog,
)
from campaignos.performance.contracts import (
    AuthorizationScope,
    CleanupResult,
    LoadVerificationReceipt,
    OperationResult,
    PoolSnapshot,
    RouteClass,
    RunnerLimits,
    ScenarioId,
    WorkloadCatalog,
    WorkloadScenario,
    assert_receipt_sanitized,
)
from campaignos.performance.executor import CampaignOSLoadExecutor
from campaignos.performance.receipt import load_and_verify_receipt, write_receipt
from campaignos.performance.runner import BoundedLoadRunner, ScenarioExecutor, nearest_rank

__all__ = [
    "CATALOG_VERSION",
    "AuthorizationScope",
    "BoundedLoadRunner",
    "CleanupResult",
    "CampaignOSLoadExecutor",
    "LoadVerificationReceipt",
    "OperationResult",
    "PoolSnapshot",
    "RouteClass",
    "RunnerLimits",
    "ScenarioExecutor",
    "ScenarioId",
    "WorkloadCatalog",
    "WorkloadScenario",
    "assert_complete_catalog",
    "assert_receipt_sanitized",
    "default_workload_catalog",
    "load_and_verify_receipt",
    "nearest_rank",
    "write_receipt",
]
