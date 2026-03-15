# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Event store (Postgres).

This is the only place that talks to the database.  Everything goes through
EventStore.save / .query / .cleanup — the rest of the codebase never imports
SQLAlchemy directly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, JSON, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from changetrail.core.config import settings
from changetrail.core.models import (
    ChangeEvent,
    ChangeEventQuery,
    EventAction,
    EventSeverity,
    EventSource,
    TimelineResponse,
)

log = logging.getLogger(__name__)


# -- ORM model -------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "change_events"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(32), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_name = Column(String(256), nullable=False, index=True)
    namespace = Column(String(128), nullable=True, index=True)
    action = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default="info")
    summary = Column(Text, nullable=False, default="")
    metadata_json = Column(JSON, nullable=False, default=dict)
    raw_event_json = Column(JSON, nullable=True)
    labels_json = Column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_events_source_ts", "source", "timestamp"),
        Index("ix_events_resource", "resource_type", "resource_name"),
    )

    def to_change_event(self) -> ChangeEvent:
        """Row → Pydantic model."""
        return ChangeEvent(
            id=self.id,
            timestamp=self.timestamp,
            source=EventSource(self.source),
            resource_type=self.resource_type,
            resource_name=self.resource_name,
            namespace=self.namespace,
            action=EventAction(self.action),
            severity=EventSeverity(self.severity),
            summary=self.summary,
            metadata=self.metadata_json or {},
            raw_event=self.raw_event_json,
            labels=self.labels_json or {},
        )

    @staticmethod
    def from_change_event(event: ChangeEvent) -> "EventRecord":
        """Pydantic model → row."""
        return EventRecord(
            id=event.id,
            timestamp=event.timestamp,
            source=event.source.value,
            resource_type=event.resource_type,
            resource_name=event.resource_name,
            namespace=event.namespace,
            action=event.action.value,
            severity=event.severity.value,
            summary=event.summary,
            metadata_json=event.metadata,
            raw_event_json=event.raw_event,
            labels_json=event.labels,
        )


# -- async engine & session ------------------------------------------------

engine = create_async_engine(settings.database_url, echo=settings.debug, pool_size=10)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create tables if they don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database tables ready")


async def close_db() -> None:
    await engine.dispose()


# -- duration parser -------------------------------------------------------

def parse_duration(duration_str: str) -> timedelta:
    """'30m' → timedelta(minutes=30), '1h' → timedelta(hours=1), etc."""
    duration_str = duration_str.strip().lower()
    if duration_str.endswith("m"):
        return timedelta(minutes=int(duration_str[:-1]))
    if duration_str.endswith("h"):
        return timedelta(hours=int(duration_str[:-1]))
    if duration_str.endswith("d"):
        return timedelta(days=int(duration_str[:-1]))
    if duration_str.endswith("s"):
        return timedelta(seconds=int(duration_str[:-1]))
    raise ValueError(f"Invalid duration format: {duration_str}. Use e.g. 30m, 1h, 24h, 7d")


# -- public interface ------------------------------------------------------

class EventStore:
    """Thin async wrapper around the change_events table."""

    async def save(self, event: ChangeEvent) -> None:
        async with async_session() as session:
            session.add(EventRecord.from_change_event(event))
            await session.commit()

    async def save_batch(self, events: list[ChangeEvent]) -> int:
        if not events:
            return 0
        async with async_session() as session:
            session.add_all([EventRecord.from_change_event(e) for e in events])
            await session.commit()
            log.info("saved %d events", len(events))
            return len(events)

    async def query(self, q: ChangeEventQuery) -> TimelineResponse:
        """Run a filtered query and return paginated results."""
        async with async_session() as session:
            stmt = select(EventRecord)

            # time window
            if q.last:
                delta = parse_duration(q.last)
                since = datetime.now(timezone.utc) - delta
                stmt = stmt.where(EventRecord.timestamp >= since)
            if q.since:
                stmt = stmt.where(EventRecord.timestamp >= q.since)
            if q.until:
                stmt = stmt.where(EventRecord.timestamp <= q.until)

            # dimension filters
            if q.source:
                stmt = stmt.where(EventRecord.source == q.source.value)
            if q.resource_type:
                stmt = stmt.where(EventRecord.resource_type == q.resource_type)
            if q.resource_name:
                stmt = stmt.where(EventRecord.resource_name == q.resource_name)
            if q.service:
                stmt = stmt.where(EventRecord.resource_name == q.service)
            if q.namespace:
                stmt = stmt.where(EventRecord.namespace == q.namespace)
            if q.action:
                stmt = stmt.where(EventRecord.action == q.action.value)
            if q.severity:
                stmt = stmt.where(EventRecord.severity == q.severity.value)

            # total count (before pagination)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await session.execute(count_stmt)
            total = total_result.scalar() or 0

            # newest first, then paginate
            stmt = stmt.order_by(desc(EventRecord.timestamp))
            stmt = stmt.offset(q.offset).limit(q.limit)

            result = await session.execute(stmt)
            records = result.scalars().all()
            events = [r.to_change_event() for r in records]

            return TimelineResponse(
                events=events,
                total=total,
                query=q.model_dump(exclude_none=True),
            )

    async def get_by_id(self, event_id: str) -> Optional[ChangeEvent]:
        async with async_session() as session:
            result = await session.execute(
                select(EventRecord).where(EventRecord.id == event_id)
            )
            record = result.scalar_one_or_none()
            return record.to_change_event() if record else None

    async def cleanup_old_events(self, retention_days: int) -> int:
        """Purge events older than *retention_days*.  Returns rows deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        async with async_session() as session:
            result = await session.execute(
                select(func.count())
                .select_from(EventRecord)
                .where(EventRecord.timestamp < cutoff)
            )
            count = result.scalar() or 0
            if count > 0:
                from sqlalchemy import delete
                await session.execute(
                    delete(EventRecord).where(EventRecord.timestamp < cutoff)
                )
                await session.commit()
                log.info("purged %d events older than %d days", count, retention_days)
            return count


event_store = EventStore()
