# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

"""Tests for normalizer helpers."""

from changetrail.core.models import EventAction, EventSeverity
from changetrail.core.normalizer import (
    build_summary,
    determine_severity,
    normalize_action,
)


def test_normalize_action_known():
    assert normalize_action("created") == EventAction.CREATED
    assert normalize_action("DELETED") == EventAction.DELETED
    assert normalize_action("Deploy") == EventAction.DEPLOYED
    assert normalize_action("  restart  ") == EventAction.RESTARTED


def test_normalize_action_unknown_defaults_to_updated():
    assert normalize_action("something_random") == EventAction.UPDATED


def test_build_summary_basic():
    s = build_summary(EventAction.UPDATED, "configmap", "app-config")
    assert "updated" in s
    assert "app-config" in s


def test_build_summary_deployed_with_version():
    s = build_summary(
        EventAction.DEPLOYED, "deployment", "my-svc",
        {"new_version": "v2.0"}
    )
    assert "v2.0" in s


def test_build_summary_scaled():
    s = build_summary(
        EventAction.SCALED, "deployment", "api",
        {"old_replicas": 2, "replicas": 5}
    )
    assert "2" in s and "5" in s


def test_build_summary_restarted():
    s = build_summary(
        EventAction.RESTARTED, "pod", "api-xyz",
        {"restart_count": 4}
    )
    assert "4" in s


def test_determine_severity_failed_is_critical():
    assert determine_severity(EventAction.FAILED, "deployment") == EventSeverity.CRITICAL


def test_determine_severity_deleted_is_warning():
    assert determine_severity(EventAction.DELETED, "pod") == EventSeverity.WARNING


def test_determine_severity_restart_spike_is_warning():
    sev = determine_severity(EventAction.RESTARTED, "pod", {"restart_count": 5})
    assert sev == EventSeverity.WARNING


def test_determine_severity_normal_is_info():
    assert determine_severity(EventAction.CREATED, "configmap") == EventSeverity.INFO
