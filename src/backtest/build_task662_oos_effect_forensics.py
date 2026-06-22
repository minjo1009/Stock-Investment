from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task638_content_signal_refinement import simulate_account
from src.backtest.build_task661_mechanism_relation_engine import (
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    candidate_panels,
    load_task659_panel,
)


TASK_ID = "Task662"
REPORT_DIR = Path("docs/reports/task_662_oos_effect_forensics")
TASK659_PANEL = Path("docs/reports/task_659_theme_specific_relation_engine/theme_macro_company_state_panel.csv")


def build_task662_oos_effect_forensics(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    reach = build_action_reach(panel)
    accepted_delta = build_accepted_delta(panel)
    winner_cut = build_winner_cut_audit(panel)
    decision = build_decision(reach, accepted_delta, winner_cut)
    pass_fail = build_pass_fail(reach, accepted_delta, winner_cut)

    reach.to_csv(out_dir / "task662_oos_action_reach.csv", index=False, encoding="utf-8-sig")
    accepted_delta.to_csv(out_dir / "task662_candidate_accepted_delta.csv", index=False, encoding="utf-8-sig")
    winner_cut.to_csv(out_dir / "task662_winner_cut_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_662_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_662_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, reach, accepted_delta, winner_cut, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "reach": reach,
        "accepted_delta": accepted_delta,
        "winner_cut": winner_cut,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_action_reach(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["validation", "recent_oos"]:
        split = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        base = candidate_panels(split)["baseline_task639_core"]
        _, accepted = simulate_account(base, "equal_max5")
        accepted_ids = set(accepted["lifecycle_id"].astype(str)) if not accepted.empty else set()
        action_counts = base.groupby("candidate_action_family").size().to_dict()
        accepted_action_counts = accepted.groupby("candidate_action_family").size().to_dict() if not accepted.empty else {}
        rows.append(
            {
                "split_name": split_name,
                "task639_core_rows": int(len(base)),
                "baseline_accepted_count": int(len(accepted)),
                "baseline_allowed_rows": int(action_counts.get("BASELINE_ALLOWED", 0)),
                "reduce_duration_rows": int(action_counts.get("REDUCE_DURATION", 0)),
                "strength_hold_candidate_rows": int(action_counts.get("STRENGTH_HOLD_CANDIDATE", 0)),
                "confirmation_required_rows": int(action_counts.get("CONFIRMATION_REQUIRED", 0)),
                "research_only_rows": int(action_counts.get("RESEARCH_ONLY", 0)),
                "baseline_allowed_accepted": int(accepted_action_counts.get("BASELINE_ALLOWED", 0)),
                "reduce_duration_accepted": int(accepted_action_counts.get("REDUCE_DURATION", 0)),
                "strength_hold_candidate_accepted": int(accepted_action_counts.get("STRENGTH_HOLD_CANDIDATE", 0)),
                "confirmation_required_accepted": int(accepted_action_counts.get("CONFIRMATION_REQUIRED", 0)),
                "accepted_trade_ids_with_action_count": int(
                    len(
                        set(
                            base[
                                base["candidate_action_family"].isin(
                                    ["REDUCE_DURATION", "STRENGTH_HOLD_CANDIDATE", "CONFIRMATION_REQUIRED"]
                                )
                            ]["lifecycle_id"].astype(str)
                        ).intersection(accepted_ids)
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def build_accepted_delta(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["validation", "recent_oos"]:
        split = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        candidates = candidate_panels(split)
        _, base_accepted = simulate_account(candidates["baseline_task639_core"], "equal_max5")
        base_map = accepted_map(base_accepted)
        for candidate_name, candidate_panel in candidates.items():
            if candidate_name == "baseline_task639_core":
                continue
            quality, accepted = simulate_account(candidate_panel, "equal_max5")
            cand_map = accepted_map(accepted)
            common = sorted(set(base_map).intersection(cand_map))
            modified = [
                lifecycle_id
                for lifecycle_id in common
                if base_map[lifecycle_id]["timing_mode"] != cand_map[lifecycle_id]["timing_mode"]
                or base_map[lifecycle_id]["exit_mode"] != cand_map[lifecycle_id]["exit_mode"]
            ]
            base_common = sum(float(base_map[i]["net_return_from_entry"]) for i in common)
            cand_common = sum(float(cand_map[i]["net_return_from_entry"]) for i in common)
            rows.append(
                {
                    "candidate_name": candidate_name,
                    "split_name": split_name,
                    "baseline_accepted_count": int(len(base_map)),
                    "candidate_accepted_count": int(len(cand_map)),
                    "common_accepted_count": int(len(common)),
                    "modified_common_accepted_count": int(len(modified)),
                    "added_accepted_count": int(len(set(cand_map).difference(base_map))),
                    "removed_accepted_count": int(len(set(base_map).difference(cand_map))),
                    "common_return_delta_pct_point_sum": float((cand_common - base_common) * 100.0),
                    "candidate_capital_pnl_pct": float(quality["capital_pnl_pct"]),
                    "candidate_max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "candidate_entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                    "effect_summary": effect_summary(len(modified), cand_common - base_common, len(set(cand_map).difference(base_map)), len(set(base_map).difference(cand_map))),
                }
            )
    return pd.DataFrame(rows)


def accepted_map(accepted: pd.DataFrame) -> dict[str, dict[str, object]]:
    if accepted.empty:
        return {}
    cols = ["lifecycle_id", "symbol", "timing_mode", "exit_mode", "net_return_from_entry", "theme_id", "candidate_action_family"]
    return accepted[cols].drop_duplicates("lifecycle_id").set_index("lifecycle_id").to_dict(orient="index")


def effect_summary(modified_count: int, return_delta: float, added_count: int, removed_count: int) -> str:
    if modified_count == 0 and added_count == 0 and removed_count == 0:
        return "no_accepted_trade_effect"
    if return_delta < 0:
        return "accepted_winners_cut_or_returns_reduced"
    if added_count > removed_count:
        return "capacity_released_adds_trades"
    return "accepted_trade_effect_mixed"


def build_winner_cut_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["validation", "recent_oos"]:
        split = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        candidates = candidate_panels(split)
        _, base_accepted = simulate_account(candidates["baseline_task639_core"], "equal_max5")
        base_map = accepted_map(base_accepted)
        for candidate_name in ["mechanism_strength_hold20", "mechanism_combo_hold5_confirm_strength20", "mechanism_any_action_hold5"]:
            if candidate_name not in candidates:
                continue
            _, accepted = simulate_account(candidates[candidate_name], "equal_max5")
            cand_map = accepted_map(accepted)
            for lifecycle_id in sorted(set(base_map).intersection(cand_map)):
                base_row = base_map[lifecycle_id]
                cand_row = cand_map[lifecycle_id]
                if base_row["timing_mode"] == cand_row["timing_mode"] and base_row["exit_mode"] == cand_row["exit_mode"]:
                    continue
                base_return = float(base_row["net_return_from_entry"])
                cand_return = float(cand_row["net_return_from_entry"])
                rows.append(
                    {
                        "candidate_name": candidate_name,
                        "split_name": split_name,
                        "lifecycle_id": lifecycle_id,
                        "symbol": base_row.get("symbol", ""),
                        "theme_id": base_row.get("theme_id", ""),
                        "base_timing_mode": base_row["timing_mode"],
                        "base_exit_mode": base_row["exit_mode"],
                        "candidate_timing_mode": cand_row["timing_mode"],
                        "candidate_exit_mode": cand_row["exit_mode"],
                        "base_return_pct": base_return * 100.0,
                        "candidate_return_pct": cand_return * 100.0,
                        "return_delta_pct_point": (cand_return - base_return) * 100.0,
                        "base_action_family": base_row.get("candidate_action_family", ""),
                    }
                )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("return_delta_pct_point").reset_index(drop=True)


def build_decision(reach: pd.DataFrame, accepted_delta: pd.DataFrame, winner_cut: pd.DataFrame) -> pd.DataFrame:
    recent = reach[reach["split_name"].eq("recent_oos")].iloc[0]
    validation = reach[reach["split_name"].eq("validation")].iloc[0]
    no_effect_rows = int(accepted_delta["effect_summary"].eq("no_accepted_trade_effect").sum())
    winner_cut_rows = int(accepted_delta["effect_summary"].eq("accepted_winners_cut_or_returns_reduced").sum())
    decision = "OOS_EFFECT_ABSENT_BECAUSE_ACTION_REACH_AND_EXIT_MAPPING_FAIL"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "validation_reduce_duration_rows": int(validation["reduce_duration_rows"]),
                "validation_strength_rows": int(validation["strength_hold_candidate_rows"]),
                "recent_reduce_duration_rows": int(recent["reduce_duration_rows"]),
                "recent_strength_rows": int(recent["strength_hold_candidate_rows"]),
                "accepted_delta_no_effect_rows": no_effect_rows,
                "accepted_winner_cut_rows": winner_cut_rows,
                "winner_cut_trade_rows": int(len(winner_cut)),
                "root_cause": "OOS actions either do not overlap accepted trades or replace profitable existing_exit winners with shorter/weaker exits.",
                "next_action": "Build an accepted-trade-aware exit policy audit: do not blindly shorten or lengthen; decide per symbol/theme whether existing_exit already captures the move.",
            }
        ]
    )


def build_pass_fail(reach: pd.DataFrame, accepted_delta: pd.DataFrame, winner_cut: pd.DataFrame) -> pd.DataFrame:
    recent = reach[reach["split_name"].eq("recent_oos")].iloc[0]
    validation = reach[reach["split_name"].eq("validation")].iloc[0]
    return pd.DataFrame(
        [
            {"gate": "oos_action_rows_exist", "pass_flag": int(int(recent["strength_hold_candidate_rows"]) > 0 or int(recent["reduce_duration_rows"]) > 0), "observed_value": f"recent_strength={int(recent['strength_hold_candidate_rows'])}; recent_reduce={int(recent['reduce_duration_rows'])}", "required_value": "recent OOS has action-classified rows"},
            {"gate": "validation_reduce_duration_exists", "pass_flag": int(int(validation["reduce_duration_rows"]) > 0), "observed_value": f"validation_reduce={int(validation['reduce_duration_rows'])}", "required_value": "validation has reduce-duration opportunities"},
            {"gate": "accepted_trade_overlap_exists", "pass_flag": int(int(recent["accepted_trade_ids_with_action_count"]) > 0), "observed_value": f"recent_accepted_action_overlap={int(recent['accepted_trade_ids_with_action_count'])}", "required_value": "action rows overlap capacity-accepted trades"},
            {"gate": "accepted_delta_audited", "pass_flag": int(len(accepted_delta) > 0), "observed_value": f"rows={len(accepted_delta)}", "required_value": "candidate accepted-trade deltas exist"},
            {"gate": "winner_cut_detected", "pass_flag": int(len(winner_cut) > 0), "observed_value": f"winner_cut_rows={len(winner_cut)}", "required_value": "audit should identify whether action cuts winners"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "forensics only", "required_value": "requires OOS action improvement and live readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    reach: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    winner_cut: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task662 OOS Effect Forensics",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Root cause: {d['root_cause']}",
        "",
        "## Quant Expert Report",
        "",
        "Task662 explains why Task661's relation engine did not create distinct validation/recent OOS account improvement.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is Task661 mechanism state rebuilt from the Task659 panel. No new market data or source text is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `split_name`, `timing_mode`, and `exit_mode`.",
        "",
        "### Leakage Audit",
        "",
        "This task is diagnostic only. Returns are used only to explain why prior candidates failed.",
        "",
        "### Action Reach",
        "",
        table(reach),
        "",
        "### Candidate Accepted Delta",
        "",
        table(accepted_delta),
        "",
        "### Winner Cut Audit",
        "",
        table(winner_cut),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "OOS에 신호가 없던 게 아닙니다.",
        "",
        "신호는 있었는데 실제 계좌에서 돈이 걸린 accepted trade와 잘 안 겹쳤거나, 큰 승자를 짧은 exit으로 바꿔서 수익을 줄였습니다.",
        "",
        "그래서 다음은 더 많은 macro 점수가 아니라 accepted trade 기준 exit/회전 감사입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task662_oos_action_reach.csv`",
        "- `task662_candidate_accepted_delta.csv`",
        "- `task662_winner_cut_audit.csv`",
        "- `task_662_decision.csv`",
        "- `task_662_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_662_oos_effect_forensics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    cols = [str(c) for c in clipped.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(cell(row.get(c, "")) for c in clipped.columns) + " |")
    return "\n".join(lines)


def cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task662_oos_effect_forensics(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} winner_cut_rows={int(decision['winner_cut_trade_rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
