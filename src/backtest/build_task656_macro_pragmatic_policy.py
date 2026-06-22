from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task656"
REPORT_DIR = Path("docs/reports/task_656_macro_pragmatic_policy")
TASK655_COVERAGE = Path("docs/reports/task_655_macro_asof_release_repair/task_655_coverage_after_release_repair.csv")
TASK655_DECISION = Path("docs/reports/task_655_macro_asof_release_repair/task_655_decision.csv")


def build_task656_macro_pragmatic_policy(
    *,
    task655_coverage_path: Path = TASK655_COVERAGE,
    task655_decision_path: Path = TASK655_DECISION,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    coverage655 = pd.read_csv(task655_coverage_path)
    decision655 = pd.read_csv(task655_decision_path).iloc[0]
    policy = build_policy()
    pragmatic = build_pragmatic_coverage(coverage655)
    permission = build_permission_matrix()
    pass_fail = build_pass_fail(policy, pragmatic)
    decision = build_decision(decision655, pragmatic, pass_fail)

    policy.to_csv(out_dir / "task_656_macro_pragmatic_policy.csv", index=False, encoding="utf-8-sig")
    pragmatic.to_csv(out_dir / "task_656_pragmatic_coverage.csv", index=False, encoding="utf-8-sig")
    permission.to_csv(out_dir / "task_656_relation_permission_matrix.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_656_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_656_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, policy, pragmatic, permission, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "policy": policy,
        "pragmatic_coverage": pragmatic,
        "permission": permission,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def build_policy() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "policy_item": "release_time_required",
                "required_flag": 1,
                "decision": "required_for_any_macro_use",
                "reason": "Macro must not be used before it could be known intraday.",
            },
            {
                "policy_item": "exact_release_calendar_required",
                "required_flag": 0,
                "decision": "defer_for_now_use_standard_release_time_rules",
                "reason": "Official per-observation release calendars are useful but too slow for the current iteration.",
            },
            {
                "policy_item": "vintage_asof_required",
                "required_flag": 0,
                "decision": "defer_for_now_accept_latest_vintage_caveat",
                "reason": "Revision-perfect ALFRED work is intentionally deferred by user decision.",
            },
            {
                "policy_item": "macro_allowed_usage",
                "required_flag": 1,
                "decision": "soft_modifier_only",
                "reason": "Macro can shape confirmation, delay, and risk context but cannot be a standalone entry or hard blocker.",
            },
            {
                "policy_item": "macro_forbidden_usage",
                "required_flag": 1,
                "decision": "no_standalone_entry_no_full_entry_no_hard_block_no_size_boost",
                "reason": "Latest-vintage caveat means macro cannot carry strong trading authority.",
            },
        ]
    )


def build_pragmatic_coverage(coverage655: pd.DataFrame) -> pd.DataFrame:
    out = coverage655.copy()
    out["pragmatic_macro_eligible_rows"] = pd.to_numeric(out["provisional_diagnostic_eligible_rows"], errors="coerce").fillna(0).astype(int)
    out["pragmatic_macro_eligible_rate"] = pd.to_numeric(out["provisional_diagnostic_eligible_rate"], errors="coerce").fillna(0.0)
    out["strict_vintage_required_flag"] = 0
    out["macro_usage_permission"] = out["pragmatic_macro_eligible_rate"].apply(
        lambda rate: "soft_modifier_allowed" if float(rate) >= 0.95 else "diagnostic_only_gap_too_large"
    )
    return out[
        [
            "scope",
            "row_count",
            "lifecycle_count",
            "release_timestamp_repaired_rate",
            "latest_vintage_gap_rate",
            "strict_assignment_eligible_rate",
            "pragmatic_macro_eligible_rows",
            "pragmatic_macro_eligible_rate",
            "strict_vintage_required_flag",
            "macro_usage_permission",
        ]
    ]


