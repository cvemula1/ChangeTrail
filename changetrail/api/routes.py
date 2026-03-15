# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
API routes.

All endpoints live under /api/v1/.  The main one is GET /changes — that's what
the UI and Slack integration hit to build the timeline.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from changetrail.core.config import settings
from changetrail.core.models import (
    ChangeEvent,
    ChangeEventQuery,
    EventAction,
    EventSeverity,
    EventSource,
    TimelineResponse,
)
from changetrail.core.store import event_store

log = logging.getLogger(__name__)
router = APIRouter()


# -- timeline --------------------------------------------------------------
@router.get("/changes", response_model=TimelineResponse)
async def get_changes(
    last: Optional[str] = Query(None, description="Duration e.g. 30m, 1h, 24h"),
    since: Optional[datetime] = Query(None, description="Start timestamp (ISO 8601)"),
    until: Optional[datetime] = Query(None, description="End timestamp (ISO 8601)"),
    source: Optional[EventSource] = Query(None, description="Event source filter"),
    resource_type: Optional[str] = Query(None, description="Resource type filter"),
    resource_name: Optional[str] = Query(None, description="Resource name filter"),
    service: Optional[str] = Query(None, description="Service name (alias for resource_name)"),
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    action: Optional[EventAction] = Query(None, description="Action filter"),
    severity: Optional[EventSeverity] = Query(None, description="Severity filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """The main endpoint — returns filtered, paginated change events."""
    query = ChangeEventQuery(
        last=last,
        since=since,
        until=until,
        source=source,
        resource_type=resource_type,
        resource_name=resource_name,
        service=service,
        namespace=namespace,
        action=action,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return await event_store.query(query)


@router.get("/changes/{event_id}", response_model=ChangeEvent)
async def get_change_by_id(event_id: str):
    """Get a single change event by ID."""
    event = await event_store.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# -- manual ingestion ------------------------------------------------------
@router.post("/events", response_model=ChangeEvent, status_code=201)
async def create_event(event: ChangeEvent):
    """POST a change event from a CI pipeline or script."""
    await event_store.save(event)
    return event


@router.post("/events/batch", status_code=201)
async def create_events_batch(events: list[ChangeEvent]):
    """Batch version of the above."""
    count = await event_store.save_batch(events)
    return {"saved": count}


# -- github webhook --------------------------------------------------------
@router.post("/webhooks/github")
async def github_webhook(request: Request):
    """Point your GitHub repo webhook here."""
    body = await request.body()
    headers = dict(request.headers)

    # Verify signature if secret is configured
    signature = headers.get("x-hub-signature-256", "")
    if settings.github_webhook_secret:
        expected = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    try:
        from changetrail.collectors.github.collector import GitHubCollector
        collector = GitHubCollector()
        events = await collector.handle_webhook(headers, payload)
        saved = await event_store.save_batch(events)
        return {"received": len(events), "saved": saved}
    except Exception as exc:
        log.error("github webhook failed: %s", exc)
        raise HTTPException(status_code=500, detail="webhook processing failed")


# -- slack -----------------------------------------------------------------

@router.post("/integrations/slack/command")
async def slack_slash_command(request: Request):
    """Handle /changetrail slash commands from Slack."""
    from changetrail.integrations.slack import (
        format_help_message,
        format_timeline_slack,
        parse_slash_command,
        verify_slack_signature,
    )

    body = (await request.body()).decode()
    headers = dict(request.headers)

    signing_secret = getattr(settings, "slack_signing_secret", "")
    if signing_secret:
        ts = headers.get("x-slack-request-timestamp", "")
        sig = headers.get("x-slack-signature", "")
        if not verify_slack_signature(signing_secret, ts, body, sig):
            raise HTTPException(status_code=401, detail="Invalid Slack signature")

    from urllib.parse import parse_qs
    form = parse_qs(body)
    text = form.get("text", [""])[0].strip()

    if text == "help" or not text:
        return format_help_message()

    query = parse_slash_command(text)
    result = await event_store.query(query)
    return format_timeline_slack(result.events, result.total)


# -- meta ------------------------------------------------------------------

@router.get("/sources")
async def list_sources():
    from changetrail.collectors.registry import collector_registry
    return {
        "sources": [
            {"name": name, "status": "active"}
            for name in collector_registry.names
        ]
    }


@router.get("/stats")
async def get_stats():
    last_hour = await event_store.query(ChangeEventQuery(last="1h", limit=1))
    last_day = await event_store.query(ChangeEventQuery(last="24h", limit=1))

    return {
        "events_last_hour": last_hour.total,
        "events_last_24h": last_day.total,
    }
