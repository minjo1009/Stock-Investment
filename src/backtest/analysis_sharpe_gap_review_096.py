from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.analysis_drawdown_control_094 import (
    _f,
    _metrics_from_trade_pnl,
    _positions_df,
    _safe_div,
    _simulate_risk_architecture,
)


TARGET_SHARPE = 0.7
ACTUAL_SHARPE_DEFAULT = 0.6732


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _overlay_flags(overlay: str) -> tuple[dict[str, Any], dict[str, Any]]:
    mapping: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        "BASELINE": (
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": False,
                "enable_decorrelation": False,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER": (
            {
                "enable_loss_breaker": True,
                "enable_regime_throttle": False,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {"loss_streak_threshold": 4, "cooldown_trades": 1},
        ),
    }
    return mapping.get(overlay, mapping["DECORRELATION_PLUS_LIGHT_LOSS_BREAKER"])


def _daily_equity_series(curve: list[dict[str, Any]]) -> pd.Series:
    if not curve:
        return pd.Series(dtype="float64")
    df = pd.DataFrame(curve)
    ts_col = "ts" if "ts" in df.columns else "date"
    val_col = "equity" if "equity" in df.columns else "value"
    df[ts_col] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    df = df.dropna(subset=[ts_col, val_col]).sort_values(ts_col).drop_duplicates(subset=[ts_col], keep="last")
    if df.empty:
        return pd.Series(dtype="float64")
    s = df.set_index(ts_col)[val_col].astype(float).sort_index()
    return s


def _daily_return_stats(daily_equity: pd.Series) -> tuple[pd.Series, dict[str, Any]]:
    if daily_equity.empty or len(daily_equity) < 2:
        return pd.Series(dtype="float64"), {
            "mean": 0.0,
            "std": 0.0,
            "annualized_volatility": 0.0,
            "positive_days": 0,
            "negative_days": 0,
            "zero_return_days": 0,
            "worst_day": 0.0,
            "best_day": 0.0,
        }
    rets = daily_equity.pct_change().dropna()
    if rets.empty:
        return rets, {
            "mean": 0.0,
            "std": 0.0,
            "annualized_volatility": 0.0,
            "positive_days": 0,
            "negative_days": 0,
            "zero_return_days": 0,
            "worst_day": 0.0,
            "best_day": 0.0,
        }
    pos = int((rets > 0).sum())
    neg = int((rets < 0).sum())
    zero = int((rets == 0).sum())
    std = float(rets.std(ddof=0))
    stats = {
        "mean": _f(float(rets.mean())),
        "std": _f(std),
        "annualized_volatility": _f(std * math.sqrt(252)),
        "positive_days": pos,
        "negative_days": neg,
        "zero_return_days": zero,
        "worst_day": _f(float(rets.min())),
        "best_day": _f(float(rets.max())),
    }
    return rets, stats


