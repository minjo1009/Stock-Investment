from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _load_frozen_behavior_state
from src.backtest.analysis_structural_breakout_intraday_backfill_scope_337 import (
    DEFAULT_OUT_DIR,
    build_required_symbol_dates,
)
from src.data.intraday_backfill import DB_PATH, FULL_SESSION_MIN_BARS, load_market_bars_5m


def build_coverage_audit(required_df: pd.DataFrame, bars_df: pd.DataFrame) -> pd.DataFrame:
    if required_df.empty:
        return pd.DataFrame(columns=["symbol", "trade_date", "coverage_status", "bar_count", "source"])
    grouped = (
        bars_df.groupby(["symbol", "bar_date"], dropna=False)
        .agg(
            bar_count=("bar_start_ts", "count"),
            source=("source", lambda s: "|".join(sorted({str(v) for v in s if str(v)}))),
        )
        .reset_index()
        .rename(columns={"bar_date": "trade_date"})
        if not bars_df.empty
        else pd.DataFrame(columns=["symbol", "trade_date", "bar_count", "source"])
    )
    audit = required_df.merge(grouped, on=["symbol", "trade_date"], how="left")
    symbol_set = set(bars_df["symbol"].astype(str).str.upper()) if not bars_df.empty else set()

    def _status(row: pd.Series) -> str:
        if str(row["symbol"]).upper() not in symbol_set:
            return "missing_symbol"
        count = pd.to_numeric(pd.Series([row.get("bar_count")]), errors="coerce").iloc[0]
        if pd.isna(count):
            return "missing_date"
        if int(count) >= FULL_SESSION_MIN_BARS:
            return "covered"
        return "insufficient_window"

    audit["coverage_status"] = audit.apply(_status, axis=1)
    audit["bar_count"] = pd.to_numeric(audit["bar_count"], errors="coerce").fillna(0).astype(int)
    audit["source"] = audit["source"].fillna("")
    return audit[["symbol", "trade_date", "coverage_status", "bar_count", "source"]].sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def build_coverage_summary(audit_df: pd.DataFrame) -> pd.DataFrame:
    if audit_df.empty:
        return pd.DataFrame(columns=["metric", "value"])
    counts = audit_df["coverage_status"].value_counts(dropna=False).to_dict()
    rows = [
        {"metric": "required_trade_dates", "value": int(len(audit_df))},
        {"metric": "covered_trade_count", "value": int(counts.get("covered", 0))},
        {"metric": "missing_symbol_count", "value": int(counts.get("missing_symbol", 0))},
        {"metric": "missing_date_count", "value": int(counts.get("missing_date", 0))},
        {"metric": "insufficient_window_count", "value": int(counts.get("insufficient_window", 0))},
    ]
    return pd.DataFrame(rows)


def readiness_gate(oos_required_df: pd.DataFrame, audit_df: pd.DataFrame) -> dict[str, object]:
    oos_dates = build_required_symbol_dates(oos_required_df)
    oos_audit = oos_dates.merge(audit_df, on=["symbol", "trade_date"], how="left")
    oos_audit["coverage_status"] = oos_audit["coverage_status"].fillna("missing_date")
    covered_total = int((audit_df["coverage_status"] == "covered").sum()) if not audit_df.empty else 0
    oos_covered = int((oos_audit["coverage_status"] == "covered").sum()) if not oos_audit.empty else 0
    symbol_ok = True
    if not oos_audit.empty:
        per_symbol = (
            oos_audit.groupby("symbol")["coverage_status"]
            .apply(lambda s: int((s == "covered").sum()))
            .to_dict()
        )
        symbol_ok = all(count >= 1 for count in per_symbol.values())
    phase2_complete = bool(covered_total > 0 and oos_covered >= 20 and symbol_ok)
    return {
        "covered_trade_count": covered_total,
        "anchored_oos_covered_trade_count": oos_covered,
        "anchored_oos_all_symbols_have_coverage": bool(symbol_ok),
        "task_336_readiness": "ready" if phase2_complete else "phase_2_incomplete",
    }


def provider_comparison_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "provider_name": "alpaca",
                "implemented": True,
                "historical_5m_support": True,
                "auth_mode": "api_key_secret",
                "integration_fit": "high",
                "decision": "primary_initial_adapter",
            },
            {
                "provider_name": "polygon",
                "implemented": False,
                "historical_5m_support": True,
                "auth_mode": "api_key",
                "integration_fit": "medium",
                "decision": "not_implemented",
            },
            {
                "provider_name": "kis",
                "implemented": False,
                "historical_5m_support": False,
                "auth_mode": "env_file_token",
                "integration_fit": "low",
                "decision": "not_implemented",
            },
            {
                "provider_name": "csv_import",
                "implemented": False,
                "historical_5m_support": True,
                "auth_mode": "filesystem",
                "integration_fit": "medium",
                "decision": "not_implemented",
            },
        ]
    )


def _simple_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = [str(col) for col in df.columns]
    header = "| " + " | ".join(cols) + " |"
    divider = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        values = [str("" if pd.isna(row[col]) else row[col]) for col in df.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *rows])


def _report_text(summary_df: pd.DataFrame, gate: dict[str, object], audit_df: pd.DataFrame) -> str:
    lines = [
        "# Task 337: Historical Intraday Ingestion",
        "",
        f"- Task 336 reinterpretation: `NO_DATA_COVERAGE`",
        f"- Covered trade dates: `{gate['covered_trade_count']}`",
        f"- Anchored OOS covered trade dates: `{gate['anchored_oos_covered_trade_count']}`",
        f"- Task 336 readiness: `{gate['task_336_readiness']}`",
        "",
        "## Coverage Summary",
        "",
        _simple_markdown_table(summary_df) if not summary_df.empty else "_No summary available._",
        "",
        "## Readiness Gate",
        "",
        f"- each anchored OOS symbol has coverage: `{gate['anchored_oos_all_symbols_have_coverage']}`",
        f"- full historical ingestion still required: `{gate['task_336_readiness'] != 'ready'}`",
        "",
        "## Top Missing Dates",
        "",
    ]
    missing = audit_df[audit_df["coverage_status"] != "covered"].head(20)
    lines.append(_simple_markdown_table(missing) if not missing.empty else "_No missing rows._")
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append("- Current bottleneck is historical intraday coverage, not strategy edge.")
    lines.append("- Task 336 should only be rerun after Phase 2 historical backfill reaches the readiness gate.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 337: historical intraday coverage audit.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _, oos_df, full_df = _load_frozen_behavior_state()
    required_df = build_required_symbol_dates(full_df[full_df["scope"] == "full_period"].copy())
    bars_df = load_market_bars_5m(Path(args.db_path))
    audit_df = build_coverage_audit(required_df, bars_df)
    summary_df = build_coverage_summary(audit_df)
    gate = readiness_gate(oos_df[oos_df["scope"] == "anchored_oos"].copy(), audit_df)
    provider_df = provider_comparison_df()

    audit_df.to_csv(out_dir / "task_337_intraday_coverage_audit.csv", index=False)
    summary_df.to_csv(out_dir / "task_337_intraday_coverage_summary.csv", index=False)
    provider_df.to_csv(out_dir / "task_337_provider_comparison.csv", index=False)
    (out_dir / "task_337_historical_intraday_ingestion.md").write_text(
        _report_text(summary_df, gate, audit_df),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
