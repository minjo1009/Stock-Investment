from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_961_970_external_audit_redesign"
FEATURE_PATH = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay/task941_selection_feature_panel.csv"
BASELINE_TRADES_PATH = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay/task943_slot_capped_replay_trades.csv"

REQUIRED_FILES = [
    "task961_baseline_winner_loser_semantic_audit.csv",
    "task962_weakness_semantic_reclassification.csv",
    "task963_asof_duplicate_thesis_meaning_ledger.csv",
    "task964_source_gap_limitation_ledger.csv",
    "task965_stale_thesis_duration_audit.csv",
    "task966_theme_macro_policy_timing_interpreter.csv",
    "task967_trader_action_taxonomy.csv",
    "task968_cohort_attrition_ledger.csv",
    "task968_reason_marginal_attribution.csv",
    "task969_shadow_trader_ranking.csv",
    "task969_shadow_vs_baseline_comparison.csv",
    "task970_external_audit_closeout.csv",
    "task970_source_manifest.csv",
    "task961_970_external_audit_redesign_summary.csv",
    "task961_970_external_audit_redesign_summary.json",
    "artifact_manifest.csv",
]

ALLOWED_SEMANTIC_CLASSES = {
    "bad",
    "data_limitation",
    "structural_thesis",
    "conviction_repeat",
    "timing_issue",
    "unknown",
}
ALLOWED_ACTIONS = {"enter", "wait", "reduce_priority", "substitute", "monitor", "hard_block"}
ALLOWED_HARD_BLOCK_REASONS = {
    "future_evidence",
    "missing_required_lineage",
    "source_backed_invalidation",
}
STANDALONE_NON_BLOCK_FLAGS = {
    "source_gap_heavy",
    "stale_source",
    "duplicate_thesis",
    "thin_packet",
    "low_independent_evidence",
}
FORBIDDEN_OUTCOME_INPUTS = {
    "future_return",
    "realized_return",
    "pnl",
    "post_entry_price_change",
    "outcome_rank",
}


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

    features = rows(FEATURE_PATH)
    feature_ids = {row["trade_spec_id"] for row in features}
    baseline_trades = [row for row in rows(BASELINE_TRADES_PATH) if row["slot_cap"] == "10"]
    task961 = rows(ART / "task961_baseline_winner_loser_semantic_audit.csv")
    task962 = rows(ART / "task962_weakness_semantic_reclassification.csv")
    task963 = rows(ART / "task963_asof_duplicate_thesis_meaning_ledger.csv")
    task964 = rows(ART / "task964_source_gap_limitation_ledger.csv")
    task965 = rows(ART / "task965_stale_thesis_duration_audit.csv")
    task966 = rows(ART / "task966_theme_macro_policy_timing_interpreter.csv")
    task967 = rows(ART / "task967_trader_action_taxonomy.csv")
    task968 = rows(ART / "task968_cohort_attrition_ledger.csv")
    reason = rows(ART / "task968_reason_marginal_attribution.csv")
    ranking = rows(ART / "task969_shadow_trader_ranking.csv")
    comparison = rows(ART / "task969_shadow_vs_baseline_comparison.csv")
    closeout = rows(ART / "task970_external_audit_closeout.csv")
    source_manifest = rows(ART / "task970_source_manifest.csv")
    summary = json.loads((ART / "task961_970_external_audit_redesign_summary.json").read_text(encoding="utf-8"))

    panel_by_id = {
        "task963": {row["trade_spec_id"] for row in task963},
        "task964": {row["trade_spec_id"] for row in task964},
        "task965": {row["trade_spec_id"] for row in task965},
        "task966": {row["trade_spec_id"] for row in task966},
        "task967": {row["trade_spec_id"] for row in task967},
        "reason": {row["trade_spec_id"] for row in reason},
        "ranking": {row["trade_spec_id"] for row in ranking},
    }
    for name, ids in panel_by_id.items():
        if ids != feature_ids:
            errors.append(f"{name} must cover every feature trade_spec_id")

    if len(task961) != len(baseline_trades):
        errors.append("Task961 audit must cover every Task941 slot10 baseline trade")
    for row in task961:
        if row["pnl_use_mode"] != "evaluation_only_never_selection_input":
            errors.append("Task961 PnL must be evaluation-only")
            break

    for row in task962:
        if row["weakness_semantic_class"] not in ALLOWED_SEMANTIC_CLASSES:
            errors.append("Task962 has invalid semantic class")
            break
        if row["use_mode"] != "diagnostic_only":
            errors.append("Task962 weakness flags must be diagnostic_only")
            break
        if row["weakness_flag"] in STANDALONE_NON_BLOCK_FLAGS and row["standalone_hard_block_allowed"] != "0":
            errors.append("weakness flag was allowed as standalone hard block")
            break
        if not FORBIDDEN_OUTCOME_INPUTS <= set(row["does_not_use"].split()):
            errors.append("Task962 must explicitly exclude future outcome fields")
            break

    seen_by_cluster: dict[str, int] = {}
    last_sort_key = ""
    for row in task963:
        sort_key = row["prior_only_sort_key"]
        if sort_key < last_sort_key:
            errors.append("Task963 duplicate ledger is not as-of sorted")
            break
        last_sort_key = sort_key
        cluster = row["thesis_cluster_key"]
        expected = seen_by_cluster.get(cluster, 0)
        if int(row["prior_duplicate_count"]) != expected:
            errors.append("Task963 prior duplicate count is not prior-only")
            break
        seen_by_cluster[cluster] = expected + 1
        if row["standalone_hard_block_allowed"] != "0":
            errors.append("Task963 duplicate cannot be standalone hard block")
            break

    for row in task964:
        if row["blocks_trade"] != "0" or row["standalone_hard_block_allowed"] != "0":
            errors.append("Task964 source gap must not block trade by itself")
            break

    for row in task965:
        if row["stale_is_standalone_hard_block"] != "0":
            errors.append("Task965 stale source must not be standalone hard block")
            break

    for row in task966:
        if row["direction_effect"] == "buy" or row["direction_effect"] == "sell":
            errors.append("Task966 expert lens must not produce buy/sell direction")
            break

    for row in task967:
        if row["trader_action"] not in ALLOWED_ACTIONS:
            errors.append("Task967 invalid trader action")
            break
        if row["trader_action"] == "hard_block":
            if row["hard_block_reason"] not in ALLOWED_HARD_BLOCK_REASONS:
                errors.append("Task967 hard block reason is not allowed")
                break
            if row["hard_block_reason"] in set(row["weakness_flags"].split(";")):
                errors.append("Task967 used weakness flag as hard block reason")
                break

    for row in task968:
        if row["replay_executed"] != "0":
            errors.append("Task968 must not execute replay")
            break
        if int(row["shadow_selected_count"]) > 10:
            errors.append("Task968 shadow selection exceeds slot10")
            break
        if int(row["candidate_count_before"]) != int(row["hard_blocked_count"]) + int(row["ranked_count"]):
            errors.append("Task968 attrition counts do not reconcile")
            break

    selected_by_date: dict[str, int] = {}
    for row in ranking:
        if row["changes_executed_trade"] != "0":
            errors.append("Task969 shadow ranking changed executed trades")
            break
        if not FORBIDDEN_OUTCOME_INPUTS <= set(row["does_not_use"].split()):
            errors.append("Task969 must explicitly exclude future outcome fields")
            break
        for forbidden_column in ["pnl", "return_pct", "outcome_rank", "realized_return"]:
            if forbidden_column in row:
                errors.append(f"Task969 ranking contains forbidden outcome column {forbidden_column}")
                break
        if errors and errors[-1].startswith("Task969 ranking contains"):
            break
        if row["shadow_slot10_selected"] == "1":
            selected_by_date[row["entry_date"]] = selected_by_date.get(row["entry_date"], 0) + 1
    if any(count > 10 for count in selected_by_date.values()):
        errors.append("Task969 shadow selected more than 10 rows for an entry date")

    if len(comparison) != 1:
        errors.append("Task969 comparison must have one row")
    else:
        row = comparison[0]
        if row["replay_executed"] != "0":
            errors.append("Task969 comparison must record no replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("Task969 comparison changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("Task969 comparison changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("Task969 comparison changed real capital")

    if len(closeout) != 1:
        errors.append("Task970 closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0" or row["next_replay_allowed"] != "0":
            errors.append("Task970 must close with replay still blocked")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("Task970 closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("Task970 closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("Task970 closeout changed real capital")

    if summary.get("replay_executed") != "0":
        errors.append("summary must record no replay")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary changed strategy acceptance")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary changed deployment readiness")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary changed real capital")
    for key in [
        "source_gap_heavy_is_standalone_block",
        "duplicate_is_standalone_block",
        "stale_is_standalone_block",
        "thin_packet_is_standalone_block",
        "low_independent_evidence_is_standalone_block",
    ]:
        if summary.get(key) != "0":
            errors.append(f"summary allows forbidden standalone block: {key}")

    for source in source_manifest:
        if not (ROOT / source["path"]).exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_961_970_EXTERNAL_AUDIT_REDESIGN_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_961_970_EXTERNAL_AUDIT_REDESIGN_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
