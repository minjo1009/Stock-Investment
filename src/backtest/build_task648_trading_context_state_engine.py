from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task648"
REPORT_DIR = Path("docs/reports/task_648_trading_context_state_engine")
TASK617_PANEL = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv")
TASK636_PANEL = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_content_prediction_panel.csv")
TASK629_ACTIONS = Path("docs/reports/task_629_firm_grade_event_linkage_action_taxonomy/task_629_trade_action_attachment.csv")


def build_task648(
    *,
    task617_panel: Path = TASK617_PANEL,
    task636_panel: Path = TASK636_PANEL,
    task629_actions: Path = TASK629_ACTIONS,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(task617_panel)
    content = pd.read_csv(task636_panel)
    actions = pd.read_csv(task629_actions)

    content_cols = [
        "lifecycle_id",
        "linked_event_count",
        "source_text_certified_event_count",
        "content_prediction_certified_event_count",
        "content_direct_bullish_count",
        "content_direct_bearish_count",
        "content_contract_revenue_count",
        "content_guidance_margin_count",
        "content_supply_demand_count",
        "content_regulatory_policy_count",
        "content_insider_buy_count",
        "content_insider_sell_count",
        "content_net_prediction_score",
        "content_max_magnitude_score",
        "content_avg_priced_in_risk_score",
    ]
    content = content[[c for c in content_cols if c in content.columns]].drop_duplicates("lifecycle_id")
    actions = actions.drop_duplicates("lifecycle_id")

    panel = base.merge(content, on="lifecycle_id", how="left", suffixes=("", "_content"))
    panel = panel.merge(actions, on="lifecycle_id", how="left", suffixes=("", "_task629"))

    panel["macro_raw_source_gap_flag"] = 1
    panel["macro_raw_source_gap_reason"] = "employment_cpi_pce_rates_fed_dollar_oil_credit_liquidity_not_integrated"
    panel["market_context_state"] = panel.apply(classify_market_context, axis=1)
    panel["sector_theme_context_state"] = panel.apply(classify_theme_context, axis=1)
    panel["company_content_state"] = panel.apply(classify_company_content, axis=1)
    panel["policy_geo_context_state"] = panel.apply(classify_policy_geo, axis=1)
    panel["chart_context_state"] = panel.apply(classify_chart_context, axis=1)
    panel["provisional_trading_context_state"] = panel.apply(classify_trading_context, axis=1)
    panel["suggested_action_bucket_diagnostic"] = panel.apply(classify_action_bucket, axis=1)
    panel["label_used_in_state_assignment_flag"] = 0
    panel["outcome_used_in_state_assignment_flag"] = 0
    panel["strategy_promotion_flag"] = 0

    selected_cols = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "macro_raw_source_gap_flag",
        "market_context_state",
        "sector_theme_context_state",
        "company_content_state",
        "policy_geo_context_state",
        "chart_context_state",
        "provisional_trading_context_state",
        "suggested_action_bucket_diagnostic",
        "macro_raw_source_gap_reason",
        "label_used_in_state_assignment_flag",
        "outcome_used_in_state_assignment_flag",
        "strategy_promotion_flag",
        "net_return_from_entry",
        "win_flag",
        "entry_reduce_failure_flag",
    ]
    state_panel = panel[[c for c in selected_cols if c in panel.columns]].copy()
    state_summary = summarize_states(panel)
    coverage = build_coverage_audit(panel)
    pass_fail = build_pass_fail(panel)
    decision = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "PROVISIONAL_CONTEXT_STATE_ENGINE_BUILT_SOURCE_GAPS_BLOCK_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "state_panel_rows": int(len(panel)),
                "distinct_context_states": int(panel["provisional_trading_context_state"].nunique()),
                "macro_raw_source_gap_flag": 1,
                "strategy_promotion_flag": 0,
            }
        ]
    )

    state_panel.to_csv(out_dir / "task_648_trading_context_state_panel.csv", index=False, encoding="utf-8-sig")
    state_summary.to_csv(out_dir / "task_648_context_state_evaluation.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(out_dir / "task_648_source_layer_coverage_audit.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_648_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_648_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, state_summary, coverage, pass_fail, decision)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "state_panel": state_panel,
        "state_summary": state_summary,
        "coverage": coverage,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def classify_market_context(row: pd.Series) -> str:
    score = num(row.get("broad_market_score"))
    stress = num(row.get("broad_market_stress"))
    breadth = num(row.get("breadth_20d"))
    market_ret = num(row.get("market_ret_20d"))
    state = text(row.get("multi_day_market_state_v4"))
    if pd.isna(score) and pd.isna(stress) and pd.isna(breadth) and not state:
        return "source_gap"
    if stress >= 60 or breadth < 0.35 or market_ret < -0.05 or "risk_off" in state:
        return "hostile"
    if score >= 55 and stress <= 45 and breadth >= 0.50 and market_ret >= 0:
        return "supportive"
    return "mixed"


