# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for the GitHub collector."""

from changetrail.collectors.github.collector import GitHubCollector, _parse_gh_ts
from changetrail.core.models import EventAction, EventSource


def _make_collector() -> GitHubCollector:
    return GitHubCollector()


def test_parse_gh_timestamp():
    dt = _parse_gh_ts("2026-03-14T12:41:00Z")
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.hour == 12


def test_parse_gh_timestamp_none():
    dt = _parse_gh_ts(None)
    assert dt is not None  # defaults to now


def test_handle_push_to_main():
    c = _make_collector()
    payload = {
        "ref": "refs/heads/main",
        "repository": {"name": "my-app", "full_name": "org/my-app", "owner": {"login": "org"}},
        "commits": [{"id": "abc"}, {"id": "def"}, {"id": "ghi"}],
        "head_commit": {
            "id": "abc12345",
            "message": "Fix login bug",
            "timestamp": "2026-03-14T12:00:00Z",
        },
        "pusher": {"name": "alice"},
        "compare": "https://github.com/org/my-app/compare/abc...def",
    }
    events = c._handle_push(payload, "delivery-1")
    assert len(events) == 1
    assert events[0].source == EventSource.GITHUB
    assert events[0].action == EventAction.UPDATED
    assert events[0].resource_name == "my-app"
    assert "3 commit(s)" in events[0].summary
    assert "alice" in events[0].summary


def test_handle_push_to_feature_branch_ignored():
    c = _make_collector()
    payload = {
        "ref": "refs/heads/feature/new-stuff",
        "repository": {"name": "my-app", "owner": {"login": "org"}},
        "commits": [{"id": "abc"}],
        "head_commit": {"id": "abc", "message": "WIP", "timestamp": "2026-03-14T12:00:00Z"},
        "pusher": {"name": "bob"},
    }
    events = c._handle_push(payload, "delivery-2")
    assert len(events) == 0  # feature branches not tracked


def test_handle_deployment():
    c = _make_collector()
    payload = {
        "deployment": {
            "environment": "production",
            "ref": "main",
            "sha": "abc12345deadbeef",
            "creator": {"login": "deploy-bot"},
            "description": "Auto deploy",
            "created_at": "2026-03-14T12:41:00Z",
        },
        "repository": {"name": "checkout-svc", "full_name": "org/checkout-svc", "owner": {"login": "org"}},
    }
    events = c._handle_deployment(payload, "delivery-3")
    assert len(events) == 1
    assert events[0].action == EventAction.DEPLOYED
    assert events[0].metadata["environment"] == "production"


def test_handle_release():
    c = _make_collector()
    payload = {
        "action": "published",
        "release": {
            "tag_name": "v2.1.0",
            "name": "Version 2.1.0",
            "prerelease": False,
            "author": {"login": "releaser"},
            "html_url": "https://github.com/org/app/releases/tag/v2.1.0",
            "published_at": "2026-03-14T15:00:00Z",
        },
        "repository": {"name": "app", "owner": {"login": "org"}},
    }
    events = c._handle_release(payload, "delivery-4")
    assert len(events) == 1
    assert events[0].action == EventAction.CREATED
    assert "v2.1.0" in events[0].summary


def test_handle_pr_merged():
    c = _make_collector()
    payload = {
        "action": "closed",
        "pull_request": {
            "merged": True,
            "number": 42,
            "title": "Add caching",
            "user": {"login": "dev"},
            "base": {"ref": "main"},
            "head": {"ref": "feat/cache"},
            "merge_commit_sha": "deadbeef12345678",
            "merged_at": "2026-03-14T14:00:00Z",
            "additions": 100,
            "deletions": 20,
            "changed_files": 5,
        },
        "repository": {"name": "app", "owner": {"login": "org"}},
    }
    events = c._handle_pull_request(payload, "delivery-5")
    assert len(events) == 1
    assert "PR #42" in events[0].summary
    assert events[0].metadata["title"] == "Add caching"


def test_handle_pr_closed_not_merged():
    c = _make_collector()
    payload = {
        "action": "closed",
        "pull_request": {"merged": False, "number": 99},
        "repository": {"name": "app", "owner": {"login": "org"}},
    }
    events = c._handle_pull_request(payload, "delivery-6")
    assert len(events) == 0
