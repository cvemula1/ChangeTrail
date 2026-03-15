# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
Config.

All settings come from env vars prefixed with CT_ (e.g. CT_DATABASE_URL).
Copy .env.example to .env and tweak what you need.
"""

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ChangeTrail"
    app_version: str = "0.1.0"
    debug: bool = False

    # postgres
    database_url: str = "postgresql+asyncpg://changetrail:changetrail@localhost:5432/changetrail"
    database_url_sync: str = "postgresql+psycopg2://changetrail:changetrail@localhost:5432/changetrail"

    # api server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # kubernetes collector
    kubernetes_enabled: bool = True
    kubernetes_namespace: str = ""       # blank = watch every namespace
    kubernetes_poll_interval: int = 30   # seconds between polls

    # github collector (webhook-based, off by default)
    github_enabled: bool = False
    github_token: str = ""
    github_webhook_secret: str = ""
    github_repos: List[str] = []         # e.g. ["cvemula1/ChangeTrail"]

    # aws cloudtrail collector (planned)
    aws_enabled: bool = False
    aws_region: str = "us-east-1"
    aws_cloudtrail_poll_interval: int = 60

    # slack integration
    slack_signing_secret: str = ""
    slack_bot_token: str = ""
    slack_webhook_url: str = ""           # incoming webhook for alert push

    # how long to keep events before auto-cleanup
    event_retention_days: int = 30

    model_config = {"env_prefix": "CT_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
