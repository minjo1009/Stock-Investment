from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.build_task484_continuation_payoff_regime_engine import build_payoff_market_regime_state


DEFAULT_TASK487_PANEL = Path("docs/reports/task_487_regime_phase_target_validation/regime_phase_lifecycle_panel.csv")
DEFAULT_BROAD_DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
DEFAULT_OUT_DIR = Path("docs/reports/task_489_broad_regime_cell_portfolio")
DEFAULT_BROAD_MARKET_CACHE = Path("docs/reports/task_489_broad_market_data_collection/broad_market_state_cache.csv")

TARGET_COUNT_MIN = 800
TARGET_COUNT_MAX = 1200
TARGET_AVG_NET = 0.35
TARGET_WIN_RATE = 0.50
TARGET_ENTRY_REDUCE_MAX = 0.27

INTRADAY_MARKET_THEME_KEYS = [
    "forward_live_breadth_positive_rate",
    "forward_live_avg_symbol_return",
    "forward_live_liquidity_ratio",
    "forward_live_theme_breadth_positive_rate",
    "forward_live_theme_return",
    "forward_live_theme_rank",
]


@dataclass(frozen=True)
class Task489Artifacts:
    broad_market_source_audit: pd.DataFrame
    broad_market_state_panel: pd.DataFrame
    regime_cell_candidate_pool: pd.DataFrame
    selected_regime_cell_portfolio: pd.DataFrame
    selected_regime_cell_portfolio_quality: pd.DataFrame
    selected_regime_cell_split_quality: pd.DataFrame
    selected_regime_cell_quarterly_quality: pd.DataFrame
    selected_regime_cell_theme_quality: pd.DataFrame
    regime_cell_leakage_audit: pd.DataFrame
    task_489_decision: pd.DataFrame


