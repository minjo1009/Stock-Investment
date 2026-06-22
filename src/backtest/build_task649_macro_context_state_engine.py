from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task649"
REPORT_DIR = Path("docs/reports/task_649_macro_context_state_engine")
RAW_DIR = Path("data/raw/macro_fred/task_649")
TASK648_PANEL = Path("docs/reports/task_648_trading_context_state_engine/task_648_trading_context_state_panel.csv")


@dataclass(frozen=True)
class FredSeriesConfig:
    series_id: str
    category: str
    description: str
    frequency: str
    conservative_lag_days: int


SERIES_CONFIGS = [
    FredSeriesConfig("UNRATE", "employment", "Civilian unemployment rate", "monthly", 45),
    FredSeriesConfig("PAYEMS", "employment", "Total nonfarm payrolls", "monthly", 45),
    FredSeriesConfig("CPIAUCSL", "inflation", "CPI all urban consumers all items", "monthly", 45),
    FredSeriesConfig("PCEPI", "inflation", "PCE price index", "monthly", 45),
    FredSeriesConfig("PCEPILFE", "inflation", "Core PCE price index", "monthly", 45),
    FredSeriesConfig("DFF", "fed_rates", "Effective federal funds rate", "daily", 1),
    FredSeriesConfig("DGS2", "fed_rates", "2-year Treasury yield", "daily", 1),
    FredSeriesConfig("DGS10", "fed_rates", "10-year Treasury yield", "daily", 1),
    FredSeriesConfig("T10Y2Y", "fed_rates", "10-year minus 2-year Treasury spread", "daily", 1),
    FredSeriesConfig("DTWEXBGS", "dollar", "Trade weighted US dollar index broad goods and services", "daily", 1),
    FredSeriesConfig("DCOILWTICO", "oil", "WTI crude oil price", "daily", 1),
    FredSeriesConfig("BAMLH0A0HYM2", "credit", "High yield option-adjusted spread", "daily", 1),
    FredSeriesConfig("BAA10Y", "credit", "Moody's Baa corporate bond yield less 10-year Treasury", "daily", 1),
    FredSeriesConfig("WALCL", "liquidity", "Federal Reserve total assets", "weekly", 7),
    FredSeriesConfig("RRPONTSYD", "liquidity", "Overnight reverse repurchase agreements", "daily", 1),
]


def build_task649(
    *,
    task648_panel: Path = TASK648_PANEL,
    raw_dir: Path = RAW_DIR,
    out_dir: Path = REPORT_DIR,
    macro_raw_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    task_panel = pd.read_csv(task648_panel)
    start_date, end_date = infer_date_range(task_panel)
    if macro_raw_path is None:
        macro_raw = fetch_macro_series(start_date=start_date, end_date=end_date)
        macro_raw.to_csv(raw_dir / "fred_macro_series_latest_vintage.csv", index=False, encoding="utf-8-sig")
    else:
        macro_raw = pd.read_csv(macro_raw_path)
    macro_features = build_macro_feature_panel(macro_raw)
    macro_features.to_csv(raw_dir / "fred_macro_feature_panel_latest_vintage.csv", index=False, encoding="utf-8-sig")

    entry_macro = attach_macro_to_entries(task_panel, macro_features)
    augmented = classify_augmented_context(entry_macro)
    evaluation = summarize_augmented_context(augmented)
    source_audit = build_source_audit(macro_raw, macro_features)
    pass_fail = build_pass_fail(augmented, source_audit)
    decision = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "MACRO_SOURCES_ATTACHED_PROVISIONAL_STATE_ENGINE_NOT_PROMOTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "entry_rows": int(len(augmented)),
                "macro_series_count": int(macro_raw["series_id"].nunique()) if not macro_raw.empty else 0,
                "augmented_context_state_count": int(augmented["augmented_trading_context_state"].nunique()),
                "vintage_source_gap_flag": 1,
                "release_calendar_gap_flag": 1,
                "strategy_promotion_flag": 0,
            }
        ]
    )

    augmented.to_csv(out_dir / "task_649_macro_augmented_context_panel.csv", index=False, encoding="utf-8-sig")
    evaluation.to_csv(out_dir / "task_649_macro_context_evaluation.csv", index=False, encoding="utf-8-sig")
    source_audit.to_csv(out_dir / "task_649_macro_source_audit.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_649_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_649_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, evaluation, source_audit, pass_fail, decision)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "augmented": augmented,
        "evaluation": evaluation,
        "source_audit": source_audit,
        "pass_fail": pass_fail,
        "decision": decision,
        "macro_raw": macro_raw,
    }


