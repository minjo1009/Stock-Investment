from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    digest = stable_hash([str(part or "") for part in parts])[:24]
    return f"{prefix}:{digest}"
