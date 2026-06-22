from __future__ import annotations

import argparse
import concurrent.futures
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    StructuralConfig,
    _asset_type,
    _full_configs,
    _label,
    _prepare_preloaded_frames,
    _quick_configs,
    _run_config_list,
    _scenario_name,
    run_structural_backtest,
)


def _result_row(result: dict[str, Any]) -> dict[str, Any]:
    cfg = StructuralConfig(**result["config"])
    metrics = dict(result["metrics"])
    diag = dict(result["diagnostics"])
    row = {
        "scenario": _scenario_name(cfg),
        "structure_mode": cfg.structure_mode,
        "stop_mode": cfg.stop_mode,
        "entry_bar_stop_mode": cfg.entry_bar_stop_mode,
        "atr_multiplier": cfg.atr_multiplier,
        "max_holding_days": cfg.max_holding_days,
        "min_avg_dollar_volume_20": cfg.min_avg_dollar_volume_20,
        **metrics,
        "top1_symbol_total_R_share": diag["top1_symbol_total_R_share"],
        "top3_symbol_total_R_share": diag["top3_symbol_total_R_share"],
        "open_gt_planned_entry_ratio": diag["open_gt_planned_entry_ratio"],
        "open_gt_actual_entry_ratio": diag["open_gt_actual_entry_ratio"],
        "fill_at_open_ratio": diag["fill_at_open_ratio"],
        "rejected_by_gap_over_entry_ratio_vs_triggered": diag["rejected_by_gap_over_entry_ratio_vs_triggered"],
        "triggered_candidates": diag["triggered_candidates"],
        "executed_entries": diag["executed_entries"],
    }
    row["label"] = _label(metrics, diag)
    return row


def _ranked_frame(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [_result_row(r) for r in results]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    label_rank = {"valid": 0, "weak_but_interesting": 1, "reject": 2}
    df["label_rank"] = df["label"].map(label_rank).fillna(9)
    return df.sort_values(
        ["label_rank", "sharpe", "expectancy_r", "cagr_pct", "trade_count", "max_drawdown_pct"],
        ascending=[True, False, False, False, False, True],
    ).reset_index(drop=True)


def _period_timestamps(timestamps: list[pd.Timestamp], start: str | None, end: str | None) -> list[pd.Timestamp]:
    start_ts = pd.Timestamp(start, tz="UTC") if start else None
    end_ts = pd.Timestamp(end, tz="UTC") if end else None
    out: list[pd.Timestamp] = []
    for ts in timestamps:
        if start_ts is not None and ts < start_ts:
            continue
        if end_ts is not None and ts > end_ts:
            continue
        out.append(ts)
    return out


def _run_single(
    cfg: StructuralConfig,
    *,
    base_dir: Path,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
    symbols: list[str],
) -> dict[str, Any]:
    return run_structural_backtest(
        cfg,
        base_dir,
        preloaded_frames=frames,
        preloaded_timestamps=timestamps,
        preloaded_symbols=symbols,
    )


def _chunked(items: list[Any], n: int) -> list[list[Any]]:
    n = max(1, n)
    return [items[i::n] for i in range(n) if items[i::n]]


def _run_symbol_exclusion_batch_worker(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_dir = Path(payload["base_dir"])
    stocks = list(payload["stocks"])
    tasks = list(payload["tasks"])
    pre_frames, pre_ts = _prepare_preloaded_frames(base_dir, stocks)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        cfg = StructuralConfig(**task["config"])
        rerun = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=pre_frames,
            preloaded_timestamps=pre_ts,
            preloaded_symbols=list(task["symbols"]),
        )
        rows.append(
            {
                "index": int(task["index"]),
                "scenario": task["scenario"],
                "excluded_symbol": task["excluded_symbol"],
                "exclusion_type": task["exclusion_type"],
                "cagr_pct": rerun["metrics"]["cagr_pct"],
                "sharpe": rerun["metrics"]["sharpe"],
                "expectancy_r": rerun["metrics"]["expectancy_r"],
                "trade_count": rerun["metrics"]["trade_count"],
                "total_return_pct": rerun["metrics"]["total_return_pct"],
            }
        )
    return rows


def _run_symbol_exclusion_reruns(
    tasks: list[dict[str, Any]],
    *,
    base_dir: Path,
    stocks: list[str],
    jobs: int,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
) -> list[dict[str, Any]]:
    if not tasks:
        return []
    if jobs <= 1:
        rows: list[dict[str, Any]] = []
        for task in tasks:
            cfg = StructuralConfig(**task["config"])
            rerun = _run_single(
                cfg,
                base_dir=base_dir,
                frames=frames,
                timestamps=timestamps,
                symbols=list(task["symbols"]),
            )
            rows.append(
                {
                    "index": int(task["index"]),
                    "scenario": task["scenario"],
                    "excluded_symbol": task["excluded_symbol"],
                    "exclusion_type": task["exclusion_type"],
                    "cagr_pct": rerun["metrics"]["cagr_pct"],
                    "sharpe": rerun["metrics"]["sharpe"],
                    "expectancy_r": rerun["metrics"]["expectancy_r"],
                    "trade_count": rerun["metrics"]["trade_count"],
                    "total_return_pct": rerun["metrics"]["total_return_pct"],
                }
            )
        return sorted(rows, key=lambda row: row["index"])

    workers = max(1, min(jobs, len(tasks)))
    payloads = [
        {"base_dir": str(base_dir), "stocks": list(stocks), "tasks": chunk}
        for chunk in _chunked(tasks, workers)
    ]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_run_symbol_exclusion_batch_worker, payload) for payload in payloads]
        for fut in concurrent.futures.as_completed(futures):
            rows.extend(fut.result())
    return sorted(rows, key=lambda row: row["index"])


