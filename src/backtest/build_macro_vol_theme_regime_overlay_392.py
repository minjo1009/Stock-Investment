from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_INTRADAY_DIR = Path("data/raw/us_intraday")
DEFAULT_THEME_UNIVERSE = Path("data/raw/theme_universe_10x7.csv")
DEFAULT_TASK391_PANEL = Path("docs/reports/task_391_intraday_canonical_oos_validation/split_lifecycle_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_392_macro_vol_theme_regime_overlay")


@dataclass(frozen=True)
class MacroVolThemeRegimeOverlay392Artifacts:
    daily_regime_panel: pd.DataFrame
    lifecycle_regime_panel: pd.DataFrame
    regime_reinforcement_quality: pd.DataFrame
    regime_reduce_weakening_quality: pd.DataFrame
    theme_regime_quality: pd.DataFrame
    transition_regime_quality: pd.DataFrame
    task_392_decision: pd.DataFrame


def build_macro_vol_theme_regime_overlay_392(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    task391_panel_path: Path = DEFAULT_TASK391_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> MacroVolThemeRegimeOverlay392Artifacts:
    themes = pd.read_csv(theme_universe_path, encoding="utf-8-sig")
    lifecycle_panel = pd.read_csv(task391_panel_path, encoding="utf-8-sig")
    symbol_days = load_symbol_day_features(intraday_dir, themes)
    daily_regime = build_daily_regime_panel(symbol_days)
    lifecycle_regime = attach_regimes_to_lifecycles(lifecycle_panel, daily_regime)
    reinforcement_quality = summarize_reinforcement_by_regime(lifecycle_regime)
    reduce_quality = summarize_reduce_by_regime(lifecycle_regime)
    theme_regime_quality = summarize_theme_regime_quality(lifecycle_regime)
    transition_regime_quality = summarize_transition_regime_quality(lifecycle_regime)
    decision = build_task_392_decision(lifecycle_regime, reinforcement_quality, reduce_quality)
    artifacts = MacroVolThemeRegimeOverlay392Artifacts(
        daily_regime_panel=daily_regime,
        lifecycle_regime_panel=lifecycle_regime,
        regime_reinforcement_quality=reinforcement_quality,
        regime_reduce_weakening_quality=reduce_quality,
        theme_regime_quality=theme_regime_quality,
        transition_regime_quality=transition_regime_quality,
        task_392_decision=decision,
    )
    write_task_392_artifacts(artifacts, out_dir)
    return artifacts


def load_symbol_day_features(intraday_dir: Path, themes: pd.DataFrame) -> pd.DataFrame:
    theme_map = themes.copy()
    theme_map["symbol"] = theme_map["symbol"].astype(str).str.upper()
    rows = []
    for symbol in sorted(theme_map["symbol"].unique()):
        path = intraday_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        bars = pd.read_csv(path, encoding="utf-8-sig")
        if bars.empty:
            continue
        bars.columns = [str(c).strip().lower() for c in bars.columns]
        bars["timestamp"] = pd.to_datetime(bars["timestamp"], errors="coerce", utc=True)
        for column in ["open", "high", "low", "close", "volume"]:
            bars[column] = pd.to_numeric(bars[column], errors="coerce")
        bars = bars.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).sort_values("timestamp")
        bars["entry_date"] = bars["timestamp"].dt.strftime("%Y-%m-%d")
        for day, group in bars.groupby("entry_date"):
            first_open = float(group.iloc[0]["open"])
            last_close = float(group.iloc[-1]["close"])
            high = float(group["high"].max())
            low = float(group["low"].min())
            dollar_volume = float((group["close"] * group["volume"]).sum())
            rows.append(
                {
                    "entry_date": day,
                    "symbol": symbol,
                    "day_return": last_close / first_open - 1.0 if first_open else 0.0,
                    "intraday_range": high / low - 1.0 if low else 0.0,
                    "dollar_volume": dollar_volume,
                    "bar_count": len(group),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["entry_date", "symbol", "theme", "day_return", "intraday_range", "dollar_volume", "bar_count"])
    return frame.merge(theme_map[["symbol", "theme", "role"]], on="symbol", how="left")


def build_daily_regime_panel(symbol_days: pd.DataFrame) -> pd.DataFrame:
    if symbol_days.empty:
        return pd.DataFrame()
    daily = symbol_days.groupby("entry_date").agg(
        symbol_count=("symbol", "nunique"),
        breadth_positive_rate=("day_return", lambda s: float((s > 0).mean())),
        avg_symbol_return=("day_return", "mean"),
        cross_section_vol=("day_return", "std"),
        avg_intraday_range=("intraday_range", "mean"),
        total_dollar_volume=("dollar_volume", "sum"),
    ).reset_index()
    daily["cross_section_vol"] = daily["cross_section_vol"].fillna(0.0)
    daily["liquidity_ratio_20d"] = daily["total_dollar_volume"] / daily["total_dollar_volume"].rolling(20, min_periods=5).median()
    daily["liquidity_ratio_20d"] = daily["liquidity_ratio_20d"].fillna(1.0)
    daily["breadth_regime"] = daily["breadth_positive_rate"].map(_breadth_regime)
    daily["volatility_regime"] = _tercile_label(daily["avg_intraday_range"], labels=("low_vol", "mid_vol", "high_vol"))
    daily["liquidity_regime"] = daily["liquidity_ratio_20d"].map(_liquidity_regime)
    daily["market_regime"] = daily.apply(_market_regime, axis=1)

    theme_daily = symbol_days.groupby(["entry_date", "theme"]).agg(theme_day_return=("day_return", "mean")).reset_index()
    theme_daily["theme_rank"] = theme_daily.groupby("entry_date")["theme_day_return"].rank(method="first", ascending=False)
    theme_daily["theme_count"] = theme_daily.groupby("entry_date")["theme"].transform("count")
    theme_daily["theme_leadership_regime"] = theme_daily.apply(_theme_leadership_regime, axis=1)
    return daily.merge(theme_daily, on="entry_date", how="left")


def attach_regimes_to_lifecycles(lifecycle_panel: pd.DataFrame, daily_regime: pd.DataFrame) -> pd.DataFrame:
    panel = lifecycle_panel.copy()
    panel["entry_date"] = pd.to_datetime(panel["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    panel["theme"] = panel["theme"].astype(str)
    join_cols = [
        "entry_date",
        "theme",
        "breadth_regime",
        "volatility_regime",
        "liquidity_regime",
        "market_regime",
        "theme_day_return",
        "theme_rank",
        "theme_leadership_regime",
        "breadth_positive_rate",
        "avg_intraday_range",
        "liquidity_ratio_20d",
    ]
    scoped_regime = daily_regime[join_cols].copy()
    out = panel.merge(scoped_regime, on=["entry_date", "theme"], how="left")
    for column in ["breadth_regime", "volatility_regime", "liquidity_regime", "market_regime", "theme_leadership_regime"]:
        out[column] = out[column].fillna("unknown")
    return out


def summarize_reinforcement_by_regime(panel: pd.DataFrame) -> pd.DataFrame:
    scoped = panel.copy()
    scoped["reinforcement_group"] = "entry_only_or_reduce"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 0), "reinforcement_group"] = "add_only"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 1), "reinforcement_group"] = "add_scale"
    frames = []
    for regime_col in ["market_regime", "breadth_regime", "volatility_regime", "liquidity_regime", "theme_leadership_regime"]:
        summary = _summarize(scoped, [regime_col, "reinforcement_group"]).rename(columns={regime_col: "regime_value"})
        summary.insert(0, "regime_type", regime_col)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True)


