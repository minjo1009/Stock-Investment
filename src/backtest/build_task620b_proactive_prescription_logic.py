from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate


TASK_ID = "Task620B"
REPORT_DIR = Path("docs/reports/task_620b_proactive_prescription_logic")
TASK617_PANEL = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv")

SPLITS = ("train_design", "validation", "recent_oos")
FORBIDDEN_RULE_COLUMNS = {
    "net_return_from_entry",
    "win_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "exit_reason",
    "simulated_exit_ts",
    "simulated_exit_price",
    "holding_days",
    "same_day_exit_flag",
}


def build_task620b_proactive_prescription_logic(
    *,
    panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(panel_path)
    rulebook = build_rulebook()
    evaluation = evaluate_rules(panel, rulebook)
    policy = evaluate_policies(panel)
    pass_fail = build_pass_fail(rulebook, evaluation, policy)
    decision = build_decision(evaluation, policy, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    rulebook.to_csv(out_dir / "task_620b_proactive_rulebook.csv", index=False)
    evaluation.to_csv(out_dir / "task_620b_proactive_rule_evaluation.csv", index=False)
    policy.to_csv(out_dir / "task_620b_policy_variant_evaluation.csv", index=False)
    pass_fail.to_csv(out_dir / "task_620b_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_620b_decision.csv", index=False)
    (out_dir / "task_620b_proactive_prescription_logic.md").write_text(
        render_report(rulebook, evaluation, policy, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_620b_proactive_rulebook": rulebook,
        "task_620b_proactive_rule_evaluation": evaluation,
        "task_620b_policy_variant_evaluation": policy,
        "task_620b_pass_fail_matrix": pass_fail,
        "task_620b_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {
        "split_name",
        "theme_id",
        "theme_regime_state_v4",
        "timing_state",
        "theme_ret20_prev",
        "net_return_from_entry",
        "win_flag",
        "entry_reduce_failure_flag",
    }
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel = panel.copy()
    for col in [
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "volume_ratio_prev",
        "intraday_ret_from_open",
        "range_pos",
        "net_return_from_entry",
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
        "ceo_ir_proxy_pre14d_flag",
        "passive_13g_pre30d_flag",
        "p0_source_event_density",
    ]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    for col in ["win_flag", "entry_reduce_failure_flag", "false_positive_flag"]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).astype(int)
    return panel


def build_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "AEROSPACE_SPACE_RISK_OFF_GATE",
                "pre_entry_action": "BLOCK_UNTIL_SOURCE_RETYPED",
                "condition_columns": "theme_id|political_statement_pre7d_flag|geopolitical_event_pre7d_flag|institution_ownership_pre30d_flag",
                "condition_description": "theme is aerospace_defense_space while broad political/geopolitical/institution flags are all active",
                "firm_grade_rationale": "This is not a permanent theme ban. It is a source-quality risk-off gate: current broad event support cannot distinguish good catalyst from crowded late theme entry.",
                "validation_use": "diagnostic_candidate_only",
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            },
            {
                "rule_id": "AEROSPACE_HOT_LEADER_ZERO_EXPOSURE",
                "pre_entry_action": "ENTRY_BLOCK",
                "condition_columns": "theme_id|theme_regime_state_v4|theme_ret20_prev",
                "condition_description": "theme is aerospace_defense_space, regime is persistent_theme_leader, and theme_ret20_prev > 0.15",
                "firm_grade_rationale": "Treat as late-crowding exhaustion risk before entry, not as an after-loss cleanup.",
                "validation_use": "diagnostic_candidate_only",
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            },
            {
                "rule_id": "HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED",
                "pre_entry_action": "DELAY_ENTRY_OR_REQUIRE_CONFIRMATION",
                "condition_columns": "timing_state|theme_ret20_prev",
                "condition_description": "midday_continuation while theme_ret20_prev > 0.15",
                "firm_grade_rationale": "This is not a hard deletion yet. It asks whether late continuation should wait for confirmation instead of chasing immediately.",
                "validation_use": "needs_delayed_entry_replay",
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            },
            {
                "rule_id": "BROAD_EVENT_NO_IR_GLOBAL_FILTER",
                "pre_entry_action": "DO_NOT_USE_GLOBAL_FILTER",
                "condition_columns": "political_statement_pre7d_flag|geopolitical_event_pre7d_flag|institution_ownership_pre30d_flag|ceo_ir_proxy_pre14d_flag",
                "condition_description": "broad event flags active while ceo_ir_proxy_pre14d_flag is absent",
                "firm_grade_rationale": "Global company-IR requirement damages validation and does not improve recent OOS enough; keep it as source retyping work, not a global entry rule.",
                "validation_use": "rejected_as_global_filter",
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            },
            {
                "rule_id": "OVEREXTENDED_THEME_LEADER_SIZE_DOWN",
                "pre_entry_action": "SIZE_DOWN",
                "condition_columns": "theme_regime_state_v4|theme_ret20_prev",
                "condition_description": "persistent_theme_leader and theme_ret20_prev > 0.20",
                "firm_grade_rationale": "Risk is visible before entry, but hard-block support is not strong enough yet; test smaller exposure first.",
                "validation_use": "size_down_candidate_only",
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            },
        ]
    )


