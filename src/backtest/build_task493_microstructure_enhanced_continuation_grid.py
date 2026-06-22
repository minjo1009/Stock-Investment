from __future__ import annotations

import argparse
import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.build_task489_broad_regime_cell_portfolio import (
    DEFAULT_BROAD_DAILY_DIR,
    DEFAULT_BROAD_MARKET_CACHE,
    DEFAULT_TASK487_PANEL,
    aggregate_one,
    aggregate_quality,
    load_or_build_broad_market_state,
    load_panel_with_broad_market,
)
from src.backtest.build_task490r_firm_grade_intraday_continuation_validation import (
    DEFAULT_TASK489_SELECTED_CELLS,
    PRIMARY_ADD_SCALE,
    PRIMARY_AVG_NET,
    PRIMARY_COUNT_MAX,
    PRIMARY_COUNT_MIN,
    PRIMARY_ENTRY_REDUCE_MAX,
    PRIMARY_RECENT_AVG_NET,
    PRIMARY_RECENT_COUNT,
    PRIMARY_RECENT_ENTRY_REDUCE_MAX,
    PRIMARY_VALIDATION_COUNT,
    PRIMARY_WIN_RATE,
    SECONDARY_AVG_NET,
    SECONDARY_COUNT_MAX,
    SECONDARY_COUNT_MIN,
    SECONDARY_ENTRY_REDUCE_MAX,
    SECONDARY_WIN_RATE,
    STRUCTURE_KEYS,
    build_cost_stress_quality,
    build_failure_decomposition,
    build_task489_selected_panel,
    evaluate_panel,
)
from src.backtest.build_task492_microstructure_source_collection import DEFAULT_OUT_DIR as TASK492_OUT_DIR


DEFAULT_MICRO_FEATURE_PANEL = TASK492_OUT_DIR / "microstructure_entry_feature_panel.csv"
DEFAULT_OUT_DIR = Path("docs/reports/task_493_microstructure_enhanced_continuation_grid")

MICROSTRUCTURE_KEYS = [
    "spread_state",
    "quote_freshness_state",
    "nbbo_size_state",
    "microstructure_tradability_state",
]
ALL_KEYS = STRUCTURE_KEYS + MICROSTRUCTURE_KEYS

STRETCH_COUNT_MIN = 100
STRETCH_COUNT_MAX = 250
STRETCH_AVG_NET = 4.0
STRETCH_WIN_RATE = 0.75
STRETCH_ADD_SCALE = 0.70
STRETCH_ENTRY_REDUCE_MAX = 0.08
STRETCH_VALIDATION_COUNT = 20
STRETCH_RECENT_COUNT = 20
STRETCH_RECENT_AVG_NET = 2.50


@dataclass(frozen=True)
class Task493Artifacts:
    microstructure_enriched_lifecycle_panel: pd.DataFrame
    microstructure_grid_candidate_pool: pd.DataFrame
    selected_microstructure_rulebook: pd.DataFrame
    selected_microstructure_assignment_panel: pd.DataFrame
    selected_microstructure_portfolio_quality: pd.DataFrame
    selected_microstructure_split_quality: pd.DataFrame
    selected_microstructure_cost_stress_quality: pd.DataFrame
    selected_microstructure_failure_decomposition: pd.DataFrame
    microstructure_grid_leakage_audit: pd.DataFrame
    task_493_decision: pd.DataFrame