def _run_period_config_batch_worker(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_dir = Path(payload["base_dir"])
    stocks = list(payload["stocks"])
    cfg_dicts = list(payload["configs"])
    rerun_timestamps = list(payload["timestamps"])
    pre_frames, _ = _prepare_preloaded_frames(base_dir, stocks)
    results: list[dict[str, Any]] = []
    for cfg_dict in cfg_dicts:
        cfg = StructuralConfig(**cfg_dict)
        results.append(
            run_structural_backtest(
                cfg,
                base_dir,
                preloaded_frames=pre_frames,
                preloaded_timestamps=rerun_timestamps,
                preloaded_symbols=stocks,
            )
        )
    return results


def _run_period_reruns(
    configs: list[StructuralConfig],
    *,
    base_dir: Path,
    stocks: list[str],
    jobs: int,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
) -> list[dict[str, Any]]:
    if not configs:
        return []
    if jobs <= 1:
        return [
            _run_single(cfg, base_dir=base_dir, frames=frames, timestamps=timestamps, symbols=stocks)
            for cfg in configs
        ]

    workers = max(1, min(jobs, len(configs)))
    payloads = [
        {
            "base_dir": str(base_dir),
            "stocks": list(stocks),
            "timestamps": list(timestamps),
            "configs": [cfg.__dict__ for cfg in chunk],
        }
        for chunk in _chunked(configs, workers)
    ]
    results: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_run_period_config_batch_worker, payload) for payload in payloads]
        for fut in concurrent.futures.as_completed(futures):
            results.extend(fut.result())
    result_by_scenario = {_scenario_name(StructuralConfig(**result["config"])): result for result in results}
    return [result_by_scenario[_scenario_name(cfg)] for cfg in configs]


def _symbol_contribution_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    scenario = _scenario_name(StructuralConfig(**result["config"]))
    total_r = sum(float(t["realized_R"]) for t in result["trade_log"])
    rows: list[dict[str, Any]] = []
    for row in result["diagnostics"]["by_symbol"]:
        share = float(row["total_r"]) / total_r if total_r else 0.0
        rows.append({"scenario": scenario, **row, "total_r_share": round(share, 6)})
    return rows


def _trade_overlap_matrix(results: list[dict[str, Any]]) -> pd.DataFrame:
    scenario_sets: dict[str, set[tuple[str, str]]] = {}
    for result in results:
        scenario = _scenario_name(StructuralConfig(**result["config"]))
        scenario_sets[scenario] = {(str(t["symbol"]), str(t["entry_date"])) for t in result["trade_log"]}
    labels = list(scenario_sets.keys())
    rows: list[dict[str, Any]] = []
    for lhs in labels:
        row = {"scenario": lhs}
        left = scenario_sets[lhs]
        for rhs in labels:
            right = scenario_sets[rhs]
            union = left | right
            overlap = len(left & right) / len(union) if union else 0.0
            row[rhs] = round(overlap, 6)
        rows.append(row)
    return pd.DataFrame(rows)


