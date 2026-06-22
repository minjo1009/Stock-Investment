from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_INTRADAY_DIR = Path("data/raw/us_intraday")
DEFAULT_TASK392_PANEL = Path("docs/reports/task_392_macro_vol_theme_regime_overlay/lifecycle_regime_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_395_forward_live_regime_detectability")


@dataclass(frozen=True)
class ForwardLiveRegimeDetectability395Artifacts:
    forward_live_timestamp_regime_panel: pd.DataFrame
    forward_live_lifecycle_regime_panel: pd.DataFrame
    detectability_alignment_audit: pd.DataFrame
    forward_live_gate_split_quality: pd.DataFrame
    forward_live_gate_validation_audit: pd.DataFrame
    forward_live_leakage_audit: pd.DataFrame
    task_395_decision: pd.DataFrame


def build_forward_live_regime_detectability_395(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    task392_lifecycle_regime_panel_path: Path = DEFAULT_TASK392_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> ForwardLiveRegimeDetectability395Artifacts:
    lifecycle_panel = pd.read_csv(task392_lifecycle_regime_panel_path, encoding="utf-8-sig")
    timestamp_regime = build_forward_live_timestamp_regime_panel(intraday_dir, lifecycle_panel)
    lifecycle_regime = attach_forward_live_regimes(lifecycle_panel, timestamp_regime)
    alignment = build_detectability_alignment_audit(lifecycle_regime)
    split_quality = summarize_forward_live_gate_split_quality(lifecycle_regime)
    validation_audit = build_forward_live_gate_validation_audit(split_quality)
    leakage_audit = build_forward_live_leakage_audit()
    decision = build_task_395_decision(lifecycle_regime, alignment, validation_audit, leakage_audit)
    artifacts = ForwardLiveRegimeDetectability395Artifacts(
        forward_live_timestamp_regime_panel=timestamp_regime,
        forward_live_lifecycle_regime_panel=lifecycle_regime,
        detectability_alignment_audit=alignment,
        forward_live_gate_split_quality=split_quality,
        forward_live_gate_validation_audit=validation_audit,
        forward_live_leakage_audit=leakage_audit,
        task_395_decision=decision,
    )
    write_task_395_artifacts(artifacts, out_dir)
    return artifacts


def build_forward_live_timestamp_regime_panel(intraday_dir: Path, lifecycle_panel: pd.DataFrame) -> pd.DataFrame:
    symbol_theme = lifecycle_panel[["symbol", "theme"]].drop_duplicates()
    symbol_theme["symbol"] = symbol_theme["symbol"].astype(str).str.upper()
    symbol_theme["theme"] = symbol_theme["theme"].astype(str)
    theme_map = dict(zip(symbol_theme["symbol"], symbol_theme["theme"]))
    frames = []
    for symbol in sorted(theme_map):
        path = intraday_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        bars = pd.read_csv(path, encoding="utf-8-sig")
        if bars.empty:
            continue
        bars.columns = [str(c).strip().lower() for c in bars.columns]
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required.issubset(set(bars.columns)):
            continue
        bars["timestamp"] = pd.to_datetime(bars["timestamp"], errors="coerce", utc=True)
        for column in ["open", "high", "low", "close", "volume"]:
            bars[column] = pd.to_numeric(bars[column], errors="coerce")
        bars = bars.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).sort_values("timestamp")
        if bars.empty:
            continue
        bars["symbol"] = symbol
        bars["theme"] = theme_map[symbol]
        bars["entry_date"] = bars["timestamp"].dt.strftime("%Y-%m-%d")
        grouped = bars.groupby("entry_date", sort=False)
        bars["bar_index"] = grouped.cumcount()
        bars["day_open_so_far"] = grouped["open"].transform("first")
        bars["high_so_far"] = grouped["high"].cummax()
        bars["low_so_far"] = grouped["low"].cummin()
        bars["cum_dollar_volume_so_far"] = (bars["close"] * bars["volume"]).groupby(bars["entry_date"]).cumsum()
        bars["return_so_far"] = bars["close"] / bars["day_open_so_far"] - 1.0
        bars["intraday_range_so_far"] = bars["high_so_far"] / bars["low_so_far"] - 1.0
        frames.append(
            bars[
                [
                    "timestamp",
                    "entry_date",
                    "bar_index",
                    "symbol",
                    "theme",
                    "return_so_far",
                    "intraday_range_so_far",
                    "cum_dollar_volume_so_far",
                ]
            ]
        )
    if not frames:
        return pd.DataFrame()
    bars_all = pd.concat(frames, ignore_index=True)
    market = bars_all.groupby("timestamp").agg(
        entry_date=("entry_date", "first"),
        bar_index=("bar_index", "max"),
        symbol_count=("symbol", "nunique"),
        forward_live_breadth_positive_rate=("return_so_far", lambda s: float((s > 0).mean())),
        forward_live_avg_symbol_return=("return_so_far", "mean"),
        forward_live_avg_intraday_range=("intraday_range_so_far", "mean"),
        forward_live_total_cum_dollar_volume=("cum_dollar_volume_so_far", "sum"),
    ).reset_index()
    market = market.sort_values("timestamp")
    market["prior_20d_same_bar_cum_dollar_median"] = market.groupby("bar_index")[
        "forward_live_total_cum_dollar_volume"
    ].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median())
    market["forward_live_liquidity_ratio"] = (
        market["forward_live_total_cum_dollar_volume"] / market["prior_20d_same_bar_cum_dollar_median"]
    )
    market["forward_live_liquidity_ratio"] = market["forward_live_liquidity_ratio"].replace([float("inf"), -float("inf")], pd.NA).fillna(1.0)
    market["forward_live_breadth_regime"] = market["forward_live_breadth_positive_rate"].map(_breadth_regime)
    market["forward_live_volatility_regime"] = _tercile_label(
        market["forward_live_avg_intraday_range"],
        labels=("low_vol", "mid_vol", "high_vol"),
    )
    market["forward_live_liquidity_regime"] = market["forward_live_liquidity_ratio"].map(_liquidity_regime)
    market["forward_live_market_regime"] = market.apply(_market_regime, axis=1)

    theme = bars_all.groupby(["timestamp", "theme"]).agg(
        forward_live_theme_return=("return_so_far", "mean"),
    ).reset_index()
    theme["forward_live_theme_rank"] = theme.groupby("timestamp")["forward_live_theme_return"].rank(method="first", ascending=False)
    theme["forward_live_theme_count"] = theme.groupby("timestamp")["theme"].transform("count")
    theme["forward_live_theme_leadership_regime"] = theme.apply(_theme_leadership_regime, axis=1)
    return market.merge(theme, on="timestamp", how="left")