def build_permission_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"relation_use": "standalone_entry", "permission": "BLOCKED", "reason": "Macro is context, not entry alpha."},
            {"relation_use": "full_entry_promotion", "permission": "BLOCKED", "reason": "Latest-vintage caveat blocks strong action."},
            {"relation_use": "hard_block", "permission": "BLOCKED", "reason": "Macro can be wrong or revised; company/chart evidence must carry hard block."},
            {"relation_use": "size_boost", "permission": "BLOCKED", "reason": "No leverage or boost from latest-vintage macro."},
            {"relation_use": "confirmation_required", "permission": "ALLOWED_FOR_BACKTEST", "reason": "Soft modifier can require cleaner entry confirmation."},
            {"relation_use": "delay_entry", "permission": "ALLOWED_FOR_BACKTEST", "reason": "Soft modifier can test delayed entry around macro pressure."},
            {"relation_use": "reduced_size", "permission": "ALLOWED_FOR_BACKTEST", "reason": "Soft risk trim is allowed only if it preserves Task639 baseline and OOS gates."},
            {"relation_use": "research_tagging", "permission": "ALLOWED", "reason": "Context tags are allowed for diagnostics."},
        ]
    )


def build_pass_fail(policy: pd.DataFrame, pragmatic: pd.DataFrame) -> pd.DataFrame:
    task639 = pragmatic[pragmatic["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    vintage_required = int(policy[policy["policy_item"].eq("vintage_asof_required")]["required_flag"].iloc[0])
    return pd.DataFrame(
        [
            {"gate": "release_time_required", "pass_flag": 1, "observed_value": "required=1", "required_value": "release time must remain required"},
            {"gate": "vintage_requirement_deferred", "pass_flag": int(vintage_required == 0), "observed_value": f"required={vintage_required}", "required_value": "vintage-as-of is intentionally deferred"},
            {"gate": "task639_pragmatic_macro_coverage", "pass_flag": int(float(task639["pragmatic_macro_eligible_rate"]) >= 0.95), "observed_value": f"rate={float(task639['pragmatic_macro_eligible_rate']):.4f}", "required_value": ">=0.95"},
            {"gate": "strict_assignment_not_claimed", "pass_flag": int(float(task639["strict_assignment_eligible_rate"]) == 0.0), "observed_value": f"strict_rate={float(task639['strict_assignment_eligible_rate']):.4f}", "required_value": "must not pretend vintage-perfect assignment"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "policy enables backtest research only", "required_value": "strategy still needs relation backtest and OOS acceptance"},
        ]
    )


def build_decision(task655: pd.Series, pragmatic: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    task639 = pragmatic[pragmatic["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PRAGMATIC_RELEASE_TIME_MACRO_POLICY_READY_FOR_SOFT_RELATION_BACKTEST",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "task655_parent_decision": task655["decision"],
                "task639_pragmatic_macro_eligible_rate": float(task639["pragmatic_macro_eligible_rate"]),
                "vintage_asof_required_flag": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Run relation engine backtest with macro as soft modifier only. Do not use macro for standalone entry, hard block, full entry, or size boost.",
            }
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    policy: pd.DataFrame,
    pragmatic: pd.DataFrame,
    permission: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task656 Macro Pragmatic Policy",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639 pragmatic macro eligible rate: {float(d['task639_pragmatic_macro_eligible_rate']):.4f}.",
        "- What changed: vintage-perfect ALFRED work is deferred by policy; release-time repaired macro can be used for soft backtest research.",
        "- Next action: test relation engine with macro as soft modifier only.",
        "",
        "## Quant Expert Report",
        "",
        "Task656 changes the research standard from strict vintage-perfect macro assignment to a pragmatic release-time-valid policy. This is not a deployment approval.",
        "",
        "### Data Source And Source Readiness",
        "",
        table(pragmatic),
        "",
        "### Exact Join Keys",
        "",
        "Task655 context remains keyed by lifecycle, entry timestamp, timing mode, and exit mode. Release-time validity stays mandatory.",
        "",
        "### Leakage Audit",
        "",
        "The policy explicitly does not claim vintage-perfect as-of values. Therefore macro can only be a soft modifier in backtests.",
        "",
        "### Failure Decomposition",
        "",
        table(policy),
        "",
        "### Remaining Blockers",
        "",
        table(permission),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We will not chase the perfect old unrevised macro value right now.",
        "",
        "We keep the important part: the macro number must already have been released before the trade.",
        "",
        "Because revised-value risk remains, macro gets limited power. It can help us be more careful, but it cannot force a buy, hard block a trade, or boost size.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task_656_macro_pragmatic_policy.csv`",
        "- `task_656_pragmatic_coverage.csv`",
        "- `task_656_relation_permission_matrix.csv`",
        "- `task_656_pass_fail_matrix.csv`",
        "- `task_656_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_656_macro_pragmatic_policy.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    result = build_task656_macro_pragmatic_policy(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} task639_pragmatic={float(decision['task639_pragmatic_macro_eligible_rate']):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
