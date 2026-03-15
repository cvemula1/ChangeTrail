# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Collector base classes.

Want to add a new event source?  Subclass BaseCollector (or WebhookCollector
for push-based sources), implement the handful of required methods, and
register it in collectors/registry.py.  That's it.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator

from changetrail.core.models import ChangeEvent

log = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Poll-based collector — subclass this for K8s, AWS CloudTrail, etc."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def setup(self) -> None:
        """Open connections, load creds, whatever you need."""
        ...

    @abstractmethod
    async def collect(self) -> list[ChangeEvent]:
        """Return new events since the last call."""
        ...

    async def teardown(self) -> None:
        """Clean up on shutdown (optional)."""
        pass

    async def stream(self) -> AsyncIterator[ChangeEvent]:
        """Default polling loop.  Override if you want a real watch/stream."""
        while True:
            try:
                for event in await self.collect():
                    yield event
            except Exception as exc:
                log.error("[%s] collection failed: %s", self.name, exc)
            await asyncio.sleep(30)


class WebhookCollector(BaseCollector):
    """Push-based collector — subclass this for GitHub, GitLab webhooks, etc."""

    @abstractmethod
    async def handle_webhook(
        self, headers: dict[str, str], payload: dict
    ) -> list[ChangeEvent]:
        """Turn an incoming webhook POST into ChangeEvents."""
        ...

    async def collect(self) -> list[ChangeEvent]:
        # webhook collectors don't poll
        return []