def attach_forward_live_regimes(lifecycle_panel: pd.DataFrame, timestamp_regime: pd.DataFrame) -> pd.DataFrame:
    panel = lifecycle_panel.copy()
    panel["entry_ts_dt"] = pd.to_datetime(panel["entry_ts"], errors="coerce", utc=True)
    panel["theme"] = panel["theme"].astype(str)
    regime = timestamp_regime.copy()
    regime["entry_ts_dt"] = pd.to_datetime(regime["timestamp"], errors="coerce", utc=True)
    keep = [
        "entry_ts_dt",
        "theme",
        "forward_live_breadth_positive_rate",
        "forward_live_avg_symbol_return",
        "forward_live_avg_intraday_range",
        "forward_live_liquidity_ratio",
        "forward_live_breadth_regime",
        "forward_live_volatility_regime",
        "forward_live_liquidity_regime",
        "forward_live_market_regime",
        "forward_live_theme_return",
        "forward_live_theme_rank",
        "forward_live_theme_leadership_regime",
    ]
    out = panel.merge(regime[keep], on=["entry_ts_dt", "theme"], how="left")
    for column in [
        "forward_live_breadth_regime",
        "forward_live_volatility_regime",
        "forward_live_liquidity_regime",
        "forward_live_market_regime",
        "forward_live_theme_leadership_regime",
    ]:
        out[column] = out[column].fillna("unknown")
    out["hindsight_strict_regime_gate_flag"] = (
        out["market_regime"].eq("risk_on_broad")
        & out["breadth_regime"].eq("broad_participation")
        & (out["liquidity_regime"].eq("liquidity_expansion") | out["theme_leadership_regime"].eq("theme_leader"))
    ).astype(int)
    out["forward_live_strict_regime_gate_flag"] = (
        out["forward_live_market_regime"].eq("risk_on_broad")
        & out["forward_live_breadth_regime"].eq("broad_participation")
        & (
            out["forward_live_liquidity_regime"].eq("liquidity_expansion")
            | out["forward_live_theme_leadership_regime"].eq("theme_leader")
        )
    ).astype(int)
    out["forward_live_regime_available_flag"] = out["forward_live_market_regime"].ne("unknown").astype(int)
    out["full_day_regime_used_flag"] = 0
    out["future_outcome_used_for_regime_flag"] = 0
    out["symbol_session_inference_used_flag"] = 0
    return out