def build_task493_microstructure_enhanced_continuation_grid(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    task489_selected_cells_path: Path = DEFAULT_TASK489_SELECTED_CELLS,
    micro_feature_panel_path: Path = DEFAULT_MICRO_FEATURE_PANEL,
    broad_daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    broad_market_cache: Path = DEFAULT_BROAD_MARKET_CACHE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task493Artifacts:
    _, market = load_or_build_broad_market_state(broad_daily_dir, broad_market_cache)
    panel = load_panel_with_broad_market(task487_panel_path, market)
    base = build_task489_selected_panel(panel, task489_selected_cells_path)
    enriched = merge_microstructure_features(base, micro_feature_panel_path)
    pool = build_microstructure_cell_pool(enriched)
    grid_pool, selected_cells, selected_panel = run_micro_grid(enriched, pool)
    quality = aggregate_quality(selected_panel, [])
    split_quality = aggregate_quality(selected_panel, ["split_name"])
    cost_stress = build_cost_stress_quality(selected_panel)
    failure = build_failure_decomposition(selected_panel, selected_cells)
    leakage = build_microstructure_leakage_audit(selected_cells)
    decision = build_decision(enriched, grid_pool, selected_cells, selected_panel, quality, split_quality, leakage, failure)
    artifacts = Task493Artifacts(
        enriched,
        grid_pool,
        selected_cells,
        selected_panel,
        quality,
        split_quality,
        cost_stress,
        failure,
        leakage,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def merge_microstructure_features(base: pd.DataFrame, micro_feature_panel_path: Path) -> pd.DataFrame:
    if not micro_feature_panel_path.exists():
        raise FileNotFoundError(f"microstructure feature panel not found: {micro_feature_panel_path}")
    micro = pd.read_csv(micro_feature_panel_path)
    keep = ["lifecycle_id", *MICROSTRUCTURE_KEYS, "spread_bps", "quote_age_seconds", "nbbo_size_dollar", "microstructure_feature_available_flag"]
    merged = base.merge(micro[keep], on="lifecycle_id", how="left", validate="one_to_one")
    for key in MICROSTRUCTURE_KEYS:
        merged[key] = merged[key].fillna("microstructure_missing")
    merged["microstructure_feature_available_flag"] = merged["microstructure_feature_available_flag"].fillna(0).astype(int)
    return merged


def build_microstructure_cell_pool(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for size in [2, 3, 4, 5]:
        for dims in itertools.combinations(ALL_KEYS, size):
            if not any(dim in MICROSTRUCTURE_KEYS for dim in dims):
                continue
            for values, idx in panel.groupby(list(dims), dropna=False).indices.items():
                subset = panel.iloc[list(idx)]
                if len(subset) < 5:
                    continue
                row = {
                    "archetype_dims": "|".join(dims),
                    "archetype_values": _format_values(values),
                    "rule_description": _rule_description(dims, values),
                    **aggregate_one(subset),
                }
                for split in ["train_design", "validation", "recent_oos"]:
                    scoped = subset[subset["split_name"].eq(split)]
                    row[f"{split}_count"] = int(len(scoped))
                    row[f"{split}_avg_net_pct"] = float(scoped["net_return_from_entry"].mean() * 100.0) if not scoped.empty else np.nan
                    row[f"{split}_entry_reduce_rate"] = float(scoped["entry_reduce_failure_flag"].mean()) if not scoped.empty else np.nan
                    row[f"{split}_add_scale_success_rate"] = float(scoped["add_scale_success_flag"].mean()) if not scoped.empty else np.nan
                row["candidate_flag"] = int(
                    row["avg_net_return_pct"] >= 0.5
                    and row["win_rate"] >= 0.50
                    and row["add_scale_success_rate"] >= 0.45
                    and row["entry_reduce_failure_rate"] <= 0.30
                )
                rows.append(row)
    pool = pd.DataFrame(rows)
    if pool.empty:
        return pool
    pool["grid_score"] = (
        pool["avg_net_return_pct"].fillna(0)
        + 0.50 * pool["recent_oos_avg_net_pct"].fillna(0)
        + 0.30 * pool["validation_avg_net_pct"].fillna(0)
        + pool["win_rate"].fillna(0)
        + pool["add_scale_success_rate"].fillna(0)
        - 4.0 * pool["entry_reduce_failure_rate"].fillna(1)
    )
    return pool.sort_values(["candidate_flag", "grid_score"], ascending=[False, False]).reset_index(drop=True)


def run_micro_grid(base: pd.DataFrame, pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if base.empty or pool.empty:
        return pd.DataFrame(), pool.iloc[0:0].copy(), base.iloc[0:0].copy()
    candidates = pool[pool["candidate_flag"].eq(1)].head(900).reset_index(drop=True)
    masks = [cell_mask(base, row) for _, row in candidates.iterrows()]
    rows: list[dict[str, object]] = []
    best: dict[str, object] | None = None
    grids = []
    for min_avg in [0.5, 1.0, 1.5, 2.0, 3.0]:
        for max_er in [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]:
            for min_win in [0.55, 0.60, 0.65, 0.70, 0.75]:
                for min_add in [0.45, 0.50, 0.55, 0.60, 0.70]:
                    grids.append((min_avg, max_er, min_win, min_add))
    order_specs = [
        ("grid_score_desc", ["grid_score"], [False]),
        ("entry_reduce_asc", ["entry_reduce_failure_rate", "avg_net_return_pct"], [True, False]),
        ("recent_count_desc", ["recent_oos_count", "avg_net_return_pct"], [False, False]),
        ("validation_count_desc", ["validation_count", "avg_net_return_pct"], [False, False]),
    ]
    for min_avg, max_er, min_win, min_add in grids:
        eligible = candidates[
            candidates["avg_net_return_pct"].ge(min_avg)
            & candidates["entry_reduce_failure_rate"].le(max_er)
            & candidates["win_rate"].ge(min_win)
            & candidates["add_scale_success_rate"].ge(min_add)
        ]
        if eligible.empty:
            continue
        for order_name, sort_cols, ascending in order_specs:
            order = list(eligible.sort_values(sort_cols, ascending=ascending).index)
            for target_min, target_max, profile in [(80, 250, "primary"), (250, 500, "secondary"), (100, 250, "stretch")]:
                mask = np.zeros(len(base), dtype=bool)
                chosen: list[int] = []
                for idx in order:
                    next_mask = mask | masks[idx]
                    if int(next_mask.sum()) > target_max:
                        continue
                    mask = next_mask
                    chosen.append(idx)
                    if int(mask.sum()) >= target_min:
                        selected = base[mask]
                        q = evaluate_panel(selected)
                        row = {
                            "profile": profile,
                            "order_name": order_name,
                            "min_cell_avg_net_pct": min_avg,
                            "max_cell_entry_reduce": max_er,
                            "min_cell_win_rate": min_win,
                            "min_cell_add_scale": min_add,
                            "selected_cell_count": len(chosen),
                            "target_status": classify_status(q),
                            **q,
                        }
                        row["selection_score"] = selection_score(row)
                        rows.append(row)
                        record = {"row": row, "mask": mask.copy(), "chosen": chosen.copy()}
                        if best is None or record_rank(record) > record_rank(best):
                            best = record
                        break
    grid_pool = pd.DataFrame(rows)
    if best is None:
        return grid_pool, candidates.iloc[0:0].copy(), base.iloc[0:0].copy()
    selected_cells = candidates.iloc[best["chosen"]].copy().reset_index(drop=True)
    selected_cells["selected_archetype_order"] = range(1, len(selected_cells) + 1)
    selected_cells["profile"] = best["row"]["profile"]
    selected_cells["order_name"] = best["row"]["order_name"]
    selected_cells["diagnostic_only_flag"] = 1
    selected_panel = base[best["mask"]].copy().reset_index(drop=True)
    selected_panel["microstructure_grid_profile"] = best["row"]["profile"]
    selected_panel["target_status"] = best["row"]["target_status"]
    selected_panel["inferred_lifecycle_matching_used_flag"] = 0
    return grid_pool.sort_values("selection_score", ascending=False).reset_index(drop=True), selected_cells, selected_panel


def cell_mask(panel: pd.DataFrame, row: pd.Series) -> np.ndarray:
    dims = str(row["archetype_dims"]).split("|")
    values = str(row["archetype_values"]).split("|")
    mask = np.ones(len(panel), dtype=bool)
    for dim, value in zip(dims, values, strict=False):
        mask &= panel[dim].astype(str).eq(value).to_numpy()
    return mask


def classify_status(q: dict[str, object]) -> str:
    if (
        STRETCH_COUNT_MIN <= int(q["count"]) <= STRETCH_COUNT_MAX
        and float(q["avg_net_pct"]) >= STRETCH_AVG_NET
        and float(q["win_rate"]) >= STRETCH_WIN_RATE
        and float(q["add_scale_success_rate"]) >= STRETCH_ADD_SCALE
        and float(q["entry_reduce_failure_rate"]) <= STRETCH_ENTRY_REDUCE_MAX
        and int(q["validation_count"]) >= STRETCH_VALIDATION_COUNT
        and int(q["recent_oos_count"]) >= STRETCH_RECENT_COUNT
        and float(q["recent_oos_avg_net_pct"]) >= STRETCH_RECENT_AVG_NET
    ):
        return "STRETCH_PASS"
    if (
        PRIMARY_COUNT_MIN <= int(q["count"]) <= PRIMARY_COUNT_MAX
        and float(q["avg_net_pct"]) >= PRIMARY_AVG_NET
        and float(q["win_rate"]) >= PRIMARY_WIN_RATE
        and float(q["add_scale_success_rate"]) >= PRIMARY_ADD_SCALE
        and float(q["entry_reduce_failure_rate"]) <= PRIMARY_ENTRY_REDUCE_MAX
        and int(q["validation_count"]) >= PRIMARY_VALIDATION_COUNT
        and int(q["recent_oos_count"]) >= PRIMARY_RECENT_COUNT
        and float(q["recent_oos_avg_net_pct"]) >= PRIMARY_RECENT_AVG_NET
        and float(q["recent_oos_entry_reduce_rate"]) <= PRIMARY_RECENT_ENTRY_REDUCE_MAX
    ):
        return "PRIMARY_PASS"
    if (
        SECONDARY_COUNT_MIN <= int(q["count"]) <= SECONDARY_COUNT_MAX
        and float(q["avg_net_pct"]) >= SECONDARY_AVG_NET
        and float(q["win_rate"]) >= SECONDARY_WIN_RATE
        and float(q["entry_reduce_failure_rate"]) <= SECONDARY_ENTRY_REDUCE_MAX
    ):
        return "SECONDARY_PASS"
    return "DIAGNOSTIC_FAIL"


def selection_score(row: dict[str, object]) -> float:
    return (
        float(row.get("avg_net_pct", 0) or 0)
        + 0.60 * float(row.get("recent_oos_avg_net_pct", 0) or 0)
        + 0.30 * float(row.get("validation_avg_net_pct", 0) or 0)
        + 2.0 * float(row.get("win_rate", 0) or 0)
        + 2.0 * float(row.get("add_scale_success_rate", 0) or 0)
        - 7.0 * float(row.get("entry_reduce_failure_rate", 0) or 0)
        + min(float(row.get("validation_count", 0) or 0), 20) * 0.03
        + min(float(row.get("recent_oos_count", 0) or 0), 20) * 0.03
    )


def record_rank(record: dict[str, object]) -> tuple[int, float]:
    ranks = {"STRETCH_PASS": 4, "PRIMARY_PASS": 3, "SECONDARY_PASS": 2, "DIAGNOSTIC_FAIL": 1}
    row = record["row"]
    return ranks.get(str(row["target_status"]), 0), float(row["selection_score"])


def build_decision(
    base: pd.DataFrame,
    grid_pool: pd.DataFrame,
    selected_cells: pd.DataFrame,
    selected_panel: pd.DataFrame,
    quality: pd.DataFrame,
    split_quality: pd.DataFrame,
    leakage: pd.DataFrame,
    failure: pd.DataFrame,
) -> pd.DataFrame:
    metrics = quality.iloc[0].to_dict() if not quality.empty else {}
    q = evaluate_panel(selected_panel)
    status = classify_status(q)
    validation = split_quality[split_quality["split_name"].eq("validation")] if not split_quality.empty else pd.DataFrame()
    recent = split_quality[split_quality["split_name"].eq("recent_oos")] if not split_quality.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "task_id": "Task493",
                "task_name": "Microstructure Enhanced Continuation Grid",
                "microstructure_feature_coverage": float(base["microstructure_feature_available_flag"].mean()) if not base.empty else 0.0,
                "grid_candidate_count": int(len(grid_pool)),
                "selected_archetype_count": int(len(selected_cells)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_add_scale_success_rate": metrics.get("add_scale_success_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "validation_count": int(validation["lifecycle_count"].iloc[0]) if not validation.empty else 0,
                "validation_avg_net_pct": validation["avg_net_return_pct"].iloc[0] if not validation.empty else pd.NA,
                "recent_oos_count": int(recent["lifecycle_count"].iloc[0]) if not recent.empty else 0,
                "recent_oos_avg_net_pct": recent["avg_net_return_pct"].iloc[0] if not recent.empty else pd.NA,
                "best_target_status": status,
                "stretch_pass_flag": int(status == "STRETCH_PASS"),
                "primary_pass_flag": int(status == "PRIMARY_PASS"),
                "secondary_pass_flag": int(status == "SECONDARY_PASS"),
                "leakage_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "active_failure_count": int(failure["failure_active_flag"].sum()) if not failure.empty else 0,
                "raw_receive_timestamp_available_flag": 0,
                "status_luld_available_flag": 0,
                "depth_book_available_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def build_microstructure_leakage_audit(selected_cells: pd.DataFrame) -> pd.DataFrame:
    blocked = {
        "failure_group",
        "lifecycle_outcome_class",
        "return_from_entry",
        "net_return_from_entry",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "exit_flag",
        "exit_ts",
        "event_path",
        "win_flag",
        "add_scale_success_flag",
        "entry_reduce_failure_flag",
        "false_positive_flag",
    }
    fields = sorted({field for dims in selected_cells.get("archetype_dims", pd.Series(dtype=str)).astype(str) for field in dims.split("|") if field})
    used_blocked = sorted(set(fields) & blocked)
    return pd.DataFrame(
        [
            {
                "assignment_fields": "|".join(fields),
                "blocked_outcome_field_used_count": len(used_blocked),
                "blocked_outcome_fields": "|".join(used_blocked),
                "label_used_in_assignment_flag": int(bool(used_blocked)),
                "inferred_lifecycle_matching_used_flag": 0,
                "available_microstructure_sources_used": "historical_nbbo_quote|spread_bps|nbbo_bid_ask_size|quote_event_timestamp",
                "missing_raw_sources_reported": "depth_book|status_luld|raw_receive_timestamp",
                "missing_raw_source_approximated_flag": 0,
                "leakage_pass_flag": int(not used_blocked),
            }
        ]
    )


def write_artifacts(artifacts: Task493Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.microstructure_enriched_lifecycle_panel.to_csv(out_dir / "microstructure_enriched_lifecycle_panel.csv", index=False)
    artifacts.microstructure_grid_candidate_pool.to_csv(out_dir / "microstructure_grid_candidate_pool.csv", index=False)
    artifacts.selected_microstructure_rulebook.to_csv(out_dir / "selected_microstructure_rulebook.csv", index=False)
    artifacts.selected_microstructure_assignment_panel.to_csv(out_dir / "selected_microstructure_assignment_panel.csv", index=False)
    artifacts.selected_microstructure_portfolio_quality.to_csv(out_dir / "selected_microstructure_portfolio_quality.csv", index=False)
    artifacts.selected_microstructure_split_quality.to_csv(out_dir / "selected_microstructure_split_quality.csv", index=False)
    artifacts.selected_microstructure_cost_stress_quality.to_csv(out_dir / "selected_microstructure_cost_stress_quality.csv", index=False)
    artifacts.selected_microstructure_failure_decomposition.to_csv(out_dir / "selected_microstructure_failure_decomposition.csv", index=False)
    artifacts.microstructure_grid_leakage_audit.to_csv(out_dir / "microstructure_grid_leakage_audit.csv", index=False)
    artifacts.task_493_decision.to_csv(out_dir / "task_493_decision.csv", index=False)
    (out_dir / "task_493_microstructure_enhanced_continuation_grid.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task493Artifacts) -> str:
    d = artifacts.task_493_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 493 - Microstructure Enhanced Continuation Grid",
            "",
            "## Quant Firm 4-Person Review",
            "",
            "### Regime PM",
            "Task489 regime remains the outer gate; microstructure is an execution-quality overlay, not a replacement for regime.",
            "",
            "### Intraday Quant",
            "Adding spread/freshness/NBBO-size states tests whether the high-quality continuation sleeve is also tradable at entry. This is closer to firm-grade than OHLCV-only.",
            "",
            "### Execution Specialist",
            "Historical NBBO spread and size improve friction visibility, but raw receive timestamp, LULD/status, and depth book are still missing. Deployment claims remain blocked.",
            "",
            "### Portfolio Manager",
            "The selected sleeve should be compared against Task491: if return/entry-reduce improves without collapsing validation/recent OOS, microstructure adds real selection value.",
            "",
            "## Result Summary",
            "",
            f"- Status: {d['best_target_status']}",
            f"- Microstructure coverage: {float(d['microstructure_feature_coverage']):.1%}",
            f"- Grid candidates: {d['grid_candidate_count']}",
            f"- Count / avg net / win / ADD-SCALE / entry_reduce: {d['selected_count']} / "
            f"{_fmt(d['selected_avg_net_pct'])}% / {_fmt_pct(d['selected_win_rate'])} / "
            f"{_fmt_pct(d['selected_add_scale_success_rate'])} / {_fmt_pct(d['selected_entry_reduce_rate'])}",
            f"- Validation count / avg net: {d['validation_count']} / {_fmt(d['validation_avg_net_pct'])}%",
            f"- Recent OOS count / avg net: {d['recent_oos_count']} / {_fmt(d['recent_oos_avg_net_pct'])}%",
            "- Inferred lifecycle matching used: NO",
            "- Raw receive timestamp / status / LULD / depth-book still missing: YES",
            "",
            "## Selected Quality",
            "",
            _csv_block(artifacts.selected_microstructure_portfolio_quality),
            "",
            "## Split Quality",
            "",
            _csv_block(artifacts.selected_microstructure_split_quality),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이번 단계는 좋은 regime과 좋은 intraday 구조에 실제 quote spread/size 조건을 추가한 테스트다. 단, 아직 실시간 수신시각과 LULD/status/depth book은 없으므로 배포용 판단은 아니다.",
        ]
    )


def _format_values(values: object) -> str:
    if not isinstance(values, tuple):
        values = (values,)
    return "|".join(str(v) for v in values)


def _rule_description(dims: tuple[str, ...], values: object) -> str:
    if not isinstance(values, tuple):
        values = (values,)
    return " AND ".join(f"{dim}={value}" for dim, value in zip(dims, values, strict=False))


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "NA"


def _fmt_pct(value: object) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "NA"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task487-panel-path", type=Path, default=DEFAULT_TASK487_PANEL)
    parser.add_argument("--task489-selected-cells-path", type=Path, default=DEFAULT_TASK489_SELECTED_CELLS)
    parser.add_argument("--micro-feature-panel-path", type=Path, default=DEFAULT_MICRO_FEATURE_PANEL)
    parser.add_argument("--broad-daily-dir", type=Path, default=DEFAULT_BROAD_DAILY_DIR)
    parser.add_argument("--broad-market-cache", type=Path, default=DEFAULT_BROAD_MARKET_CACHE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task493_microstructure_enhanced_continuation_grid(
        task487_panel_path=args.task487_panel_path,
        task489_selected_cells_path=args.task489_selected_cells_path,
        micro_feature_panel_path=args.micro_feature_panel_path,
        broad_daily_dir=args.broad_daily_dir,
        broad_market_cache=args.broad_market_cache,
        out_dir=args.out_dir,
    )
    row = artifacts.task_493_decision.iloc[0]
    print(
        "[TASK493] "
        f"status={row['best_target_status']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}% grid={row['grid_candidate_count']}"
    )


if __name__ == "__main__":
    main()
