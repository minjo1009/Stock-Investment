from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OFFICIAL_REGISTRY_PATH = Path("configs/source_registry/l0_official_public_releases.json")
GDELT_REGISTRY_PATH = Path("configs/source_registry/l0_gdelt_queries.json")
MARKETAUX_REGISTRY_PATH = Path("configs/source_registry/l0_marketaux_queries.json")


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_official_public_release_sources(path: Path = OFFICIAL_REGISTRY_PATH) -> list[dict[str, Any]]:
    registry = load_registry(path)
    return list(registry.get("sources", []))


def enabled_official_sources(path: Path = OFFICIAL_REGISTRY_PATH) -> list[dict[str, Any]]:
    return [source for source in load_official_public_release_sources(path) if bool(source.get("enabled"))]


def validate_official_registry(path: Path = OFFICIAL_REGISTRY_PATH) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing official registry: {path}"]
    registry = load_registry(path)
    if registry.get("authority_class") != "official_primary":
        errors.append("official registry authority_class must be official_primary")
    for source in registry.get("sources", []):
        source_id = str(source.get("source_id", "")).strip()
        if not source_id:
            errors.append("source missing source_id")
        if bool(source.get("enabled")) and source.get("authority_class") != "official_primary":
            errors.append(f"{source_id}: enabled source must be official_primary")
        if bool(source.get("enabled")) and not str(source.get("url", "")).startswith("https://"):
            errors.append(f"{source_id}: enabled source must have https URL")
        if not bool(source.get("enabled")) and source.get("verification_status") == "TODO_VERIFY_ENDPOINT":
            if source.get("authority_class") != "official_primary_candidate":
                errors.append(f"{source_id}: unverified placeholder must be official_primary_candidate")
    return errors