def classify_theme_context(row: pd.Series) -> str:
    regime = text(row.get("theme_regime_state_v4"))
    ret20 = num(row.get("theme_ret20_prev"))
    breadth = num(row.get("theme_breadth20_prev"))
    volume = num(row.get("theme_volume_ratio_prev"))
    if not regime and pd.isna(ret20) and pd.isna(breadth):
        return "source_gap"
    if "narrow" in regime or breadth < 0.35 or ret20 < -0.05:
        return "fragile"
    if ("persistent" in regime or "participation" in regime) and breadth >= 0.50 and ret20 >= 0 and (pd.isna(volume) or volume >= 0.80):
        return "supportive"
    return "mixed"


def classify_company_content(row: pd.Series) -> str:
    certified = num(row.get("content_prediction_certified_event_count"), default=0)
    if certified <= 0:
        return "source_gap"
    support = (
        num(row.get("content_direct_bullish_count"), default=0)
        + num(row.get("content_contract_revenue_count"), default=0)
        + num(row.get("content_guidance_margin_count"), default=0)
        + num(row.get("content_supply_demand_count"), default=0)
        + num(row.get("content_insider_buy_count"), default=0)
    )
    adverse = (
        num(row.get("content_direct_bearish_count"), default=0)
        + num(row.get("content_regulatory_policy_count"), default=0)
        + num(row.get("content_insider_sell_count"), default=0)
    )
    net_score = num(row.get("content_net_prediction_score"), default=0)
    priced_in = num(row.get("content_avg_priced_in_risk_score"), default=0)
    if adverse > support and net_score < 0:
        return "adverse"
    if support > 0 and adverse > 0:
        return "mixed"
    if support > 0 and net_score > 0 and priced_in < 0.75:
        return "supportive"
    if support > 0 and priced_in >= 0.75:
        return "supportive_but_priced_in"
    return "neutral"


def classify_policy_geo(row: pd.Series) -> str:
    bucket = text(row.get("action_bucket"))
    if num(row.get("block_hold_flag"), default=0) > 0 or bucket == "block_hold":
        return "block"
    if num(row.get("delay_entry_flag"), default=0) > 0 or bucket == "delay_entry":
        return "delay_entry"
    if num(row.get("confirmation_required_flag"), default=0) > 0 or bucket == "confirmation_required":
        return "confirmation_required"
    if num(row.get("size_down_flag"), default=0) > 0 or bucket == "size_down":
        return "size_down"
    if bucket:
        return "no_action"
    return "source_gap"


def classify_chart_context(row: pd.Series) -> str:
    chart = num(row.get("tq_pre_entry_chart_health_score"))
    intraday = text(row.get("intraday_entry_state_v4"))
    if pd.isna(chart) and not intraday:
        return "source_gap"
    if chart < 0.50:
        return "fragile"
    if chart >= 0.75 and "acceptance" in intraday:
        return "supportive"
    return "mixed"


def classify_trading_context(row: pd.Series) -> str:
    market = row["market_context_state"]
    theme = row["sector_theme_context_state"]
    company = row["company_content_state"]
    policy = row["policy_geo_context_state"]
    chart = row["chart_context_state"]
    if company == "source_gap":
        return "source_gap"
    if market == "hostile" or policy == "block":
        return "risk_off_override"
    if company in {"supportive", "supportive_but_priced_in"} and (
        policy in {"size_down", "delay_entry", "confirmation_required"} or theme == "fragile" or chart == "fragile"
    ):
        return "conflicted_alignment"
    if company == "supportive" and market == "supportive" and theme == "supportive" and chart == "supportive" and policy in {"no_action", "source_gap"}:
        return "supportive_alignment"
    if company == "adverse" and market in {"hostile", "mixed"}:
        return "risk_off_override"
    return "mixed_alignment"


def classify_action_bucket(row: pd.Series) -> str:
    context = row["provisional_trading_context_state"]
    company = row["company_content_state"]
    policy = row["policy_geo_context_state"]
    if context == "source_gap":
        return "NO_ACTION_SOURCE_GAP"
    if context == "risk_off_override" or policy == "block":
        return "BLOCK_HOLD"
    if policy == "delay_entry":
        return "DELAY_ENTRY"
    if policy == "confirmation_required" or company == "supportive_but_priced_in":
        return "CONFIRMATION_REQUIRED"
    if policy == "size_down" or context == "conflicted_alignment":
        return "SIZE_DOWN"
    if context == "supportive_alignment":
        return "FULL_ENTRY_CANDIDATE"
    if company == "supportive":
        return "NORMAL_ENTRY"
    return "NO_ACTION_CONTEXT_WEAK"


