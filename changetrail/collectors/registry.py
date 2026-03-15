# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Collector registry.

Keeps track of every enabled collector, starts them on boot, and feeds their
events into the store.  New collectors register themselves here.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from changetrail.core.collector import BaseCollector
from changetrail.core.config import settings
from changetrail.core.store import event_store

log = logging.getLogger(__name__)


class CollectorRegistry:

    def __init__(self):
        self._collectors: dict[str, BaseCollector] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False

    def register(self, collector: BaseCollector) -> None:
        self._collectors[collector.name] = collector
        log.info("registered collector: %s", collector.name)

    def get(self, name: str) -> Optional[BaseCollector]:
        return self._collectors.get(name)

    @property
    def names(self) -> list[str]:
        return list(self._collectors.keys())

    async def start_all(self) -> None:
        self._running = True
        for name, collector in self._collectors.items():
            try:
                await collector.setup()
                task = asyncio.create_task(self._run_collector(collector))
                self._tasks[name] = task
                log.info("started collector: %s", name)
            except Exception as exc:
                log.error("collector %s failed to start: %s", name, exc)

    async def stop_all(self) -> None:
        self._running = False
        for name, task in self._tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            log.info("stopped collector: %s", name)
        for collector in self._collectors.values():
            await collector.teardown()
        self._tasks.clear()

    async def _run_collector(self, collector: BaseCollector) -> None:
        try:
            async for event in collector.stream():
                if not self._running:
                    break
                try:
                    await event_store.save(event)
                except Exception as exc:
                    log.error("[%s] save failed: %s", collector.name, exc)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.error("[%s] crashed: %s", collector.name, exc)

    async def collect_once(self, collector_name: str) -> int:
        """One-shot collect (useful for testing / CLI)."""
        collector = self._collectors.get(collector_name)
        if not collector:
            raise ValueError(f"unknown collector: {collector_name}")
        return await event_store.save_batch(await collector.collect())


def _build() -> CollectorRegistry:
    """Wire up whichever collectors are enabled in config."""
    registry = CollectorRegistry()

    if settings.kubernetes_enabled:
        try:
            from changetrail.collectors.kubernetes.collector import KubernetesCollector
            registry.register(KubernetesCollector())
        except ImportError:
            log.warning("kubernetes package missing — K8s collector disabled")

    if settings.github_enabled:
        try:
            from changetrail.collectors.github.collector import GitHubCollector
            registry.register(GitHubCollector())
        except ImportError:
            log.warning("httpx package missing — GitHub collector disabled")

    return registry


class _Lazy:
    """Defer registry construction until something actually needs it."""

    def __init__(self):
        self._instance: CollectorRegistry | None = None

    def __getattr__(self, name: str):
        if self._instance is None:
            self._instance = _build()
        return getattr(self._instance, name)


collector_registry = _Lazy()
