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


def send_message(text: str) -> None:
    webhook_url = _required_env("SLACK_WEBHOOK_URL")
    payload = json.dumps({"text": text}).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with request.urlopen(req, timeout=10):
        return None