def summarize_states(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (split, state, action), group in panel.groupby(["split_name", "provisional_trading_context_state", "suggested_action_bucket_diagnostic"], dropna=False):
        ret = pd.to_numeric(group.get("net_return_from_entry"), errors="coerce")
        wins = pd.to_numeric(group.get("win_flag"), errors="coerce")
        er = pd.to_numeric(group.get("entry_reduce_failure_flag"), errors="coerce")
        rows.append(
            {
                "split_name": split,
                "provisional_trading_context_state": state,
                "suggested_action_bucket_diagnostic": action,
                "entry_count": int(len(group)),
                "avg_net_return_pct": round(float(ret.mean()), 6) if ret.notna().any() else 0.0,
                "win_rate": round(float(wins.mean()), 6) if wins.notna().any() else 0.0,
                "entry_reduce_failure_rate": round(float(er.mean()), 6) if er.notna().any() else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "entry_count"], ascending=[True, False]).reset_index(drop=True)


def build_coverage_audit(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"layer": "macro_raw_sources", "available_flag": 0, "coverage_note": "employment/CPI/PCE/rates/Fed/dollar/oil/credit/liquidity not integrated", "source_gap_blocks_promotion": 1},
            {"layer": "market_context_existing", "available_flag": int(panel["market_context_state"].ne("source_gap").any()), "coverage_note": "Task617 broad market score/stress/breadth/liquidity fields", "source_gap_blocks_promotion": 0},
            {"layer": "sector_theme_existing", "available_flag": int(panel["sector_theme_context_state"].ne("source_gap").any()), "coverage_note": "Task617 theme regime/return/breadth fields", "source_gap_blocks_promotion": 0},
            {"layer": "company_content_existing", "available_flag": int(panel["company_content_state"].ne("source_gap").any()), "coverage_note": "Task636 certified content prediction fields", "source_gap_blocks_promotion": 0},
            {"layer": "policy_geo_existing", "available_flag": int(panel["policy_geo_context_state"].ne("source_gap").any()), "coverage_note": "Task629 economic linkage action bucket", "source_gap_blocks_promotion": 0},
            {"layer": "chart_existing", "available_flag": int(panel["chart_context_state"].ne("source_gap").any()), "coverage_note": "Task617 chart health and intraday acceptance fields", "source_gap_blocks_promotion": 0},
        ]
    )


def build_pass_fail(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"gate": "state_panel_created", "pass_flag": int(len(panel) > 0), "observed": f"rows={len(panel)}", "required": "state panel must be nonempty"},
            {"gate": "no_label_or_outcome_assignment", "pass_flag": 1, "observed": "assignment functions do not read return/win/entry_reduce labels", "required": "labels/outcomes evaluation-only"},
            {"gate": "macro_source_gap_reported", "pass_flag": int(panel["macro_raw_source_gap_flag"].eq(1).all()), "observed": "macro_raw_source_gap_flag=1", "required": "missing macro raw sources must be explicit"},
            {"gate": "context_state_diversity", "pass_flag": int(panel["provisional_trading_context_state"].nunique() >= 2), "observed": f"states={panel['provisional_trading_context_state'].nunique()}", "required": "at least two states for diagnostic value"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed": "provisional state engine only", "required": "requires raw macro/sector/positioning sources, split validation, cost/account rerun"},
        ]
    )


def write_report(out_dir: Path, state_summary: pd.DataFrame, coverage: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> None:
    lines = [
        "# Task648 Trading Context State Engine",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `PROVISIONAL_CONTEXT_STATE_ENGINE_BUILT_SOURCE_GAPS_BLOCK_PROMOTION`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- This task builds a first trading context state engine from existing market, theme, company-content, policy/geopolitical, and chart fields.",
        "- Missing macro raw sources remain explicit source gaps.",
        "- The output is diagnostic only and does not promote a strategy.",
        "",
        "## Quant Expert Report",
        "",
        "The first state engine combines existing layers into a provisional context:",
        "",
        "```text",
        "Market + Sector/Theme + Company Content + Policy/Geopolitics + Chart = Provisional Trading Context State",
        "```",
        "",
        "True macro raw sources are not yet integrated, so every row carries `macro_raw_source_gap_flag=1`.",
        "",
        "### State Evaluation",
        "",
        table(state_summary),
        "",
        "### Source Layer Coverage",
        "",
        table(coverage),
        "",
        "### Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- We now have the first version of the combined state engine.",
        "- It asks whether a trade candidate has supportive, mixed, conflicted, risk-off, or source-gap context.",
        "- It still is not final because true macro data is missing.",
        "- The next real upgrade is to add employment, inflation, rates, Fed, dollar, oil, credit, liquidity, analyst revisions, sector flow, and positioning.",
        "- Until then, this is a diagnostic map, not a live trading rule.",
        "",
        "## Artifact Manifest",
        "",
        "- `task_648_trading_context_state_panel.csv`",
        "- `task_648_context_state_evaluation.csv`",
        "- `task_648_source_layer_coverage_audit.csv`",
        "- `task_648_pass_fail_matrix.csv`",
        "- `task_648_decision.csv`",
        "- `artifact_manifest.csv`",
        "",
    ]
    (out_dir / "task_648_trading_context_state_engine.md").write_text("\n".join(lines), encoding="utf-8")


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def num(value: object, *, default: float = float("nan")) -> float:
    try:
        out = pd.to_numeric(value, errors="coerce")
    except Exception:  # noqa: BLE001
        return default
    if pd.isna(out):
        return default
    return float(out)


def text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task648(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(f"[{TASK_ID}] verdict={decision['verdict']} rows={decision['state_panel_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
