# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Demo / seed data.

Run `python -m changetrail demo` to print a realistic incident timeline to
stdout (no database needed).  Run `python -m changetrail seed` to push the
same events into Postgres so the UI has something to show.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from changetrail.core.models import (
    ChangeEvent,
    EventAction,
    EventSeverity,
    EventSource,
)

log = logging.getLogger(__name__)

# Scenario: "checkout-service deployment causes latency spike"
# This is the kind of timeline an engineer would see during an incident.
INCIDENT_SCENARIO = [
    {
        "offset_min": -28,
        "source": EventSource.GITHUB,
        "resource_type": "pull_request",
        "resource_name": "checkout-service",
        "namespace": "cvemula1",
        "action": EventAction.UPDATED,
        "severity": EventSeverity.INFO,
        "summary": "PR #142 merged: Add Redis caching layer",
        "metadata": {"pr_number": 142, "title": "Add Redis caching layer", "author": "alice", "changed_files": 12},
    },
    {
        "offset_min": -22,
        "source": EventSource.GITHUB,
        "resource_type": "repository",
        "resource_name": "checkout-service",
        "namespace": "cvemula1",
        "action": EventAction.UPDATED,
        "severity": EventSeverity.INFO,
        "summary": "push to main: 3 commit(s) by alice",
        "metadata": {"branch": "main", "commit_count": 3, "pusher": "alice", "head_sha": "a1b2c3d4"},
    },
    {
        "offset_min": -18,
        "source": EventSource.KUBERNETES,
        "resource_type": "deployment",
        "resource_name": "checkout-service",
        "namespace": "production",
        "action": EventAction.DEPLOYED,
        "severity": EventSeverity.INFO,
        "summary": "deployed checkout-service → v1.23",
        "metadata": {"old_version": "v1.22", "new_version": "v1.23", "replicas": 3, "images": {"checkout": "checkout:v1.23"}},
    },
    {
        "offset_min": -16,
        "source": EventSource.KUBERNETES,
        "resource_type": "configmap",
        "resource_name": "checkout-config",
        "namespace": "production",
        "action": EventAction.UPDATED,
        "severity": EventSeverity.INFO,
        "summary": "updated configmap checkout-config",
        "metadata": {"keys": ["REDIS_HOST", "REDIS_PORT", "CACHE_TTL"], "key_count": 3},
    },
    {
        "offset_min": -12,
        "source": EventSource.KUBERNETES,
        "resource_type": "pod",
        "resource_name": "checkout-service-7f8b9c6d4-x2k9p",
        "namespace": "production",
        "action": EventAction.RESTARTED,
        "severity": EventSeverity.WARNING,
        "summary": "restarted pod checkout-service-7f8b9c6d4-x2k9p (×2)",
        "metadata": {"restart_count": 2, "container": "checkout", "reason": "Error", "exit_code": 1},
    },
    {
        "offset_min": -10,
        "source": EventSource.KUBERNETES,
        "resource_type": "pod",
        "resource_name": "checkout-service-7f8b9c6d4-m4n5o",
        "namespace": "production",
        "action": EventAction.RESTARTED,
        "severity": EventSeverity.WARNING,
        "summary": "restarted pod checkout-service-7f8b9c6d4-m4n5o (×3)",
        "metadata": {"restart_count": 3, "container": "checkout", "reason": "OOMKilled", "exit_code": 137},
    },
    {
        "offset_min": -8,
        "source": EventSource.AWS,
        "resource_type": "iam-role",
        "resource_name": "checkout-svc-role",
        "namespace": "aws-123456789",
        "action": EventAction.MODIFIED,
        "severity": EventSeverity.WARNING,
        "summary": "modified iam-role checkout-svc-role — policy attached",
        "metadata": {"change": "policy attachment added", "policy": "AmazonElastiCacheFullAccess", "actor": "deploy-bot"},
    },
    {
        "offset_min": -5,
        "source": EventSource.KUBERNETES,
        "resource_type": "deployment",
        "resource_name": "checkout-service",
        "namespace": "production",
        "action": EventAction.SCALED,
        "severity": EventSeverity.INFO,
        "summary": "scaled checkout-service (3 → 5 replicas)",
        "metadata": {"old_replicas": 3, "replicas": 5, "trigger": "HPA"},
    },
]

