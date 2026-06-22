"""Minimal Slack webhook client."""

from __future__ import annotations

import json
import os
from urllib import request


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _configured_secret_values() -> list[str]:
    names = [
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NUMBER",
        "SLACK_WEBHOOK_URL",
        "APCA_API_KEY_ID",
        "APCA_API_SECRET_KEY",
    ]
    values: list[str] = []
    for name in names:
        value = os.environ.get(name, "").strip()
        if len(value) >= 8:
            values.append(value)
    return values


def _contains_configured_secret(text: str) -> bool:
    return any(secret in text for secret in _configured_secret_values())


def send_message(text: str) -> None:
    webhook_url = _required_env("SLACK_WEBHOOK_URL")
    if _contains_configured_secret(text):
        raise RuntimeError("Slack message contains a configured secret")
    payload = json.dumps({"text": text}).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with request.urlopen(req, timeout=10):
        return None
