# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Normalizer helpers.

Collectors deal with messy real-world data.  These functions smooth out the
rough edges: fuzzy action matching, flexible timestamps, severity heuristics,
and summary generation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from changetrail.core.models import (
    ChangeEvent,
    EventAction,
    EventSeverity,
    EventSource,
)

log = logging.getLogger(__name__)

# Fuzzy lookup: raw strings from various APIs → our canonical actions.
ACTION_MAP: dict[str, EventAction] = {
    "create": EventAction.CREATED,
    "created": EventAction.CREATED,
    "add": EventAction.CREATED,
    "added": EventAction.CREATED,
    "update": EventAction.UPDATED,
    "updated": EventAction.UPDATED,
    "modify": EventAction.MODIFIED,
    "modified": EventAction.MODIFIED,
    "patch": EventAction.UPDATED,
    "delete": EventAction.DELETED,
    "deleted": EventAction.DELETED,
    "remove": EventAction.DELETED,
    "removed": EventAction.DELETED,
    "restart": EventAction.RESTARTED,
    "restarted": EventAction.RESTARTED,
    "scale": EventAction.SCALED,
    "scaled": EventAction.SCALED,
    "deploy": EventAction.DEPLOYED,
    "deployed": EventAction.DEPLOYED,
    "rollback": EventAction.ROLLED_BACK,
    "rolled_back": EventAction.ROLLED_BACK,
    "fail": EventAction.FAILED,
    "failed": EventAction.FAILED,
    "error": EventAction.FAILED,
}


def normalize_action(raw_action: str) -> EventAction:
    """Best-effort mapping from whatever string the source gives us."""
    return ACTION_MAP.get(raw_action.lower().strip(), EventAction.UPDATED)


def normalize_timestamp(ts: Any) -> datetime:
    """Accept a datetime, ISO string, or epoch — always return tz-aware UTC."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    if isinstance(ts, str):
        from dateutil.parser import parse as parse_dt

        dt = parse_dt(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return datetime.now(timezone.utc)


def build_summary(
    action: EventAction,
    resource_type: str,
    resource_name: str,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """One-liner for the timeline, e.g. 'deployed checkout-service → v1.23'."""
    meta = metadata or {}
    base = f"{action.value} {resource_type} {resource_name}"

    if action == EventAction.DEPLOYED and "new_version" in meta:
        return f"{base} → {meta['new_version']}"
    if action == EventAction.SCALED and "replicas" in meta:
        old = meta.get("old_replicas", "?")
        new = meta.get("replicas", "?")
        return f"{base} ({old} → {new} replicas)"
    if action == EventAction.RESTARTED and "restart_count" in meta:
        return f"{base} (×{meta['restart_count']})"

    return base


def determine_severity(
    action: EventAction,
    resource_type: str,
    metadata: Optional[dict[str, Any]] = None,
) -> EventSeverity:
    """Simple heuristic — failures are critical, deletes are warnings, etc."""
    if action == EventAction.FAILED:
        return EventSeverity.CRITICAL
    if action in (EventAction.DELETED, EventAction.ROLLED_BACK):
        return EventSeverity.WARNING
    if action == EventAction.RESTARTED:
        meta = metadata or {}
        if meta.get("restart_count", 0) >= 3:
            return EventSeverity.WARNING
    return EventSeverity.INFO