def rule_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    broad = (
        panel["political_statement_pre7d_flag"].fillna(0).eq(1)
        & panel["geopolitical_event_pre7d_flag"].fillna(0).eq(1)
        & panel["institution_ownership_pre30d_flag"].fillna(0).eq(1)
    )
    aerospace = panel["theme_id"].astype(str).eq("aerospace_defense_space")
    persistent = panel["theme_regime_state_v4"].astype(str).eq("persistent_theme_leader")
    return {
        "AEROSPACE_SPACE_RISK_OFF_GATE": aerospace & broad,
        "AEROSPACE_HOT_LEADER_ZERO_EXPOSURE": aerospace & persistent & panel["theme_ret20_prev"].gt(0.15),
        "HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED": panel["timing_state"].astype(str).eq("midday_continuation") & panel["theme_ret20_prev"].gt(0.15),
        "BROAD_EVENT_NO_IR_GLOBAL_FILTER": broad & panel["ceo_ir_proxy_pre14d_flag"].fillna(0).eq(0),
        "OVEREXTENDED_THEME_LEADER_SIZE_DOWN": persistent & panel["theme_ret20_prev"].gt(0.20),
    }


def evaluate_rules(panel: pd.DataFrame, rulebook: pd.DataFrame) -> pd.DataFrame:
    masks = rule_masks(panel)
    rows = []
    for _, rule in rulebook.iterrows():
        mask = masks[str(rule["rule_id"])]
        for split_name in SPLITS:
            split = panel[panel["split_name"].astype(str).eq(split_name)]
            triggered = split[mask.loc[split.index]]
            kept = split[~mask.loc[split.index]]
            base_m = quality(split)
            trig_m = quality(triggered)
            kept_m = quality(kept)
            rows.append(
                {
                    "rule_id": rule["rule_id"],
                    "pre_entry_action": rule["pre_entry_action"],
                    "split_name": split_name,
                    "base_trade_count": int(len(split)),
                    "trigger_trade_count": int(len(triggered)),
                    "kept_trade_count": int(len(kept)),
                    "trigger_avg_net_return_pct": trig_m["avg_net_return_pct"],
                    "trigger_win_rate": trig_m["win_rate"],
                    "trigger_entry_reduce_failure_rate": trig_m["entry_reduce_failure_rate"],
                    "kept_avg_net_return_pct": kept_m["avg_net_return_pct"],
                    "kept_win_rate": kept_m["win_rate"],
                    "kept_entry_reduce_failure_rate": kept_m["entry_reduce_failure_rate"],
                    "base_avg_net_return_pct": base_m["avg_net_return_pct"],
                    "base_entry_reduce_failure_rate": base_m["entry_reduce_failure_rate"],
                    "kept_avg_delta_vs_base_pct_point": kept_m["avg_net_return_pct"] - base_m["avg_net_return_pct"],
                    "kept_entry_reduce_delta_vs_base_pct_point": (kept_m["entry_reduce_failure_rate"] - base_m["entry_reduce_failure_rate"]) * 100.0,
                    "clean_winner_rejected_count": int(((triggered["win_flag"].eq(1)) & (triggered["entry_reduce_failure_flag"].eq(0))).sum()) if not triggered.empty else 0,
                    "label_used_in_assignment_flag": 0,
                    "gpt_or_plugin_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def quality(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {"avg_net_return_pct": 0.0, "win_rate": 0.0, "entry_reduce_failure_rate": 0.0}
    metrics = aggregate(frame)
    return {
        "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
        "win_rate": float(metrics.get("win_rate", 0.0)),
        "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
    }


def evaluate_policies(panel: pd.DataFrame) -> pd.DataFrame:
    masks = rule_masks(panel)
    policies = {
        "PROACTIVE_V1_AEROSPACE_RISK_OFF": masks["AEROSPACE_SPACE_RISK_OFF_GATE"],
        "PROACTIVE_V2_AEROSPACE_HOT_ONLY": masks["AEROSPACE_HOT_LEADER_ZERO_EXPOSURE"],
        "PROACTIVE_V3_AERO_RISK_OFF_PLUS_HOT_MIDDAY_CONFIRM": (
            masks["AEROSPACE_SPACE_RISK_OFF_GATE"] | masks["HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED"]
        ),
        "REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT": masks["BROAD_EVENT_NO_IR_GLOBAL_FILTER"],
    }
    rows = []
    for policy_name, reject_mask in policies.items():
        for split_name in SPLITS:
            split = panel[panel["split_name"].astype(str).eq(split_name)]
            rejected = split[reject_mask.loc[split.index]]
            kept = split[~reject_mask.loc[split.index]]
            base_m = quality(split)
            kept_m = quality(kept)
            reject_m = quality(rejected)
            rows.append(
                {
                    "policy_name": policy_name,
                    "split_name": split_name,
                    "base_trade_count": int(len(split)),
                    "rejected_trade_count": int(len(rejected)),
                    "kept_trade_count": int(len(kept)),
                    "base_avg_net_return_pct": base_m["avg_net_return_pct"],
                    "rejected_avg_net_return_pct": reject_m["avg_net_return_pct"],
                    "kept_avg_net_return_pct": kept_m["avg_net_return_pct"],
                    "base_entry_reduce_failure_rate": base_m["entry_reduce_failure_rate"],
                    "rejected_entry_reduce_failure_rate": reject_m["entry_reduce_failure_rate"],
                    "kept_entry_reduce_failure_rate": kept_m["entry_reduce_failure_rate"],
                    "kept_avg_delta_vs_base_pct_point": kept_m["avg_net_return_pct"] - base_m["avg_net_return_pct"],
                    "kept_entry_reduce_delta_vs_base_pct_point": (kept_m["entry_reduce_failure_rate"] - base_m["entry_reduce_failure_rate"]) * 100.0,
                    "clean_winner_rejected_count": int(((rejected["win_flag"].eq(1)) & (rejected["entry_reduce_failure_flag"].eq(0))).sum()) if not rejected.empty else 0,
                    "label_used_in_assignment_flag": 0,
                    "gpt_or_plugin_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_pass_fail(rulebook: pd.DataFrame, evaluation: pd.DataFrame, policy: pd.DataFrame) -> pd.DataFrame:
    forbidden_hits = []
    for _, rule in rulebook.iterrows():
        cols = set(str(rule["condition_columns"]).split("|"))
        forbidden_hits.extend(sorted(cols.intersection(FORBIDDEN_RULE_COLUMNS)))
    v1_recent = policy_row(policy, "PROACTIVE_V1_AEROSPACE_RISK_OFF", "recent_oos")
    v1_validation = policy_row(policy, "PROACTIVE_V1_AEROSPACE_RISK_OFF", "validation")
    global_ir_recent = policy_row(policy, "REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT", "recent_oos")
    global_ir_validation = policy_row(policy, "REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT", "validation")
    return pd.DataFrame(
        [
            {
                "gate": "pre_entry_only_rule_columns",
                "pass_flag": int(len(forbidden_hits) == 0),
                "observed_value": ",".join(forbidden_hits) if forbidden_hits else "none",
                "required_value": "no outcome, exit, or holding-period columns in rule conditions",
            },
            {
                "gate": "aerospace_risk_off_diagnostic_candidate",
                "pass_flag": int(
                    float(v1_recent["kept_avg_net_return_pct"]) >= 5.0
                    and float(v1_recent["kept_entry_reduce_failure_rate"]) <= 0.50
                    and float(v1_validation["kept_avg_net_return_pct"]) >= float(v1_validation["base_avg_net_return_pct"])
                ),
                "observed_value": (
                    f"recent_kept_avg={float(v1_recent['kept_avg_net_return_pct']):.2f}%; "
                    f"recent_kept_er={float(v1_recent['kept_entry_reduce_failure_rate']) * 100.0:.2f}%; "
                    f"validation_kept_avg={float(v1_validation['kept_avg_net_return_pct']):.2f}%"
                ),
                "required_value": "recent kept avg>=5%, recent kept entry_reduce<=50%, validation kept avg>=base",
            },
            {
                "gate": "global_ir_requirement_rejected",
                "pass_flag": int(
                    float(global_ir_recent["kept_avg_net_return_pct"]) < float(global_ir_recent["base_avg_net_return_pct"])
                    and float(global_ir_validation["kept_avg_net_return_pct"]) < float(global_ir_validation["base_avg_net_return_pct"])
                ),
                "observed_value": (
                    f"recent_kept_avg={float(global_ir_recent['kept_avg_net_return_pct']):.2f}%; "
                    f"validation_kept_avg={float(global_ir_validation['kept_avg_net_return_pct']):.2f}%"
                ),
                "required_value": "global company-IR requirement should not be promoted if it damages both splits",
            },
            {
                "gate": "treatment_rule_acceptance",
                "pass_flag": 0,
                "observed_value": "diagnostic proactive rule candidates only",
                "required_value": "must pass split/OOS, cost/slippage, parameter, and source-retyping audits",
            },
        ]
    )


def policy_row(policy: pd.DataFrame, policy_name: str, split_name: str) -> pd.Series:
    return policy[policy["policy_name"].eq(policy_name) & policy["split_name"].eq(split_name)].iloc[0]


def build_decision(evaluation: pd.DataFrame, policy: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    v1_recent = policy_row(policy, "PROACTIVE_V1_AEROSPACE_RISK_OFF", "recent_oos")
    v1_validation = policy_row(policy, "PROACTIVE_V1_AEROSPACE_RISK_OFF", "validation")
    candidate_pass = int(pass_fail[pass_fail["gate"].eq("aerospace_risk_off_diagnostic_candidate")]["pass_flag"].iloc[0])
    decision = "LOCK_PROACTIVE_AEROSPACE_RISK_OFF_CANDIDATE_NOT_ACCEPTED"
    if not candidate_pass:
        decision = "FAIL_PROACTIVE_AEROSPACE_RISK_OFF_CANDIDATE"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "primary_proactive_rule": "AEROSPACE_SPACE_RISK_OFF_GATE",
                "primary_pre_entry_action": "BLOCK_UNTIL_SOURCE_RETYPED",
                "recent_oos_kept_avg_net_return_pct": float(v1_recent["kept_avg_net_return_pct"]),
                "recent_oos_kept_entry_reduce_failure_rate": float(v1_recent["kept_entry_reduce_failure_rate"]),
                "validation_kept_avg_net_return_pct": float(v1_validation["kept_avg_net_return_pct"]),
                "treatment_rule_accepted_flag": 0,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run source-retyped aerospace risk-off validation and same-capital cost stress before accepting any treatment rule.",
            }
        ]
    )


def render_report(
    rulebook: pd.DataFrame,
    evaluation: pd.DataFrame,
    policy: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task620B Proactive Prescription Logic",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Primary proactive rule: `{d['primary_proactive_rule']}`",
        f"- Primary pre-entry action: `{d['primary_pre_entry_action']}`",
        "- This is a proactive rule candidate, not an accepted trading rule.",
        "",
        "## Quant Expert Report",
        "",
        "### Proactive Rulebook",
        "",
        "| Rule | Action | Condition Columns | Validation Use |",
        "|---|---|---|---|",
    ]
    for _, row in rulebook.iterrows():
        lines.append(
            f"| `{row['rule_id']}` | `{row['pre_entry_action']}` | `{row['condition_columns']}` | `{row['validation_use']}` |"
        )
    lines.extend(
        [
            "",
            "### Rule Evaluation",
            "",
            "| Rule | Split | Trigger N | Trigger Avg | Kept Avg | Kept Entry-Reduce | Clean Winners Rejected |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in evaluation.iterrows():
        lines.append(
            f"| `{row['rule_id']}` | `{row['split_name']}` | {int(row['trigger_trade_count'])} | "
            f"{float(row['trigger_avg_net_return_pct']):.2f}% | {float(row['kept_avg_net_return_pct']):.2f}% | "
            f"{float(row['kept_entry_reduce_failure_rate']) * 100.0:.2f}% | {int(row['clean_winner_rejected_count'])} |"
        )
    lines.extend(
        [
            "",
            "### Policy Variants",
            "",
            "| Policy | Split | Rejected | Kept | Kept Avg | Kept Entry-Reduce |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in policy.iterrows():
        lines.append(
            f"| `{row['policy_name']}` | `{row['split_name']}` | {int(row['rejected_trade_count'])} | "
            f"{int(row['kept_trade_count'])} | {float(row['kept_avg_net_return_pct']):.2f}% | "
            f"{float(row['kept_entry_reduce_failure_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- The new logic is not 'it lost a lot, so delete it.'",
            "- The new logic is a pre-entry risk-off rule: aerospace/space plus broad, non-discriminating event support is blocked until the source layer can prove a company-specific catalyst.",
            "- A global 'must have recent IR' rule is rejected because it damages validation and recent OOS.",
            "- Trailing-stop failures remain exit research, not entry logic.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_620b_proactive_rulebook.csv`",
            "- `task_620b_proactive_rule_evaluation.csv`",
            "- `task_620b_policy_variant_evaluation.csv`",
            "- `task_620b_pass_fail_matrix.csv`",
            "- `task_620b_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task620b_proactive_prescription_logic`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task620b_proactive_prescription_logic(out_dir=args.out_dir)
    row = artifacts["task_620b_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={row['decision']} primary={row['primary_proactive_rule']}")


if __name__ == "__main__":
    main()
