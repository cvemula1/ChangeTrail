# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for store duration parser and EventRecord."""

import pytest
from datetime import timedelta

from changetrail.core.store import parse_duration, EventRecord
from changetrail.core.models import (
    ChangeEvent,
    EventAction,
    EventSeverity,
    EventSource,
)


def test_parse_duration_minutes():
    assert parse_duration("30m") == timedelta(minutes=30)
    assert parse_duration("5m") == timedelta(minutes=5)


def test_parse_duration_hours():
    assert parse_duration("1h") == timedelta(hours=1)
    assert parse_duration("24h") == timedelta(hours=24)


def test_parse_duration_days():
    assert parse_duration("7d") == timedelta(days=7)


def test_parse_duration_seconds():
    assert parse_duration("60s") == timedelta(seconds=60)


def test_parse_duration_invalid():
    with pytest.raises(ValueError):
        parse_duration("abc")


def test_event_record_roundtrip():
    event = ChangeEvent(
        source=EventSource.KUBERNETES,
        resource_type="deployment",
        resource_name="api-server",
        namespace="production",
        action=EventAction.DEPLOYED,
        severity=EventSeverity.INFO,
        summary="deployed api-server v2.0",
        metadata={"new_version": "v2.0"},
        labels={"team": "backend"},
    )

    record = EventRecord.from_change_event(event)
    assert record.id == event.id
    assert record.source == "kubernetes"
    assert record.action == "deployed"
    assert record.metadata_json == {"new_version": "v2.0"}

    restored = record.to_change_event()
    assert restored.id == event.id
    assert restored.source == EventSource.KUBERNETES
    assert restored.action == EventAction.DEPLOYED
    assert restored.metadata == {"new_version": "v2.0"}
    assert restored.labels == {"team": "backend"}
