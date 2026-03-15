# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Kubernetes collector.

Polls the K8s API for deployment image changes, pod restart spikes, and
configmap edits.  Uses resourceVersion diffing so we only emit events for
things that actually changed since the last poll.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from changetrail.core.collector import BaseCollector
from changetrail.core.config import settings
from changetrail.core.models import ChangeEvent, EventAction, EventSeverity, EventSource
from changetrail.core.normalizer import build_summary, determine_severity

log = logging.getLogger(__name__)


class KubernetesCollector(BaseCollector):
    """Polls K8s for deploy changes, pod restarts, and configmap edits."""

    def __init__(self):
        self._client = None
        self._apps_v1 = None
        self._core_v1 = None
        self._last_seen: dict[str, str] = {}  # resource_uid -> last resourceVersion

    @property
    def name(self) -> str:
        return "kubernetes"

    async def setup(self) -> None:
        try:
            from kubernetes import client, config as k8s_config

            try:
                k8s_config.load_incluster_config()
                log.info("using in-cluster config")
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()
                log.info("using local kubeconfig")

            self._apps_v1 = client.AppsV1Api()
            self._core_v1 = client.CoreV1Api()
        except Exception as exc:
            log.error("k8s client init failed: %s", exc)
            raise

    async def collect(self) -> list[ChangeEvent]:
        events: list[ChangeEvent] = []
        for fn in (self._collect_deployments, self._collect_pod_restarts, self._collect_configmaps):
            try:
                events.extend(await fn())
            except Exception as exc:
                log.error("k8s collect (%s) failed: %s", fn.__name__, exc)
        return events

    async def _collect_deployments(self) -> list[ChangeEvent]:
        events: list[ChangeEvent] = []
        ns = settings.kubernetes_namespace

        loop = asyncio.get_event_loop()
        if ns:
            deploys = await loop.run_in_executor(
                None, lambda: self._apps_v1.list_namespaced_deployment(ns)
            )
        else:
            deploys = await loop.run_in_executor(
                None, self._apps_v1.list_deployment_for_all_namespaces
            )

        for dep in deploys.items:
            uid = dep.metadata.uid
            rv = dep.metadata.resource_version
            dep_name = dep.metadata.name
            dep_ns = dep.metadata.namespace

            if uid in self._last_seen and self._last_seen[uid] != rv:
                containers = dep.spec.template.spec.containers or []
                images = {c.name: c.image for c in containers}
                replicas = dep.spec.replicas or 0
                ready = dep.status.ready_replicas or 0

                meta = {
                    "images": images,
                    "replicas": replicas,
                    "ready_replicas": ready,
                    "generation": dep.metadata.generation,
                }

                action = EventAction.UPDATED
                if dep.status.conditions:
                    for cond in dep.status.conditions:
                        if cond.type == "Progressing" and cond.reason == "NewReplicaSetAvailable":
                            action = EventAction.DEPLOYED

                event = ChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    source=EventSource.KUBERNETES,
                    resource_type="deployment",
                    resource_name=dep_name,
                    namespace=dep_ns,
                    action=action,
                    severity=determine_severity(action, "deployment", meta),
                    summary=build_summary(action, "deployment", dep_name, meta),
                    metadata=meta,
                    labels=dict(dep.metadata.labels or {}),
                )
                events.append(event)

            self._last_seen[uid] = rv

        return events

    async def _collect_pod_restarts(self) -> list[ChangeEvent]:
        events: list[ChangeEvent] = []
        ns = settings.kubernetes_namespace

        loop = asyncio.get_event_loop()
        if ns:
            pods = await loop.run_in_executor(
                None, lambda: self._core_v1.list_namespaced_pod(ns)
            )
        else:
            pods = await loop.run_in_executor(
                None, self._core_v1.list_pod_for_all_namespaces
            )

        for pod in pods.items:
            if not pod.status or not pod.status.container_statuses:
                continue

            for cs in pod.status.container_statuses:
                restart_key = f"restart:{pod.metadata.uid}:{cs.name}"
                restart_count = cs.restart_count or 0

                if restart_count > 0:
                    prev = int(self._last_seen.get(restart_key, "0"))
                    if restart_count > prev:
                        meta = {
                            "restart_count": restart_count,
                            "container": cs.name,
                            "new_restarts": restart_count - prev,
                        }

                        if cs.last_state and cs.last_state.terminated:
                            meta["exit_code"] = cs.last_state.terminated.exit_code
                            meta["reason"] = cs.last_state.terminated.reason or "Unknown"

                        event = ChangeEvent(
                            timestamp=datetime.now(timezone.utc),
                            source=EventSource.KUBERNETES,
                            resource_type="pod",
                            resource_name=pod.metadata.name,
                            namespace=pod.metadata.namespace,
                            action=EventAction.RESTARTED,
                            severity=determine_severity(EventAction.RESTARTED, "pod", meta),
                            summary=build_summary(EventAction.RESTARTED, "pod", pod.metadata.name, meta),
                            metadata=meta,
                            labels=dict(pod.metadata.labels or {}),
                        )
                        events.append(event)

                    self._last_seen[restart_key] = str(restart_count)

        return events

    async def _collect_configmaps(self) -> list[ChangeEvent]:
        events: list[ChangeEvent] = []
        ns = settings.kubernetes_namespace

        loop = asyncio.get_event_loop()
        if ns:
            cms = await loop.run_in_executor(
                None, lambda: self._core_v1.list_namespaced_config_map(ns)
            )
        else:
            cms = await loop.run_in_executor(
                None, self._core_v1.list_config_map_for_all_namespaces
            )

        for cm in cms.items:
            # skip kube-system noise
            if cm.metadata.namespace in ("kube-system", "kube-public"):
                continue

            uid = cm.metadata.uid
            rv = cm.metadata.resource_version

            if uid in self._last_seen and self._last_seen[uid] != rv:
                meta = {
                    "keys": list((cm.data or {}).keys()),
                    "key_count": len(cm.data or {}),
                }
                event = ChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    source=EventSource.KUBERNETES,
                    resource_type="configmap",
                    resource_name=cm.metadata.name,
                    namespace=cm.metadata.namespace,
                    action=EventAction.UPDATED,
                    severity=EventSeverity.INFO,
                    summary=build_summary(EventAction.UPDATED, "configmap", cm.metadata.name, meta),
                    metadata=meta,
                    labels=dict(cm.metadata.labels or {}),
                )
                events.append(event)

            self._last_seen[uid] = rv

        return events

    async def stream(self):
        while True:
            try:
                for event in await self.collect():
                    yield event
            except Exception as exc:
                log.error("[kubernetes] poll error: %s", exc)
            await asyncio.sleep(settings.kubernetes_poll_interval)

    async def teardown(self) -> None:
        self._last_seen.clear()
        log.info("kubernetes collector stopped")
