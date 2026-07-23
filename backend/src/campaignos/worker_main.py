"""Executable, tenant-explicit outbox worker runtime."""

from __future__ import annotations

import argparse
import signal
import socket
import threading
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from campaignos.config import get_settings
from campaignos.data import Database
from campaignos.observability import configure_json_logger, write_worker_metrics
from campaignos.workers import InternalCampaignUpdatedHandler, OutboxWorker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process CampaignOS internal outbox events")
    parser.add_argument(
        "--tenant-id",
        action="append",
        required=True,
        type=UUID,
        dest="tenant_ids",
        help="Explicit tenant UUID to process; repeat for multiple tenants",
    )
    parser.add_argument("--once", action="store_true", help="Run one bounded pass and exit")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--worker-id", default=f"{socket.gethostname()}-outbox")
    parser.add_argument(
        "--metrics-file",
        type=Path,
        help="Optional Prometheus textfile path updated atomically after each pass",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.batch_size <= 100:
        raise SystemExit("--batch-size must be between 1 and 100")
    if args.poll_seconds < 0.1:
        raise SystemExit("--poll-seconds must be at least 0.1")
    if not args.worker_id.strip() or len(args.worker_id) > 255:
        raise SystemExit("--worker-id must contain 1 to 255 characters")

    settings = get_settings()
    if not settings.database_url:
        raise SystemExit("CAMPAIGNOS_DATABASE_URL is required for the outbox worker")
    logger = configure_json_logger(settings, "campaignos.worker")
    database = Database.from_url(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout_seconds=settings.database_pool_timeout_seconds,
    )
    worker_id = args.worker_id.strip()
    worker = OutboxWorker(
        database=database,
        worker_id=worker_id,
        handler=InternalCampaignUpdatedHandler(),
    )
    stop = threading.Event()

    def request_stop(signum: int, frame: object) -> None:
        del frame
        logger.info("worker_stop_requested", extra={"signal": signum, "worker_id": worker_id})
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    logger.info("outbox_worker_started", extra={"worker_id": worker_id})
    cumulative_totals = {"claimed": 0, "delivered": 0, "retried": 0, "dead_lettered": 0}
    try:
        while not stop.is_set():
            totals = {"claimed": 0, "delivered": 0, "retried": 0, "dead_lettered": 0}
            for tenant_id in args.tenant_ids:
                result = worker.run_once(tenant_id, batch_size=args.batch_size)
                totals["claimed"] += result.claimed
                totals["delivered"] += result.delivered
                totals["retried"] += result.retried
                totals["dead_lettered"] += result.dead_lettered
            logger.info("outbox_pass_complete", extra={**totals, "worker_id": worker_id})
            for outcome, value in totals.items():
                cumulative_totals[outcome] += value
            if args.metrics_file is not None:
                write_worker_metrics(args.metrics_file, totals=cumulative_totals)
            if args.once:
                return 0
            stop.wait(args.poll_seconds)
        return 0
    finally:
        database.dispose()
        logger.info("outbox_worker_stopped", extra={"worker_id": worker_id})


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