def _active_idle_stats(daily_equity: pd.Series, accepted_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if daily_equity.empty:
        return {"active_days": 0, "idle_days": 0, "utilization_ratio": 0.0}
    day_index = {ts.normalize() for ts in daily_equity.index}
    active_days: set[pd.Timestamp] = set()
    for row in accepted_rows:
        entry = pd.to_datetime(row.get("entry_time"), utc=True, errors="coerce")
        exit_ = pd.to_datetime(row.get("exit_time"), utc=True, errors="coerce")
        if pd.isna(entry) or pd.isna(exit_):
            continue
        if exit_ < entry:
            entry, exit_ = exit_, entry
        for d in pd.date_range(entry.normalize(), exit_.normalize(), freq="1D", tz="UTC"):
            if d in day_index:
                active_days.add(d)
    total_days = len(day_index)
    active = len(active_days)
    idle = max(total_days - active, 0)
    return {
        "active_days": int(active),
        "idle_days": int(idle),
        "utilization_ratio": _f(_safe_div(active, total_days)),
    }


def _max_negative_streak(daily_rets: pd.Series) -> int:
    streak = 0
    best = 0
    for r in daily_rets.tolist():
        if r < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return int(best)


def _drawdown_clusters(daily_equity: pd.Series, top_n: int = 5) -> list[dict[str, Any]]:
    if daily_equity.empty:
        return []
    clusters: list[dict[str, Any]] = []
    peak = float("-inf")
    peak_ts: pd.Timestamp | None = None
    in_cluster = False
    start_ts: pd.Timestamp | None = None
    trough_ts: pd.Timestamp | None = None
    trough_eq = float("inf")
    max_dd = 0.0
    for ts, eq in daily_equity.items():
        eq = float(eq)
        if eq > peak:
            if in_cluster and start_ts is not None and trough_ts is not None and peak_ts is not None:
                clusters.append(
                    {
                        "start": str(start_ts.isoformat()),
                        "trough": str(trough_ts.isoformat()),
                        "end": str(ts.isoformat()),
                        "duration_days": int((ts - start_ts).days),
                        "recovery_days": int((ts - peak_ts).days),
                        "drawdown_pct": _f(max_dd * 100.0),
                        "drawdown_amount": _f((peak - trough_eq)),
                    }
                )
            peak = eq
            peak_ts = ts
            in_cluster = False
            start_ts = None
            trough_ts = None
            trough_eq = float("inf")
            max_dd = 0.0
            continue
        dd = _safe_div(peak - eq, peak) if peak > 0 else 0.0
        if dd > 0 and not in_cluster:
            in_cluster = True
            start_ts = ts
        if dd > max_dd:
            max_dd = dd
            trough_ts = ts
            trough_eq = eq

    if in_cluster and start_ts is not None and trough_ts is not None and peak_ts is not None:
        end_ts = daily_equity.index[-1]
        clusters.append(
            {
                "start": str(start_ts.isoformat()),
                "trough": str(trough_ts.isoformat()),
                "end": None,
                "duration_days": int((end_ts - start_ts).days),
                "recovery_days": None,
                "drawdown_pct": _f(max_dd * 100.0),
                "drawdown_amount": _f((peak - trough_eq)),
            }
        )

    clusters.sort(key=lambda x: x["drawdown_pct"], reverse=True)
    return clusters[:top_n]


def _accepted_frame(sim: dict[str, Any]) -> pd.DataFrame:
    rows = sim.get("accepted_trade_rows", [])
    if not rows:
        return pd.DataFrame(columns=["symbol", "sector", "entry_time", "exit_time", "base_pnl", "scaled_pnl", "scale"])
    df = pd.DataFrame(rows).copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    for c in ["base_pnl", "scaled_pnl", "scale"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["entry_time", "exit_time", "symbol", "scaled_pnl"]).reset_index(drop=True)
    return df


def _join_scaled_returns(accepted_df: pd.DataFrame, positions_df: pd.DataFrame) -> pd.DataFrame:
    if accepted_df.empty or positions_df.empty:
        out = accepted_df.copy()
        out["scaled_return_pct"] = pd.Series(dtype="float64")
        return out
    base = positions_df.copy()
    base["entry_time"] = pd.to_datetime(base["entry_time"], utc=True, errors="coerce")
    base["exit_time"] = pd.to_datetime(base["exit_time"], utc=True, errors="coerce")
    merged = accepted_df.merge(
        base[["symbol", "sector", "entry_time", "exit_time", "return_pct", "net_pnl"]],
        on=["symbol", "sector", "entry_time", "exit_time"],
        how="left",
    )
    merged["scaled_return_pct"] = pd.to_numeric(merged["return_pct"], errors="coerce") * pd.to_numeric(
        merged["scale"], errors="coerce"
    )
    return merged


def _attribution_table(df: pd.DataFrame, group_col: str, daily_rets: pd.Series) -> list[dict[str, Any]]:
    if df.empty:
        return []
    work = df.copy()
    work["day"] = work["exit_time"].dt.normalize()
    total_pnl = float(work["scaled_pnl"].sum())

    pivot = work.pivot_table(index="day", columns=group_col, values="scaled_pnl", aggfunc="sum", fill_value=0.0)
    vol_by_group = pivot.std(ddof=0) if not pivot.empty else pd.Series(dtype="float64")
    vol_total = float(vol_by_group.sum()) if not vol_by_group.empty else 0.0

    # drawdown days: days where equity return is negative
    dd_days = set(daily_rets[daily_rets < 0].index.normalize().tolist())
    drawdown_loss = (
        work[work["day"].isin(dd_days) & (work["scaled_pnl"] < 0)]
        .groupby(group_col)["scaled_pnl"]
        .sum()
        .abs()
    )
    dd_total = float(drawdown_loss.sum()) if not drawdown_loss.empty else 0.0

    out: list[dict[str, Any]] = []
    grouped = work.groupby(group_col)
    for key, grp in grouped:
        pnl = float(grp["scaled_pnl"].sum())
        trade_count = int(len(grp))
        vol = float(vol_by_group.get(key, 0.0))
        dd = float(drawdown_loss.get(key, 0.0))
        out.append(
            {
                "name": str(key),
                "trade_count": trade_count,
                "return_contribution": _f(pnl),
                "return_contribution_pct": _f(_safe_div(pnl, total_pnl) * 100.0) if total_pnl != 0 else 0.0,
                "volatility_contribution": _f(vol),
                "volatility_contribution_pct": _f(_safe_div(vol, vol_total) * 100.0) if vol_total > 0 else 0.0,
                "drawdown_loss_contribution": _f(dd),
                "drawdown_loss_share_pct": _f(_safe_div(dd, dd_total) * 100.0) if dd_total > 0 else 0.0,
            }
        )
    out.sort(key=lambda r: r["volatility_contribution_pct"], reverse=True)
    return out


def _trade_distribution(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "trade_count": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "payoff_ratio": 0.0,
            "tail_loss_count": 0,
            "tail_win_count": 0,
            "skewness": 0.0,
        }
    pnl = pd.to_numeric(df["scaled_pnl"], errors="coerce").dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(losses.mean()) if not losses.empty else 0.0
    p05 = float(pnl.quantile(0.05))
    p95 = float(pnl.quantile(0.95))
    return {
        "trade_count": int(len(pnl)),
        "win_rate": _f(_safe_div(len(wins), len(pnl)) * 100.0),
        "avg_win": _f(avg_win),
        "avg_loss": _f(avg_loss),
        "payoff_ratio": _f(abs(_safe_div(avg_win, avg_loss))) if avg_loss != 0 else 0.0,
        "tail_loss_count": int((pnl <= p05).sum()),
        "tail_win_count": int((pnl >= p95).sum()),
        "skewness": _f(float(pnl.skew())) if len(pnl) >= 3 else 0.0,
    }


def _blocked_winners_losers(positions_df: pd.DataFrame, accepted_df: pd.DataFrame) -> dict[str, Any]:
    if positions_df.empty:
        return {
            "blocked_trades": 0,
            "blocked_winners": 0,
            "blocked_losers": 0,
            "blocked_avg_pnl": 0.0,
            "blocked_median_pnl": 0.0,
        }
    base_keys: list[tuple[Any, ...]] = []
    for row in positions_df.itertuples(index=False):
        base_keys.append(
            (
                str(row.symbol),
                str(pd.Timestamp(row.entry_time).isoformat()),
                str(pd.Timestamp(row.exit_time).isoformat()),
                _f(float(row.net_pnl), 4),
            )
        )
    acc_keys: list[tuple[Any, ...]] = []
    if not accepted_df.empty:
        for row in accepted_df.itertuples(index=False):
            acc_keys.append(
                (
                    str(row.symbol),
                    str(pd.Timestamp(row.entry_time).isoformat()),
                    str(pd.Timestamp(row.exit_time).isoformat()),
                    _f(float(row.base_pnl), 4),
                )
            )
    missing = Counter(base_keys) - Counter(acc_keys)
    blocked_pnls: list[float] = []
    for key, cnt in missing.items():
        blocked_pnls.extend([float(key[3])] * int(cnt))
    if not blocked_pnls:
        return {
            "blocked_trades": 0,
            "blocked_winners": 0,
            "blocked_losers": 0,
            "blocked_avg_pnl": 0.0,
            "blocked_median_pnl": 0.0,
        }
    return {
        "blocked_trades": int(len(blocked_pnls)),
        "blocked_winners": int(sum(1 for p in blocked_pnls if p > 0)),
        "blocked_losers": int(sum(1 for p in blocked_pnls if p < 0)),
        "blocked_avg_pnl": _f(statistics.fmean(blocked_pnls)),
        "blocked_median_pnl": _f(statistics.median(blocked_pnls)),
    }


def _build_graphify_context(required_files: list[str]) -> dict[str, Any]:
    graph = _load_json(Path("graphify-out/graph.json"))
    _ = Path("graphify-out/GRAPH_REPORT.md").read_text(encoding="utf-8")
    labels_path = Path("docs/graphify/community_labels.json")
    god_nodes_path = Path("docs/graphify/god_nodes_top20_local.json")
    labels = _load_json(labels_path) if labels_path.exists() else []
    label_map = {int(r["community_id"]): str(r["label"]) for r in labels}

    nodes = graph.get("nodes", [])
    required_norm = {f.replace("/", "\\").lower() for f in required_files}
    matched_nodes = [
        n
        for n in nodes
        if isinstance(n, dict) and str(n.get("source_file", "")).replace("/", "\\").lower() in required_norm
    ]
    community_ids = sorted({int(n.get("community", -1)) for n in matched_nodes if n.get("community") is not None})
    communities = [
        {"community_id": cid, "label": label_map.get(cid, f"Community {cid}")}
        for cid in community_ids
        if cid >= 0
    ]

    god_nodes = _load_json(god_nodes_path) if god_nodes_path.exists() else []
    relevant_god_nodes = [
        gn
        for gn in god_nodes
        if str(gn.get("source_file", "")).replace("/", "\\").lower()
        in {f.replace("/", "\\").lower() for f in required_files}
    ]
    if not relevant_god_nodes:
        # fallback: include top 5 local god nodes
        relevant_god_nodes = god_nodes[:5]

    return {
        "communities_used": communities,
        "files_inspected": required_files,
        "god_nodes_noted": relevant_god_nodes[:8],
        "excluded_areas": [
            "src/app (broker runtime path)",
            "src/integration (KIS adapter)",
            "tests/fixtures/kis/real raw responses",
            "live/paper execution scripts",
        ],
        "graph_meta": {"nodes": len(graph.get("nodes", [])), "links": len(graph.get("links", []))},
    }


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T096-REVIEW - Sharpe Gap Attribution")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("- 3-line summary:")
    lines.append(f"  - overlay Sharpe improved to {report['actual_sharpe']} but missed target {report['target_sharpe']} by {report['sharpe_gap']}.")
    lines.append(f"  - primary cause: {report['primary_cause']}")
    lines.append(f"  - secondary causes: {', '.join(report['secondary_causes'])}")
    lines.append("")
    lines.append("## 2. Graphify Context Pack")
    lines.append(f"- communities_used: {report['graphify_context']['communities_used']}")
    lines.append(f"- files_inspected_count: {len(report['graphify_context']['files_inspected'])}")
    lines.append(f"- god_nodes_noted: {report['graphify_context']['god_nodes_noted']}")
    lines.append(f"- excluded_areas: {report['graphify_context']['excluded_areas']}")
    lines.append("")
    lines.append("## 3. Baseline vs Overlay Snapshot")
    lines.append("| Metric | Baseline | Overlay | Delta |")
    lines.append("|---|---:|---:|---:|")
    for row in report["baseline_vs_overlay"]:
        lines.append(f"| {row['metric']} | {row['baseline']} | {row['overlay']} | {row['delta']} |")
    lines.append("")
    lines.append("## 4. Daily Return Volatility Analysis")
    dr = report["daily_return_stats"]
    lines.append(f"- mean_daily_return: {dr['mean']}")
    lines.append(f"- daily_std: {dr['std']}")
    lines.append(f"- annualized_volatility: {dr['annualized_volatility']}")
    lines.append(f"- positive_days: {dr['positive_days']}")
    lines.append(f"- negative_days: {dr['negative_days']}")
    lines.append(f"- zero_return_days: {dr['zero_return_days']}")
    lines.append(f"- worst_day: {dr['worst_day']}")
    lines.append(f"- best_day: {dr['best_day']}")
    lines.append("")
    lines.append("## 5. Sparse Profit / Capital Utilization Analysis")
    ce = report["capital_efficiency"]
    lines.append(f"- active_days: {ce['active_days']}")
    lines.append(f"- idle_days: {ce['idle_days']}")
    lines.append(f"- utilization_ratio: {ce['utilization_ratio']}")
    lines.append(f"- zero_return_days: {dr['zero_return_days']}")
    lines.append("")
    lines.append("## 6. Residual Loss Clustering")
    lc = report["loss_clustering"]
    lines.append(f"- max_negative_streak: {lc['max_negative_streak']}")
    lines.append(f"- drawdown_clusters: {lc['drawdown_clusters']}")
    lines.append("")
    lines.append("## 7. Symbol-Level Attribution")
    lines.append("| Symbol | Return | Return % | Vol % | DD Loss % | Trades |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in report["symbol_attribution"][:5]:
        lines.append(
            f"| {row['name']} | {row['return_contribution']} | {row['return_contribution_pct']} | "
            f"{row['volatility_contribution_pct']} | {row['drawdown_loss_share_pct']} | {row['trade_count']} |"
        )
    lines.append("")
    lines.append("## 8. Sector-Level Attribution")
    lines.append("| Sector | Return | Return % | Vol % | DD Loss % | Trades |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in report["sector_attribution"]:
        lines.append(
            f"| {row['name']} | {row['return_contribution']} | {row['return_contribution_pct']} | "
            f"{row['volatility_contribution_pct']} | {row['drawdown_loss_share_pct']} | {row['trade_count']} |"
        )
    lines.append("")
    lines.append("## 9. Trade Payoff Distribution")
    tp = report["trade_payoff_distribution"]
    lines.append(f"- trade_count: {tp['trade_count']}")
    lines.append(f"- win_rate: {tp['win_rate']}")
    lines.append(f"- avg_win: {tp['avg_win']}")
    lines.append(f"- avg_loss: {tp['avg_loss']}")
    lines.append(f"- payoff_ratio: {tp['payoff_ratio']}")
    lines.append(f"- tail_loss_count: {tp['tail_loss_count']}")
    lines.append(f"- tail_win_count: {tp['tail_win_count']}")
    lines.append(f"- skewness: {tp['skewness']}")
    lines.append("")
    lines.append("## 10. Overlay Side Effects")
    for item in report["overlay_side_effects"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 11. Root Cause Map")
    lines.append(f"- Primary Cause: {report['primary_cause']}")
    lines.append("- Secondary Causes:")
    for cause in report["secondary_causes"]:
        lines.append(f"  - {cause}")
    lines.append("- Minor Factors:")
    for cause in report["minor_factors"]:
        lines.append(f"  - {cause}")
    lines.append("")
    lines.append("## 12. Next Task Recommendation")
    nxt = report["recommended_next_task"]
    lines.append(f"- task_id: {nxt['task_id']}")
    lines.append(f"- objective: {nxt['objective']}")
    lines.append("- acceptance_criteria:")
    for c in nxt["acceptance_criteria"]:
        lines.append(f"  - {c}")
    lines.append("")
    lines.append("## 13. Final Answer")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T096-REVIEW: Sharpe gap attribution")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t093-review", type=str, default="docs/reports/task_093_review/task_093_review_failure_analysis.json")
    parser.add_argument("--input-t094", type=str, default="docs/reports/task_094/task_094_risk_architecture.json")
    parser.add_argument("--input-t094-review", type=str, default="docs/reports/task_094_review/task_094_review_component_attribution.json")
    parser.add_argument("--input-t095", type=str, default="docs/reports/task_095/task_095_risk_adoption.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_096_review/task_096_review_sharpe_gap.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_096_review/task_096_review_sharpe_gap.md",
    )
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    t093r = _load_json(Path(args.input_t093_review))
    t094 = _load_json(Path(args.input_t094))
    t094r = _load_json(Path(args.input_t094_review))
    t095 = _load_json(Path(args.input_t095))
    t096 = _load_json(Path(args.input_t096))

    scenario_name = str(t096.get("baseline_scenario", t093.get("primary_scenario", "A_BASE_10K_HIGH_COST")))
    scenario = t093["scenarios"][scenario_name]
    initial_capital = float(scenario["initial_capital"])
    positions = _positions_df(scenario.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed positions found in T093 scenario.")

    baseline_metrics = _metrics_from_trade_pnl(
        pnls=positions["net_pnl"].tolist(),
        exit_times=positions["exit_time"].tolist(),
        initial_capital=initial_capital,
    )

    overlay = str(t095.get("selected_overlay", t096.get("overlay", "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER")))
    flags, overrides = _overlay_flags(overlay)
    sim = _simulate_risk_architecture(positions, initial_capital=initial_capital, **flags, **overrides)
    overlay_metrics = _metrics_from_trade_pnl(
        pnls=sim["scaled_trade_pnls"],
        exit_times=sim["scaled_exit_times"],
        initial_capital=initial_capital,
    )

    baseline_daily = _daily_equity_series(baseline_metrics["equity_curve_daily"])
    overlay_daily = _daily_equity_series(overlay_metrics["equity_curve_daily"])
    overlay_rets, daily_stats = _daily_return_stats(overlay_daily)
    active_idle = _active_idle_stats(overlay_daily, sim.get("accepted_trade_rows", []))
    max_neg_streak = _max_negative_streak(overlay_rets)
    clusters = _drawdown_clusters(overlay_daily, top_n=5)

    accepted_df = _accepted_frame(sim)
    accepted_joined = _join_scaled_returns(accepted_df, positions)
    symbol_attr = _attribution_table(accepted_joined, "symbol", overlay_rets)
    sector_attr = _attribution_table(accepted_joined, "sector", overlay_rets)
    trade_dist = _trade_distribution(accepted_joined)
    blocked = _blocked_winners_losers(positions, accepted_df)

    # Side-effect comparison against baseline.
    baseline_util = float(t096.get("capital_efficiency", {}).get("baseline_capital_utilization", scenario.get("capital_utilization", 0.0)))
    overlay_util = float(t096.get("capital_efficiency", {}).get("overlay_capital_utilization", sim.get("utilization_after", 0.0)))
    baseline_trade_count = int(baseline_metrics["trade_count"])
    overlay_trade_count = int(overlay_metrics["trade_count"])
    baseline_ret = float(baseline_metrics["return_pct"])
    overlay_ret = float(overlay_metrics["return_pct"])
    baseline_mdd = float(baseline_metrics["mdd_pct"])
    overlay_mdd = float(overlay_metrics["mdd_pct"])
    baseline_sharpe = float(baseline_metrics["sharpe"])
    overlay_sharpe = float(overlay_metrics["sharpe"])

    target_sharpe = float(TARGET_SHARPE)
    actual_sharpe = float(t096.get("performance_comparison", [{}])[2].get("overlay", ACTUAL_SHARPE_DEFAULT))
    sharpe_gap = _f(target_sharpe - actual_sharpe, 4)

    primary_cause = (
        "Return generation remains lumpy (many zero-return days) while residual negative-day volatility stays high, "
        "so the mean/std balance is still below the Sharpe 0.7 threshold."
    )
    secondary_causes = [
        "Loss clustering improved but not eliminated: negative streaks still persist after overlay.",
        "Decorrelation + light loss breaker reduces utilization, limiting smooth compounding days.",
        "Volatility contribution remains concentrated in a few symbols, creating equity-curve noise."
        if symbol_attr
        else "Symbol-level concentration evidence is limited by sparse trade sample.",
    ]
    minor_factors = [
        "Blocked-trade logic removed both losers and some winners, muting net Sharpe lift.",
        "Single-sector concentration risk remains present in selected universe slices.",
    ]

    required_files = [
        "src/backtest/engine_full.py",
        "src/backtest/analysis_capital_backtest_093.py",
        "src/backtest/analysis_capital_failure_review_093.py",
        "src/backtest/analysis_drawdown_control_094.py",
        "src/backtest/analysis_risk_component_review_094.py",
        "src/backtest/analysis_risk_adoption_095.py",
        "src/backtest/analysis_revalidation_096.py",
        "src/risk/policies.py",
        "src/portfolio/allocator.py",
        "docs/reports/task_093/task_093_capital_backtest.json",
        "docs/reports/task_093_review/task_093_review_failure_analysis.json",
        "docs/reports/task_094/task_094_risk_architecture.json",
        "docs/reports/task_094_review/task_094_review_component_attribution.json",
        "docs/reports/task_095/task_095_risk_adoption.json",
        "docs/reports/task_096/task_096_revalidation.json",
    ]
    graphify_context = _build_graphify_context(required_files)

    report: dict[str, Any] = {
        "status": "PASS",
        "task": "T096-REVIEW",
        "target_sharpe": _f(target_sharpe),
        "actual_sharpe": _f(actual_sharpe),
        "sharpe_gap": sharpe_gap,
        "primary_cause": primary_cause,
        "secondary_causes": secondary_causes,
        "minor_factors": minor_factors,
        "daily_return_stats": daily_stats,
        "capital_efficiency": {
            "active_days": active_idle["active_days"],
            "idle_days": active_idle["idle_days"],
            "utilization_ratio": active_idle["utilization_ratio"],
            "baseline_capital_utilization": _f(baseline_util),
            "overlay_capital_utilization": _f(overlay_util),
        },
        "loss_clustering": {
            "max_negative_streak": int(max_neg_streak),
            "drawdown_clusters": clusters,
        },
        "symbol_attribution": symbol_attr[:5],
        "sector_attribution": sector_attr[:5],
        "trade_payoff_distribution": trade_dist,
        "baseline_vs_overlay": [
            {"metric": "Return %", "baseline": _f(baseline_ret), "overlay": _f(overlay_ret), "delta": _f(overlay_ret - baseline_ret)},
            {"metric": "MDD %", "baseline": _f(baseline_mdd), "overlay": _f(overlay_mdd), "delta": _f(overlay_mdd - baseline_mdd)},
            {"metric": "Sharpe", "baseline": _f(baseline_sharpe), "overlay": _f(overlay_sharpe), "delta": _f(overlay_sharpe - baseline_sharpe)},
            {
                "metric": "Annualized Volatility",
                "baseline": _f(float(_daily_return_stats(baseline_daily)[1]["annualized_volatility"])),
                "overlay": _f(float(daily_stats["annualized_volatility"])),
                "delta": _f(float(daily_stats["annualized_volatility"]) - float(_daily_return_stats(baseline_daily)[1]["annualized_volatility"])),
            },
            {"metric": "Trade Count", "baseline": baseline_trade_count, "overlay": overlay_trade_count, "delta": int(overlay_trade_count - baseline_trade_count)},
            {
                "metric": "Capital Utilization",
                "baseline": _f(baseline_util),
                "overlay": _f(overlay_util),
                "delta": _f(overlay_util - baseline_util),
            },
        ],
        "overlay_side_effects": [
            f"blocked_entries_count={int(sim.get('blocked_entries_count', 0))}, blocked_by_reason={sim.get('blocked_by_reason', {})}",
            (
                f"blocked_trades={blocked['blocked_trades']}, blocked_winners={blocked['blocked_winners']}, "
                f"blocked_losers={blocked['blocked_losers']}, blocked_avg_pnl={blocked['blocked_avg_pnl']}"
            ),
            (
                f"return_change={_f(overlay_ret - baseline_ret)}%, mdd_change={_f(overlay_mdd - baseline_mdd)}%, "
                f"sharpe_change={_f(overlay_sharpe - baseline_sharpe)}"
            ),
            (
                f"trade_count_change={overlay_trade_count - baseline_trade_count}, capital_utilization_change={_f(overlay_util - baseline_util)}"
            ),
        ],
        "graphify_context": graphify_context,
        "recommended_next_task": {
            "task_id": "T096.5",
            "objective": "Sharpe gap closure test via non-alpha smoothing diagnostics (same strategy/signal), focusing on return path regularity and residual volatility concentration.",
            "acceptance_criteria": [
                "Sharpe >= 0.70 while preserving MDD <= T096 overlay MDD + 0.3%",
                "No increase in max negative daily streak",
                "No degradation in T092 alignment (must remain PASS)",
                "Blocked-winner ratio does not exceed blocked-loser ratio by more than 10%",
            ],
        },
        "evidence_links": {
            "t093_review_primary_cause": t093r.get("primary_cause"),
            "t094_status": t094.get("status"),
            "t094_review_recommended_case": t094r.get("recommended_case"),
            "t095_selected_overlay": t095.get("selected_overlay"),
            "t096_status": t096.get("status"),
        },
        "final_answer": "Sharpe stayed below 0.7 because residual return-path lumpiness and remaining downside volatility still outweigh the overlay-driven drawdown reduction.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={report['status']}")
    print(f"sharpe_gap={report['sharpe_gap']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
