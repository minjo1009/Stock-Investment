from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL_TEXT = [
    "paper_operation:",
    "strategy_acceptance:",
    "deployment_readiness:",
    "real_capital:",
    "blockers:",
    "program_level_acceptance_review:",
    "forbidden_claims_until_sell_lifecycle_validated:",
]

REQUIRED_BLOCKER_FIELDS = {
    "blocker_id",
    "priority",
    "owner",
    "team",
    "artifact",
    "validation",
    "next_gate",
    "status",
}

REQUIRED_ACCEPTANCE_GATES = {
    "SELL_FILLS_EXIST",
    "REALIZED_TRADES_100_PLUS",
    "REPLAY_MATCH_99_PLUS",
    "SOURCE_HEALTH_20_SESSIONS",
    "CANDIDATE_FUNNEL_AUDITED",
    "KILL_SWITCH_TESTED",
    "REVIEW_PACKET_100_PERCENT",
}

FORBIDDEN_CLAIMS = {
    "strategy validated",
    "profitable strategy",
    "deployment ready",
    "production ready",
}


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
            current = {start.group(1): start.group(2).strip()}
            continue
        field = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*)$", line)
        if field and current is not None:
            current[field.group(1)] = field.group(2).strip()
    if current:
        items.append(current)
    return items


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing readiness registry: {path}"]
    text = path.read_text(encoding="utf-8")

    for required in REQUIRED_TOP_LEVEL_TEXT:
        if required not in text:
            errors.append(f"missing top-level section: {required}")

    if "status: READY_FOR_CONTROLLED_PAPER_RUN" not in text:
        errors.append("paper_operation.status must be READY_FOR_CONTROLLED_PAPER_RUN")
    if "status: NOT_ACCEPTED" not in text:
        errors.append("strategy_acceptance.status must remain NOT_ACCEPTED")
    if "target_status: ACCEPTANCE_REVIEW" not in text:
        errors.append("strategy_acceptance.target_status must be ACCEPTANCE_REVIEW")
    if "status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" not in text:
        errors.append("deployment_readiness.status must be DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    if "status: FORBIDDEN" not in text:
        errors.append("real_capital.status must be FORBIDDEN")

    blockers = _extract_list_items(text, "blockers")
    if len(blockers) != 9:
        errors.append(f"expected 9 blockers, found {len(blockers)}")
    blocker_ids: set[str] = set()
    for idx, blocker in enumerate(blockers, start=1):
        missing = REQUIRED_BLOCKER_FIELDS - set(blocker)
        if missing:
            errors.append(f"blocker {idx}: missing fields: {', '.join(sorted(missing))}")
        blocker_id = blocker.get("blocker_id", "")
        if blocker_id in blocker_ids:
            errors.append(f"duplicate blocker_id: {blocker_id}")
        blocker_ids.add(blocker_id)
        for field in ["owner", "artifact", "validation", "next_gate"]:
            if not blocker.get(field, "").strip():
                errors.append(f"{blocker_id or f'blocker {idx}'}: empty {field}")

    gates = _extract_list_items(text, "program_level_acceptance_review")
    gate_ids = {gate.get("gate_id", "") for gate in gates}
    missing_gates = REQUIRED_ACCEPTANCE_GATES - gate_ids
    if missing_gates:
        errors.append(f"missing acceptance gates: {', '.join(sorted(missing_gates))}")
    for gate in gates:
        if gate.get("required") != "true":
            errors.append(f"{gate.get('gate_id', 'unknown gate')}: required must be true")
        if not gate.get("current_status"):
            errors.append(f"{gate.get('gate_id', 'unknown gate')}: missing current_status")

    lower_text = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        if claim not in lower_text:
            errors.append(f"missing forbidden claim phrase: {claim}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("docs/ownership/readiness_registry.yaml"),
    )
    args = parser.parse_args()
    errors = validate(args.registry)
    if errors:
        for error in errors:
            print(f"[READINESS_REGISTRY_ERROR] {error}")
        sys.exit(1)
    print(f"[READINESS_REGISTRY_OK] {args.registry}")


if __name__ == "__main__":
    main()