def infer_date_range(task_panel: pd.DataFrame) -> tuple[str, str]:
    entry = pd.to_datetime(task_panel["entry_ts"], utc=True, errors="coerce")
    start = (entry.min() - pd.Timedelta(days=540)).date().isoformat()
    end = (entry.max() + pd.Timedelta(days=5)).date().isoformat()
    return start, end


def fetch_macro_series(*, start_date: str, end_date: str) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for config in SERIES_CONFIGS:
        params = urlencode({"id": config.series_id, "cosd": start_date, "coed": end_date})
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{params}"
        try:
            frame = pd.read_csv(url)
            if frame.empty or config.series_id not in frame.columns:
                rows.append(error_row(config, url, "missing_series_column"))
                continue
            out = frame.rename(columns={"observation_date": "observation_date", config.series_id: "value"})
            out["value"] = pd.to_numeric(out["value"], errors="coerce")
            out = out.dropna(subset=["value"])
            out["series_id"] = config.series_id
            out["category"] = config.category
            out["description"] = config.description
            out["frequency"] = config.frequency
            out["conservative_lag_days"] = config.conservative_lag_days
            out["source_url"] = url
            out["fetch_status"] = "FETCHED"
            out["latest_vintage_only_flag"] = 1
            out["exact_release_timestamp_available_flag"] = 0
            rows.append(out)
        except Exception as exc:  # noqa: BLE001
            rows.append(error_row(config, url, str(exc)))
    if not rows:
        return pd.DataFrame()
    raw = pd.concat(rows, ignore_index=True)
    raw["observation_date"] = pd.to_datetime(raw["observation_date"], errors="coerce").dt.date.astype(str)
    return raw


def error_row(config: FredSeriesConfig, url: str, error: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "observation_date": "",
                "value": pd.NA,
                "series_id": config.series_id,
                "category": config.category,
                "description": config.description,
                "frequency": config.frequency,
                "conservative_lag_days": config.conservative_lag_days,
                "source_url": url,
                "fetch_status": "FAILED",
                "fetch_error": error,
                "latest_vintage_only_flag": 1,
                "exact_release_timestamp_available_flag": 0,
            }
        ]
    )


