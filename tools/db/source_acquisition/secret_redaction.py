from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SECRET_KEY_PATTERNS = ("secret", "token", "api_key", "apikey", "password", "authorization", "access_key")
SECRET_VALUE_PATTERNS = [
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}"),
]


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:3]}***{text[-3:]}"


def redact_text(value: object) -> str:
    text = "" if value is None else str(value)
    for pattern in SECRET_VALUE_PATTERNS:
        text = pattern.sub("***REDACTED***", text)
    return text


def looks_like_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(pattern in normalized for pattern in SECRET_KEY_PATTERNS)


def looks_like_secret_value(value: object) -> bool:
    if value is None:
        return False
    text = str(value)
    if not text:
        return False
    return any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)


def find_secret_paths(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if looks_like_secret_key(str(key)) and value not in ("", None, [], {}):
                hits.append(path)
            hits.extend(find_secret_paths(value, prefix=path))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            hits.extend(find_secret_paths(value, prefix=f"{prefix}[{idx}]"))
    elif looks_like_secret_value(payload):
        hits.append(prefix or "<value>")
    return hits


def scan_repo_for_plaintext_marketaux_token(root: Path, include_paths: list[Path] | None = None) -> list[Path]:
    hits: list[Path] = []
    excluded_parts = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "data",
        "logs",
        "downloads",
        "frontend",
        "frontend_data",
        "graphify-out",
    }
    excluded_names = {".env", "trading.db"}
    candidates: list[Path] = []
    if include_paths is None:
        candidates = list(root.rglob("*"))
    else:
        for include_path in include_paths:
            path = include_path if include_path.is_absolute() else root / include_path
            if path.is_dir():
                candidates.extend(path.rglob("*"))
            else:
                candidates.append(path)
    for path in candidates:
        if not path.is_file():
            continue
        if path.name in excluded_names:
            continue
        if any(part in excluded_parts for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".json", ".md", ".yaml", ".yml", ".ps1", ".csv", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            lower = line.lower()
            if "marketaux" not in lower:
                continue
            if re.search(r"marketaux[_\- ]?(api[_\- ]?)?(key|token)\s*[:=]\s*[A-Za-z0-9_\-]{16,}", line, flags=re.I):
                hits.append(path)
                break
    return sorted(set(hits))