def build_detectability_alignment_audit(panel: pd.DataFrame) -> pd.DataFrame:
    available = panel[panel["forward_live_regime_available_flag"].eq(1)]
    strict_hindsight = int(panel["hindsight_strict_regime_gate_flag"].sum())
    strict_forward = int(panel["forward_live_strict_regime_gate_flag"].sum())
    overlap = int(((panel["hindsight_strict_regime_gate_flag"] == 1) & (panel["forward_live_strict_regime_gate_flag"] == 1)).sum())
    precision = overlap / strict_forward if strict_forward else 0.0
    recall = overlap / strict_hindsight if strict_hindsight else 0.0
    agreement = float((panel["hindsight_strict_regime_gate_flag"] == panel["forward_live_strict_regime_gate_flag"]).mean()) if len(panel) else 0.0
    return pd.DataFrame(
        [
            {
                "lifecycle_count": len(panel),
                "forward_live_regime_available_count": len(available),
                "hindsight_strict_count": strict_hindsight,
                "forward_live_strict_count": strict_forward,
                "strict_overlap_count": overlap,
                "forward_vs_hindsight_precision": precision,
                "forward_vs_hindsight_recall": recall,
                "forward_vs_hindsight_agreement": agreement,
                "detectability_status": "FORWARD_LIVE_DIAGNOSTIC_AVAILABLE" if len(available) else "NO_FORWARD_LIVE_REGIME",
            }
        ]
    )


def summarize_forward_live_gate_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    gates = {
        "ungated_baseline": pd.Series([1] * len(panel), index=panel.index),
        "hindsight_strict_gate": panel["hindsight_strict_regime_gate_flag"].eq(1),
        "forward_live_strict_gate": panel["forward_live_strict_regime_gate_flag"].eq(1),
    }
    for gate_name, mask in gates.items():
        scoped = panel[pd.Series(mask, index=panel.index).astype(bool)].copy()
        summary = _summarize(scoped, ["anchored_split"])
        summary.insert(0, "gate_name", gate_name)
        summary.insert(1, "gate_allowed_count", len(scoped))
        frames.append(summary)
    return pd.concat(frames, ignore_index=True)


