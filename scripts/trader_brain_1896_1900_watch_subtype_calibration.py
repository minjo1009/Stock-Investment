from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1878 = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
TASK1886 = ROOT / "data/artifacts/task_1886_1895_desk_replay_detailed_analysis"
OUT_DIR = ROOT / "data/artifacts/task_1896_1900_watch_subtype_calibration"
REPORT_DIR = ROOT / "docs/reports/task_1896_1900_watch_subtype_calibration"
REPORT = REPORT_DIR / "task_1896_1900_watch_subtype_calibration.md"
DECISION = REPORT_DIR / "task_1896_1900_decision.csv"

AUTHORITY = "DIAGNOSTIC_WATCH_SUBTYPE_CALIBRATION_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("policy_delta_trade_join", TASK1886 / "task1887_policy_delta_trade_join.csv"),
        ("desk_specific_budget", TASK1878 / "task1884_l5_desk_specific_budget.csv"),
        ("winner_thesis_override", TASK1878 / "task1879_winner_thesis_override_panel.csv"),
        ("sec_financing_specificity", TASK1878 / "task1878_sec_financing_specificity_panel.csv"),
        ("l2_sleeve_meaning", TASK1808 / "task1812_l2_sleeve_meaning_panel.csv"),
        ("watch_analysis_closeout", TASK1886 / "task1895_closeout.csv"),
    ]
    return [
        {
            "task_id": "Task1896",
            "input_manifest_id": f"WATCHINPUT-1896-{idx:03d}",
            "input_name": name,
            "input_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def load_maps() -> tuple[
    list[dict[str, str]],
    dict[tuple[str, str], dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    joined = read_csv(TASK1886 / "task1887_policy_delta_trade_join.csv")
    meaning = {
        (row["target_policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1808 / "task1812_l2_sleeve_meaning_panel.csv")
    }
    winner = {row["trade_spec_id"]: row for row in read_csv(TASK1878 / "task1879_winner_thesis_override_panel.csv")}
    sec = {row["trade_spec_id"]: row for row in read_csv(TASK1878 / "task1878_sec_financing_specificity_panel.csv")}
    return joined, meaning, winner, sec


def source_policy_from_desk(policy_variant_id: str) -> str:
    return "winner_defense_budget_top3_v1" if policy_variant_id.endswith("top3_v1") else "winner_defense_budget_top5_v1"


def classify_watch(
    row: dict[str, str],
    meaning: dict[str, str],
    winner: dict[str, str],
    sec: dict[str, str],
) -> tuple[str, str, str, str]:
    quality = to_float(winner.get("winner_quality_beta", meaning.get("winner_quality_beta")))
    sleeve_quality = to_float(winner.get("sleeve_quality_score", meaning.get("sleeve_quality_score")))
    payoff = to_float(winner.get("payoff_quality_score", meaning.get("payoff_quality_score")))
    rel = to_float(meaning.get("relative_return_63d"))
    prior = to_float(meaning.get("prior_return_63d"))
    drawdown = to_float(meaning.get("prior_drawdown_126d"))
    volatility = winner.get("volatility_cause", meaning.get("volatility_cause", ""))
    expectation = meaning.get("expectation_state", "")
    absorption = meaning.get("absorption_state", "")
    breadth = row.get("theme_breadth_state", "")
    financing = row.get("financing_specificity_state", "")
    live_flag = sec.get("live_terms_detected_flag", "0")
    current_flag = sec.get("financing_current_flag", "0")
    source_gap_like = any(
        "source_gap" in value
        for value in [
            financing,
            expectation,
            absorption,
            meaning.get("materiality_state", ""),
            meaning.get("source_independence_state", ""),
        ]
    )
    strong_winner = (
        quality >= 68.0
        and sleeve_quality >= 50.0
        and payoff >= 68.0
        and volatility in {"leader_momentum_volatility", "normal_winner_volatility", "ordinary_noise"}
        and expectation in {"true_surprise_proxy", "good_words_only", "guidance_change_proxy"}
        and absorption in {"accepted_underreaction_or_followthrough", "initial_reaction_only", "sustained_market_acceptance"}
    )
    upgrade_ready = (
        quality >= 85.0
        and sleeve_quality >= 65.0
        and payoff >= 90.0
        and rel > 0.10
        and breadth == "theme_breadth_supportive"
        and financing in {"boilerplate_or_sparse", "historical_or_closed_financing", ""}
    )
    normal_vol = (
        strong_winner
        and financing not in {"live_active_dilution"}
        and prior > 0.0
        and drawdown > -0.35
    )
    if financing == "live_active_dilution" and (live_flag == "1" or current_flag == "1"):
        return "damage_watch", "reduce_or_cap_until_live_financing_clears", "live_current_financing_or_dilution_detected", "replay_candidate_only_after_live_terms_precision"
    if upgrade_ready:
        return "upgrade_candidate_watch", "restore_full_hold_candidate", "quality_payoff_breadth_and_relative_strength_support_rerisk", "eligible_for_next_frozen_replay"
    if normal_vol:
        return "normal_winner_volatility_watch", "hold_full_or_near_full", "winner_quality_intact_and_volatility_is_normal", "eligible_for_next_frozen_replay"
    if financing == "shelf_capacity_watch":
        return "overhang_watch", "cap_not_exit", "shelf_capacity_without_live_terms", "needs_live_dilution_precision_upgrade"
    if source_gap_like:
        return "information_gap_watch", "small_hold_and_source_request", "source_gap_is_unknown_not_negative", "needs_source_request_not_bearish_score"
    if quality < 60.0 or payoff < 62.0 or expectation == "negative_expectation_proxy":
        return "damage_watch", "reduce_or_no_rerisk", "quality_or_expectation_not_sufficient_for_winner_hold", "not_replay_upgrade_candidate"
    return "overhang_watch", "cap_not_exit", "mixed_watch_without_confirmed_thesis_break", "needs_subtype_review"


def watch_subtype_rows() -> list[dict[str, object]]:
    joined, meaning_map, winner_map, sec_map = load_maps()
    rows = []
    idx = 1
    for row in joined:
        if row["strategy_sleeve"] != "winner_compounder" or row["desk_action"] != "watch":
            continue
        source_policy = source_policy_from_desk(row["policy_variant_id"])
        meaning = meaning_map.get((source_policy, row["trade_spec_id"]), {})
        winner = winner_map.get(row["trade_spec_id"], {})
        sec = sec_map.get(row["trade_spec_id"], {})
        subtype, recommended_action, reason, replay_gate = classify_watch(row, meaning, winner, sec)
        rows.append(
            {
                "task_id": "Task1896",
                "watch_subtype_id": f"WATCHSUBTYPE-1896-{idx:06d}",
                "policy_variant_id": row["policy_variant_id"],
                "slot_group": row["slot_group"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "desk_action": row["desk_action"],
                "watch_subtype": subtype,
                "recommended_next_action": recommended_action,
                "subtype_reason": reason,
                "next_replay_gate": replay_gate,
                "desk_thesis_state": row["desk_thesis_state"],
                "winner_quality_beta": winner.get("winner_quality_beta", meaning.get("winner_quality_beta", "")),
                "sleeve_quality_score": winner.get("sleeve_quality_score", meaning.get("sleeve_quality_score", "")),
                "payoff_quality_score": winner.get("payoff_quality_score", meaning.get("payoff_quality_score", "")),
                "volatility_cause": winner.get("volatility_cause", meaning.get("volatility_cause", "")),
                "expectation_state": meaning.get("expectation_state", ""),
                "absorption_state": meaning.get("absorption_state", ""),
                "relative_return_63d": meaning.get("relative_return_63d", ""),
                "prior_return_63d": meaning.get("prior_return_63d", ""),
                "prior_drawdown_126d": meaning.get("prior_drawdown_126d", ""),
                "financing_specificity_state": row["financing_specificity_state"],
                "live_terms_detected_flag": sec.get("live_terms_detected_flag", ""),
                "financing_current_flag": sec.get("financing_current_flag", ""),
                "offering_type": sec.get("offering_type", ""),
                "remaining_capacity_state": sec.get("remaining_capacity_state", ""),
                "theme_breadth_state": row["theme_breadth_state"],
                "baseline_multiplier": row["baseline_multiplier"],
                "desk_multiplier": row["desk_multiplier"],
                "baseline_pnl_audit_only": row["baseline_pnl_audit_only"],
                "desk_pnl_audit_only": row["desk_pnl_audit_only"],
                "desk_delta_vs_baseline_pnl_audit_only": row["desk_delta_vs_baseline_pnl_audit_only"],
                "desk_delta_vs_source_attached_pnl_audit_only": row["desk_delta_vs_source_attached_pnl_audit_only"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def group_rows(rows: list[dict[str, object]], fields: list[str], task_id: str, prefix: str) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(field, "")) for field in fields)].append(row)
    out = []
    for idx, (key, items) in enumerate(sorted(grouped.items()), 1):
        out.append(
            {
                "task_id": task_id,
                "analysis_id": f"{prefix}-{idx:05d}",
                **{field: value for field, value in zip(fields, key)},
                "row_count": len(items),
                "baseline_pnl_sum_audit_only": round(sum(to_float(row["baseline_pnl_audit_only"]) for row in items), 4),
                "desk_pnl_sum_audit_only": round(sum(to_float(row["desk_pnl_audit_only"]) for row in items), 4),
                "desk_delta_vs_baseline_sum_audit_only": round(sum(to_float(row["desk_delta_vs_baseline_pnl_audit_only"]) for row in items), 4),
                "desk_delta_vs_source_attached_sum_audit_only": round(sum(to_float(row["desk_delta_vs_source_attached_pnl_audit_only"]) for row in items), 4),
                "restore_full_hold_candidate_count": sum(1 for row in items if row["recommended_next_action"] == "restore_full_hold_candidate"),
                "damage_watch_count": sum(1 for row in items if row["watch_subtype"] == "damage_watch"),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def live_dilution_precision_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    live_rows = [row for row in rows if row["financing_specificity_state"] == "live_active_dilution"]
    for idx, row in enumerate(live_rows, 1):
        offering = str(row["offering_type"])
        quality = to_float(row["winner_quality_beta"])
        rel = to_float(row["relative_return_63d"])
        if offering in {"at_the_market", "convertible_debt", "warrants_units"}:
            precision_state = "hard_live_financing_risk"
            action = "keep_damage_watch"
        elif offering == "common_stock_offering" and rel > 0 and quality >= 75:
            precision_state = "current_common_offering_but_winner_quality_offsets"
            action = "manual_precision_review_before_damage_watch"
        else:
            precision_state = "live_financing_needs_filing_item_precision"
            action = "manual_precision_review"
        out.append(
            {
                "task_id": "Task1898",
                "live_dilution_precision_id": f"LIVEDILPREC-1898-{idx:05d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "watch_subtype": row["watch_subtype"],
                "offering_type": offering,
                "live_terms_detected_flag": row["live_terms_detected_flag"],
                "financing_current_flag": row["financing_current_flag"],
                "winner_quality_beta": row["winner_quality_beta"],
                "relative_return_63d": row["relative_return_63d"],
                "precision_state": precision_state,
                "recommended_precision_action": action,
                "desk_delta_vs_baseline_pnl_audit_only": row["desk_delta_vs_baseline_pnl_audit_only"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def speculative_block_rows() -> list[dict[str, object]]:
    joined = read_csv(TASK1886 / "task1887_policy_delta_trade_join.csv")
    rows = []
    idx = 1
    for row in joined:
        if row["strategy_sleeve"] != "speculative_event" or row["desk_action"] != "no_entry":
            continue
        prevented_loss = "1" if to_float(row["desk_delta_vs_baseline_pnl_audit_only"]) > 0 else "0"
        rows.append(
            {
                "task_id": "Task1899",
                "speculative_block_audit_id": f"SPECBLOCK-1899-{idx:05d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "financing_specificity_state": row["financing_specificity_state"],
                "theme_breadth_state": row["theme_breadth_state"],
                "baseline_pnl_audit_only": row["baseline_pnl_audit_only"],
                "desk_pnl_audit_only": row["desk_pnl_audit_only"],
                "desk_delta_vs_baseline_pnl_audit_only": row["desk_delta_vs_baseline_pnl_audit_only"],
                "block_prevented_loss_audit_only": prevented_loss,
                "audit_interpretation": "block_helped_audit_only" if prevented_loss == "1" else "block_removed_optional_payoff_audit_only",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def hold_calibration_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("damage_watch", "reduce_or_cap_until_live_financing_clears", "live current financing, confirmed thesis break, or negative expectation", "not_eligible_for_rerisk"),
        ("normal_winner_volatility_watch", "hold_full_or_near_full", "quality/payoff intact, no live financing, volatility is normal winner volatility", "eligible_for_frozen_replay"),
        ("information_gap_watch", "small_hold_and_source_request", "source gap means unknown, not bearish", "requires_source_fill_before_rerisk"),
        ("overhang_watch", "cap_not_exit", "shelf or mixed overhang without confirmed thesis break", "eligible_only_after_precision_review"),
        ("upgrade_candidate_watch", "restore_full_hold_candidate", "quality/payoff/breadth/relative strength align and no live damage", "eligible_for_frozen_replay"),
    ]
    return [
        {
            "task_id": "Task1900",
            "hold_calibration_rule_id": f"HOLDCAL-1900-{idx:03d}",
            "watch_subtype": subtype,
            "calibrated_action": action,
            "entry_condition": condition,
            "next_replay_gate": gate,
            "policy_freeze_state": "preregistered_no_replay_executed",
            "forbidden_fields": "future_price/future_return/pnl/drawdown/outcome_label",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (subtype, action, condition, gate) in enumerate(rows, 1)
    ]


def subtype_decision_rows(subtypes: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(row["watch_subtype"]) for row in subtypes)
    upgrade_count = counts["upgrade_candidate_watch"] + counts["normal_winner_volatility_watch"]
    damage_count = counts["damage_watch"]
    return [
        {
            "task_id": "Task1900",
            "decision": "watch_subtype_calibration_complete_no_replay",
            "watch_rows": len(subtypes),
            "upgrade_or_full_hold_candidate_rows": upgrade_count,
            "damage_watch_rows": damage_count,
            "primary_result": "watch_is_not_one_state_anymore",
            "next_action": "run one frozen replay only after reviewing upgrade candidates and live dilution precision rows",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    subtype_attr: list[dict[str, object]],
    policy_attr: list[dict[str, object]],
    live_precision: list[dict[str, object]],
    speculative: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sorted_subtypes = sorted(subtype_attr, key=lambda row: to_float(row["desk_delta_vs_baseline_sum_audit_only"]))
    lines = [
        "# Task1896-1900 Watch Subtype Calibration",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['decision']}`.",
        f"- Watch rows classified: {closeout['watch_rows']}.",
        f"- Upgrade/full-hold candidate rows: {closeout['upgrade_or_full_hold_candidate_rows']}.",
        f"- Damage watch rows: {closeout['damage_watch_rows']}.",
        "- No replay was executed in this task.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "What changed:",
        "",
        "- `watch` is now split into damage, normal winner volatility, information gap, overhang, and upgrade candidate states.",
        "- Subtype assignment uses as-of quality, payoff, volatility cause, expectation, absorption, financing specificity, and breadth fields.",
        "- PnL deltas are attached only for audit and are forbidden from assignment.",
        "- Hold calibration was preregistered but not replayed.",
        "",
        "| Watch subtype | Rows | Desk PnL | Baseline PnL | Delta vs Baseline | Delta vs Source | Restore Candidates | Damage Count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted_subtypes:
        lines.append(
            f"| `{row['watch_subtype']}` | {row['row_count']} | {row['desk_pnl_sum_audit_only']} | {row['baseline_pnl_sum_audit_only']} | {row['desk_delta_vs_baseline_sum_audit_only']} | {row['desk_delta_vs_source_attached_sum_audit_only']} | {row['restore_full_hold_candidate_count']} | {row['damage_watch_count']} |"
        )
    lines.extend(["", "Policy-level watch subtype split:", "", "| Policy | Subtype | Rows | Delta vs Baseline |", "| --- | --- | ---: | ---: |"])
    for row in sorted(policy_attr, key=lambda item: (str(item["policy_variant_id"]), str(item["watch_subtype"]))):
        lines.append(f"| `{row['policy_variant_id']}` | `{row['watch_subtype']}` | {row['row_count']} | {row['desk_delta_vs_baseline_sum_audit_only']} |")
    live_loss = sum(to_float(row["desk_delta_vs_baseline_pnl_audit_only"]) for row in live_precision)
    spec_loss = sum(to_float(row["desk_delta_vs_baseline_pnl_audit_only"]) for row in speculative)
    lines.extend(
        [
            "",
            "Specific audits:",
            "",
            f"- Live dilution precision rows: {len(live_precision)}, audit delta vs baseline: {round(live_loss, 4)}.",
            f"- Speculative no-entry rows: {len(speculative)}, audit delta vs baseline: {round(spec_loss, 4)}.",
            "",
            "Interpretation:",
            "",
            "- If watch is `damage_watch`, the brain should stay defensive.",
            "- If watch is `normal_winner_volatility_watch` or `upgrade_candidate_watch`, the next frozen replay can test restoring full hold.",
            "- If watch is `information_gap_watch`, the answer is source fill, not bearish scoring.",
            "- If watch is `overhang_watch`, the answer is cap/precision review, not automatic exit.",
            "",
            "Leakage audit:",
            "",
            "- No price matching was introduced.",
            "- No replay was executed.",
            "- Outcome deltas are audit-only.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Watch is no longer one bucket.",
            "2. Some watch rows are real danger.",
            "3. Some watch rows are winners that should probably be held harder.",
            "4. Some watch rows are just missing information.",
            "5. Next replay should only test the preregistered restore/full-hold candidates.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1896_input_manifest.csv`",
            "- `task1896_watch_subtype_panel.csv`",
            "- `task1897_watch_subtype_attribution.csv`",
            "- `task1898_live_dilution_precision_panel.csv`",
            "- `task1899_speculative_block_payoff_audit.csv`",
            "- `task1900_hold_calibration_contract.csv`",
            "- `task1900_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1896_1900_watch_subtype_calibration_validate.py`",
            "- `python scripts/task_registry_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    subtypes = watch_subtype_rows()
    subtype_attr = group_rows(subtypes, ["watch_subtype"], "Task1897", "WATCHATTR-1897")
    policy_attr = group_rows(subtypes, ["policy_variant_id", "watch_subtype"], "Task1897", "WATCHPOLICY-1897")
    action_attr = group_rows(subtypes, ["recommended_next_action", "watch_subtype"], "Task1897", "WATCHACTION-1897")
    live_precision = live_dilution_precision_rows(subtypes)
    speculative = speculative_block_rows()
    hold_contract = hold_calibration_contract_rows()
    closeout = subtype_decision_rows(subtypes)
    outputs = [
        ("task1896_input_manifest.csv", input_manifest_rows()),
        ("task1896_watch_subtype_panel.csv", subtypes),
        ("task1897_watch_subtype_attribution.csv", subtype_attr),
        ("task1897_watch_policy_attribution.csv", policy_attr),
        ("task1897_watch_action_attribution.csv", action_attr),
        ("task1898_live_dilution_precision_panel.csv", live_precision),
        ("task1899_speculative_block_payoff_audit.csv", speculative),
        ("task1900_hold_calibration_contract.csv", hold_contract),
        ("task1900_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1900_closeout.json", closeout[0])
    write_report(subtype_attr, policy_attr, live_precision, speculative, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1896_1900] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
