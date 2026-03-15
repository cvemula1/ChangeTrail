# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
FastAPI application.

This is the main ASGI entry point.  On startup it creates the DB tables and
starts any enabled collectors; on shutdown it tears everything down cleanly.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from changetrail import __version__
from changetrail.core.config import settings
from changetrail.core.store import init_db, close_db
from changetrail.api.routes import router as api_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting ChangeTrail v%s", __version__)
    await init_db()

    # collectors are nice-to-have — don't let them block the API
    try:
        from changetrail.collectors.registry import collector_registry
        await collector_registry.start_all()
    except Exception as exc:
        log.warning("collectors failed to start (API still works): %s", exc)

    yield

    try:
        from changetrail.collectors.registry import collector_registry
        await collector_registry.stop_all()
    except Exception:
        pass
    await close_db()
    log.info("shut down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Unified change timeline for incident context",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__}
