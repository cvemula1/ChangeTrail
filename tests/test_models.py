# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for the event data model."""

from datetime import datetime, timezone

from changetrail.core.models import (
    ChangeEvent,
    ChangeEventQuery,
    EventAction,
    EventSeverity,
    EventSource,
)


def test_change_event_defaults():
    event = ChangeEvent(
        source=EventSource.KUBERNETES,
        resource_type="deployment",
        resource_name="checkout-service",
        action=EventAction.DEPLOYED,
    )
    assert event.id  # auto-generated UUID
    assert event.timestamp  # auto-generated
    assert event.severity == EventSeverity.INFO
    assert event.metadata == {}
    assert event.labels == {}


def test_change_event_full():
    event = ChangeEvent(
        source=EventSource.GITHUB,
        resource_type="repository",
        resource_name="my-app",
        namespace="cvemula1",
        action=EventAction.UPDATED,
        severity=EventSeverity.WARNING,
        summary="push to main: 3 commits",
        metadata={"branch": "main", "commit_count": 3},
        labels={"team": "platform"},
    )
    assert event.source == EventSource.GITHUB
    assert event.metadata["commit_count"] == 3
    assert event.labels["team"] == "platform"


def test_change_event_short_summary():
    event = ChangeEvent(
        timestamp=datetime(2026, 3, 14, 12, 41, 0, tzinfo=timezone.utc),
        source=EventSource.KUBERNETES,
        resource_type="deployment",
        resource_name="checkout-service",
        action=EventAction.DEPLOYED,
    )
    summary = event.short_summary()
    assert "12:41" in summary
    assert "deployed" in summary
    assert "checkout-service" in summary


def test_change_event_query_defaults():
    q = ChangeEventQuery()
    assert q.limit == 100
    assert q.offset == 0
    assert q.last is None
    assert q.source is None


def test_change_event_query_with_filters():
    q = ChangeEventQuery(
        last="30m",
        source=EventSource.KUBERNETES,
        action=EventAction.DEPLOYED,
        limit=50,
    )
    assert q.last == "30m"
    assert q.source == EventSource.KUBERNETES
    assert q.limit == 50


def test_event_serialization_roundtrip():
    event = ChangeEvent(
        source=EventSource.KUBERNETES,
        resource_type="pod",
        resource_name="app-abc123",
        namespace="default",
        action=EventAction.RESTARTED,
        severity=EventSeverity.WARNING,
        summary="restarted pod app-abc123 (×3)",
        metadata={"restart_count": 3, "reason": "OOMKilled"},
    )
    data = event.model_dump()
    restored = ChangeEvent(**data)
    assert restored.id == event.id
    assert restored.source == event.source
    assert restored.metadata == event.metadata
