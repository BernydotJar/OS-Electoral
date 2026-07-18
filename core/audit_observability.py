#!/usr/bin/env python3
"""Bounded context: Audit Observability and Cryptographic Integrity Read Model."""
from __future__ import annotations

import copy
from typing import Any

from core.persistence_audit import validate_store, event_hash


class AuditIntegrityReadModel:
    def __init__(self, store: dict[str, Any]) -> None:
        """Initialize the read model with a persistence store.
        
        Raises ValueError if the store structure is malformed.
        """
        if not isinstance(store, dict):
            raise ValueError("store must be an object")
        # Create a deep copy to ensure immutability of the read model's source
        self._store = copy.deepcopy(store)
        self._events = self._store.get("events", [])

    def verify_integrity(self) -> dict[str, Any]:
        """Perform a cryptographic audit of the event chain to check for tampering, reordering, gaps, or corruption.
        
        Returns a report dictionary:
          - {"status": "VALID", "events_processed": int}
          - {"status": "CORRUPTED", "reason": str, "mismatched_version": int}
        """
        try:
            validate_store(self._store)
        except Exception as exc:
            return {
                "status": "CORRUPTED",
                "reason": str(exc),
                "mismatched_version": self._store.get("aggregate_version", 0)
            }
        events = self._events
        if not events:
            if self._store["aggregate_version"] != 0:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Store version is {self._store['aggregate_version']} but events list is empty",
                    "mismatched_version": 0
                }
            if self._store["last_event_hash"] != "GENESIS":
                return {
                    "status": "CORRUPTED",
                    "reason": f"Store last_event_hash is '{self._store['last_event_hash']}' but events list is empty",
                    "mismatched_version": 0
                }
            return {
                "status": "VALID",
                "events_processed": 0
            }

        # Check total count matches version
        if self._store["aggregate_version"] != len(events):
            return {
                "status": "CORRUPTED",
                "reason": f"Store aggregate_version ({self._store['aggregate_version']}) does not match event count ({len(events)})",
                "mismatched_version": self._store["aggregate_version"]
            }

        # Track unique keys and IDs to detect duplicates
        seen_keys = set()
        seen_ids = set()
        previous = "GENESIS"

        for index, event in enumerate(events, start=1):
            version = event.get("aggregate_version")
            event_id = event.get("id")
            idem_key = event.get("idempotency_key")
            prev_hash = event.get("previous_hash")
            evt_hash = event.get("event_hash")

            # Check sequence version continuity
            if version != index:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Event at list index {index-1} has non-sequential aggregate_version: {version}",
                    "mismatched_version": version
                }

            # Check for duplicate event IDs
            if event_id in seen_ids:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Duplicate event ID detected: {event_id}",
                    "mismatched_version": version
                }
            seen_ids.add(event_id)

            # Check for duplicate idempotency keys
            if idem_key in seen_keys:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Duplicate idempotency key detected: {idem_key}",
                    "mismatched_version": version
                }
            seen_keys.add(idem_key)

            # Check hash chain continuity
            if prev_hash != previous:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Hash chain broken at event {event_id}. Expected previous_hash: {previous}, got: {prev_hash}",
                    "mismatched_version": version
                }

            # Recalculate event hash and compare
            try:
                computed = event_hash(event)
            except Exception as e:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Failed to compute hash for event {event_id}: {e}",
                    "mismatched_version": version
                }

            if evt_hash != computed:
                return {
                    "status": "CORRUPTED",
                    "reason": f"Event hash mismatch at event {event_id}. Expected: {computed}, got: {evt_hash}",
                    "mismatched_version": version
                }

            previous = evt_hash

        # Validate that the store's last_event_hash matches the final event hash
        if self._store["last_event_hash"] != previous:
            return {
                "status": "CORRUPTED",
                "reason": f"Store last_event_hash ({self._store['last_event_hash']}) does not match last event hash ({previous})",
                "mismatched_version": len(events)
            }

        return {
            "status": "VALID",
            "events_processed": len(events)
        }

    def query(
        self,
        principal_id: str | None = None,
        resource_id: str | None = None,
        resource_type: str | None = None,
        operation: str | None = None
    ) -> list[dict[str, Any]]:
        """Query and filter events by security principal, resource, or operation.
        
        Returns a list of copied event dictionaries matching the filters.
        """
        results = []
        for event in self._events:
            if principal_id and event.get("principal_id") != principal_id:
                continue
            if resource_id and event.get("resource_id") != resource_id:
                continue
            if resource_type and event.get("resource_type") != resource_type:
                continue
            if operation and event.get("operation") != operation:
                continue
            results.append(copy.deepcopy(event))
        return results
