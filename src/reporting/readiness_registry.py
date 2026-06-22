from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = Path("docs/ownership/readiness_registry.yaml")


def _extract_block(text: str, key: str) -> dict[str, str]:
    lines = text.splitlines()
    block: dict[str, str] = {}
    in_block = False
    for line in lines:
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            in_block = True
            continue
        if in_block and line and not line.startswith(" ") and not line.startswith("\t"):
            break
        if not in_block:
            continue
        match = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*)$", line)
        if match:
            block[match.group(1)] = match.group(2).strip().strip('"')
    return block


def _extract_list_items(text: str, parent_key: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    items: list[dict[str, str]] = []
    in_section = False
    current: dict[str, str] | None = None
    for line in lines:
        if re.match(rf"^{re.escape(parent_key)}:\s*$", line):
            in_section = True
            continue
        if in_section and line and not line.startswith(" ") and not line.startswith("\t"):
            break
        if not in_section:
            continue
        start = re.match(r"^\s*-\s+([A-Za-z0-9_]+):\s*(.*)$", line)
        if start:
            if current:
                items.append(current)
            current = {start.group(1): start.group(2).strip().strip('"')}
            continue
        field = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*)$", line)
        if field and current is not None:
            current[field.group(1)] = field.group(2).strip().strip('"')
    if current:
        items.append(current)
    return items


def _extract_forbidden_claims(text: str) -> list[str]:
    claims = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("forbidden_claims_until_sell_lifecycle_validated:"):
            in_section = True
            continue
        if in_section and line and not line.startswith(" ") and not line.startswith("\t"):
            break
        if not in_section:
            continue
        match = re.match(r"^\s*-\s+(.*)$", line)
        if match:
            claims.append(match.group(1).strip())
    return claims


def build_readiness_registry_payload(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    if not registry_path.exists():
        return {
            "generated_utc": datetime.now(UTC).isoformat(),
            "contract_version": "readiness-registry-v1",
            "canonical_source": registry_path.as_posix(),
            "load_status": "MISSING_REGISTRY",
            "strategy_acceptance": {"status": "NOT_ACCEPTED", "target_status": ""},
            "paper_operation": {"status": "", "ready_for_controlled_paper_run_flag": 0},
            "deployment_readiness": {"status": "", "deployment_ready_flag": 0},
            "real_capital": {"status": "FORBIDDEN"},
            "blockers": [],
            "acceptance_gates": [],
            "forbidden_claims": [],
        }
    text = registry_path.read_text(encoding="utf-8")
    paper_operation = _extract_block(text, "paper_operation")
    strategy_acceptance = _extract_block(text, "strategy_acceptance")
    deployment_readiness = _extract_block(text, "deployment_readiness")
    real_capital = _extract_block(text, "real_capital")
    blockers = _extract_list_items(text, "blockers")
    acceptance_gates = _extract_list_items(text, "program_level_acceptance_review")
    blocker_counts = Counter(item.get("status", "") for item in blockers)
    gate_counts = Counter(item.get("current_status", "") for item in acceptance_gates)
    paper_status = paper_operation.get("status", "")
    strategy_status = strategy_acceptance.get("status", "NOT_ACCEPTED")
    deployment_status = deployment_readiness.get("status", "")
    real_capital_status = real_capital.get("status", "FORBIDDEN")
    return {
        "generated_utc": datetime.now(UTC).isoformat(),
        "contract_version": "readiness-registry-v1",
        "canonical_source": registry_path.as_posix(),
        "load_status": "READINESS_REGISTRY_LOADED",
        "registry": {
            "paper_operation_status": paper_status,
            "strategy_acceptance_status": strategy_status,
            "strategy_acceptance_target_status": strategy_acceptance.get("target_status", ""),
            "deployment_readiness_status": deployment_status,
            "real_capital_status": real_capital_status,
        },
        "paper_operation": {
            "status": paper_status,
            "ready_for_controlled_paper_run_flag": int(paper_status == "READY_FOR_CONTROLLED_PAPER_RUN"),
        },
        "strategy_acceptance": {
            "status": strategy_status,
            "target_status": strategy_acceptance.get("target_status", ""),
            "accepted_flag": int(strategy_status not in {"", "NOT_ACCEPTED"}),
        },
        "deployment_readiness": {
            "status": deployment_status,
            "deployment_ready_flag": int(deployment_status == "DEPLOYMENT_READY"),
        },
        "real_capital": {
            "status": real_capital_status,
            "forbidden_flag": int(real_capital_status == "FORBIDDEN"),
        },
        "blockers": blockers,
        "blocker_status_counts": dict(sorted(blocker_counts.items())),
        "acceptance_gates": acceptance_gates,
        "acceptance_gate_status_counts": dict(sorted(gate_counts.items())),
        "forbidden_claims": _extract_forbidden_claims(text),
        "active_blocker_ids": [item.get("blocker_id", "") for item in blockers if item.get("status", "") not in {"PRIMARY_PASS", "ACCEPTED", "PASS"}],
    }


def write_readiness_registry_payload(
    payload: dict[str, Any] | None = None,
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    outputs: list[Path] | None = None,
) -> dict[str, Any]:
    payload = payload or build_readiness_registry_payload(registry_path)
    outputs = outputs or [
        Path("frontend_data/catalog"),
        Path("frontend/trader-terminal/public/catalog"),
    ]
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str, allow_nan=False)
    for output in outputs:
        output.mkdir(parents=True, exist_ok=True)
        (output / "readiness_registry.json").write_text(text, encoding="utf-8")
    return payload