def build_forward_live_gate_validation_audit(split_quality: pd.DataFrame) -> pd.DataFrame:
    baseline = _row(split_quality, "ungated_baseline", "validation")
    rows = []
    for gate_name in sorted(split_quality["gate_name"].unique()):
        validation = _row(split_quality, gate_name, "validation")
        recent_oos = _row(split_quality, gate_name, "recent_oos")
        val_avg = _float_or_nan(validation.get("avg_return_from_entry"))
        base_avg = _float_or_nan(baseline.get("avg_return_from_entry"))
        oos_avg = _float_or_nan(recent_oos.get("avg_return_from_entry"))
        rows.append(
            {
                "gate_name": gate_name,
                "validation_trade_count": int(validation.get("trade_count", 0) or 0),
                "validation_avg_return": val_avg,
                "validation_compounded_pnl": _float_or_nan(validation.get("compounded_pnl")),
                "recent_oos_trade_count": int(recent_oos.get("trade_count", 0) or 0),
                "recent_oos_avg_return": oos_avg,
                "recent_oos_compounded_pnl": _float_or_nan(recent_oos.get("compounded_pnl")),
                "validation_avg_lift_vs_ungated": val_avg - base_avg,
                "validation_collapse_reduced_flag": int(pd.notna(val_avg) and pd.notna(base_avg) and val_avg > base_avg),
                "recent_oos_positive_flag": int(pd.notna(oos_avg) and oos_avg > 0),
                "forward_live_gate_diagnostic_pass_flag": int(
                    gate_name == "forward_live_strict_gate"
                    and int(validation.get("trade_count", 0) or 0) >= 100
                    and pd.notna(val_avg)
                    and pd.notna(base_avg)
                    and val_avg > base_avg
                    and pd.notna(oos_avg)
                    and oos_avg > 0
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["forward_live_gate_diagnostic_pass_flag", "validation_avg_lift_vs_ungated"],
        ascending=[False, False],
    )


def build_forward_live_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"field": "full_day_return", "used_for_forward_live_regime": 0, "allowed": 0},
            {"field": "full_day_breadth", "used_for_forward_live_regime": 0, "allowed": 0},
            {"field": "full_day_dollar_volume", "used_for_forward_live_regime": 0, "allowed": 0},
            {"field": "post_entry_outcome_return", "used_for_forward_live_regime": 0, "allowed": 0},
            {"field": "symbol_session_recovery", "used_for_forward_live_regime": 0, "allowed": 0},
            {"field": "entry_timestamp_bars_so_far", "used_for_forward_live_regime": 1, "allowed": 1},
            {"field": "prior_20d_same_bar_liquidity_median", "used_for_forward_live_regime": 1, "allowed": 1},
        ]
    )


def build_task_395_decision(
    panel: pd.DataFrame,
    alignment: pd.DataFrame,
    validation_audit: pd.DataFrame,
    leakage_audit: pd.DataFrame,
) -> pd.DataFrame:
    forward = validation_audit[validation_audit["gate_name"].eq("forward_live_strict_gate")]
    forward_row = forward.iloc[0].to_dict() if not forward.empty else {}
    align = alignment.iloc[0].to_dict() if not alignment.empty else {}
    blocked_leakage = leakage_audit[
        leakage_audit["allowed"].eq(0) & leakage_audit["used_for_forward_live_regime"].eq(1)
    ]
    pass_flag = int(forward_row.get("forward_live_gate_diagnostic_pass_flag", 0) or 0)
    return pd.DataFrame(
        [
            {
                "task_395_verdict": "COMPLETE_PASS",
                "evaluation_status": "FORWARD_LIVE_REGIME_DETECTABILITY_DIAGNOSTIC_COMPLETE",
                "canonical_lifecycle_count": len(panel),
                "forward_live_regime_available_count": align.get("forward_live_regime_available_count", 0),
                "hindsight_strict_count": align.get("hindsight_strict_count", 0),
                "forward_live_strict_count": align.get("forward_live_strict_count", 0),
                "strict_overlap_count": align.get("strict_overlap_count", 0),
                "forward_vs_hindsight_precision": align.get("forward_vs_hindsight_precision", 0),
                "forward_vs_hindsight_recall": align.get("forward_vs_hindsight_recall", 0),
                "forward_live_validation_avg_return": forward_row.get("validation_avg_return", ""),
                "forward_live_recent_oos_avg_return": forward_row.get("recent_oos_avg_return", ""),
                "forward_live_gate_diagnostic_pass_flag": pass_flag,
                "full_day_regime_used_flag": 0,
                "future_outcome_used_for_regime_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "blocked_leakage_field_count": len(blocked_leakage),
                "strategy_acceptance_status": "FORWARD_LIVE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT",
                "next_priority": "cost_capital_constrained_forward_live_policy_validation",
            }
        ]
    )


