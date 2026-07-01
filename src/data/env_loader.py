from __future__ import annotations

import os
from pathlib import Path


REPO_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_repo_env(path: Path | None = None, *, override: bool = False) -> dict[str, str]:
    """Load local repo .env values without logging secrets.

    Supports standard KEY=VALUE lines. For the user's existing Alpaca shorthand,
    also accepts:
    - key <value> -> APCA_API_KEY_ID
    - secret key <value> -> APCA_API_SECRET_KEY
    """

    env_path = path or REPO_ENV_PATH
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        key, value = _parse_line(raw_line)
        if not key or value is None:
            continue
        if override or not os.environ.get(key):
            os.environ[key] = value
        loaded[key] = value
    return loaded


def _parse_line(raw_line: str) -> tuple[str, str | None]:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return "", None
    if line.lower().startswith("export "):
        line = line[7:].strip()
    if "=" in line:
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        normalized = _normalize_key_alias(key)
        key = normalized or key
        return key, value
    lower = line.lower()
    if lower.startswith("secret key "):
        return "APCA_API_SECRET_KEY", line[len("secret key ") :].strip()
    if lower.startswith("secret_key "):
        return "APCA_API_SECRET_KEY", line[len("secret_key ") :].strip()
    if lower.startswith("key "):
        return "APCA_API_KEY_ID", line[len("key ") :].strip()
    if lower.startswith("api_key "):
        return "APCA_API_KEY_ID", line[len("api_key ") :].strip()
    return "", None


def _normalize_key_alias(key: str) -> str:
    normalized = key.strip().upper().replace("-", "_")
    collapsed = " ".join(normalized.replace("_", " ").split())
    if normalized in {"ALPACA_KEY", "ALPACA_API_KEY", "APCA_KEY"} or collapsed in {"API KEY", "ALPACA API KEY"}:
        return "APCA_API_KEY_ID"
    if normalized in {"ALPACA_SECRET", "ALPACA_SECRET_KEY", "ALPACA_API_SECRET_KEY", "APCA_SECRET"} or collapsed in {
        "SECRET API KEY",
        "API SECRET KEY",
        "ALPACA SECRET KEY",
        "ALPACA API SECRET KEY",
    }:
        return "APCA_API_SECRET_KEY"
    return ""


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
