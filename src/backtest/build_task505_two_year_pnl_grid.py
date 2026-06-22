from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, holding_quality, quality


DEFAULT_TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_505_two_year_pnl_grid")

DEFAULT_MIN_CELL_COUNT = 10
DEFAULT_LOOKBACK_DAYS = 730


@dataclass(frozen=True)
class PortfolioResult:
    quality: dict[str, object]
    accepted_panel: pd.DataFrame
    equity_curve: pd.DataFrame


@dataclass(frozen=True)
class Task505Artifacts:
    two_year_pnl_grid_candidate_pool: pd.DataFrame
    selected_two_year_pnl_strategy_rulebook: pd.DataFrame
    selected_two_year_pnl_strategy_panel: pd.DataFrame
    selected_two_year_pnl_strategy_quality: pd.DataFrame
    selected_two_year_pnl_equity_curve: pd.DataFrame
    selected_two_year_pnl_quarterly_quality: pd.DataFrame
    selected_two_year_pnl_theme_quality: pd.DataFrame
    selected_two_year_pnl_concentration_audit: pd.DataFrame
    task_505_decision: pd.DataFrame


def build_task505_two_year_pnl_grid(
    *,
    task503_panel_path: Path = DEFAULT_TASK503_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> Task505Artifacts:
    source = load_source_panel(task503_panel_path)
    two_year = latest_window(source, lookback_days=lookback_days)
    cell_pool = build_cell_pool(two_year)
    candidate_pool, candidate_panels = run_grid(two_year, cell_pool)
    selected_row = select_best_candidate(candidate_pool)
    selected_panel = candidate_panels.get(str(selected_row["candidate_strategy_name"]), two_year.iloc[0:0].copy())
    selected_rulebook = selected_cell_rulebook(cell_pool, selected_row)
    selected_quality = pd.DataFrame([strategy_quality(selected_panel, selected_row)])
    selected_equity = simulate_portfolio(selected_panel, max_positions=int(selected_row["max_positions"])).equity_curve
    quarterly = quality(selected_panel, ["quarter"]) if not selected_panel.empty else pd.DataFrame()
    theme = quality(selected_panel, ["theme_id"]) if not selected_panel.empty else pd.DataFrame()
    concentration = concentration_audit(selected_panel)
    decision = build_decision(candidate_pool, selected_quality, selected_row, lookback_days)
    artifacts = Task505Artifacts(
        candidate_pool,
        selected_rulebook,
        selected_panel,
        selected_quality,
        selected_equity,
        quarterly,
        theme,
        concentration,
        decision,
    )
    write_artifacts(out_dir, artifacts)
    return artifacts


def load_source_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {
        "lifecycle_id",
        "entry_ts",
        "simulated_exit_ts",
        "net_return_from_entry",
        "theme_id",
        "symbol_multiday_setup_state",
        "timing_state",
    }
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"Task505 source panel missing required columns: {missing}")
    panel = panel.copy()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    panel = panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()
    panel["inferred_lifecycle_matching_used_flag"] = 0
    panel["label_used_in_assignment_flag"] = 0
    if "quarter" not in panel.columns:
        panel["quarter"] = panel["entry_ts"].dt.to_period("Q").astype(str)
    return panel.sort_values("entry_ts").reset_index(drop=True)


def latest_window(panel: pd.DataFrame, *, lookback_days: int) -> pd.DataFrame:
    if panel.empty:
        return panel.copy()
    end_ts = panel["entry_ts"].max()
    start_ts = end_ts - pd.Timedelta(days=lookback_days)
    return panel[panel["entry_ts"].between(start_ts, end_ts)].copy().reset_index(drop=True)


def build_cell_pool(panel: pd.DataFrame) -> pd.DataFrame:
    dimensions = [
        ["theme_id", "symbol_multiday_setup_state", "timing_state"],
        ["theme_id", "symbol_multiday_setup_state"],
        ["theme_id", "timing_state"],
        ["symbol_multiday_setup_state", "timing_state"],
    ]
    rows: list[dict[str, object]] = []
    for dims in dimensions:
        for values, subset in panel.groupby(dims, dropna=False):
            if len(subset) < DEFAULT_MIN_CELL_COUNT:
                continue
            if not isinstance(values, tuple):
                values = (values,)
            row = aggregate(subset)
            row.update(
                {
                    "cell_key": "|".join([",".join(dims), *[str(v) for v in values]]),
                    "cell_dims": "|".join(dims),
                    "cell_values": "|".join(str(v) for v in values),
                    "min_cell_count": DEFAULT_MIN_CELL_COUNT,
                    "label_used_in_assignment_flag": 0,
                    "inferred_lifecycle_matching_used_flag": 0,
                }
            )
            row["cell_selection_score"] = (
                float(row["avg_net_return_pct"])
                + 12.0 * float(row["win_rate"])
                - 10.0 * float(row["entry_reduce_failure_rate"])
                + min(float(row["lifecycle_count"]), 80.0) / 20.0
            )
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("cell_selection_score", ascending=False).reset_index(drop=True)


