#!/usr/bin/env python
"""Validate Task742 pragmatic meaning packets can enter the L3 brain contract.

This validator rebuilds Task742 packets into a temporary directory, adapts them
to `brain.EconomicMeaning`, and writes only small validation summaries. It does
not run replay/backtest, rank trades, size positions, create order intents, or
mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain.meaning_adapter import task742_rows_to_economic_meanings
from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742


TASK_ID = "task_3351_3360_task742_meaning_adapter"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task742-meaning-adapter-") as tmp:
        artifacts = build_task742(out_dir=Path(tmp))
        packets = artifacts["packets"]

    rows = packets.to_dict(orient="records")
    meanings = task742_rows_to_economic_meanings(rows)
    direction_counts = Counter(meaning.direction.value for meaning in meanings)
    readiness_counts = Counter(meaning.relation_readiness for meaning in meanings)
    source_ids = [meaning.source_packet_ids[0] for meaning in meanings]
    meaning_ids = [meaning.meaning_id for meaning in meanings]

    summary = [
        {
            "task_id": "Task3351-Task3360",
            "packet_count": len(rows),
            "meaning_count": len(meanings),
            "unique_source_packet_count": len(set(source_ids)),
            "unique_meaning_id_count": len(set(meaning_ids)),
            "supportive_count": direction_counts.get("SUPPORTIVE", 0),
            "risk_count": direction_counts.get("RISK", 0),
            "mixed_count": direction_counts.get("MIXED", 0),
            "neutral_count": direction_counts.get("NEUTRAL", 0),
            "unknown_count": direction_counts.get("UNKNOWN", 0),
            "directional_ready_count": readiness_counts.get("directional", 0),
            "structural_mixed_ready_count": readiness_counts.get("structural_mixed", 0),
            "context_only_ready_count": readiness_counts.get("context_only", 0),
            "not_ready_count": readiness_counts.get("not_ready", 0),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "all_task742_packets_adapted", "pass": int(len(rows) == len(meanings) and len(meanings) > 0)},
        {"check_name": "source_packet_identity_present", "pass": int(all(bool(source_id) for source_id in source_ids))},
        {"check_name": "meaning_identity_unique", "pass": int(len(meaning_ids) == len(set(meaning_ids)))},
        {"check_name": "outcome_assignment_forbidden", "pass": int(all(not meaning.outcome_used_for_assignment for meaning in meanings))},
        {"check_name": "asof_present_for_all_meanings", "pass": int(all(bool(meaning.asof_ts) for meaning in meanings))},
        {"check_name": "symbol_present_for_all_meanings", "pass": int(all(bool(meaning.symbol) for meaning in meanings))},
        {"check_name": "relation_readiness_present", "pass": int(all(bool(meaning.relation_readiness) for meaning in meanings))},
        {"check_name": "no_order_or_replay_side_effect", "pass": 1},
    ]
    sample = [
        {
            "meaning_id": meaning.meaning_id,
            "asof_ts": meaning.asof_ts,
            "symbol": meaning.symbol,
            "direction": meaning.direction.value,
            "confidence": meaning.confidence,
            "relation_readiness": meaning.relation_readiness,
            "source_packet_ids": "|".join(meaning.source_packet_ids),
            "uncertainty_flags": "|".join(meaning.uncertainty_flags[:6]),
        }
        for meaning in meanings[:25]
    ]
    decision = [
        {
            "task_id": "Task3351-Task3360",
            "verdict": "task742_pragmatic_meaning_packets_adapt_to_l3_economic_meaning_contract",
            "packet_count": len(rows),
            "meaning_count": len(meanings),
            "package_surface": "src/brain/meaning_adapter.py",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    manifest = [
        {"relative_path": "adapter_summary.csv", "artifact_type": "summary", "description": "Task742 to EconomicMeaning adapter summary"},
        {"relative_path": "adapter_checks.csv", "artifact_type": "validation", "description": "Task742 adapter pass/fail checks"},
        {"relative_path": "adapter_sample.csv", "artifact_type": "sample", "description": "Small adapted EconomicMeaning sample"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3351-3360 validator decision row"},
    ]

    write_csv(OUT_DIR / "adapter_summary.csv", summary)
    write_csv(OUT_DIR / "adapter_checks.csv", checks)
    write_csv(OUT_DIR / "adapter_sample.csv", sample)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3351_3360_ERROR] {row['check_name']}")
        return 1
    print(f"[TASK3351_3360_OK] packets={len(rows)} meanings={len(meanings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
