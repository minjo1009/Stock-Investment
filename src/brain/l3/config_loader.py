from __future__ import annotations

from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text == "":
        return ""
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text.strip('"').strip("'")


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Load the small repo-owned YAML configs used by L3 without PyYAML."""

    config_path = Path(path)
    data: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, sep, value = line.strip().partition(":")
        if not sep:
            continue
        if indent == 0:
            if value.strip():
                data[key] = _parse_scalar(value)
                current_section = None
            else:
                data[key] = {}
                current_section = key
        elif current_section is not None and isinstance(data.get(current_section), dict):
            data[current_section][key] = _parse_scalar(value)
    return data
