from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed"
UNIVERSE = ROOT / "data/raw/theme_universe_10x7.csv"
DECISIONS = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv"

REQUIRED_FILES = [
    "current_state_to_be_diagnosis.csv",
    "source_time_symbol_coverage_matrix.csv",
    "source_time_decision_coverage_panel.csv",
    "l1_source_evidence_seed_state.csv",
    "missing_source_acquisition_queue.csv",
    "task_894_current_state_to_be_l1_seed_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_TRADING_FIELDS = {"side", "entry", "exit", "position_size", "rank", "score", "future_return", "realized_return", "pnl"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    universe = rows(UNIVERSE)
    decisions = rows(DECISIONS)
    diagnosis = rows(ART / "current_state_to_be_diagnosis.csv")
    coverage = rows(ART / "source_time_symbol_coverage_matrix.csv")
    decision_panel = rows(ART / "source_time_decision_coverage_panel.csv")
    l1_states = rows(ART / "l1_source_evidence_seed_state.csv")
    queue = rows(ART / "missing_source_acquisition_queue.csv")
    summary = json.loads((ART / "task_894_current_state_to_be_l1_seed_summary.json").read_text(encoding="utf-8"))

    if len(diagnosis) < 4:
        errors.append("diagnosis must cover universe, source_time, asof_decision_coverage, and l1_brain_seed")
    if len(coverage) != len(universe):
        errors.append("symbol coverage matrix must have exactly one row per universe symbol")
    if len({row["symbol"] for row in coverage}) != len(universe):
        errors.append("symbol coverage matrix contains duplicate or missing symbols")
    if len(decision_panel) != len(universe) * len(decisions):
        errors.append("decision coverage panel must equal decision_count * universe_symbols")
    if len(queue) != len(universe):
        errors.append("missing source acquisition queue must have one row per universe symbol")
    if not l1_states:
        errors.append("L1 seed state must not be empty")
    if l1_states and FORBIDDEN_TRADING_FIELDS & set(l1_states[0].keys()):
        errors.append("L1 seed state contains forbidden trading fields")

    seed_symbols = {row["symbol"] for row in coverage if row["coverage_state"] == "l1_seed_available"}
    missing_symbols = {row["symbol"] for row in coverage if row["coverage_state"] == "missing_l1_source_seed"}
    if seed_symbols & missing_symbols:
        errors.append("a symbol cannot be both seed_available and missing")
    if int(summary.get("universe_symbols_with_l1_seed", -1)) != len(seed_symbols):
        errors.append("summary seed symbol count mismatch")
    if int(summary.get("universe_symbols_missing_l1_seed", -1)) != len(missing_symbols):
        errors.append("summary missing symbol count mismatch")
    if summary.get("decision_symbol_rows") != len(decision_panel):
        errors.append("summary decision-symbol row count mismatch")
    if summary.get("brain_layer_status") != "L1_SOURCE_EVIDENCE_SEED_ONLY":
        errors.append("brain layer status must remain L1 seed only")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic-only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain FORBIDDEN")

    decision_asof_by_id = {row["decision_id"]: parse_ts(row["decision_asof_ts"]) for row in decisions}
    for row in l1_states:
        if row["brain_layer"] != "L1_SOURCE_EVIDENCE_SEED":
            errors.append("unexpected brain layer in L1 seed state")
            break
        if row["primitive_fact_state"] != "not_generated" or row["economic_meaning_state"] != "not_generated" or row["relation_state"] != "not_generated":
            errors.append("L1 seed state must not generate L2/L3 semantics")
            break
        if row["first_eligible_decision_id"]:
            decision_asof = decision_asof_by_id[row["first_eligible_decision_id"]]
            if decision_asof < parse_ts(row["available_to_brain_ts"]):
                errors.append("first eligible decision precedes evidence availability")
                break

    for row in decision_panel:
        count = int(row["available_l1_seed_count"])
        if (row["has_l1_seed"] == "1") != (count > 0):
            errors.append("decision panel has_l1_seed inconsistent with available count")
            break
        if "trade signal" not in row["does_not_mean"]:
            errors.append("decision panel missing does_not_mean guardrail")
            break

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_894_CURRENT_STATE_TO_BE_L1_SEED_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_894_CURRENT_STATE_TO_BE_L1_SEED_OK] current-state TO-BE L1 seed artifacts validated")


if __name__ == "__main__":
    main()
