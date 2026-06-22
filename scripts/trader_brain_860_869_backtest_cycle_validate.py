from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_860_869_backtest_cycle"

REQUIRED_ARTIFACTS = [
    "controlled_replay_attempts.csv",
    "qqq_benchmark_reference.csv",
    "managed_acquisition_audit.csv",
    "post_attempt_gap_diagnosis.csv",
    "cycle_summary.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = ARTIFACT_DIR / name
        if not path.exists():
            errors.append(f"missing artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty artifact {name}")
    if errors:
        return errors
    attempts = rows(ARTIFACT_DIR / "controlled_replay_attempts.csv")
    if len(attempts) != 2:
        errors.append("expected exactly two gate-aware replay attempts")
    for row in attempts:
        if row.get("strategy_replay_decision") != "not_executed":
            errors.append("strategy replay must remain not_executed")
        for field in ["price_lookup_count", "trade_row_count", "pnl_metric_count", "engine_call_count"]:
            if row.get(field) != "0":
                errors.append(f"{field} must be 0 for strategy attempts")
        if "adapter_missing_symbol_side_entry_exit_position_size" not in row.get("blocked_reason", ""):
            errors.append("attempt must report adapter trade-spec blocker")
    qqq = rows(ARTIFACT_DIR / "qqq_benchmark_reference.csv")
    if len(qqq) != 1:
        errors.append("expected one QQQ benchmark row")
    else:
        row = qqq[0]
        if row.get("symbol") != "QQQ":
            errors.append("benchmark symbol must be QQQ")
        if row.get("initial_capital") not in {"1000.0", "1000.00", "1000"}:
            errors.append("initial capital must be 1000")
        if "REFERENCE_ONLY" not in row.get("validation_authority", ""):
            errors.append("QQQ benchmark must be reference-only")
    gaps = rows(ARTIFACT_DIR / "post_attempt_gap_diagnosis.csv")
    if not any(row.get("gap_id") == "gap_adapter_trade_spec" for row in gaps):
        errors.append("missing adapter trade-spec gap")
    summary = json.loads((ARTIFACT_DIR / "cycle_summary.json").read_text(encoding="utf-8"))
    if summary.get("no_strategy_backtest_executed") is not True:
        errors.append("summary must assert no strategy backtest executed")
    if summary.get("qqq_reference_only_executed") is not True:
        errors.append("summary must assert QQQ reference-only benchmark executed")
    for field, expected in [
        ("strategy_acceptance", "NOT_ACCEPTED"),
        ("deployment_readiness", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY"),
        ("real_capital", "FORBIDDEN"),
    ]:
        if summary.get(field) != expected:
            errors.append(f"{field} must be {expected}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_860_869_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_860_869_OK] gate-aware cycle complete; strategy replay not executed; QQQ reference-only benchmark present")


if __name__ == "__main__":
    main()
