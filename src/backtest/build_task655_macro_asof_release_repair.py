from __future__ import annotations

import argparse
import sys
from calendar import monthrange
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task649_macro_context_state_engine import (
    SERIES_CONFIGS,
    classify_credit,
    classify_dollar,
    classify_employment,
    classify_inflation,
    classify_liquidity,
    classify_macro_action_modifier,
    classify_macro_overall,
    classify_oil,
    classify_rates,
    fetch_macro_series,
)


TASK_ID = "Task655"
REPORT_DIR = Path("docs/reports/task_655_macro_asof_release_repair")
RAW_DIR = Path("data/raw/macro_fred/task_655")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def build_task655_macro_asof_release_repair(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    raw_dir: Path = RAW_DIR,
    out_dir: Path = REPORT_DIR,
    macro_raw_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    execution = load_execution_panel(execution_panel_path)
    start_date, end_date = infer_fetch_range(execution)
    if macro_raw_path is None:
        macro_raw = fetch_macro_series(start_date=start_date, end_date=end_date)
    else:
        macro_raw = pd.read_csv(macro_raw_path)
    macro_raw.to_csv(raw_dir / "fred_macro_series_latest_vintage_refreshed.csv", index=False, encoding="utf-8-sig")
    feature = build_release_repaired_feature_panel(macro_raw)
    feature.to_csv(raw_dir / "fred_macro_release_repaired_feature_panel.csv", index=False, encoding="utf-8-sig")
    context = attach_release_repaired_macro(execution, feature)
    context.to_csv(out_dir / "task_655_macro_asof_context_panel.csv", index=False, encoding="utf-8-sig")
    source_audit = build_source_audit(macro_raw, feature)
    coverage = build_coverage_after_repair(execution, context)
    bridge = build_task654_coverage_bridge(coverage)
    pass_fail = build_pass_fail(source_audit, coverage)
    decision = build_decision(source_audit, coverage, pass_fail)

    source_audit.to_csv(out_dir / "task_655_macro_source_audit.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(out_dir / "task_655_coverage_after_release_repair.csv", index=False, encoding="utf-8-sig")
    bridge.to_csv(out_dir / "task_655_task654_coverage_bridge.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_655_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_655_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, source_audit, coverage, bridge, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "macro_raw": macro_raw,
        "feature": feature,
        "context": context,
        "source_audit": source_audit,
        "coverage": coverage,
        "bridge": bridge,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in panel.columns:
            panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["positive_contract_customer_count", "content_supply_demand_flag", "net_return_from_entry"]:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts"]).copy()


def infer_fetch_range(panel: pd.DataFrame) -> tuple[str, str]:
    start = (panel["entry_ts"].min() - pd.Timedelta(days=900)).date().isoformat()
    end = (panel["entry_ts"].max() + pd.Timedelta(days=10)).date().isoformat()
    return start, end


def build_release_repaired_feature_panel(raw: pd.DataFrame) -> pd.DataFrame:
    fetched = raw[raw["fetch_status"].eq("FETCHED")].copy()
    fetched["observation_dt"] = pd.to_datetime(fetched["observation_date"], errors="coerce")
    fetched = fetched.dropna(subset=["observation_dt", "value"]).copy()
    fetched["value"] = pd.to_numeric(fetched["value"], errors="coerce")
    fetched = fetched.dropna(subset=["value"]).copy()
    fetched["release_ts_utc"] = fetched.apply(release_timestamp_utc, axis=1)
    fetched["tradable_after_ts_utc"] = fetched["release_ts_utc"].apply(tradable_after)
    fetched["release_timestamp_method"] = fetched["series_id"].map(release_method)
    fetched["release_time_repaired_flag"] = 1
    fetched["exact_release_calendar_verified_flag"] = 0
    fetched["latest_vintage_only_flag"] = 1
    fetched["vintage_asof_certified_flag"] = 0
    fetched = fetched.sort_values(["series_id", "tradable_after_ts_utc"])
    grouped = fetched.groupby("series_id", group_keys=False)
    fetched["value_change_1obs"] = grouped["value"].diff(1)
    fetched["value_change_3obs"] = grouped["value"].diff(3)
    fetched["value_change_12obs"] = grouped["value"].diff(12)
    fetched["value_change_20obs"] = grouped["value"].diff(20)
    fetched["pct_change_3obs"] = grouped["value"].pct_change(3)
    fetched["pct_change_12obs"] = grouped["value"].pct_change(12)
    fetched["pct_change_20obs"] = grouped["value"].pct_change(20)
    return fetched


def release_timestamp_utc(row: pd.Series) -> pd.Timestamp:
    series_id = str(row["series_id"])
    obs = pd.Timestamp(row["observation_dt"]).to_pydatetime().date()
    if series_id in {"UNRATE", "PAYEMS"}:
        local = combine_et(first_friday_next_month(obs), 8, 30)
    elif series_id == "CPIAUCSL":
        local = combine_et(first_business_day_on_or_after(next_month_date(obs, 10)), 8, 30)
    elif series_id in {"PCEPI", "PCEPILFE"}:
        local = combine_et(last_business_day_next_month(obs), 8, 30)
    elif series_id == "WALCL":
        local = combine_et(next_business_day(obs), 16, 30)
    else:
        local = combine_et(next_business_day(obs), 9, 30)
    return pd.Timestamp(local.astimezone(UTC))


def release_method(series_id: str) -> str:
    if series_id in {"UNRATE", "PAYEMS"}:
        return "standard_employment_first_friday_next_month_0830_et"
    if series_id == "CPIAUCSL":
        return "standard_cpi_first_business_day_on_or_after_10th_next_month_0830_et"
    if series_id in {"PCEPI", "PCEPILFE"}:
        return "standard_pce_last_business_day_next_month_0830_et"
    if series_id == "WALCL":
        return "standard_weekly_fed_h41_next_business_day_1630_et"
    return "conservative_daily_next_business_day_0930_et"


def tradable_after(release_ts_utc: pd.Timestamp) -> pd.Timestamp:
    local = release_ts_utc.tz_convert(ET)
    market_open = local.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = local.replace(hour=16, minute=0, second=0, microsecond=0)
    if local <= market_open:
        return pd.Timestamp(market_open.astimezone(UTC))
    if local < market_close:
        return pd.Timestamp(local.astimezone(UTC))
    next_open = combine_et(next_business_day(local.date()), 9, 30)
    return pd.Timestamp(next_open.astimezone(UTC))


def combine_et(day: object, hour: int, minute: int) -> pd.Timestamp:
    return pd.Timestamp(year=day.year, month=day.month, day=day.day, hour=hour, minute=minute, tz=ET)


def next_month_date(day: object, target_day: int) -> object:
    year = day.year + int(day.month == 12)
    month = 1 if day.month == 12 else day.month + 1
    return pd.Timestamp(year=year, month=month, day=min(target_day, monthrange(year, month)[1])).date()


def first_friday_next_month(day: object) -> object:
    cur = next_month_date(day, 1)
    while cur.weekday() != 4:
        cur = (pd.Timestamp(cur) + pd.Timedelta(days=1)).date()
    return cur


def last_business_day_next_month(day: object) -> object:
    year = day.year + int(day.month == 12)
    month = 1 if day.month == 12 else day.month + 1
    cur = pd.Timestamp(year=year, month=month, day=monthrange(year, month)[1]).date()
    while cur.weekday() >= 5:
        cur = (pd.Timestamp(cur) - pd.Timedelta(days=1)).date()
    return cur


def first_business_day_on_or_after(day: object) -> object:
    cur = day
    while cur.weekday() >= 5:
        cur = (pd.Timestamp(cur) + pd.Timedelta(days=1)).date()
    return cur


def next_business_day(day: object) -> object:
    cur = (pd.Timestamp(day) + pd.Timedelta(days=1)).date()
    while cur.weekday() >= 5:
        cur = (pd.Timestamp(cur) + pd.Timedelta(days=1)).date()
    return cur


def attach_release_repaired_macro(entries: pd.DataFrame, feature: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["lifecycle_id", "symbol", "theme_id", "split_name", "entry_ts", "timing_mode", "exit_mode"]
    out = entries[[c for c in base_cols if c in entries.columns]].copy()
    out["entry_ts_dt"] = pd.to_datetime(entries["entry_ts"], utc=True, errors="coerce")
    out["row_id"] = range(len(out))
    left = out[["row_id", "entry_ts_dt"]].sort_values("entry_ts_dt").copy()
    macro_cols: dict[str, pd.Series] = {}
    availability_cols = []
    for config in SERIES_CONFIGS:
        series = feature[feature["series_id"].eq(config.series_id)].sort_values("tradable_after_ts_utc")
        value_cols = [
            "tradable_after_ts_utc",
            "observation_date",
            "value",
            "value_change_3obs",
            "value_change_12obs",
            "value_change_20obs",
            "pct_change_3obs",
            "pct_change_12obs",
            "pct_change_20obs",
            "release_ts_utc",
            "release_timestamp_method",
        ]
        available_col = f"macro_{config.series_id}_available_flag"
        availability_cols.append(available_col)
        if series.empty:
            macro_cols[available_col] = pd.Series(0, index=out.index)
            continue
        merged = pd.merge_asof(left, series[value_cols], left_on="entry_ts_dt", right_on="tradable_after_ts_utc", direction="backward")
        merged = merged.set_index("row_id")
        macro_cols[available_col] = out["row_id"].map(merged["value"].notna().astype(int)).fillna(0).astype(int)
        for col in value_cols[1:]:
            macro_cols[f"macro_{config.series_id}_{col}"] = out["row_id"].map(merged[col])
    wide = pd.concat([out, pd.DataFrame(macro_cols, index=out.index)], axis=1)
    wide["macro_series_available_count"] = wide[availability_cols].sum(axis=1)
    wide["macro_employment_state"] = wide.apply(classify_employment, axis=1)
    wide["macro_inflation_state"] = wide.apply(classify_inflation, axis=1)
    wide["macro_rates_state"] = wide.apply(classify_rates, axis=1)
    wide["macro_dollar_state"] = wide.apply(classify_dollar, axis=1)
    wide["macro_oil_state"] = wide.apply(classify_oil, axis=1)
    wide["macro_credit_state"] = wide.apply(classify_credit, axis=1)
    wide["macro_liquidity_state"] = wide.apply(classify_liquidity, axis=1)
    wide["macro_overall_state"] = wide.apply(classify_macro_overall, axis=1)
    wide["macro_action_modifier"] = wide.apply(classify_macro_action_modifier, axis=1)
    wide["macro_raw_source_gap_flag"] = wide["macro_series_available_count"].eq(0).astype(int)
    wide["macro_release_timestamp_repaired_flag"] = wide["macro_series_available_count"].gt(0).astype(int)
    wide["macro_release_calendar_gap_flag"] = 0
    wide["macro_vintage_source_gap_flag"] = 1
    wide["macro_latest_vintage_gap_flag"] = 1
    wide["macro_asof_certified_for_assignment_flag"] = 0
    wide["macro_asof_provisional_for_diagnostic_flag"] = wide["macro_series_available_count"].gt(0).astype(int)
    keep = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "split_name",
        "entry_ts",
        "timing_mode",
        "exit_mode",
        "macro_series_available_count",
        "macro_employment_state",
        "macro_inflation_state",
        "macro_rates_state",
        "macro_dollar_state",
        "macro_oil_state",
        "macro_credit_state",
        "macro_liquidity_state",
        "macro_overall_state",
        "macro_action_modifier",
        "macro_raw_source_gap_flag",
        "macro_release_timestamp_repaired_flag",
        "macro_release_calendar_gap_flag",
        "macro_vintage_source_gap_flag",
        "macro_latest_vintage_gap_flag",
        "macro_asof_certified_for_assignment_flag",
        "macro_asof_provisional_for_diagnostic_flag",
    ]
    return wide[keep].copy()


def build_source_audit(raw: pd.DataFrame, feature: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for config in SERIES_CONFIGS:
        raw_series = raw[raw["series_id"].eq(config.series_id)]
        features = feature[feature["series_id"].eq(config.series_id)]
        rows.append(
            {
                "series_id": config.series_id,
                "category": config.category,
                "frequency": config.frequency,
                "fetched_flag": int(raw_series["fetch_status"].eq("FETCHED").any()) if not raw_series.empty else 0,
                "feature_rows": int(len(features)),
                "first_observation": str(features["observation_date"].min()) if not features.empty else "",
                "last_observation": str(features["observation_date"].max()) if not features.empty else "",
                "first_tradable_after_ts_utc": str(features["tradable_after_ts_utc"].min()) if not features.empty else "",
                "last_tradable_after_ts_utc": str(features["tradable_after_ts_utc"].max()) if not features.empty else "",
                "release_timestamp_method": str(features["release_timestamp_method"].iloc[0]) if not features.empty else "",
                "release_time_repaired_flag": int(not features.empty),
                "exact_release_calendar_verified_flag": 0,
                "latest_vintage_only_flag": 1,
                "vintage_asof_certified_flag": 0,
                "assignment_blocker_flag": 1,
            }
        )
    return pd.DataFrame(rows)


def build_coverage_after_repair(execution: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    scopes = {
        "execution_all_variants": context,
        "execution_delay1d_existing": context[context["timing_mode"].eq("delay1d") & context["exit_mode"].eq("existing_exit")].copy(),
        "task639_core_delay1d_existing": context.loc[task639_core_index(execution)].copy(),
    }
    rows = []
    for scope, panel in scopes.items():
        release_repaired = pd.to_numeric(panel["macro_release_timestamp_repaired_flag"], errors="coerce").fillna(0).eq(1)
        vintage_gap = pd.to_numeric(panel["macro_latest_vintage_gap_flag"], errors="coerce").fillna(1).eq(1)
        certified = pd.to_numeric(panel["macro_asof_certified_for_assignment_flag"], errors="coerce").fillna(0).eq(1)
        provisional = pd.to_numeric(panel["macro_asof_provisional_for_diagnostic_flag"], errors="coerce").fillna(0).eq(1)
        rows.append(
            {
                "scope": scope,
                "row_count": int(len(panel)),
                "lifecycle_count": int(panel["lifecycle_id"].nunique()) if not panel.empty else 0,
                "release_timestamp_repaired_rows": int(release_repaired.sum()),
                "release_timestamp_repaired_rate": rate(release_repaired.sum(), len(panel)),
                "latest_vintage_gap_rows": int(vintage_gap.sum()),
                "latest_vintage_gap_rate": rate(vintage_gap.sum(), len(panel)),
                "strict_assignment_eligible_rows": int(certified.sum()),
                "strict_assignment_eligible_rate": rate(certified.sum(), len(panel)),
                "provisional_diagnostic_eligible_rows": int(provisional.sum()),
                "provisional_diagnostic_eligible_rate": rate(provisional.sum(), len(panel)),
                "median_macro_series_available": float(panel["macro_series_available_count"].median()) if not panel.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def task639_core_index(execution: pd.DataFrame) -> pd.Series:
    core = (
        pd.to_numeric(execution.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(execution.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return core & execution["timing_mode"].eq("delay1d") & execution["exit_mode"].eq("existing_exit")


def build_task654_coverage_bridge(coverage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    prior = {
        "execution_all_variants": {"release_or_macro_covered_rate": 0.0942348573785576, "strict_assignment_eligible_rate": 0.0},
        "execution_delay1d_existing": {"release_or_macro_covered_rate": 0.0980780661779275, "strict_assignment_eligible_rate": 0.0},
        "task639_core_delay1d_existing": {"release_or_macro_covered_rate": 0.1591610117211598, "strict_assignment_eligible_rate": 0.0},
    }
    for _, row in coverage.iterrows():
        scope = str(row["scope"])
        before = prior.get(scope, {"release_or_macro_covered_rate": 0.0, "strict_assignment_eligible_rate": 0.0})
        rows.append(
            {
                "scope": scope,
                "task654_macro_context_covered_rate_before": before["release_or_macro_covered_rate"],
                "task655_release_repaired_rate_after": float(row["release_timestamp_repaired_rate"]),
                "task654_strict_assignment_rate_before": before["strict_assignment_eligible_rate"],
                "task655_strict_assignment_rate_after": float(row["strict_assignment_eligible_rate"]),
                "task655_provisional_diagnostic_rate_after": float(row["provisional_diagnostic_eligible_rate"]),
                "remaining_blocker": "latest_vintage_asof_not_certified",
            }
        )
    return pd.DataFrame(rows)


def build_pass_fail(source_audit: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    all_fetched = int(source_audit["fetched_flag"].eq(1).all())
    all_release_repaired = int(source_audit["release_time_repaired_flag"].eq(1).all())
    exact_verified = int(source_audit["exact_release_calendar_verified_flag"].eq(1).all())
    vintage_certified = int(source_audit["vintage_asof_certified_flag"].eq(1).all())
    task639 = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    return pd.DataFrame(
        [
            {"gate": "macro_sources_refreshed", "pass_flag": all_fetched, "observed_value": f"fetched={int(source_audit['fetched_flag'].sum())}/{len(source_audit)}", "required_value": "all configured FRED graph series fetched"},
            {"gate": "release_timestamp_repair_built", "pass_flag": all_release_repaired, "observed_value": f"repaired={int(source_audit['release_time_repaired_flag'].sum())}/{len(source_audit)}", "required_value": "all series get deterministic release timestamps"},
            {"gate": "task639_core_release_repair_coverage", "pass_flag": int(float(task639["release_timestamp_repaired_rate"]) >= 0.95), "observed_value": f"rate={float(task639['release_timestamp_repaired_rate']):.4f}", "required_value": ">=0.95 Task639 core rows have release-time repaired macro context"},
            {"gate": "exact_release_calendar_verified", "pass_flag": exact_verified, "observed_value": f"verified={int(source_audit['exact_release_calendar_verified_flag'].sum())}/{len(source_audit)}", "required_value": "official exact release calendar per observation"},
            {"gate": "vintage_asof_certified", "pass_flag": vintage_certified, "observed_value": f"certified={int(source_audit['vintage_asof_certified_flag'].sum())}/{len(source_audit)}", "required_value": "ALFRED/FRED vintage as-of values available"},
            {"gate": "strict_assignment_eligible", "pass_flag": int(float(task639["strict_assignment_eligible_rate"]) >= 0.80), "observed_value": f"rate={float(task639['strict_assignment_eligible_rate']):.4f}", "required_value": ">=0.80 strict assignment coverage before relation authority"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "macro release repair diagnostic only", "required_value": "exact calendar plus vintage plus relation/backtest promotion gates"},
        ]
    )


def build_decision(source_audit: pd.DataFrame, coverage: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    task639 = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "RELEASE_TIME_REPAIRED_VINTAGE_ASOF_STILL_BLOCKS_ASSIGNMENT",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "series_count": int(len(source_audit)),
                "task639_core_rows": int(task639["row_count"]),
                "task639_release_timestamp_repaired_rate": float(task639["release_timestamp_repaired_rate"]),
                "task639_provisional_diagnostic_eligible_rate": float(task639["provisional_diagnostic_eligible_rate"]),
                "task639_strict_assignment_eligible_rate": float(task639["strict_assignment_eligible_rate"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Use Task655 macro context as diagnostic input only. Task656 should add exact official release calendars and ALFRED/FRED vintage values before relation engine assignment authority.",
            }
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    source_audit: pd.DataFrame,
    coverage: pd.DataFrame,
    bridge: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task655 Macro As-Of Release Repair",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639 release-time repaired rate: {float(d['task639_release_timestamp_repaired_rate']):.4f}.",
        f"- Task639 provisional diagnostic eligible rate: {float(d['task639_provisional_diagnostic_eligible_rate']):.4f}.",
        f"- Task639 strict assignment eligible rate: {float(d['task639_strict_assignment_eligible_rate']):.4f}.",
        "- What changed: FRED graph sources were refreshed and deterministic ET release timestamps were attached.",
        "- Next action: exact official release calendars and ALFRED/FRED vintage values are still needed before trading authority.",
        "",
        "## Quant Expert Report",
        "",
        "Task655 repairs the release-time side of the macro as-of problem. It does not claim full vintage correctness.",
        "",
        "### Data Source And Source Readiness",
        "",
        table(source_audit),
        "",
        "### Exact Join Keys",
        "",
        "The output `task_655_macro_asof_context_panel.csv` is keyed by `lifecycle_id`, `entry_ts`, `timing_mode`, and `exit_mode`. Macro features are attached with `tradable_after_ts_utc <= entry_ts`.",
        "",
        "### Leakage Audit",
        "",
        "Release timestamps are applied before merge-as-of. Latest-vintage values remain marked with `macro_latest_vintage_gap_flag=1`, so strict assignment stays blocked.",
        "",
        "### Split/OOS Metrics",
        "",
        "No PnL strategy is promoted in Task655. This is data repair only.",
        "",
        "### Failure Decomposition",
        "",
        table(coverage),
        "",
        "### Task654 Bridge",
        "",
        table(bridge),
        "",
        "### Remaining Blockers",
        "",
        table(pass_fail),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We fixed the easier half: when a macro number could first be traded.",
        "",
        "But the harder half remains: whether the value is the exact old value known on that day, not a later revised value.",
        "",
        "So this is progress, but still not trading permission.",
        "",
        "## Artifact Manifest",
        "",
        "- `task_655_macro_asof_context_panel.csv`",
        "- `task_655_macro_source_audit.csv`",
        "- `task_655_coverage_after_release_repair.csv`",
        "- `task_655_task654_coverage_bridge.csv`",
        "- `task_655_pass_fail_matrix.csv`",
        "- `task_655_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_655_macro_asof_release_repair.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def rate(count: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return float(count) / float(total)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--macro-raw-path", type=Path)
    args = parser.parse_args()
    result = build_task655_macro_asof_release_repair(out_dir=args.out_dir, raw_dir=args.raw_dir, macro_raw_path=args.macro_raw_path)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"task639_release_repaired={float(decision['task639_release_timestamp_repaired_rate']):.4f} "
        f"strict_assignment={float(decision['task639_strict_assignment_eligible_rate']):.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
