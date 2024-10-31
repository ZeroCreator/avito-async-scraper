# syntax=docker/dockerfile:1
FROM python:3.12-alpine3.20

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/app

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.lock,target=requirements.lock \
    python -m pip install -r requirements.lock

USER appuser

COPY . .

CMD python3 avito_scraper/main.py