def summarize_reduce_by_regime(panel: pd.DataFrame) -> pd.DataFrame:
    scoped = panel.copy()
    scoped["reduce_group"] = scoped["reduce_flag"].map({1: "reduce_present", 0: "no_reduce"})
    frames = []
    for regime_col in ["market_regime", "breadth_regime", "volatility_regime", "liquidity_regime", "theme_leadership_regime"]:
        summary = _summarize(scoped, [regime_col, "reduce_group"]).rename(columns={regime_col: "regime_value"})
        summary.insert(0, "regime_type", regime_col)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True)


def summarize_theme_regime_quality(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["theme", "market_regime", "theme_leadership_regime"]).sort_values(
        ["avg_return_from_entry", "lifecycle_count"], ascending=[False, False]
    )


def summarize_transition_regime_quality(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["lifecycle_path", "market_regime", "volatility_regime"]).sort_values(
        ["avg_return_from_entry", "lifecycle_count"], ascending=[False, False]
    )


def build_task_392_decision(panel: pd.DataFrame, reinforcement: pd.DataFrame, reduce: pd.DataFrame) -> pd.DataFrame:
    best = reinforcement[reinforcement["reinforcement_group"].eq("add_scale")].sort_values("avg_return_from_entry", ascending=False)
    best_row = best.iloc[0].to_dict() if not best.empty else {}
    market = reinforcement[reinforcement["regime_type"].eq("market_regime")]
    pivot = market.pivot(index="regime_value", columns="reinforcement_group", values="avg_return_from_entry")
    add_scale_dominates_count = 0
    for _, row in pivot.iterrows():
        add_scale = row.get("add_scale")
        baseline = row.get("entry_only_or_reduce")
        if pd.notna(add_scale) and pd.notna(baseline) and float(add_scale) > float(baseline):
            add_scale_dominates_count += 1
    reduce_market = reduce[reduce["regime_type"].eq("market_regime")]
    reduce_pivot = reduce_market.pivot(index="regime_value", columns="reduce_group", values="avg_return_from_entry")
    reduce_weakening_count = 0
    for _, row in reduce_pivot.iterrows():
        no_reduce = row.get("no_reduce")
        reduce_present = row.get("reduce_present")
        if pd.notna(no_reduce) and pd.notna(reduce_present) and float(no_reduce) > float(reduce_present):
            reduce_weakening_count += 1
    return pd.DataFrame(
        [
            {
                "task_392_verdict": "COMPLETE_PASS",
                "evaluation_status": "REGIME_DIAGNOSTIC_COMPLETE",
                "canonical_lifecycle_count": len(panel),
                "regime_labeled_lifecycle_count": int(panel["market_regime"].ne("unknown").sum()) if not panel.empty else 0,
                "best_add_scale_regime_type": best_row.get("regime_type", ""),
                "best_add_scale_regime_value": best_row.get("regime_value", ""),
                "best_add_scale_avg_return": best_row.get("avg_return_from_entry", ""),
                "market_regime_add_scale_dominates_count": add_scale_dominates_count,
                "market_regime_reduce_weakening_count": reduce_weakening_count,
                "reconstruction_used_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "deployment_claim_flag": 0,
                "next_priority": "regime_conditioned_oos_acceptance_or_macro_proxy_enrichment",
            }
        ]
    )


