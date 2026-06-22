from __future__ import annotations

import argparse
import csv
from datetime import datetime
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "attention_packet_id",
    "asof_ts",
    "source_event_id",
    "evidence_id",
    "source_family",
    "thesis_question",
    "minimal_fact",
    "uncertainty_cap",
    "sufficiency_state",
    "owner_next_check",
    "forbidden_output_audit",
}

ALLOWED_STATES = {"enough_for_review", "defer", "source_gap", "block", "noise"}

FORBIDDEN_MARKERS = {
    "buy_signal",
    "sell_signal",
    "trade_permission",
    "rank",
    "alpha_score",
    "sizing",
    "backtest_eligibility",
    "real_capital",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str, scope: str, errors: list[str]) -> None:
    if not value:
        errors.append(f"{scope}: missing asof_ts")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{scope}: invalid ISO timestamp {value}")


def validate_packet_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing {path}"]
    rows = read_csv(path)
    if not rows:
        return [f"{path}: no rows"]
    missing = REQUIRED_COLUMNS - set(rows[0].keys())
    if missing:
        errors.append(f"{path.name}: missing columns {','.join(sorted(missing))}")
        return errors
    seen: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        packet_id = row.get("attention_packet_id", "")
        scope = f"{path.name} row {idx} {packet_id or '<missing>'}"
        if not packet_id:
            errors.append(f"{scope}: missing attention_packet_id")
        elif packet_id in seen:
            errors.append(f"{scope}: duplicate attention_packet_id")
        seen.add(packet_id)
        parse_ts(row.get("asof_ts", ""), scope, errors)
        state = row.get("sufficiency_state", "")
        if state not in ALLOWED_STATES:
            errors.append(f"{scope}: invalid sufficiency_state {state}")
        for field in ["source_family", "thesis_question", "minimal_fact", "uncertainty_cap", "owner_next_check", "forbidden_output_audit"]:
            if not row.get(field):
                errors.append(f"{scope}: missing {field}")
        if state == "enough_for_review":
            for field in ["source_event_id", "evidence_id"]:
                if not row.get(field):
                    errors.append(f"{scope}: enough_for_review missing {field}")
        if state == "source_gap":
            if "source_gap" not in row.get("minimal_fact", "").lower() and "missing" not in row.get("minimal_fact", "").lower():
                errors.append(f"{scope}: source_gap state must preserve missing source in minimal_fact")
        if "negative" in row.get("minimal_fact", "").lower() and state == "source_gap":
            errors.append(f"{scope}: missing_to_negative_detected")
        for field, value in row.items():
            if field == "forbidden_output_audit":
                continue
            lowered = str(value).lower()
            for marker in FORBIDDEN_MARKERS:
                if marker in lowered:
                    errors.append(f"{scope}: forbidden output marker {marker} in {field}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    args = parser.parse_args()
    errors = validate_packet_file(args.packet)
    if errors:
        for error in errors:
            print(f"[ATTENTION_PACKET_ERROR] {error}")
        sys.exit(1)
    print(f"[ATTENTION_PACKET_OK] {args.packet}")


if __name__ == "__main__":
    main()
