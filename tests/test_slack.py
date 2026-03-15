# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for Slack integration."""

from changetrail.integrations.slack import (
    format_help_message,
    format_timeline_slack,
    parse_slash_command,
    verify_slack_signature,
)
from changetrail.core.models import (
    ChangeEvent,
    ChangeEventQuery,
    EventAction,
    EventSeverity,
    EventSource,
)
from datetime import datetime, timezone


def test_parse_slash_command_last():
    q = parse_slash_command("last 30m")
    assert q.last == "30m"


def test_parse_slash_command_service():
    q = parse_slash_command("service checkout-service")
    assert q.service == "checkout-service"


def test_parse_slash_command_combined():
    q = parse_slash_command("last 1h source kubernetes")
    assert q.last == "1h"
    assert q.source == EventSource.KUBERNETES


def test_parse_slash_command_empty_defaults_to_30m():
    q = parse_slash_command("")
    assert q.last == "30m"


def test_format_timeline_empty():
    result = format_timeline_slack([], 0)
    assert result["response_type"] == "ephemeral"
    assert "No changes" in result["text"]


def test_format_timeline_with_events():
    events = [
        ChangeEvent(
            timestamp=datetime(2026, 3, 14, 12, 41, 0, tzinfo=timezone.utc),
            source=EventSource.KUBERNETES,
            resource_type="deployment",
            resource_name="checkout-service",
            action=EventAction.DEPLOYED,
            severity=EventSeverity.INFO,
            summary="deployed checkout-service → v1.23",
        ),
        ChangeEvent(
            timestamp=datetime(2026, 3, 14, 12, 45, 0, tzinfo=timezone.utc),
            source=EventSource.KUBERNETES,
            resource_type="pod",
            resource_name="checkout-pod-abc",
            action=EventAction.RESTARTED,
            severity=EventSeverity.WARNING,
            summary="restarted pod checkout-pod-abc (×3)",
        ),
    ]
    result = format_timeline_slack(events, 2)
    assert result["response_type"] == "in_channel"
    assert "blocks" in result
    text = result["blocks"][0]["text"]["text"]
    assert "deployed" in text
    assert "restarted" in text


def test_format_help():
    result = format_help_message()
    assert "response_type" in result
    assert "/changetrail last 30m" in result["text"]


def test_verify_signature_valid():
    import hmac, hashlib, time

    secret = "test-secret"
    ts = str(int(time.time()))
    body = "token=abc&text=last+30m"
    sig_base = f"v0:{ts}:{body}"
    sig = "v0=" + hmac.new(secret.encode(), sig_base.encode(), hashlib.sha256).hexdigest()

    assert verify_slack_signature(secret, ts, body, sig) is True


def test_verify_signature_invalid():
    assert verify_slack_signature("secret", "123", "body", "v0=bad") is False
