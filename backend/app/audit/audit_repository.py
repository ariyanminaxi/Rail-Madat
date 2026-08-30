"""
RailMaintain - Audit Repository

Handles audit-event persistence. Uses an in-memory store for the MVP
and tests. Replace with Supabase or another database for production.

Invariants:
  - Audit events are append-only (no update, no delete).
  - Each event has a unique log_id.
  - Idempotency keys prevent duplicate recording of the same logical event.
"""

import threading
from datetime import datetime, timezone
from typing import Optional


class AuditRepository:
    """Append-only, in-memory audit event store."""

    def __init__(self):
        self._events: list[dict] = []
        self._lock = threading.Lock()
        self._idempotency_keys: set[str] = set()

    def save(self, event: dict) -> dict:
        """Persist an audit event. Returns the saved event.

        Raises ValueError if the event is missing required fields or
        if an event with the same idempotency_key has already been saved.
        """
        required = {"log_id", "user_id", "role", "action",
                     "resource_type", "resource_id", "timestamp", "status"}
        missing = required - event.keys()
        if missing:
            raise ValueError(f"Audit event missing required fields: {missing}")

        idempotency_key = event.get("idempotency_key")
        if idempotency_key:
            with self._lock:
                if idempotency_key in self._idempotency_keys:
                    raise ValueError(
                        f"Duplicate event with idempotency_key={idempotency_key!r}"
                    )
                self._idempotency_keys.add(idempotency_key)

        with self._lock:
            self._events.append(dict(event))

        return event

    def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[dict]:
        """Return all audit events for a given resource, newest first."""
        with self._lock:
            return [
                e for e in self._events
                if e["resource_type"] == resource_type
                and e["resource_id"] == resource_id
            ][::-1]

    def exists_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> bool:
        """Check whether an event with this idempotency key was already saved."""
        with self._lock:
            return idempotency_key in self._idempotency_keys

    def get_all(self) -> list[dict]:
        """Return all stored events (for testing / admin review)."""
        with self._lock:
            return list(self._events)

    def reset(self) -> None:
        """Clear all events. FOR TEST USE ONLY."""
        with self._lock:
            self._events.clear()
            self._idempotency_keys.clear()


# Module-level singleton for convenience
_default_repo = AuditRepository()


def get_audit_repository() -> AuditRepository:
    """Return the module-level audit repository singleton."""
    return _default_repo
