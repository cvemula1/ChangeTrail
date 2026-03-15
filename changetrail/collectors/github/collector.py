# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
GitHub collector.

Receives webhook POSTs for deployment, push, release, and pull-request events.
Signature verification is optional but recommended for production.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from changetrail.core.collector import BaseCollector, WebhookCollector
from changetrail.core.config import settings
from changetrail.core.models import ChangeEvent, EventAction, EventSeverity, EventSource
from changetrail.core.normalizer import build_summary, determine_severity

log = logging.getLogger(__name__)


class GitHubCollector(WebhookCollector):
    """Webhook-based collector for GitHub events."""

    def __init__(self):
        self._http: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "github"

    async def setup(self) -> None:
        headers = {}
        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"
        headers["Accept"] = "application/vnd.github.v3+json"
        self._http = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers,
            timeout=30.0,
        )
        log.info("github collector ready (repos: %s)", settings.github_repos)

    async def teardown(self) -> None:
        if self._http:
            await self._http.aclose()

    def verify_webhook_signature(self, payload_body: bytes, signature: str) -> bool:
        if not settings.github_webhook_secret:
            log.warning("no webhook secret configured — skipping sig check")
            return True

        expected = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, headers: dict[str, str], payload: dict) -> list[ChangeEvent]:
        event_type = headers.get("x-github-event", "")
        delivery_id = headers.get("x-github-delivery", "")

        handlers = {
            "deployment": self._handle_deployment,
            "deployment_status": self._handle_deployment_status,
            "push": self._handle_push,
            "release": self._handle_release,
            "pull_request": self._handle_pull_request,
        }

        handler = handlers.get(event_type)
        if not handler:
            log.debug("ignoring github event: %s", event_type)
            return []

        try:
            events = handler(payload, delivery_id)
            log.info("github %s → %d events", event_type, len(events))
            return events
        except Exception as exc:
            log.error("github %s webhook failed: %s", event_type, exc)
            return []

    def _handle_deployment(self, payload: dict, delivery_id: str) -> list[ChangeEvent]:
        deployment = payload.get("deployment", {})
        repo = payload.get("repository", {})

        meta = {
            "environment": deployment.get("environment", "unknown"),
            "ref": deployment.get("ref", ""),
            "sha": deployment.get("sha", "")[:8],
            "creator": deployment.get("creator", {}).get("login", "unknown"),
            "description": deployment.get("description", ""),
            "repo": repo.get("full_name", ""),
        }

        return [ChangeEvent(
            timestamp=_parse_gh_ts(deployment.get("created_at")),
            source=EventSource.GITHUB,
            resource_type="deployment",
            resource_name=repo.get("name", "unknown"),
            namespace=repo.get("owner", {}).get("login", ""),
            action=EventAction.DEPLOYED,
            severity=EventSeverity.INFO,
            summary=f"deployed {repo.get('name')} to {meta['environment']} ({meta['sha']})",
            metadata=meta,
            raw_event=payload,
        )]

    def _handle_deployment_status(self, payload: dict, delivery_id: str) -> list[ChangeEvent]:
        status = payload.get("deployment_status", {})
        deployment = payload.get("deployment", {})
        repo = payload.get("repository", {})
        state = status.get("state", "")

        if state not in ("success", "failure", "error"):
            return []

        action = EventAction.DEPLOYED if state == "success" else EventAction.FAILED
        severity = EventSeverity.INFO if state == "success" else EventSeverity.CRITICAL

        meta = {
            "state": state,
            "environment": deployment.get("environment", ""),
            "description": status.get("description", ""),
            "target_url": status.get("target_url", ""),
        }

        return [ChangeEvent(
            timestamp=_parse_gh_ts(status.get("created_at")),
            source=EventSource.GITHUB,
            resource_type="deployment",
            resource_name=repo.get("name", "unknown"),
            namespace=repo.get("owner", {}).get("login", ""),
            action=action,
            severity=severity,
            summary=f"deployment {state}: {repo.get('name')} → {meta['environment']}",
            metadata=meta,
            raw_event=payload,
        )]

    def _handle_push(self, payload: dict, delivery_id: str) -> list[ChangeEvent]:
        repo = payload.get("repository", {})
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")

        # only care about main/production branches
        tracked_branches = {"main", "master", "production", "release"}
        if branch not in tracked_branches:
            return []

        commits = payload.get("commits", [])
        head_commit = payload.get("head_commit", {})
        pusher = payload.get("pusher", {})

        meta = {
            "branch": branch,
            "commit_count": len(commits),
            "head_sha": (head_commit.get("id", "") or "")[:8],
            "head_message": head_commit.get("message", ""),
            "pusher": pusher.get("name", "unknown"),
            "compare_url": payload.get("compare", ""),
        }

        return [ChangeEvent(
            timestamp=_parse_gh_ts(head_commit.get("timestamp")),
            source=EventSource.GITHUB,
            resource_type="repository",
            resource_name=repo.get("name", "unknown"),
            namespace=repo.get("owner", {}).get("login", ""),
            action=EventAction.UPDATED,
            severity=EventSeverity.INFO,
            summary=f"push to {branch}: {len(commits)} commit(s) by {meta['pusher']}",
            metadata=meta,
            raw_event=payload,
        )]

    def _handle_release(self, payload: dict, delivery_id: str) -> list[ChangeEvent]:
        action_str = payload.get("action", "")
        if action_str != "published":
            return []

        release = payload.get("release", {})
        repo = payload.get("repository", {})

        meta = {
            "tag": release.get("tag_name", ""),
            "name": release.get("name", ""),
            "prerelease": release.get("prerelease", False),
            "author": release.get("author", {}).get("login", "unknown"),
            "url": release.get("html_url", ""),
        }

        return [ChangeEvent(
            timestamp=_parse_gh_ts(release.get("published_at")),
            source=EventSource.GITHUB,
            resource_type="release",
            resource_name=repo.get("name", "unknown"),
            namespace=repo.get("owner", {}).get("login", ""),
            action=EventAction.CREATED,
            severity=EventSeverity.INFO,
            summary=f"release {meta['tag']} published for {repo.get('name')}",
            metadata=meta,
            raw_event=payload,
        )]

    def _handle_pull_request(self, payload: dict, delivery_id: str) -> list[ChangeEvent]:
        action_str = payload.get("action", "")
        if action_str != "closed":
            return []

        pr = payload.get("pull_request", {})
        if not pr.get("merged", False):
            return []

        repo = payload.get("repository", {})

        meta = {
            "pr_number": pr.get("number"),
            "title": pr.get("title", ""),
            "author": pr.get("user", {}).get("login", "unknown"),
            "base_branch": pr.get("base", {}).get("ref", ""),
            "head_branch": pr.get("head", {}).get("ref", ""),
            "merge_sha": (pr.get("merge_commit_sha", "") or "")[:8],
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
        }

        return [ChangeEvent(
            timestamp=_parse_gh_ts(pr.get("merged_at")),
            source=EventSource.GITHUB,
            resource_type="pull_request",
            resource_name=repo.get("name", "unknown"),
            namespace=repo.get("owner", {}).get("login", ""),
            action=EventAction.UPDATED,
            severity=EventSeverity.INFO,
            summary=f"PR #{meta['pr_number']} merged: {meta['title']}",
            metadata=meta,
            raw_event=payload,
        )]


def _parse_gh_ts(ts: str | None) -> datetime:
    """GitHub sends ISO-8601 with trailing Z.  Handle it gracefully."""
    if not ts:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)