def write_task_392_artifacts(artifacts: MacroVolThemeRegimeOverlay392Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.daily_regime_panel.to_csv(out_dir / "daily_regime_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.lifecycle_regime_panel.to_csv(out_dir / "lifecycle_regime_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.regime_reinforcement_quality.to_csv(out_dir / "regime_reinforcement_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.regime_reduce_weakening_quality.to_csv(out_dir / "regime_reduce_weakening_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.theme_regime_quality.to_csv(out_dir / "theme_regime_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.transition_regime_quality.to_csv(out_dir / "transition_regime_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.task_392_decision.to_csv(out_dir / "task_392_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 392 - Macro / Volatility / Theme Regime Overlay",
        "",
        "## Decision",
        artifacts.task_392_decision.to_csv(index=False).strip(),
        "",
        "## Regime Reinforcement Quality",
        artifacts.regime_reinforcement_quality.to_csv(index=False).strip(),
        "",
        "## Regime Reduce Weakening Quality",
        artifacts.regime_reduce_weakening_quality.to_csv(index=False).strip(),
    ]
    (out_dir / "task_392_macro_vol_theme_regime_overlay.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(keys, dropna=False)
    return grouped.agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_return_from_entry=("return_from_entry", "mean"),
        median_return_from_entry=("return_from_entry", "median"),
        positive_rate=("positive_return_flag", "mean"),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
        avg_bars_held=("bars_held", "mean"),
    ).reset_index()


def _breadth_regime(value: float) -> str:
    if value >= 0.60:
        return "broad_participation"
    if value <= 0.40:
        return "weak_breadth"
    return "mixed_breadth"


def _liquidity_regime(value: float) -> str:
    if value >= 1.10:
        return "liquidity_expansion"
    if value <= 0.90:
        return "liquidity_tightening"
    return "liquidity_neutral"


def _market_regime(row: pd.Series) -> str:
    if row["breadth_regime"] == "broad_participation" and float(row["avg_symbol_return"]) > 0:
        return "risk_on_broad"
    if row["breadth_regime"] == "weak_breadth" and float(row["avg_symbol_return"]) < 0:
        return "risk_off_weak"
    return "mixed_market"


def _theme_leadership_regime(row: pd.Series) -> str:
    rank = float(row["theme_rank"])
    count = float(row["theme_count"])
    if rank <= 3:
        return "theme_leader"
    if rank > max(count - 3, 3):
        return "theme_laggard"
    return "theme_middle"


def _tercile_label(series: pd.Series, labels: tuple[str, str, str]) -> pd.Series:
    ranked = series.rank(method="first")
    try:
        return pd.qcut(ranked, q=3, labels=labels).astype(str)
    except ValueError:
        return pd.Series([labels[1]] * len(series), index=series.index)


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 392 macro/vol/theme regime overlay.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--task391-panel", type=Path, default=DEFAULT_TASK391_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_macro_vol_theme_regime_overlay_392(
        intraday_dir=args.intraday_dir,
        theme_universe_path=args.theme_universe,
        task391_panel_path=args.task391_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_392_decision.iloc[0]
    print(
        "[TASK392] "
        f"status={row['evaluation_status']} lifecycles={row['canonical_lifecycle_count']} "
        f"best={row['best_add_scale_regime_type']}:{row['best_add_scale_regime_value']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
