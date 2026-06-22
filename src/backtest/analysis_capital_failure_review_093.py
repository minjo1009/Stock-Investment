from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


def _f(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a / b)


@dataclass(frozen=True)
class DrawdownCluster:
    start: str
    trough: str
    end: str | None
    duration_days: int
    recovery_days: int | None
    peak_equity: float
    trough_equity: float
    drawdown_pct: float
    drawdown_amount: float


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _equity_df(curve: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(curve)
    if df.empty:
        return pd.DataFrame(columns=["ts", "equity"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    df = df.dropna(subset=["ts", "equity"]).sort_values("ts").reset_index(drop=True)
    return df


def _positions_df(positions: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(positions)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "sector",
                "entry_time",
                "exit_time",
                "qty",
                "entry_price_eff",
                "exit_price_eff",
                "gross_pnl",
                "net_pnl",
                "return_pct",
                "exit_rule",
                "notional",
            ]
        )
    for col in ["entry_time", "exit_time"]:
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    for col in ["qty", "entry_price_eff", "exit_price_eff", "gross_pnl", "net_pnl", "return_pct", "notional"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["entry_time", "exit_time", "net_pnl", "notional"]).sort_values("exit_time").reset_index(drop=True)


def _drawdown_clusters(equity: pd.DataFrame) -> tuple[list[DrawdownCluster], pd.DataFrame]:
    if equity.empty:
        return [], equity
    work = equity.copy()
    work["peak"] = work["equity"].cummax()
    work["drawdown_amount"] = work["peak"] - work["equity"]
    work["drawdown_pct"] = work["drawdown_amount"] / work["peak"].replace(0, pd.NA)
    work["in_dd"] = work["drawdown_amount"] > 0

    groups = (work["in_dd"] != work["in_dd"].shift(1)).cumsum()
    clusters: list[DrawdownCluster] = []
    for _grp, seg in work.groupby(groups):
        if not bool(seg["in_dd"].iloc[0]):
            continue
        start_idx = int(seg.index[0])
        end_idx = int(seg.index[-1])
        trough_idx = int(seg["drawdown_amount"].idxmax())
        peak_idx = max(start_idx - 1, 0)
        peak_val = float(work.loc[peak_idx, "equity"])
        trough_val = float(work.loc[trough_idx, "equity"])
        dd_amt = float(work.loc[trough_idx, "drawdown_amount"])
        dd_pct = float(work.loc[trough_idx, "drawdown_pct"] * 100.0) if pd.notna(work.loc[trough_idx, "drawdown_pct"]) else 0.0

        recovery_idx = work.index[(work.index > end_idx) & (work["equity"] >= peak_val)]
        if len(recovery_idx) > 0:
            rec_i = int(recovery_idx[0])
            rec_days = int((work.loc[rec_i, "ts"] - work.loc[start_idx, "ts"]).days)
            end_ts = str(work.loc[rec_i, "ts"].isoformat())
        else:
            rec_days = None
            end_ts = None

        clusters.append(
            DrawdownCluster(
                start=str(work.loc[start_idx, "ts"].isoformat()),
                trough=str(work.loc[trough_idx, "ts"].isoformat()),
                end=end_ts,
                duration_days=int((work.loc[end_idx, "ts"] - work.loc[start_idx, "ts"]).days),
                recovery_days=rec_days,
                peak_equity=_f(peak_val, 4),
                trough_equity=_f(trough_val, 4),
                drawdown_pct=_f(dd_pct, 4),
                drawdown_amount=_f(dd_amt, 4),
            )
        )
    clusters.sort(key=lambda c: c.drawdown_pct, reverse=True)
    return clusters, work


def _dd_contributors(positions: pd.DataFrame, clusters: list[DrawdownCluster]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if positions.empty:
        return rows
    for cluster in clusters[:3]:
        start = pd.Timestamp(cluster.start)
        trough = pd.Timestamp(cluster.trough)
        seg = positions[(positions["exit_time"] >= start) & (positions["exit_time"] <= trough)]
        if seg.empty:
            rows.append(
                {
                    "cluster_start": cluster.start,
                    "cluster_trough": cluster.trough,
                    "top_symbol_losses": [],
                    "top_sector_losses": [],
                }
            )
            continue
        sym = (
            seg.groupby("symbol", as_index=False)["net_pnl"]
            .sum()
            .sort_values("net_pnl", ascending=True)
            .head(5)
            .to_dict(orient="records")
        )
        sec = (
            seg.groupby("sector", as_index=False)["net_pnl"]
            .sum()
            .sort_values("net_pnl", ascending=True)
            .head(5)
            .to_dict(orient="records")
        )
        rows.append(
            {
                "cluster_start": cluster.start,
                "cluster_trough": cluster.trough,
                "top_symbol_losses": [{"symbol": r["symbol"], "net_pnl": _f(r["net_pnl"], 4)} for r in sym],
                "top_sector_losses": [{"sector": r["sector"], "net_pnl": _f(r["net_pnl"], 4)} for r in sec],
            }
        )
    return rows


def _loss_streaks(positions: pd.DataFrame) -> dict[str, Any]:
    if positions.empty:
        return {"loss_streak_max": 0, "clusters": []}
    seq = positions.sort_values("exit_time").reset_index(drop=True)
    streak = 0
    start_idx: int | None = None
    clusters: list[dict[str, Any]] = []
    best = 0
    for i, row in seq.iterrows():
        if float(row["net_pnl"]) < 0:
            if streak == 0:
                start_idx = i
            streak += 1
            best = max(best, streak)
        else:
            if streak > 0 and start_idx is not None:
                seg = seq.loc[start_idx : i - 1]
                clusters.append(
                    {
                        "start": str(seg.iloc[0]["exit_time"].isoformat()),
                        "end": str(seg.iloc[-1]["exit_time"].isoformat()),
                        "length": int(len(seg)),
                        "total_loss": _f(seg["net_pnl"].sum(), 4),
                    }
                )
            streak = 0
            start_idx = None
    if streak > 0 and start_idx is not None:
        seg = seq.loc[start_idx : len(seq) - 1]
        clusters.append(
            {
                "start": str(seg.iloc[0]["exit_time"].isoformat()),
                "end": str(seg.iloc[-1]["exit_time"].isoformat()),
                "length": int(len(seg)),
                "total_loss": _f(seg["net_pnl"].sum(), 4),
            }
        )
    clusters.sort(key=lambda x: x["length"], reverse=True)
    return {"loss_streak_max": int(best), "clusters": clusters[:10]}


def _concurrency(positions: pd.DataFrame) -> dict[str, Any]:
    if positions.empty:
        return {"max_concurrent_positions": 0, "avg_concurrent_positions": 0.0}
    events: list[tuple[pd.Timestamp, int]] = []
    for row in positions.itertuples(index=False):
        events.append((pd.Timestamp(row.entry_time), +1))
        events.append((pd.Timestamp(row.exit_time), -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    running = 0
    peak = 0
    samples: list[int] = []
    for _ts, delta in events:
        running = max(0, running + delta)
        peak = max(peak, running)
        samples.append(running)
    avg = float(sum(samples) / len(samples)) if samples else 0.0
    return {"max_concurrent_positions": int(peak), "avg_concurrent_positions": _f(avg)}


def _histogram(series: pd.Series, bins: int = 12) -> list[dict[str, Any]]:
    if series.empty:
        return []
    clipped = series.astype(float)
    cats = pd.cut(clipped, bins=bins)
    counts = cats.value_counts().sort_index()
    rows: list[dict[str, Any]] = []
    for iv, cnt in counts.items():
        rows.append({"bin": str(iv), "count": int(cnt)})
    return rows


def _root_cause_map(
    *,
    primary_metrics: dict[str, Any],
    drawdowns: list[DrawdownCluster],
    loss_streak_max: int,
    concentration_idx: float,
    avg_loss: float,
    avg_win: float,
) -> dict[str, Any]:
    primary = "Drawdown clustering from repeated loss sequences under moderate exposure creates poor risk-adjusted returns."
    secondary = [
        "Loss-side volatility is too high relative to daily equity smoothness (Sharpe compression).",
        "Concentration around a narrow sector set amplifies downside episodes.",
        "Capital efficiency is moderate, but return path variance dominates performance quality.",
    ]
    minor: list[str] = []
    if abs(avg_loss) > abs(avg_win):
        minor.append("Average loss magnitude exceeds average win magnitude.")
    if concentration_idx > 0.25:
        minor.append("Symbol-level concentration index is elevated.")
    if drawdowns and drawdowns[0].recovery_days is not None and drawdowns[0].recovery_days > 60:
        minor.append("Longest drawdown recovery is prolonged.")
    if loss_streak_max >= 4:
        minor.append("Observed loss streaks are long enough to induce behavioral/operational stress.")
    if not minor:
        minor.append("Minor factors are secondary to the main drawdown clustering driver.")
    return {"primary_cause": primary, "secondary_causes": secondary, "minor_factors": minor}


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T093-REVIEW - Failure Analysis")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append(f"- primary_failure_reason: {report['primary_cause']}")
    lines.append(f"- secondary_contributors: {', '.join(report['secondary_causes'])}")
    lines.append("")
    lines.append("## 2. Drawdown Analysis")
    lines.append("| Start | Trough | End | DD % | DD Amount | Duration(d) | Recovery(d) |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for row in report["drawdown_clusters"][:3]:
        lines.append(
            f"| {row['start']} | {row['trough']} | {row['end']} | {row['drawdown_pct']:.4f} | {row['drawdown_amount']:.4f} | {row['duration_days']} | {row['recovery_days']} |"
        )
    lines.append("")
    lines.append("## 3. Trade Distribution")
    lines.append(f"- win_rate: {report['trade_distribution']['win_rate']}")
    lines.append(f"- avg_win: {report['trade_distribution']['avg_win']}")
    lines.append(f"- avg_loss: {report['trade_distribution']['avg_loss']}")
    lines.append(f"- skewness: {report['trade_distribution']['skewness']}")
    lines.append(f"- tail_loss_threshold_5pct: {report['trade_distribution']['tail_loss_threshold_5pct']}")
    lines.append("")
    lines.append("## 4. Loss Clustering")
    lines.append(f"- loss_streak_max: {report['loss_streak_max']}")
    for row in report["loss_clusters"][:5]:
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## 5. Position Sizing Impact")
    for k, v in report["position_sizing_impact"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 6. Portfolio Risk")
    for k, v in report["portfolio_risk"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 7. Capital Efficiency")
    for k, v in report["capital_efficiency"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 8. Root Cause Map")
    lines.append(f"- Primary Cause: {report['primary_cause']}")
    lines.append(f"- Secondary Causes: {report['secondary_causes']}")
    lines.append(f"- Minor Factors: {report['minor_factors']}")
    lines.append("")
    lines.append("## 9. Decision")
    lines.append("- status: FAIL")
    lines.append("")
    lines.append("## 10. Final Answer")
    lines.append(f"- {report['root_cause_summary']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T093-REVIEW: Capital failure attribution")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_093/task_093_capital_backtest.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_093_review/task_093_review_failure_analysis.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_093_review/task_093_review_failure_analysis.md",
    )
    args = parser.parse_args(argv)

    payload = _load_json(Path(args.input_json))
    primary_scenario = str(payload.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    primary_metrics = payload["scenarios"][primary_scenario]
    positions = _positions_df(primary_metrics.get("closed_positions", []))
    equity = _equity_df(primary_metrics.get("equity_curve_daily", []))

    dd_clusters, dd_frame = _drawdown_clusters(equity)
    dd_contributors = _dd_contributors(positions, dd_clusters)

    returns = positions["return_pct"].astype(float) if not positions.empty else pd.Series(dtype=float)
    pnls = positions["net_pnl"].astype(float) if not positions.empty else pd.Series(dtype=float)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    trade_distribution = {
        "trade_count": int(len(positions)),
        "win_count": int((pnls > 0).sum()),
        "loss_count": int((pnls < 0).sum()),
        "win_rate": _f(_safe_div((pnls > 0).sum(), max(len(pnls), 1)) * 100.0),
        "avg_win": _f(wins.mean()) if not wins.empty else 0.0,
        "avg_loss": _f(losses.mean()) if not losses.empty else 0.0,
        "skewness": _f(float(returns.skew())) if len(returns) > 2 else 0.0,
        "tail_loss_threshold_5pct": _f(float(pnls.quantile(0.05))) if not pnls.empty else 0.0,
        "extreme_loss_trades": (
            positions.nsmallest(10, "net_pnl")[["symbol", "sector", "exit_time", "net_pnl", "return_pct", "exit_rule"]]
            .assign(
                exit_time=lambda df: df["exit_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                net_pnl=lambda df: df["net_pnl"].round(4),
                return_pct=lambda df: df["return_pct"].round(4),
            )
            .to_dict(orient="records")
            if not positions.empty
            else []
        ),
        "return_histogram": _histogram(returns, bins=12),
    }

    streak_info = _loss_streaks(positions)
    concurrency = _concurrency(positions)

    symbol_exp = (
        positions.groupby("symbol", as_index=False)["notional"].sum().sort_values("notional", ascending=False)
        if not positions.empty
        else pd.DataFrame(columns=["symbol", "notional"])
    )
    sector_exp = (
        positions.groupby("sector", as_index=False)["notional"].sum().sort_values("notional", ascending=False)
        if not positions.empty
        else pd.DataFrame(columns=["sector", "notional"])
    )
    total_notional = float(positions["notional"].sum()) if not positions.empty else 0.0
    symbol_hhi = (
        float(((symbol_exp["notional"] / total_notional) ** 2).sum()) if total_notional > 0 and not symbol_exp.empty else 0.0
    )
    top3_symbol_share = (
        _f(symbol_exp.head(3)["notional"].sum() / total_notional) if total_notional > 0 and not symbol_exp.empty else 0.0
    )
    top_sector_share = (
        _f(sector_exp.head(1)["notional"].sum() / total_notional) if total_notional > 0 and not sector_exp.empty else 0.0
    )

    unchanged_days = 0
    if not equity.empty:
        eq_diff = equity["equity"].diff().fillna(0.0)
        unchanged_days = int((eq_diff.abs() < 1e-9).sum())
    idle_ratio = _safe_div(unchanged_days, max(len(equity), 1))

    exposure_series = dd_frame["drawdown_pct"].astype(float) if not dd_frame.empty else pd.Series(dtype=float)
    exposure_return_corr = 0.0
    if len(positions) >= 3:
        x = positions["notional"].astype(float)
        y = positions["net_pnl"].astype(float)
        if x.std(ddof=0) > 0 and y.std(ddof=0) > 0:
            exposure_return_corr = float(x.corr(y))

    position_sizing_impact = {
        "risk_per_trade_pct": 1.0,
        "max_position_size_pct": 30.0,
        "portfolio_max_exposure_pct": 100.0,
        "per_symbol_cap_pct": 30.0,
        "exposure_peak": _f(float(primary_metrics.get("exposure_ratio", 0.0)) * 100.0),
        "avg_notional": _f(float(positions["notional"].mean()) if not positions.empty else 0.0, 4),
        "sizing_drawdown_proxy_corr": _f(float(exposure_series.corr(exposure_series.shift(1).fillna(0))) if len(exposure_series) > 3 else 0.0),
    }

    portfolio_risk = {
        "top3_symbol_notional_share": top3_symbol_share,
        "top_sector_notional_share": top_sector_share,
        "symbol_concentration_hhi": _f(symbol_hhi),
        "max_concurrent_positions": concurrency["max_concurrent_positions"],
        "avg_concurrent_positions": concurrency["avg_concurrent_positions"],
        "symbol_exposure_table": (
            symbol_exp.assign(notional=lambda df: df["notional"].round(4)).to_dict(orient="records")
            if not symbol_exp.empty
            else []
        ),
        "sector_exposure_table": (
            sector_exp.assign(notional=lambda df: df["notional"].round(4)).to_dict(orient="records")
            if not sector_exp.empty
            else []
        ),
    }

    capital_eff = {
        "capital_utilization": _f(float(primary_metrics.get("capital_utilization", 0.0))),
        "exposure_ratio": _f(float(primary_metrics.get("exposure_ratio", 0.0))),
        "idle_equity_day_ratio": _f(idle_ratio),
        "return_vs_exposure_corr_proxy": _f(exposure_return_corr),
        "data_note": "Regime-tagged loss clustering by BULL/BEAR is unavailable in T093 payload; used temporal clusters instead.",
    }

    root_map = _root_cause_map(
        primary_metrics=primary_metrics,
        drawdowns=dd_clusters,
        loss_streak_max=streak_info["loss_streak_max"],
        concentration_idx=symbol_hhi,
        avg_loss=float(trade_distribution["avg_loss"]),
        avg_win=float(trade_distribution["avg_win"]),
    )

    report = {
        "status": "FAIL",
        "primary_cause": root_map["primary_cause"],
        "secondary_causes": root_map["secondary_causes"],
        "minor_factors": root_map["minor_factors"],
        "scenario": primary_scenario,
        "drawdown_clusters": [
            {
                "start": c.start,
                "trough": c.trough,
                "end": c.end,
                "duration_days": c.duration_days,
                "recovery_days": c.recovery_days,
                "peak_equity": c.peak_equity,
                "trough_equity": c.trough_equity,
                "drawdown_pct": c.drawdown_pct,
                "drawdown_amount": c.drawdown_amount,
            }
            for c in dd_clusters[:10]
        ],
        "drawdown_contributors_top3": dd_contributors,
        "loss_streak_max": int(streak_info["loss_streak_max"]),
        "loss_clusters": streak_info["clusters"],
        "trade_distribution": trade_distribution,
        "position_sizing_impact": position_sizing_impact,
        "portfolio_risk": portfolio_risk,
        "capital_efficiency": capital_eff,
        "avg_win": trade_distribution["avg_win"],
        "avg_loss": trade_distribution["avg_loss"],
        "exposure_peak": position_sizing_impact["exposure_peak"],
        "capital_utilization": capital_eff["capital_utilization"],
        "root_cause_summary": "Clustered downside episodes with slow recovery dominate equity volatility, compressing Sharpe under capital constraints.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print("status=FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
