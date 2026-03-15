# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Event data model.

Every collector normalises its raw data into a ChangeEvent before it hits the
store.  Keeping a single schema makes the timeline API and UI simple — they
never have to care where an event came from.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- enums -----------------------------------------------------------------

class EventSource(str, Enum):
    KUBERNETES = "kubernetes"
    GITHUB = "github"
    AWS = "aws"
    AZURE = "azure"
    TERRAFORM = "terraform"
    ARGOCD = "argocd"
    GITLAB = "gitlab"
    MANUAL = "manual"


class EventAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTARTED = "restarted"
    SCALED = "scaled"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    MODIFIED = "modified"
    FAILED = "failed"


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# -- core model ------------------------------------------------------------

class ChangeEvent(BaseModel):
    """One thing that changed in your infrastructure."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: EventSource
    resource_type: str          # "deployment", "configmap", "iam-role", …
    resource_name: str          # "checkout-service", "checkout-config", …
    namespace: Optional[str] = None   # k8s ns, AWS account, GH org — whatever fits
    action: EventAction
    severity: EventSeverity = EventSeverity.INFO
    summary: str = ""          # human-readable one-liner shown in the timeline
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_event: Optional[dict[str, Any]] = None   # stash the original payload for debugging
    labels: dict[str, str] = Field(default_factory=dict)

    def short_summary(self) -> str:
        ts = self.timestamp.strftime("%H:%M")
        return f"{ts}  {self.action.value:<12} {self.resource_type}/{self.resource_name}"


# -- query / response models -----------------------------------------------

class ChangeEventQuery(BaseModel):
    """Filters the user can pass to GET /api/v1/changes."""

    last: Optional[str] = None        # "30m", "1h", "24h"
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    source: Optional[EventSource] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    service: Optional[str] = None     # handy alias for resource_name
    namespace: Optional[str] = None
    action: Optional[EventAction] = None
    severity: Optional[EventSeverity] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TimelineResponse(BaseModel):
    events: list[ChangeEvent]
    total: int
    query: dict[str, Any]
