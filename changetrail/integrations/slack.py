# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Slack integration.

Adds /changetrail slash-command support and outgoing webhook alerts.
See the README for setup instructions.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Optional
from urllib.parse import parse_qs

import httpx

from changetrail.core.models import ChangeEvent, ChangeEventQuery, EventSource
from changetrail.core.store import event_store

log = logging.getLogger(__name__)


# -- slash command parsing -------------------------------------------------

def parse_slash_command(text: str) -> ChangeEventQuery:
    """Turn `/changetrail last 30m service foo` into a query object."""
    tokens = text.strip().split()
    query = ChangeEventQuery(limit=10)  # Slack messages shouldn't be huge

    i = 0
    while i < len(tokens):
        tok = tokens[i].lower()
        if tok == "last" and i + 1 < len(tokens):
            query.last = tokens[i + 1]
            i += 2
        elif tok == "service" and i + 1 < len(tokens):
            query.service = tokens[i + 1]
            i += 2
        elif tok == "source" and i + 1 < len(tokens):
            try:
                query.source = EventSource(tokens[i + 1].lower())
            except ValueError:
                pass
            i += 2
        elif tok == "namespace" and i + 1 < len(tokens):
            query.namespace = tokens[i + 1]
            i += 2
        else:
            i += 1

    if not query.last and not query.service:
        query.last = "30m"

    return query


# -- message formatting ----------------------------------------------------

def format_timeline_slack(events: list[ChangeEvent], total: int) -> dict[str, Any]:
    """Build a Block Kit response with emoji severity markers."""
    if not events:
        return {
            "response_type": "ephemeral",
            "text": "No changes found for this time range.",
        }

    severity_emoji = {"info": "🔵", "warning": "🟡", "critical": "🔴"}
    source_emoji = {
        "kubernetes": "☸️",
        "github": "🐙",
        "aws": "☁️",
        "azure": "☁️",
    }

    lines = []
    for event in events:
        ts = event.timestamp.strftime("%H:%M")
        sev = severity_emoji.get(event.severity.value, "⚪")
        src = source_emoji.get(event.source.value, "📦")
        lines.append(f"{sev} `{ts}` {src} {event.summary}")

    header = f"*Recent Changes* ({total} total)\n"
    body = "\n".join(lines)

    if total > len(events):
        body += f"\n\n_Showing {len(events)} of {total} events. Use the web UI for full timeline._"

    return {
        "response_type": "in_channel",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header + body},
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🔍 _Powered by ChangeTrail_"},
                ],
            },
        ],
    }


def format_help_message() -> dict[str, Any]:
    help_text = (
        "*ChangeTrail — Slash Commands*\n\n"
        "`/changetrail last 30m` — Changes in last 30 minutes\n"
        "`/changetrail last 1h` — Changes in last hour\n"
        "`/changetrail service checkout-service` — Changes for a service\n"
        "`/changetrail source kubernetes last 1h` — Filter by source\n"
        "`/changetrail help` — Show this message\n"
    )
    return {"response_type": "ephemeral", "text": help_text}


# -- signature verification ------------------------------------------------

def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    body: str,
    signature: str,
) -> bool:
    """Verify the v0 HMAC signature Slack sends on every request."""
    if abs(time.time() - int(timestamp)) > 300:
        return False  # stale → possible replay

    sig_basestring = f"v0:{timestamp}:{body}"
    expected = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# -- outgoing alerts -------------------------------------------------------

async def send_slack_alert(webhook_url: str, event: ChangeEvent) -> bool:
    """Push a high-severity event to a Slack channel via incoming webhook."""
    severity_emoji = {"info": "🔵", "warning": "🟡", "critical": "🔴"}
    emoji = severity_emoji.get(event.severity.value, "⚪")

    text = (
        f"{emoji} *{event.action.value.upper()}* — "
        f"`{event.resource_type}/{event.resource_name}`\n"
        f"_{event.summary}_\n"
        f"Source: {event.source.value} | Namespace: {event.namespace or 'n/a'}"
    )

    payload = {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    },
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload, timeout=10)
            return resp.status_code == 200
    except Exception as exc:
        log.error("slack alert failed: %s", exc)
        return False