def _cluster_name(cfg: StructuralConfig) -> str:
    return f"{cfg.structure_mode}|{cfg.stop_mode}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 323 structural breakout robustness audit")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", type=str, default="docs/reports/task_323_structural_breakout_audit")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--max-full-scenarios", type=int, default=0)
    args = parser.parse_args(argv)

    base_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = max(1, int(args.jobs))

    stocks = [s for s in sorted(p.stem.upper() for p in base_dir.glob("*.csv")) if _asset_type(s) == "STOCK"]
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)

    quick = _run_config_list(_quick_configs(), base_dir=base_dir, stocks=stocks, jobs=jobs)
    full_cfgs = _full_configs(quick)
    if int(args.max_full_scenarios) > 0:
        full_cfgs = full_cfgs[: int(args.max_full_scenarios)]
    full = _run_config_list(full_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs)
    bias_cfgs = [
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=55, entry_bar_stop_mode="ALLOW_SAME_BAR_STOP"),
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=55, entry_bar_stop_mode="DISABLE_ENTRY_BAR_STOP"),
    ]
    bias = _run_config_list(bias_cfgs, base_dir=base_dir, stocks=stocks, jobs=1)
    all_results = quick + full + bias

    ranked = _ranked_frame(all_results)
    ranked.to_csv(out_dir / "all_scenarios_ranked.csv", index=False)
    top_n = max(1, int(args.top_n))
    top_rows = ranked.head(top_n).copy()
    top_ids = set(top_rows["scenario"].tolist())
    top_results = [r for r in all_results if _scenario_name(StructuralConfig(**r["config"])) in top_ids]

    contribution_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    exclusion_tasks: list[dict[str, Any]] = []

    result_by_scenario = {_scenario_name(StructuralConfig(**r["config"])): r for r in all_results}
    exclusion_index = 0
    for scenario in top_rows["scenario"].tolist():
        result = result_by_scenario[scenario]
        cfg = StructuralConfig(**result["config"])
        contribution_rows.extend(_symbol_contribution_rows(result))

        diag = result["diagnostics"]
        by_symbol = sorted(diag["by_symbol"], key=lambda x: float(x["total_r"]), reverse=True)
        best_symbol = by_symbol[0]["symbol"] if by_symbol else ""
        worst_symbol = by_symbol[-1]["symbol"] if by_symbol else ""

        for excluded_symbol, exclusion_type in ((best_symbol, "best_symbol_excluded"), (worst_symbol, "worst_symbol_excluded")):
            remaining = [s for s in stocks if s != excluded_symbol]
            exclusion_tasks.append(
                {
                    "index": exclusion_index,
                    "config": cfg.__dict__,
                    "symbols": remaining,
                    "scenario": scenario,
                    "excluded_symbol": excluded_symbol,
                    "exclusion_type": exclusion_type,
                }
            )
            exclusion_index += 1

        fill_rows.append(
            {
                "scenario": scenario,
                "open_gt_planned_entry_ratio": diag["open_gt_planned_entry_ratio"],
                "open_gt_actual_entry_ratio": diag["open_gt_actual_entry_ratio"],
                "fill_at_open_ratio": diag["fill_at_open_ratio"],
                "rejected_by_gap_over_entry_ratio_vs_triggered": diag["rejected_by_gap_over_entry_ratio_vs_triggered"],
                "triggered_candidates": diag["triggered_candidates"],
                "executed_entries": diag["executed_entries"],
            }
        )

    contribution_df = pd.DataFrame(contribution_rows).sort_values(["scenario", "total_r"], ascending=[True, False])
    contribution_df.to_csv(out_dir / "top20_symbol_contribution.csv", index=False)
    exclusion_rows = _run_symbol_exclusion_reruns(
        exclusion_tasks,
        base_dir=base_dir,
        stocks=stocks,
        jobs=jobs,
        frames=frames,
        timestamps=timestamps,
    )
    exclusion_df = pd.DataFrame([{k: v for k, v in row.items() if k != "index"} for row in exclusion_rows])
    exclusion_df.to_csv(out_dir / "top20_symbol_exclusion_impact.csv", index=False)
    fill_df = pd.DataFrame(fill_rows)
    fill_df.to_csv(out_dir / "top20_fill_assumption_audit.csv", index=False)

    top20_summary = top_rows.merge(
        exclusion_df.pivot(index="scenario", columns="exclusion_type", values="cagr_pct").reset_index(),
        on="scenario",
        how="left",
    )
    top20_summary.to_csv(out_dir / "top20_summary.csv", index=False)

    liquidity_rows: list[dict[str, Any]] = []
    best_full_result = result_by_scenario[top_rows.iloc[0]["scenario"]]
    best_full_cfg = StructuralConfig(**best_full_result["config"])
    for multiplier in (0.5, 1.0, 1.5, 2.0):
        threshold = best_full_cfg.min_avg_dollar_volume_20 * multiplier
        cfg = StructuralConfig(**{**best_full_cfg.__dict__, "min_avg_dollar_volume_20": threshold})
        rerun = _run_single(cfg, base_dir=base_dir, frames=frames, timestamps=timestamps, symbols=stocks)
        liquidity_rows.append(
            {
                "scenario": _scenario_name(cfg),
                "liquidity_multiplier": multiplier,
                "min_avg_dollar_volume_20": threshold,
                "cagr_pct": rerun["metrics"]["cagr_pct"],
                "sharpe": rerun["metrics"]["sharpe"],
                "expectancy_r": rerun["metrics"]["expectancy_r"],
                "trade_count": rerun["metrics"]["trade_count"],
                "total_return_pct": rerun["metrics"]["total_return_pct"],
            }
        )
    liquidity_df = pd.DataFrame(liquidity_rows)
    liquidity_df.to_csv(out_dir / "liquidity_sensitivity.csv", index=False)

    allow_disable_rows: list[dict[str, Any]] = []
    for mode in ("ALLOW_SAME_BAR_STOP", "DISABLE_ENTRY_BAR_STOP"):
        cfg = StructuralConfig(**{**best_full_cfg.__dict__, "entry_bar_stop_mode": mode})
        rerun = _run_single(cfg, base_dir=base_dir, frames=frames, timestamps=timestamps, symbols=stocks)
        allow_disable_rows.append({"scenario": _scenario_name(cfg), "entry_bar_stop_mode": mode, **rerun["metrics"], **{
            "fill_at_open_ratio": rerun["diagnostics"]["fill_at_open_ratio"],
            "rejected_by_gap_over_entry_ratio_vs_triggered": rerun["diagnostics"]["rejected_by_gap_over_entry_ratio_vs_triggered"],
        }})
    same_bar_df = pd.DataFrame(allow_disable_rows)
    same_bar_df.to_csv(out_dir / "same_bar_stop_comparison.csv", index=False)

    cluster_rows: list[dict[str, Any]] = []
    for result in all_results:
        cfg = StructuralConfig(**result["config"])
        metrics = result["metrics"]
        cluster_rows.append(
            {
                "cluster": _cluster_name(cfg),
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
            }
        )
    cluster_df = pd.DataFrame(cluster_rows)
    cluster_summary = (
        cluster_df.groupby("cluster")
        .agg(
            scenario_count=("cluster", "size"),
            cagr_mean=("cagr_pct", "mean"),
            cagr_median=("cagr_pct", "median"),
            sharpe_mean=("sharpe", "mean"),
            sharpe_median=("sharpe", "median"),
            expectancy_mean=("expectancy_r", "mean"),
            expectancy_median=("expectancy_r", "median"),
            trade_count_mean=("trade_count", "mean"),
            trade_count_median=("trade_count", "median"),
        )
        .reset_index()
        .sort_values(["sharpe_mean", "expectancy_mean"], ascending=[False, False])
    )
    cluster_summary.to_csv(out_dir / "parameter_cluster_summary.csv", index=False)

    overlap_df = _trade_overlap_matrix(top_results)
    overlap_df.to_csv(out_dir / "top20_trade_overlap_matrix.csv", index=False)

    all_configs = [StructuralConfig(**r["config"]) for r in all_results]
    is_results = _run_period_reruns(
        all_configs,
        base_dir=base_dir,
        stocks=stocks,
        jobs=jobs,
        frames=frames,
        timestamps=_period_timestamps(timestamps, "2021-01-01", "2023-12-31"),
    )
    oos_results = _run_period_reruns(
        all_configs,
        base_dir=base_dir,
        stocks=stocks,
        jobs=jobs,
        frames=frames,
        timestamps=_period_timestamps(timestamps, "2024-01-01", "2026-12-31"),
    )
    is_ranked = _ranked_frame(is_results)
    oos_ranked = _ranked_frame(oos_results)
    is_ranked.to_csv(out_dir / "in_sample_ranked.csv", index=False)
    oos_ranked.to_csv(out_dir / "out_of_sample_ranked.csv", index=False)

    full_best_scenario = top_rows.iloc[0]["scenario"]
    oos_rank_map = {scenario: idx + 1 for idx, scenario in enumerate(oos_ranked["scenario"].tolist())}
    is_rank_map = {scenario: idx + 1 for idx, scenario in enumerate(is_ranked["scenario"].tolist())}
    walk_forward_df = pd.DataFrame(
        [
            {
                "view": "full_period_best",
                "scenario": full_best_scenario,
                "full_period_rank": 1,
                "in_sample_rank": is_rank_map.get(full_best_scenario, 0),
                "out_of_sample_rank": oos_rank_map.get(full_best_scenario, 0),
                "out_of_sample_top1": oos_ranked.iloc[0]["scenario"],
                "holds_in_oos": bool(oos_ranked.iloc[0]["scenario"] == full_best_scenario),
            },
            {
                "view": "in_sample_best",
                "scenario": is_ranked.iloc[0]["scenario"],
                "full_period_rank": int(ranked.index[ranked["scenario"] == is_ranked.iloc[0]["scenario"]][0]) + 1,
                "in_sample_rank": 1,
                "out_of_sample_rank": oos_rank_map.get(is_ranked.iloc[0]["scenario"], 0),
                "out_of_sample_top1": oos_ranked.iloc[0]["scenario"],
                "holds_in_oos": bool(oos_ranked.iloc[0]["scenario"] == is_ranked.iloc[0]["scenario"]),
            },
        ]
    )
    walk_forward_df.to_csv(out_dir / "walk_forward_summary.csv", index=False)

    best_exclusion = exclusion_df[exclusion_df["exclusion_type"] == "best_symbol_excluded"]
    worst_exclusion = exclusion_df[exclusion_df["exclusion_type"] == "worst_symbol_excluded"]

    lines = [
        "# Task 323 Structural Breakout Robustness Audit",
        "",
        "## Scope",
        f"- Ranked scenarios audited: top {top_n} by label -> Sharpe -> expectancy -> CAGR -> trade count.",
        "- Full-period ranking uses the same scenario universe as Task 322, rerun with unique scenario identifiers.",
        "",
        "## Top Scenario",
        f"- full-period best: `{full_best_scenario}`",
        f"- OOS top1: `{oos_ranked.iloc[0]['scenario']}`",
        f"- full-period best holds in OOS: `{bool(oos_ranked.iloc[0]['scenario'] == full_best_scenario)}`",
        "",
        "## Fill Assumption Snapshot",
        f"- median open > planned entry ratio (top {top_n}): {fill_df['open_gt_planned_entry_ratio'].median():.4f}",
        f"- median open > actual entry ratio (top {top_n}): {fill_df['open_gt_actual_entry_ratio'].median():.4f}",
        f"- median fill_at_open ratio (top {top_n}): {fill_df['fill_at_open_ratio'].median():.4f}",
        f"- median rejected_by_gap_over_entry / triggered ratio (top {top_n}): {fill_df['rejected_by_gap_over_entry_ratio_vs_triggered'].median():.4f}",
        "",
        "## Symbol Exclusion Snapshot",
        f"- median CAGR after best-symbol exclusion: {best_exclusion['cagr_pct'].median():.4f}",
        f"- median CAGR after worst-symbol exclusion: {worst_exclusion['cagr_pct'].median():.4f}",
        "",
        "## Artifacts",
        "- `all_scenarios_ranked.csv`",
        "- `top20_summary.csv`",
        "- `top20_symbol_contribution.csv`",
        "- `top20_symbol_exclusion_impact.csv`",
        "- `top20_fill_assumption_audit.csv`",
        "- `liquidity_sensitivity.csv`",
        "- `same_bar_stop_comparison.csv`",
        "- `parameter_cluster_summary.csv`",
        "- `top20_trade_overlap_matrix.csv`",
        "- `in_sample_ranked.csv`",
        "- `out_of_sample_ranked.csv`",
        "- `walk_forward_summary.csv`",
    ]
    (out_dir / "task_323_structural_breakout_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