def build_macro_feature_panel(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return raw
    frame = raw[raw["fetch_status"].eq("FETCHED")].copy()
    frame["observation_dt"] = pd.to_datetime(frame["observation_date"], utc=True, errors="coerce")
    frame["tradable_after_ts"] = frame["observation_dt"] + pd.to_timedelta(pd.to_numeric(frame["conservative_lag_days"], errors="coerce").fillna(45), unit="D")
    frame = frame.sort_values(["series_id", "observation_dt"])
    grouped = frame.groupby("series_id", group_keys=False)
    frame["value_change_1obs"] = grouped["value"].diff(1)
    frame["value_change_3obs"] = grouped["value"].diff(3)
    frame["value_change_12obs"] = grouped["value"].diff(12)
    frame["value_change_20obs"] = grouped["value"].diff(20)
    frame["pct_change_3obs"] = grouped["value"].pct_change(3)
    frame["pct_change_12obs"] = grouped["value"].pct_change(12)
    frame["pct_change_20obs"] = grouped["value"].pct_change(20)
    frame["macro_asof_method"] = "latest_vintage_conservative_lag"
    frame["vintage_source_gap_flag"] = 1
    frame["release_calendar_gap_flag"] = 1
    return frame


def attach_macro_to_entries(entries: pd.DataFrame, macro_features: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    out["entry_ts_dt"] = pd.to_datetime(out["entry_ts"], utc=True, errors="coerce")
    left = out[["lifecycle_id", "entry_ts_dt"]].sort_values("entry_ts_dt").copy()
    macro_cols: dict[str, pd.Series] = {}
    for config in SERIES_CONFIGS:
        series = macro_features[macro_features["series_id"].eq(config.series_id)].sort_values("tradable_after_ts")
        cols = ["tradable_after_ts", "observation_date", "value", "value_change_3obs", "value_change_12obs", "value_change_20obs", "pct_change_3obs", "pct_change_12obs", "pct_change_20obs"]
        if series.empty:
            macro_cols[f"macro_{config.series_id}_available_flag"] = pd.Series(0, index=out.index)
            continue
        merged = pd.merge_asof(left, series[cols], left_on="entry_ts_dt", right_on="tradable_after_ts", direction="backward")
        merged = merged.set_index("lifecycle_id")
        macro_cols[f"macro_{config.series_id}_available_flag"] = out["lifecycle_id"].map(merged["value"].notna().astype(int)).fillna(0).astype(int)
        for col in cols[1:]:
            macro_cols[f"macro_{config.series_id}_{col}"] = out["lifecycle_id"].map(merged[col])
    out = pd.concat([out, pd.DataFrame(macro_cols, index=out.index)], axis=1)
    out["macro_employment_state"] = out.apply(classify_employment, axis=1)
    out["macro_inflation_state"] = out.apply(classify_inflation, axis=1)
    out["macro_rates_state"] = out.apply(classify_rates, axis=1)
    out["macro_dollar_state"] = out.apply(classify_dollar, axis=1)
    out["macro_oil_state"] = out.apply(classify_oil, axis=1)
    out["macro_credit_state"] = out.apply(classify_credit, axis=1)
    out["macro_liquidity_state"] = out.apply(classify_liquidity, axis=1)
    out["macro_overall_state"] = out.apply(classify_macro_overall, axis=1)
    out["macro_action_modifier"] = out.apply(classify_macro_action_modifier, axis=1)
    out["macro_raw_source_gap_flag"] = 0
    out["macro_vintage_source_gap_flag"] = 1
    out["macro_release_calendar_gap_flag"] = 1
    return out


def classify_employment(row: pd.Series) -> str:
    unrate_delta = num(row.get("macro_UNRATE_value_change_3obs"))
    payroll_pct = num(row.get("macro_PAYEMS_pct_change_3obs"))
    if pd.isna(unrate_delta) and pd.isna(payroll_pct):
        return "source_gap"
    if unrate_delta >= 0.3 or payroll_pct <= 0.0005:
        return "growth_weakening"
    if unrate_delta <= -0.2 and payroll_pct >= 0.002:
        return "growth_supportive"
    return "growth_mixed"


def classify_inflation(row: pd.Series) -> str:
    cpi_yoy = num(row.get("macro_CPIAUCSL_pct_change_12obs"))
    core_pce_yoy = num(row.get("macro_PCEPILFE_pct_change_12obs"))
    core_pce_3 = num(row.get("macro_PCEPILFE_pct_change_3obs"))
    if pd.isna(cpi_yoy) and pd.isna(core_pce_yoy):
        return "source_gap"
    high = max(v for v in [cpi_yoy, core_pce_yoy] if not pd.isna(v))
    if high >= 0.035 and (pd.isna(core_pce_3) or core_pce_3 > 0.006):
        return "inflation_pressure"
    if high <= 0.032 or (not pd.isna(core_pce_3) and core_pce_3 <= 0.004):
        return "inflation_cooling"
    return "inflation_mixed"


def classify_rates(row: pd.Series) -> str:
    dgs10_chg = num(row.get("macro_DGS10_value_change_20obs"))
    dgs2_chg = num(row.get("macro_DGS2_value_change_20obs"))
    if pd.isna(dgs10_chg) and pd.isna(dgs2_chg):
        return "source_gap"
    if max(v for v in [dgs10_chg, dgs2_chg] if not pd.isna(v)) >= 0.25:
        return "rates_pressure"
    if min(v for v in [dgs10_chg, dgs2_chg] if not pd.isna(v)) <= -0.25:
        return "rates_easing"
    return "rates_mixed"


def classify_dollar(row: pd.Series) -> str:
    chg = num(row.get("macro_DTWEXBGS_pct_change_20obs"))
    if pd.isna(chg):
        return "source_gap"
    if chg >= 0.015:
        return "dollar_pressure"
    if chg <= -0.015:
        return "dollar_easing"
    return "dollar_mixed"


def classify_oil(row: pd.Series) -> str:
    chg = num(row.get("macro_DCOILWTICO_pct_change_20obs"))
    if pd.isna(chg):
        return "source_gap"
    if chg >= 0.10:
        return "oil_pressure"
    if chg <= -0.10:
        return "oil_easing"
    return "oil_mixed"


def classify_credit(row: pd.Series) -> str:
    hy = num(row.get("macro_BAMLH0A0HYM2_value"))
    hy_chg = num(row.get("macro_BAMLH0A0HYM2_value_change_20obs"))
    baa = num(row.get("macro_BAA10Y_value"))
    if pd.isna(hy) and pd.isna(baa):
        return "source_gap"
    if (not pd.isna(hy) and hy >= 4.5) or (not pd.isna(hy_chg) and hy_chg >= 0.5) or (not pd.isna(baa) and baa >= 2.5):
        return "credit_stress"
    if (not pd.isna(hy) and hy <= 3.5) and (pd.isna(hy_chg) or hy_chg <= 0.1):
        return "credit_supportive"
    return "credit_mixed"


def classify_liquidity(row: pd.Series) -> str:
    walcl_chg = num(row.get("macro_WALCL_pct_change_3obs"))
    rrp_chg = num(row.get("macro_RRPONTSYD_pct_change_20obs"))
    if pd.isna(walcl_chg) and pd.isna(rrp_chg):
        return "source_gap"
    if (not pd.isna(walcl_chg) and walcl_chg < -0.01) and (pd.isna(rrp_chg) or rrp_chg > -0.10):
        return "liquidity_tightening"
    if (not pd.isna(walcl_chg) and walcl_chg > 0.01) or (not pd.isna(rrp_chg) and rrp_chg < -0.20):
        return "liquidity_supportive"
    return "liquidity_mixed"


def classify_macro_overall(row: pd.Series) -> str:
    states = {
        "employment": row["macro_employment_state"],
        "inflation": row["macro_inflation_state"],
        "rates": row["macro_rates_state"],
        "dollar": row["macro_dollar_state"],
        "oil": row["macro_oil_state"],
        "credit": row["macro_credit_state"],
        "liquidity": row["macro_liquidity_state"],
    }
    if all(v == "source_gap" for v in states.values()):
        return "source_gap"
    hostile = sum(
        states[k] in {"growth_weakening", "inflation_pressure", "rates_pressure", "dollar_pressure", "oil_pressure", "credit_stress", "liquidity_tightening"}
        for k in states
    )
    supportive = sum(
        states[k] in {"growth_supportive", "inflation_cooling", "rates_easing", "dollar_easing", "oil_easing", "credit_supportive", "liquidity_supportive"}
        for k in states
    )
    if states["credit"] == "credit_stress" or hostile >= 3:
        return "macro_hostile"
    if supportive >= 3 and hostile <= 1:
        return "macro_supportive"
    return "macro_mixed"


def classify_macro_action_modifier(row: pd.Series) -> str:
    overall = row["macro_overall_state"]
    if overall == "macro_hostile":
        return "macro_size_down_or_block"
    if overall == "macro_supportive":
        return "macro_supports_risk"
    if overall == "source_gap":
        return "macro_source_gap"
    return "macro_neutral_or_mixed"


def classify_augmented_context(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["augmented_trading_context_state"] = out.apply(augmented_state, axis=1)
    out["augmented_action_bucket_diagnostic"] = out.apply(augmented_action, axis=1)
    out["label_used_in_macro_assignment_flag"] = 0
    out["outcome_used_in_macro_assignment_flag"] = 0
    out["strategy_promotion_flag"] = 0
    return out


def augmented_state(row: pd.Series) -> str:
    previous = str(row.get("provisional_trading_context_state", "source_gap"))
    macro = row["macro_overall_state"]
    if macro == "source_gap":
        return f"{previous}_macro_source_gap"
    if macro == "macro_hostile" and previous in {"supportive_alignment", "mixed_alignment"}:
        return "macro_conflicted_alignment"
    if macro == "macro_hostile" and previous in {"risk_off_override", "conflicted_alignment"}:
        return "risk_off_override_macro_confirmed"
    if macro == "macro_supportive" and previous == "supportive_alignment":
        return "supportive_alignment_macro_confirmed"
    if macro == "macro_supportive" and previous == "mixed_alignment":
        return "mixed_alignment_macro_supportive"
    if macro == "macro_supportive" and previous == "source_gap":
        return "source_gap_company_or_policy_missing_macro_supportive"
    return f"{previous}_macro_mixed"


def augmented_action(row: pd.Series) -> str:
    state = row["augmented_trading_context_state"]
    prior_action = str(row.get("suggested_action_bucket_diagnostic", "NO_ACTION_CONTEXT_WEAK"))
    if state.startswith("risk_off_override"):
        return "BLOCK_HOLD"
    if state == "macro_conflicted_alignment":
        return "SIZE_DOWN"
    if state.endswith("macro_source_gap"):
        return "NO_ACTION_SOURCE_GAP"
    if state == "supportive_alignment_macro_confirmed":
        return "FULL_ENTRY_CANDIDATE"
    if state == "mixed_alignment_macro_supportive" and prior_action in {"NORMAL_ENTRY", "NO_ACTION_CONTEXT_WEAK"}:
        return "NORMAL_ENTRY"
    return prior_action


def summarize_augmented_context(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (split, state, action), group in panel.groupby(["split_name", "augmented_trading_context_state", "augmented_action_bucket_diagnostic"], dropna=False):
        ret = pd.to_numeric(group.get("net_return_from_entry"), errors="coerce")
        wins = pd.to_numeric(group.get("win_flag"), errors="coerce")
        er = pd.to_numeric(group.get("entry_reduce_failure_flag"), errors="coerce")
        rows.append(
            {
                "split_name": split,
                "augmented_trading_context_state": state,
                "augmented_action_bucket_diagnostic": action,
                "entry_count": int(len(group)),
                "avg_net_return_pct": round(float(ret.mean()), 6) if ret.notna().any() else 0.0,
                "win_rate": round(float(wins.mean()), 6) if wins.notna().any() else 0.0,
                "entry_reduce_failure_rate": round(float(er.mean()), 6) if er.notna().any() else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "entry_count"], ascending=[True, False]).reset_index(drop=True)


def build_source_audit(raw: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for config in SERIES_CONFIGS:
        series = raw[raw["series_id"].eq(config.series_id)]
        fetched = int(series["fetch_status"].eq("FETCHED").any()) if not series.empty else 0
        feature_rows = features[features["series_id"].eq(config.series_id)] if not features.empty else pd.DataFrame()
        rows.append(
            {
                "series_id": config.series_id,
                "category": config.category,
                "frequency": config.frequency,
                "fetched_flag": fetched,
                "feature_rows": int(len(feature_rows)),
                "first_observation": str(feature_rows["observation_date"].min()) if not feature_rows.empty else "",
                "last_observation": str(feature_rows["observation_date"].max()) if not feature_rows.empty else "",
                "conservative_lag_days": config.conservative_lag_days,
                "latest_vintage_only_flag": 1,
                "exact_release_timestamp_available_flag": 0,
                "promotion_blocker_flag": 1,
            }
        )
    return pd.DataFrame(rows)


def build_pass_fail(panel: pd.DataFrame, source_audit: pd.DataFrame) -> pd.DataFrame:
    all_fetched = int(source_audit["fetched_flag"].eq(1).all())
    return pd.DataFrame(
        [
            {"gate": "macro_sources_fetched", "pass_flag": all_fetched, "observed": f"fetched={int(source_audit['fetched_flag'].sum())}/{len(source_audit)}", "required": "all configured macro series fetched"},
            {"gate": "macro_attached_to_entries", "pass_flag": int(panel["macro_overall_state"].ne("source_gap").any()), "observed": f"rows={len(panel)}", "required": "at least one entry has macro state"},
            {"gate": "no_label_or_outcome_assignment", "pass_flag": 1, "observed": "macro/state assignment does not read returns or labels", "required": "labels and outcomes evaluation-only"},
            {"gate": "vintage_gap_reported", "pass_flag": int(panel["macro_vintage_source_gap_flag"].eq(1).all()), "observed": "latest FRED vintage only", "required": "latest-vintage limitation must be explicit"},
            {"gate": "release_calendar_gap_reported", "pass_flag": int(panel["macro_release_calendar_gap_flag"].eq(1).all()), "observed": "conservative lag instead of exact release timestamp", "required": "exact release gap must be explicit"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed": "macro context diagnostic only", "required": "requires ALFRED/vintage or exact release calendar, split/account/cost validation, live source readiness"},
        ]
    )


def write_report(out_dir: Path, evaluation: pd.DataFrame, source_audit: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> None:
    lines = [
        "# Task649 Macro Context State Engine",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `MACRO_SOURCES_ATTACHED_PROVISIONAL_STATE_ENGINE_NOT_PROMOTED`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- FRED macro series were attached to Task648 entries with conservative as-of lag.",
        "- This is still provisional because latest-vintage values and exact release timestamp gaps remain.",
        "",
        "## Quant Expert Report",
        "",
        "Task649 adds employment, inflation, Fed/rates, dollar, oil, credit, and liquidity context to the trading context state engine.",
        "",
        "The first-stage as-of rule is conservative:",
        "",
        "- daily series: observation date + 1 day",
        "- weekly series: observation date + 7 days",
        "- monthly series: observation date + 45 days",
        "",
        "This reduces obvious timing leakage but does not solve latest-vintage revision leakage. Promotion remains blocked.",
        "",
        "### Macro Context Evaluation",
        "",
        table(evaluation),
        "",
        "### Macro Source Audit",
        "",
        table(source_audit),
        "",
        "### Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- We added real macro sources: jobs, inflation, Fed/rates, dollar, oil, credit, and liquidity.",
        "- We attached them to each candidate only after a conservative tradable-after delay.",
        "- This makes the context engine smarter, but it is not final yet.",
        "- The remaining issue is that FRED CSV gives latest revised values, not perfect historical vintage truth.",
        "- So this is a better diagnostic engine, not a tradable approval.",
        "",
        "## Artifact Manifest",
        "",
        "- `task_649_macro_augmented_context_panel.csv`",
        "- `task_649_macro_context_evaluation.csv`",
        "- `task_649_macro_source_audit.csv`",
        "- `task_649_pass_fail_matrix.csv`",
        "- `task_649_decision.csv`",
        "- `artifact_manifest.csv`",
        "",
    ]
    (out_dir / "task_649_macro_context_state_engine.md").write_text("\n".join(lines), encoding="utf-8")


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def num(value: object) -> float:
    try:
        out = pd.to_numeric(value, errors="coerce")
    except Exception:  # noqa: BLE001
        return float("nan")
    if pd.isna(out):
        return float("nan")
    return float(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--macro-raw-path", type=Path)
    args = parser.parse_args()
    result = build_task649(out_dir=args.out_dir, raw_dir=args.raw_dir, macro_raw_path=args.macro_raw_path)
    decision = result["decision"].iloc[0]
    print(f"[{TASK_ID}] verdict={decision['verdict']} rows={decision['entry_rows']} series={decision['macro_series_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
