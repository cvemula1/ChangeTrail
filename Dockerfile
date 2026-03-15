# ChangeTrail API container
# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY changetrail/ changetrail/
COPY pyproject.toml .

EXPOSE 8000

CMD ["uvicorn", "changetrail.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