# Background noise — unrelated changes that happened around the same time.
BACKGROUND_EVENTS = [
    {
        "offset_min": -45,
        "source": EventSource.KUBERNETES,
        "resource_type": "deployment",
        "resource_name": "payment-service",
        "namespace": "production",
        "action": EventAction.DEPLOYED,
        "severity": EventSeverity.INFO,
        "summary": "deployed payment-service → v3.8",
        "metadata": {"new_version": "v3.8"},
    },
    {
        "offset_min": -35,
        "source": EventSource.GITHUB,
        "resource_type": "release",
        "resource_name": "shared-lib",
        "namespace": "cvemula1",
        "action": EventAction.CREATED,
        "severity": EventSeverity.INFO,
        "summary": "release v2.1.0 published for shared-lib",
        "metadata": {"tag": "v2.1.0", "author": "bob"},
    },
    {
        "offset_min": -30,
        "source": EventSource.KUBERNETES,
        "resource_type": "configmap",
        "resource_name": "feature-flags",
        "namespace": "production",
        "action": EventAction.UPDATED,
        "severity": EventSeverity.INFO,
        "summary": "updated configmap feature-flags",
        "metadata": {"keys": ["ENABLE_NEW_CART", "AB_TEST_RATIO"]},
    },
    {
        "offset_min": -3,
        "source": EventSource.KUBERNETES,
        "resource_type": "pod",
        "resource_name": "logging-agent-9d8e7",
        "namespace": "monitoring",
        "action": EventAction.RESTARTED,
        "severity": EventSeverity.INFO,
        "summary": "restarted pod logging-agent-9d8e7 (×1)",
        "metadata": {"restart_count": 1, "reason": "Liveness probe failed"},
    },
]


def generate_demo_events(now: Optional[datetime] = None) -> list[ChangeEvent]:
    """Build a sorted list of ChangeEvents for the demo scenario."""
    now = now or datetime.now(timezone.utc)
    events: list[ChangeEvent] = []

    all_event_defs = INCIDENT_SCENARIO + BACKGROUND_EVENTS
    for defn in all_event_defs:
        ts = now + timedelta(minutes=defn["offset_min"])
        event = ChangeEvent(
            timestamp=ts,
            source=defn["source"],
            resource_type=defn["resource_type"],
            resource_name=defn["resource_name"],
            namespace=defn.get("namespace"),
            action=defn["action"],
            severity=defn.get("severity", EventSeverity.INFO),
            summary=defn["summary"],
            metadata=defn.get("metadata", {}),
            labels=defn.get("labels", {}),
        )
        events.append(event)

    events.sort(key=lambda e: e.timestamp)
    return events


async def seed_demo_events() -> int:
    """Push demo events into the database so the UI has data."""
    from changetrail.core.store import event_store, init_db

    await init_db()
    events = generate_demo_events()
    n = await event_store.save_batch(events)
    log.info("seeded %d demo events", n)
    return n


def print_demo_timeline():
    """Pretty-print the demo timeline to stdout.  No database needed."""
    events = generate_demo_events()
    print()
    print("  ChangeTrail — Demo Timeline")
    print("  ═══════════════════════════════════════════════════════")
    print("  Scenario: API latency spike on checkout-service")
    print("  ───────────────────────────────────────────────────────")
    print()
    for event in events:
        ts = event.timestamp.strftime("%H:%M")
        severity_marker = {"info": "·", "warning": "▲", "critical": "✖"}
        marker = severity_marker.get(event.severity.value, "·")
        source_tag = f"({event.source.value})"
        print(f"  {ts}  {marker} {event.summary:<55} {source_tag}")
    print()
    print("  ───────────────────────────────────────────────────────")
    print("  This is what engineers see during an incident.")
    print("  The deployment at 12:41 likely caused the pod restarts.")
    print()


if __name__ == "__main__":
    import sys

    if "--seed" in sys.argv:
        asyncio.run(seed_demo_events())
    else:
        print_demo_timeline()