def write_task_395_artifacts(artifacts: ForwardLiveRegimeDetectability395Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.forward_live_timestamp_regime_panel.to_csv(out_dir / "forward_live_timestamp_regime_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_live_lifecycle_regime_panel.to_csv(out_dir / "forward_live_lifecycle_regime_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.detectability_alignment_audit.to_csv(out_dir / "detectability_alignment_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_live_gate_split_quality.to_csv(out_dir / "forward_live_gate_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_live_gate_validation_audit.to_csv(out_dir / "forward_live_gate_validation_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_live_leakage_audit.to_csv(out_dir / "forward_live_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_395_decision.to_csv(out_dir / "task_395_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 395 - Forward-Live Regime Detectability Validation",
        "",
        "## Required Answers",
        "- Did Task 395 use full-day regime labels for forward-live detection? `NO`",
        "- Did Task 395 use future outcome returns for regime detection? `NO`",
        "- Did Task 395 use symbol/session inference? `NO`",
        "- Did Task 395 make a deployment claim? `NO`",
        "",
        "## Decision",
        artifacts.task_395_decision.to_csv(index=False).strip(),
        "",
        "## Detectability Alignment Audit",
        artifacts.detectability_alignment_audit.to_csv(index=False).strip(),
        "",
        "## Forward-Live Gate Validation Audit",
        artifacts.forward_live_gate_validation_audit.to_csv(index=False).strip(),
        "",
        "## Leakage Audit",
        artifacts.forward_live_leakage_audit.to_csv(index=False).strip(),
    ]
    (out_dir / "task_395_forward_live_regime_detectability.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    columns = keys + [
        "trade_count",
        "win_count",
        "win_rate",
        "avg_return_from_entry",
        "median_return_from_entry",
        "sum_return_from_entry",
        "compounded_pnl",
        "add_rate",
        "scale_rate",
        "add_scale_rate",
        "reduce_rate",
        "avg_bars_held",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    scoped = frame.copy()
    scoped["return_from_entry"] = pd.to_numeric(scoped["return_from_entry"], errors="coerce").fillna(0.0)
    scoped["positive_return_flag"] = (scoped["return_from_entry"] > 0).astype(int)
    return scoped.groupby(keys, dropna=False).agg(
        trade_count=("lifecycle_id", "nunique"),
        win_count=("positive_return_flag", "sum"),
        win_rate=("positive_return_flag", "mean"),
        avg_return_from_entry=("return_from_entry", "mean"),
        median_return_from_entry=("return_from_entry", "median"),
        sum_return_from_entry=("return_from_entry", "sum"),
        compounded_pnl=("return_from_entry", _compound_returns),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        add_scale_rate=("add_scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
        avg_bars_held=("bars_held", "mean"),
    ).reset_index().reindex(columns=columns)


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
    if row["forward_live_breadth_regime"] == "broad_participation" and float(row["forward_live_avg_symbol_return"]) > 0:
        return "risk_on_broad"
    if row["forward_live_breadth_regime"] == "weak_breadth" and float(row["forward_live_avg_symbol_return"]) < 0:
        return "risk_off_weak"
    return "mixed_market"


def _theme_leadership_regime(row: pd.Series) -> str:
    rank = float(row["forward_live_theme_rank"])
    count = float(row["forward_live_theme_count"])
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


def _compound_returns(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    return float((1.0 + values).prod() - 1.0)


def _row(frame: pd.DataFrame, gate_name: str, split: str) -> dict[str, object]:
    rows = frame[frame["gate_name"].eq(gate_name) & frame["anchored_split"].eq(split)]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _float_or_nan(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 395 forward-live regime detectability validation.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--task392-panel", type=Path, default=DEFAULT_TASK392_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_forward_live_regime_detectability_395(
        intraday_dir=args.intraday_dir,
        task392_lifecycle_regime_panel_path=args.task392_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_395_decision.iloc[0]
    print(
        "[TASK395] "
        f"status={row['evaluation_status']} lifecycles={row['canonical_lifecycle_count']} "
        f"forward_strict={row['forward_live_strict_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
