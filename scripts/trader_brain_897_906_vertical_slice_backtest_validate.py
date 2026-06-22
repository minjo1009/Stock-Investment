from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_897_906_vertical_slice_backtest"

REQUIRED_FILES = [
    "task897_source_admission_audit.csv",
    "task897_906_front_gate_status.csv",
    "task897_primitive_fact_seed_panel.csv",
    "task902_source_time_provider_contract.csv",
    "task903_raw_source_reality_check.csv",
    "task898_economic_meaning_seed_panel.csv",
    "task899_relation_snapshot_panel.csv",
    "task900_candidate_thesis_packets.csv",
    "task901_dry_trader_decisions.csv",
    "task906_diagnostic_trade_specs.csv",
    "task906_diagnostic_replay_trades.csv",
    "task906_diagnostic_replay_periods.csv",
    "task906_split_summary.csv",
    "task897_906_stop_gate_status.csv",
    "task897_906_vertical_slice_backtest_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_NON_TRADE_COLUMNS = {"future_return", "realized_return", "pnl", "rank", "score", "position_size"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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

    admission = rows(ART / "task897_source_admission_audit.csv")
    front_gates = rows(ART / "task897_906_front_gate_status.csv")
    primitive = rows(ART / "task897_primitive_fact_seed_panel.csv")
    contract = rows(ART / "task902_source_time_provider_contract.csv")
    reality = rows(ART / "task903_raw_source_reality_check.csv")
    meaning = rows(ART / "task898_economic_meaning_seed_panel.csv")
    relations = rows(ART / "task899_relation_snapshot_panel.csv")
    candidates = rows(ART / "task900_candidate_thesis_packets.csv")
    decisions = rows(ART / "task901_dry_trader_decisions.csv")
    trade_specs = rows(ART / "task906_diagnostic_trade_specs.csv")
    replay_trades = rows(ART / "task906_diagnostic_replay_trades.csv")
    stop_gates = rows(ART / "task897_906_stop_gate_status.csv")
    summary = json.loads((ART / "task897_906_vertical_slice_backtest_summary.json").read_text(encoding="utf-8"))

    if len(admission) != 69:
        errors.append("source admission audit must contain 69 in-universe L1 seed rows")
    if any(row["can_enter_l2"] != "0" for row in admission):
        errors.append("current source admission audit must reject all L1 rows from L2")
    if {row["rejection_reason"] for row in admission} != {"raw_external_document_not_attached"}:
        errors.append("current rejection reason must be missing raw external source documents")
    if len(primitive) != 0:
        errors.append("primitive panel must be empty when source admission is no-go")
    if len(meaning) != 0:
        errors.append("meaning panel must be empty when source admission is no-go")
    if len(contract) != 280:
        errors.append("source-time provider contract must contain 70 symbols x source families")
    if len(reality) != 70:
        errors.append("raw source reality check must cover 70 symbols")
    if len(relations) != 0:
        errors.append("relation snapshots must be empty when source admission is no-go")
    if len(candidates) != 0:
        errors.append("candidate packets must be empty when source admission is no-go")
    if len(decisions) != 0:
        errors.append("dry decisions must be empty when source admission is no-go")
    if len(trade_specs) != 0:
        errors.append("trade specs must be empty when source admission is no-go")
    if len(replay_trades) != 0:
        errors.append("diagnostic replay trades must be empty when source admission is no-go")

    for name, panel in [
        ("primitive", primitive),
        ("meaning", meaning),
        ("relations", relations),
        ("candidates", candidates),
        ("decisions", decisions),
    ]:
        if not panel:
            continue
        forbidden = FORBIDDEN_NON_TRADE_COLUMNS & set(panel[0].keys())
        if forbidden:
            errors.append(f"{name} panel contains forbidden columns: {sorted(forbidden)}")

    for row in primitive:
        for field in ["source_span_ref", "source_span_excerpt", "as_of_ts", "deterministic_rule_id", "reproducibility_hash", "uncertainty"]:
            if not row[field]:
                errors.append(f"primitive missing {field}")
                break
        if errors:
            break
    for row in meaning:
        if row["meaning_authority"] != "provisional_internal_scope_only":
            errors.append("meaning rows must remain provisional internal scope")
            break
        if row["raw_source_linkage_state"] != "missing":
            errors.append("meaning rows must preserve missing raw source linkage")
            break
    for row in relations:
        if row["relation_authority"] != "provisional_below_raw_source_linkage_threshold":
            errors.append("relations must remain provisional below raw source threshold")
            break
        if datetime.fromisoformat(row["edge_asof_ts"].replace("Z", "+00:00")) > datetime.fromisoformat(row["decision_asof_ts"].replace("Z", "+00:00")):
            errors.append("relation edge_asof exceeds decision_asof")
            break
    for row in candidates:
        if row["adapter_eligible"] != "0":
            errors.append("candidate packets must not be adapter eligible")
            break
    for row in decisions:
        if row["decision_authority"] != "dry_review_only_provisional":
            errors.append("decisions must remain dry review-only provisional")
            break
    for row in trade_specs:
        if row["trade_spec_authority"] != "DIAGNOSTIC_PROVISIONAL_BRAIN_SLICE_ONLY":
            errors.append("trade specs must remain diagnostic provisional")
            break
    for row in replay_trades:
        if not row["entry_date"] < row["exit_date"]:
            errors.append("replay trade entry_date must precede exit_date")
            break
        if row["authority"] != "DIAGNOSTIC_PROVISIONAL_BRAIN_SLICE_ONLY":
            errors.append("replay trades must remain diagnostic provisional")
            break

    front_status = {row["gate"]: row["status"] for row in front_gates}
    if front_status.get("raw_external_source_attached_for_l2") != "fail":
        errors.append("front gate must fail when no raw external source is attached")
    if front_status.get("previous_replay_result_validity") != "invalidated":
        errors.append("previous replay result must be explicitly invalidated")
    gate_status = {row["gate"]: row["status"] for row in stop_gates}
    if gate_status.get("source_admission_for_l2") != "fail_front_gate_no_go":
        errors.append("source admission gate must fail no-go")
    if gate_status.get("diagnostic_replay_allowed") != "not_run_front_gate_no_go":
        errors.append("diagnostic replay must be not-run under front-gate no-go")
    if summary.get("raw_source_linkage_rate") != 0.0:
        errors.append("raw source linkage rate must remain 0.0")
    if summary.get("front_gate_status") != "no_go_missing_raw_external_source":
        errors.append("summary must record front gate no-go")
    if summary.get("replay_status") != "not_run_front_gate_no_go":
        errors.append("summary must record replay not-run")
    if summary.get("invalidated_previous_replay_result") is not True:
        errors.append("summary must invalidate previous replay result")
    if summary.get("primitive_fact_rows") != 0 or summary.get("diagnostic_trade_spec_rows") != 0:
        errors.append("summary must keep primitive and trade spec counts at zero")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic-only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain FORBIDDEN")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_897_906_VERTICAL_SLICE_BACKTEST_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_897_906_VERTICAL_SLICE_BACKTEST_OK] vertical slice backtest artifacts validated")


if __name__ == "__main__":
    main()