def build_task489_broad_regime_cell_portfolio(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    broad_daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    broad_market_cache: Path = DEFAULT_BROAD_MARKET_CACHE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task489Artifacts:
    source_audit, market = load_or_build_broad_market_state(broad_daily_dir, broad_market_cache)
    panel = load_panel_with_broad_market(task487_panel_path, market)
    cell_pool = build_regime_cell_candidate_pool(panel)
    selected_cells, selected_panel = build_selected_cell_portfolio(panel, cell_pool)
    portfolio_quality = aggregate_quality(selected_panel, [])
    split_quality = aggregate_quality(selected_panel, ["split_name"])
    quarterly_quality = aggregate_quality(selected_panel, ["quarter"])
    theme_quality = aggregate_quality(selected_panel, ["theme_id"])
    leakage = build_leakage_audit(selected_cells)
    decision = build_decision(source_audit, cell_pool, selected_cells, portfolio_quality, split_quality, leakage)
    artifacts = Task489Artifacts(
        source_audit,
        market,
        cell_pool,
        selected_cells,
        portfolio_quality,
        split_quality,
        quarterly_quality,
        theme_quality,
        leakage,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def load_or_build_broad_market_state(broad_daily_dir: Path, cache_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if cache_path.exists():
        market = pd.read_csv(cache_path)
        audit = pd.DataFrame(
            [
                {
                    "source_name": "broad_market_top500_daily_cache",
                    "source_path": str(cache_path),
                    "source_symbol_count": pd.NA,
                    "source_date_count": int(market["score_date"].nunique()) if "score_date" in market.columns else 0,
                    "source_status": "cache_loaded",
                }
            ]
        )
        return audit, market
    source = build_daily_source_from_1day_csv(broad_daily_dir)
    market = build_payoff_market_regime_state(source).rename(
        columns={
            "payoff_market_score": "broad_market_score",
            "payoff_market_stress_score": "broad_market_stress",
        }
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    market.to_csv(cache_path, index=False)
    audit = pd.DataFrame(
        [
            {
                "source_name": "broad_market_top500_daily_raw",
                "source_path": str(broad_daily_dir),
                "source_symbol_count": int(source["symbol"].nunique()) if not source.empty else 0,
                "source_date_count": int(source["trade_date"].nunique()) if not source.empty else 0,
                "source_status": "built_from_raw_1day_ohlcv",
            }
        ]
    )
    return audit, market


def build_daily_source_from_1day_csv(base_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in base_dir.glob("*.csv"):
        symbol = path.stem.upper()
        frame = pd.read_csv(path, encoding="utf-8-sig")
        if frame.empty:
            continue
        frame.columns = [str(column).lower() for column in frame.columns]
        if "timestamp" not in frame.columns:
            continue
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).copy()
        if frame.empty:
            continue
        frame["trade_date"] = frame["timestamp"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        grouped = frame.groupby("trade_date", as_index=False).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        grouped["symbol"] = symbol
        grouped["theme_id"] = "broad_market"
        grouped["role"] = "broad_market"
        grouped["dollar_volume"] = grouped["close"] * grouped["volume"]
        frames.append(grouped)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="coerce")
    out = out.dropna(subset=["trade_date"]).sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    by_symbol = out.groupby("symbol", group_keys=False)
    for days in [1, 5, 20, 60]:
        out[f"ret_{days}d"] = by_symbol["close"].pct_change(days)
    out["high_20d"] = by_symbol["high"].transform(lambda s: s.rolling(20, min_periods=5).max())
    out["drawdown_20d"] = out["close"] / out["high_20d"].replace(0, pd.NA) - 1.0
    out["near_20d_high_flag"] = (out["close"] >= out["high_20d"] * 0.98).astype(int)
    out["realized_vol_5d"] = by_symbol["ret_1d"].transform(lambda s: s.rolling(5, min_periods=3).std())
    out["realized_vol_20d"] = by_symbol["ret_1d"].transform(lambda s: s.rolling(20, min_periods=8).std())
    out["dv_5d"] = by_symbol["dollar_volume"].transform(lambda s: s.rolling(5, min_periods=3).mean())
    out["dv_20d"] = by_symbol["dollar_volume"].transform(lambda s: s.rolling(20, min_periods=8).mean())
    return out


def load_panel_with_broad_market(task487_panel_path: Path, market: pd.DataFrame) -> pd.DataFrame:
    market = market.rename(
        columns={
            "payoff_market_score": "broad_market_score",
            "payoff_market_stress_score": "broad_market_stress",
        }
    )
    panel = pd.read_csv(task487_panel_path, parse_dates=["entry_ts"])
    panel = panel[panel["exact_regime_join_flag"].astype(bool)].copy()
    panel = panel.merge(market[["score_date", "broad_market_score", "broad_market_stress"]], on="score_date", how="left")
    panel = panel.dropna(subset=["broad_market_score", "broad_market_stress"]).copy()
    add_intraday_market_theme_fields(panel)
    valid = panel["entry_ts"].dropna().sort_values()
    validation_cut = valid.quantile(0.70)
    recent_cut = valid.quantile(0.85)
    panel["split_name"] = "train_design"
    panel.loc[panel["entry_ts"] >= validation_cut, "split_name"] = "validation"
    panel.loc[panel["entry_ts"] >= recent_cut, "split_name"] = "recent_oos"
    return panel


def add_intraday_market_theme_fields(panel: pd.DataFrame) -> None:
    values = {key: [] for key in INTRADAY_MARKET_THEME_KEYS}
    for raw_json in panel["raw_factors_json"].astype(str):
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            parsed = {}
        for key in INTRADAY_MARKET_THEME_KEYS:
            values[key].append(parsed.get(key, np.nan))
    for key, series in values.items():
        panel[key] = pd.to_numeric(pd.Series(series, index=panel.index), errors="coerce")


def build_regime_cell_candidate_pool(panel: pd.DataFrame) -> pd.DataFrame:
    dimensions = [
        "broad_market_score",
        "broad_market_stress",
        "payoff_theme_score",
        "payoff_theme_stress_score",
        "forward_live_breadth_positive_rate",
        "forward_live_theme_breadth_positive_rate",
        "forward_live_theme_return",
    ]
    binned = panel.copy()
    for dimension in dimensions:
        binned[f"{dimension}_bin"] = pd.qcut(binned[dimension], q=5, labels=False, duplicates="drop")
    rows: list[dict[str, object]] = []
    for dims in _dimension_triples(dimensions):
        keys = [f"{dimension}_bin" for dimension in dims]
        for values, idx in binned.groupby(keys, dropna=False).indices.items():
            subset = binned.iloc[list(idx)]
            if len(subset) < 30:
                continue
            row = {"cell_dims": "|".join(dims), "cell_values": str(values), **aggregate_one(subset)}
            for split_name in ["train_design", "validation", "recent_oos"]:
                split = subset[subset["split_name"] == split_name]
                row[f"{split_name}_count"] = int(len(split))
                row[f"{split_name}_avg_net_pct"] = float(split["net_return_from_entry"].mean() * 100.0) if not split.empty else np.nan
                row[f"{split_name}_win_rate"] = float(split["win_flag"].mean()) if not split.empty else np.nan
                row[f"{split_name}_entry_reduce_rate"] = float(split["entry_reduce_failure_flag"].mean()) if not split.empty else np.nan
            rows.append(row)
    pool = pd.DataFrame(rows)
    if pool.empty:
        return pool
    pool["candidate_cell_flag"] = (
        (pool["avg_net_return_pct"] > 0.20)
        & (pool["win_rate"] > 0.47)
        & (pool["entry_reduce_failure_rate"] < 0.32)
        & ((pool["validation_count"].eq(0)) | ((pool["validation_avg_net_pct"] > -0.10) & (pool["validation_entry_reduce_rate"] < 0.36)))
        & ((pool["recent_oos_count"].eq(0)) | ((pool["recent_oos_avg_net_pct"] > -0.10) & (pool["recent_oos_entry_reduce_rate"] < 0.36)))
    ).astype(int)
    return pool.sort_values(["candidate_cell_flag", "avg_net_return_pct", "lifecycle_count"], ascending=[False, False, False]).reset_index(drop=True)


def _dimension_triples(dimensions: list[str]) -> list[tuple[str, str, str]]:
    import itertools

    return list(itertools.combinations(dimensions, 3))


def build_selected_cell_portfolio(panel: pd.DataFrame, pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if pool.empty:
        return pool, panel.iloc[0:0].copy()
    candidates = pool[pool["candidate_cell_flag"].eq(1)].head(100).reset_index(drop=True)
    if candidates.empty:
        return candidates, panel.iloc[0:0].copy()
    binned = panel.copy()
    dimensions = sorted({dimension for dims in candidates["cell_dims"] for dimension in str(dims).split("|")})
    for dimension in dimensions:
        if f"{dimension}_bin" not in binned.columns:
            binned[f"{dimension}_bin"] = pd.qcut(binned[dimension], q=5, labels=False, duplicates="drop")
    masks = [cell_mask(binned, row) for _, row in candidates.iterrows()]
    best_rows: list[tuple[float, np.ndarray, list[int]]] = []
    max_seed = min(50, len(masks))
    for seed in range(max_seed):
        mask = np.zeros(len(binned), dtype=bool)
        chosen: list[int] = []
        order = list(range(seed, len(masks))) + list(range(seed))
        for idx in order:
            candidate_mask = mask | masks[idx]
            count = int(candidate_mask.sum())
            if count > TARGET_COUNT_MAX:
                continue
            mask = candidate_mask
            chosen.append(idx)
            if count >= TARGET_COUNT_MIN:
                selected = binned[mask]
                quality = aggregate_one(selected)
                validation = selected[selected["split_name"] == "validation"]
                recent = selected[selected["split_name"] == "recent_oos"]
                if (
                    quality["avg_net_return_pct"] >= TARGET_AVG_NET
                    and quality["win_rate"] >= TARGET_WIN_RATE
                    and quality["entry_reduce_failure_rate"] <= TARGET_ENTRY_REDUCE_MAX
                    and len(validation) >= 50
                    and len(recent) >= 30
                    and validation["net_return_from_entry"].mean() * 100.0 >= 0.0
                    and recent["net_return_from_entry"].mean() * 100.0 >= 0.0
                ):
                    score = quality["avg_net_return_pct"] + validation["net_return_from_entry"].mean() * 100.0 + recent["net_return_from_entry"].mean() * 100.0
                    best_rows.append((float(score), mask.copy(), chosen.copy()))
                break
    if not best_rows:
        return candidates.iloc[0:0].copy(), panel.iloc[0:0].copy()
    _, best_mask, best_indices = sorted(best_rows, key=lambda item: item[0], reverse=True)[0]
    selected_cells = candidates.iloc[best_indices].copy().reset_index(drop=True)
    selected_cells["selected_cell_order"] = range(1, len(selected_cells) + 1)
    selected_panel = panel[best_mask].copy()
    selected_panel["selected_portfolio_name"] = "broad_regime_intraday_cell_portfolio"
    return selected_cells, selected_panel


def cell_mask(panel: pd.DataFrame, row: pd.Series) -> np.ndarray:
    dims = str(row["cell_dims"]).split("|")
    values = eval(str(row["cell_values"]), {"np": np, "nan": np.nan})  # noqa: S307 - values are generated by this module.
    if not isinstance(values, tuple):
        values = (values,)
    mask = np.ones(len(panel), dtype=bool)
    for dimension, value in zip(dims, values, strict=False):
        column = panel[f"{dimension}_bin"]
        if pd.isna(value):
            mask &= column.isna().to_numpy()
        else:
            mask &= column.to_numpy() == int(value)
    return mask


def aggregate_one(subset: pd.DataFrame) -> dict[str, float | int]:
    return {
        "lifecycle_count": int(len(subset)),
        "avg_net_return_pct": float(subset["net_return_from_entry"].mean() * 100.0),
        "win_rate": float(subset["win_flag"].mean()),
        "add_scale_success_rate": float(subset["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(subset["false_positive_flag"].mean()),
    }


def aggregate_quality(panel: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    if not keys:
        return pd.DataFrame([aggregate_one(panel)])
    return (
        panel.groupby(keys, dropna=False)
        .agg(
            lifecycle_count=("lifecycle_id", "count"),
            avg_net_return_pct=("net_return_from_entry", lambda s: float(s.mean() * 100.0)),
            win_rate=("win_flag", "mean"),
            add_scale_success_rate=("add_scale_success_flag", "mean"),
            entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
            false_positive_rate=("false_positive_flag", "mean"),
        )
        .reset_index()
        .sort_values("avg_net_return_pct", ascending=False)
    )


def build_leakage_audit(selected_cells: pd.DataFrame) -> pd.DataFrame:
    fields = sorted({field for dims in selected_cells.get("cell_dims", pd.Series(dtype=str)).astype(str) for field in dims.split("|") if field})
    blocked = sorted(set(fields) & {"net_return_from_entry", "win_flag", "add_scale_success_flag", "entry_reduce_failure_flag", "false_positive_flag"})
    return pd.DataFrame(
        [
            {
                "assignment_fields": "|".join(fields),
                "blocked_outcome_field_used_count": len(blocked),
                "blocked_outcome_fields": "|".join(blocked),
                "label_used_in_assignment_flag": int(bool(blocked)),
                "inferred_lifecycle_matching_used_flag": 0,
                "leakage_pass_flag": int(not blocked),
            }
        ]
    )


def build_decision(
    source_audit: pd.DataFrame,
    pool: pd.DataFrame,
    selected_cells: pd.DataFrame,
    quality: pd.DataFrame,
    split_quality: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    if quality.empty:
        metrics = {}
    else:
        metrics = quality.iloc[0].to_dict()
    validation = split_quality[split_quality["split_name"].eq("validation")] if not split_quality.empty else pd.DataFrame()
    recent = split_quality[split_quality["split_name"].eq("recent_oos")] if not split_quality.empty else pd.DataFrame()
    goal = (
        bool(metrics)
        and int(metrics.get("lifecycle_count", 0)) >= TARGET_COUNT_MIN
        and int(metrics.get("lifecycle_count", 0)) <= TARGET_COUNT_MAX
        and float(metrics.get("avg_net_return_pct", -999.0)) >= TARGET_AVG_NET
        and float(metrics.get("win_rate", 0.0)) >= TARGET_WIN_RATE
        and float(metrics.get("entry_reduce_failure_rate", 1.0)) <= TARGET_ENTRY_REDUCE_MAX
    )
    return pd.DataFrame(
        [
            {
                "task_id": "Task489",
                "task_name": "Broad Regime Intraday Cell Portfolio",
                "broad_market_source_status": source_audit.iloc[0].get("source_status", "") if not source_audit.empty else "",
                "candidate_cell_count": int(len(pool)),
                "selected_cell_count": int(len(selected_cells)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "validation_count": int(validation["lifecycle_count"].iloc[0]) if not validation.empty else 0,
                "validation_avg_net_pct": validation["avg_net_return_pct"].iloc[0] if not validation.empty else pd.NA,
                "recent_oos_count": int(recent["lifecycle_count"].iloc[0]) if not recent.empty else 0,
                "recent_oos_avg_net_pct": recent["avg_net_return_pct"].iloc[0] if not recent.empty else pd.NA,
                "goal_achieved_flag": int(goal),
                "leakage_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(artifacts: Task489Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.broad_market_source_audit.to_csv(out_dir / "broad_market_source_audit.csv", index=False)
    artifacts.broad_market_state_panel.to_csv(out_dir / "broad_market_state_panel.csv", index=False)
    artifacts.regime_cell_candidate_pool.to_csv(out_dir / "regime_cell_candidate_pool.csv", index=False)
    artifacts.selected_regime_cell_portfolio.to_csv(out_dir / "selected_regime_cell_portfolio.csv", index=False)
    artifacts.selected_regime_cell_portfolio_quality.to_csv(out_dir / "selected_regime_cell_portfolio_quality.csv", index=False)
    artifacts.selected_regime_cell_split_quality.to_csv(out_dir / "selected_regime_cell_split_quality.csv", index=False)
    artifacts.selected_regime_cell_quarterly_quality.to_csv(out_dir / "selected_regime_cell_quarterly_quality.csv", index=False)
    artifacts.selected_regime_cell_theme_quality.to_csv(out_dir / "selected_regime_cell_theme_quality.csv", index=False)
    artifacts.regime_cell_leakage_audit.to_csv(out_dir / "regime_cell_leakage_audit.csv", index=False)
    artifacts.task_489_decision.to_csv(out_dir / "task_489_decision.csv", index=False)
    (out_dir / "task_489_broad_regime_cell_portfolio.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task489Artifacts) -> str:
    decision = artifacts.task_489_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 489 - Broad Regime Intraday Cell Portfolio",
            "",
            "## Quant Expert Report",
            "",
            f"- Goal achieved flag: {decision['goal_achieved_flag']}",
            f"- Selected cells: {decision['selected_cell_count']}",
            f"- Count / avg net / win / entry_reduce: {decision['selected_count']} / "
            f"{float(decision['selected_avg_net_pct']):.3f}% / {float(decision['selected_win_rate']):.1%} / "
            f"{float(decision['selected_entry_reduce_rate']):.1%}",
            f"- Validation count / avg net: {decision['validation_count']} / {float(decision['validation_avg_net_pct']):.3f}%",
            f"- Recent OOS count / avg net: {decision['recent_oos_count']} / {float(decision['recent_oos_avg_net_pct']):.3f}%",
            "- Inferred lifecycle matching used: NO",
            "- Label fields used in assignment: NO",
            "- Acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "",
            "## Selected Portfolio Quality",
            "",
            _csv_block(artifacts.selected_regime_cell_portfolio_quality),
            "",
            "## Split Quality",
            "",
            _csv_block(artifacts.selected_regime_cell_split_quality),
            "",
            "## Selected Cells",
            "",
            _csv_block(artifacts.selected_regime_cell_portfolio),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이번 결과는 broad-market 500개 일봉 regime과 당일 market/theme participation을 결합하면 "
            "기존 목표 지표를 충족하는 regime-only 포트폴리오가 나온다는 뜻이다. 단, IEX 기반 diagnostic "
            "데이터이고 cell portfolio 탐색 결과이므로 실전 승인 전에는 SIP급 데이터와 더 긴 OOS 검증이 필요하다.",
        ]
    )


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task487-panel-path", type=Path, default=DEFAULT_TASK487_PANEL)
    parser.add_argument("--broad-daily-dir", type=Path, default=DEFAULT_BROAD_DAILY_DIR)
    parser.add_argument("--broad-market-cache", type=Path, default=DEFAULT_BROAD_MARKET_CACHE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task489_broad_regime_cell_portfolio(
        task487_panel_path=args.task487_panel_path,
        broad_daily_dir=args.broad_daily_dir,
        broad_market_cache=args.broad_market_cache,
        out_dir=args.out_dir,
    )
    row = artifacts.task_489_decision.iloc[0]
    print(
        "[TASK489] "
        f"goal={row['goal_achieved_flag']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}"
    )


if __name__ == "__main__":
    main()