def run_grid(panel: pd.DataFrame, cell_pool: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    if cell_pool.empty:
        return pd.DataFrame(), {}
    candidate_rows: list[dict[str, object]] = []
    candidate_panels: dict[str, pd.DataFrame] = {}
    thresholds = []
    for min_avg in [0.0, 3.0, 5.0, 8.0, 12.0]:
        for min_win in [0.50, 0.55, 0.60, 0.65, 0.70]:
            for max_entry_reduce in [0.20, 0.25, 0.30, 0.35, 0.45]:
                for dims in ["theme_id|symbol_multiday_setup_state|timing_state", "theme_id|symbol_multiday_setup_state", "theme_id|timing_state", "symbol_multiday_setup_state|timing_state"]:
                    thresholds.append((min_avg, min_win, max_entry_reduce, dims))
    for min_avg, min_win, max_entry_reduce, dims in thresholds:
        cells = cell_pool[
            cell_pool["cell_dims"].eq(dims)
            & cell_pool["avg_net_return_pct"].ge(min_avg)
            & cell_pool["win_rate"].ge(min_win)
            & cell_pool["entry_reduce_failure_rate"].le(max_entry_reduce)
        ].copy()
        if cells.empty:
            continue
        assigned = assign_cells(panel, cells)
        if len(assigned) < 50:
            continue
        for max_positions in [5, 10, 20]:
            result = simulate_portfolio(assigned, max_positions=max_positions)
            if result.accepted_panel.empty:
                continue
            candidate_name = f"task505_{dims.replace('|', '_')}_avg{min_avg:g}_win{int(min_win*100)}_er{int(max_entry_reduce*100)}_pos{max_positions}"
            metrics = result.quality
            metrics.update(
                {
                    "candidate_strategy_name": candidate_name,
                    "cell_dims": dims,
                    "min_avg_net_pct": min_avg,
                    "min_win_rate": min_win,
                    "max_entry_reduce_rate": max_entry_reduce,
                    "max_positions": max_positions,
                    "source_cell_count": int(len(cells)),
                    "pre_capacity_lifecycle_count": int(len(assigned)),
                    "label_used_in_assignment_flag": 0,
                    "inferred_lifecycle_matching_used_flag": 0,
                    "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                }
            )
            candidate_rows.append(metrics)
            candidate_panels[candidate_name] = result.accepted_panel
    if not candidate_rows:
        return pd.DataFrame(), {}
    candidate_pool = pd.DataFrame(candidate_rows)
    candidate_pool["selection_rank_score"] = (
        candidate_pool["two_year_capital_pnl_pct"]
        + 0.5 * candidate_pool["avg_net_return_pct"]
        + 10.0 * candidate_pool["win_rate"]
        - 8.0 * candidate_pool["entry_reduce_failure_rate"]
        - 0.25 * candidate_pool["max_drawdown_pct"].abs()
    )
    candidate_pool = candidate_pool.sort_values(["two_year_capital_pnl_pct", "selection_rank_score"], ascending=False).reset_index(drop=True)
    return candidate_pool, candidate_panels


def assign_cells(panel: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    masks = []
    for _, cell in cells.iterrows():
        dims = str(cell["cell_dims"]).split("|")
        values = str(cell["cell_values"]).split("|")
        mask = pd.Series(True, index=out.index)
        for dim, value in zip(dims, values):
            mask &= out[dim].astype(str).eq(value)
        masks.append(mask)
    if not masks:
        return out.iloc[0:0].copy()
    combined = masks[0].copy()
    for mask in masks[1:]:
        combined |= mask
    selected = out[combined].copy().reset_index(drop=True)
    selected["task505_pre_capacity_selected_flag"] = 1
    return selected


def simulate_portfolio(panel: pd.DataFrame, *, max_positions: int) -> PortfolioResult:
    if panel.empty:
        return PortfolioResult(empty_quality(max_positions), panel.copy(), pd.DataFrame())
    ordered = panel.sort_values("entry_ts").reset_index(drop=True)
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                equity_rows.append(
                    {
                        "event_ts": pos["exit_ts"],
                        "event_type": "EXIT",
                        "lifecycle_id": pos["lifecycle_id"],
                        "equity": equity,
                        "drawdown_pct": (equity / peak - 1.0) * 100.0,
                    }
                )
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        if len(open_positions) >= max_positions:
            continue
        capital = equity / float(max_positions)
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        out = dict(row)
        out["task505_capacity_accepted_flag"] = 1
        out["task505_position_slot_cap"] = max_positions
        out["task505_position_capital_weight"] = 1.0 / float(max_positions)
        accepted_rows.append(out)
        equity_rows.append(
            {
                "event_ts": entry_ts,
                "event_type": "ENTRY",
                "lifecycle_id": row["lifecycle_id"],
                "equity": equity,
                "drawdown_pct": (equity / peak - 1.0) * 100.0,
            }
        )
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    equity_curve = pd.DataFrame(equity_rows).sort_values("event_ts").reset_index(drop=True) if equity_rows else pd.DataFrame()
    metrics = strategy_quality(accepted, {"max_positions": max_positions})
    metrics["two_year_capital_pnl_pct"] = (equity - 1.0) * 100.0
    metrics["max_drawdown_pct"] = float(equity_curve["drawdown_pct"].min()) if not equity_curve.empty else 0.0
    metrics["skipped_due_capacity_count"] = int(len(ordered) - len(accepted))
    return PortfolioResult(metrics, accepted, equity_curve)


def strategy_quality(panel: pd.DataFrame, source: dict[str, object] | pd.Series) -> dict[str, object]:
    metrics = aggregate(panel) if not panel.empty else empty_quality(int(source.get("max_positions", 0)))
    metrics["two_year_capital_pnl_pct"] = float(source.get("two_year_capital_pnl_pct", 0.0))
    metrics["max_drawdown_pct"] = float(source.get("max_drawdown_pct", 0.0))
    metrics["skipped_due_capacity_count"] = int(source.get("skipped_due_capacity_count", 0) or 0)
    metrics["max_positions"] = int(source.get("max_positions", 0) or 0)
    return metrics


def empty_quality(max_positions: int) -> dict[str, object]:
    return {
        "lifecycle_count": 0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "add_scale_success_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "false_positive_rate": 0.0,
        "median_holding_days": 0.0,
        "same_day_exit_share": 0.0,
        "two_year_capital_pnl_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "skipped_due_capacity_count": 0,
        "max_positions": max_positions,
    }


def select_best_candidate(candidate_pool: pd.DataFrame) -> pd.Series:
    if candidate_pool.empty:
        return pd.Series(
            {
                "candidate_strategy_name": "no_candidate",
                "max_positions": 0,
                "cell_dims": "",
                "min_avg_net_pct": 0.0,
                "min_win_rate": 0.0,
                "max_entry_reduce_rate": 1.0,
                "two_year_capital_pnl_pct": 0.0,
            }
        )
    return candidate_pool.iloc[0]


def selected_cell_rulebook(cell_pool: pd.DataFrame, selected_row: pd.Series) -> pd.DataFrame:
    if cell_pool.empty or str(selected_row.get("cell_dims", "")) == "":
        return pd.DataFrame()
    cells = cell_pool[
        cell_pool["cell_dims"].eq(selected_row["cell_dims"])
        & cell_pool["avg_net_return_pct"].ge(float(selected_row["min_avg_net_pct"]))
        & cell_pool["win_rate"].ge(float(selected_row["min_win_rate"]))
        & cell_pool["entry_reduce_failure_rate"].le(float(selected_row["max_entry_reduce_rate"]))
    ].copy()
    cells["selected_two_year_pnl_rule_flag"] = 1
    return cells.reset_index(drop=True)


def concentration_audit(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame(
            [
                {
                    "top_theme_share": 0.0,
                    "top_symbol_share": 0.0,
                    "theme_count": 0,
                    "symbol_count": 0,
                    "concentration_risk_flag": 0,
                }
            ]
        )
    top_theme = float(panel["theme_id"].value_counts(normalize=True).iloc[0]) if "theme_id" in panel.columns else 0.0
    top_symbol = float(panel["symbol"].value_counts(normalize=True).iloc[0]) if "symbol" in panel.columns else 0.0
    return pd.DataFrame(
        [
            {
                "top_theme_share": top_theme,
                "top_symbol_share": top_symbol,
                "theme_count": int(panel["theme_id"].nunique()) if "theme_id" in panel.columns else 0,
                "symbol_count": int(panel["symbol"].nunique()) if "symbol" in panel.columns else 0,
                "concentration_risk_flag": int(top_theme > 0.60 or top_symbol > 0.20),
            }
        ]
    )


def build_decision(candidate_pool: pd.DataFrame, selected_quality: pd.DataFrame, selected_row: pd.Series, lookback_days: int) -> pd.DataFrame:
    metrics = selected_quality.iloc[0].to_dict() if not selected_quality.empty else {}
    return pd.DataFrame(
        [
            {
                "task_id": "Task505",
                "two_year_lookback_days": lookback_days,
                "grid_candidate_count": int(len(candidate_pool)),
                "best_strategy_name": selected_row.get("candidate_strategy_name", "no_candidate"),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "median_holding_days": metrics.get("median_holding_days", pd.NA),
                "two_year_capital_pnl_pct": metrics.get("two_year_capital_pnl_pct", pd.NA),
                "max_drawdown_pct": metrics.get("max_drawdown_pct", pd.NA),
                "max_positions": int(metrics.get("max_positions", 0) or 0),
                "two_year_pnl_grid_complete_flag": int(len(candidate_pool) > 0),
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(out_dir: Path, artifacts: Task505Artifacts) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.two_year_pnl_grid_candidate_pool.to_csv(out_dir / "two_year_pnl_grid_candidate_pool.csv", index=False)
    artifacts.selected_two_year_pnl_strategy_rulebook.to_csv(out_dir / "selected_two_year_pnl_strategy_rulebook.csv", index=False)
    artifacts.selected_two_year_pnl_strategy_panel.to_csv(out_dir / "selected_two_year_pnl_strategy_panel.csv", index=False)
    artifacts.selected_two_year_pnl_strategy_quality.to_csv(out_dir / "selected_two_year_pnl_strategy_quality.csv", index=False)
    artifacts.selected_two_year_pnl_equity_curve.to_csv(out_dir / "selected_two_year_pnl_equity_curve.csv", index=False)
    artifacts.selected_two_year_pnl_quarterly_quality.to_csv(out_dir / "selected_two_year_pnl_quarterly_quality.csv", index=False)
    artifacts.selected_two_year_pnl_theme_quality.to_csv(out_dir / "selected_two_year_pnl_theme_quality.csv", index=False)
    artifacts.selected_two_year_pnl_concentration_audit.to_csv(out_dir / "selected_two_year_pnl_concentration_audit.csv", index=False)
    artifacts.task_505_decision.to_csv(out_dir / "task_505_decision.csv", index=False)
    (out_dir / "task_505_two_year_pnl_grid.md").write_text(build_report(artifacts), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_report(artifacts: Task505Artifacts) -> str:
    d = artifacts.task_505_decision.iloc[0].to_dict()
    q = artifacts.selected_two_year_pnl_strategy_quality.iloc[0].to_dict() if not artifacts.selected_two_year_pnl_strategy_quality.empty else {}
    return "\n".join(
        [
            "# Task 505 - Two-Year PnL Grid",
            "",
            "## Decision Summary",
            "",
            f"- Best strategy: {d['best_strategy_name']}",
            f"- Two-year capital PnL: {float(d['two_year_capital_pnl_pct']):.2f}%",
            f"- Count / avg net / win / entry_reduce: {d['selected_count']} / {float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Median holding days / max drawdown: {float(d['median_holding_days']):.2f} / {float(d['max_drawdown_pct']):.2f}%",
            "- Inferred lifecycle matching used: NO",
            "- Label/outcome used in assignment: NO",
            "- Strategy acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "",
            "## Quant Expert Report",
            "",
            "Task505 converts the Task503 exact lifecycle population into a two-year portfolio grid. It evaluates practical cell portfolios with a capacity-aware capital path instead of ranking only by average trade return. The selected strategy is still diagnostic because source coverage remains OHLCV/VWAP based and live execution readiness is not complete.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "This task answers which currently available strategy variant made the best two-year simulated portfolio PnL. It does not claim a deployable strategy. It uses only already linked lifecycle rows and does not guess missing trades.",
            "",
            "## Key Metrics",
            "",
            f"- Accepted trades after position cap: {int(q.get('lifecycle_count', 0) or 0)}",
            f"- Position cap: {int(q.get('max_positions', 0) or 0)}",
            f"- Capacity skips: {int(q.get('skipped_due_capacity_count', 0) or 0)}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task503-panel", type=Path, default=DEFAULT_TASK503_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    args = parser.parse_args()
    artifacts = build_task505_two_year_pnl_grid(task503_panel_path=args.task503_panel, out_dir=args.out_dir, lookback_days=args.lookback_days)
    row = artifacts.task_505_decision.iloc[0]
    print(
        "[TASK505] "
        f"complete={row['two_year_pnl_grid_complete_flag']} pnl={float(row['two_year_capital_pnl_pct']):.2f}% "
        f"count={row['selected_count']} win={float(row['selected_win_rate']):.1%}"
    )


if __name__ == "__main__":
    main()
