# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for demo event generator."""

from changetrail.demo import generate_demo_events
from changetrail.core.models import EventSource, EventAction


def test_generate_demo_events_count():
    events = generate_demo_events()
    assert len(events) > 0
    assert len(events) == 12  # 8 incident + 4 background


def test_generate_demo_events_sorted():
    events = generate_demo_events()
    timestamps = [e.timestamp for e in events]
    assert timestamps == sorted(timestamps)


def test_generate_demo_events_sources():
    events = generate_demo_events()
    sources = {e.source for e in events}
    assert EventSource.KUBERNETES in sources
    assert EventSource.GITHUB in sources
    assert EventSource.AWS in sources


def test_generate_demo_events_actions():
    events = generate_demo_events()
    actions = {e.action for e in events}
    assert EventAction.DEPLOYED in actions
    assert EventAction.RESTARTED in actions
    assert EventAction.UPDATED in actions


def test_generate_demo_events_have_summaries():
    events = generate_demo_events()
    for event in events:
        assert event.summary, f"Event {event.id} has no summary"


def test_generate_demo_events_have_metadata():
    events = generate_demo_events()
    events_with_meta = [e for e in events if e.metadata]
    assert len(events_with_meta) > 0
