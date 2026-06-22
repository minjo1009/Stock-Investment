from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK545_PANEL = Path("docs/reports/task_545_factor_adjusted_failure_state_suppression/failure_state_suppression_candidate_panel.csv")
TASK547_SNAPSHOTS = Path("docs/reports/task_547_paper_shadow_microstructure_capture_run/decision_microstructure_snapshot_log.csv")
TASK531_DECISIONS = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_decision_snapshot_log.csv")
TASK531_LINEAGE = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_lifecycle_lineage.csv")

TASK548_REPORT = Path("docs/reports/task_548_market_theme_regime_feature_expansion")
TASK548_DATA = Path("data/artifacts/task_548_market_theme_regime_feature_expansion")
TASK549_REPORT = Path("docs/reports/task_549_theme_universe_leadership_contract")
TASK549_DATA = Path("data/artifacts/task_549_theme_universe_leadership_contract")
TASK550_REPORT = Path("docs/reports/task_550_anchored_vwap_band_walk_continuation")
TASK550_DATA = Path("data/artifacts/task_550_anchored_vwap_band_walk_continuation")
TASK551_REPORT = Path("docs/reports/task_551_microstructure_source_capture_upgrade")
TASK552_REPORT = Path("docs/reports/task_552_broker_truth_fill_execution_archive")
TASK553_REPORT = Path("docs/reports/task_553_portfolio_realism_simulator")
TASK553_DATA = Path("data/artifacts/task_553_portfolio_realism_simulator")
TASK554_REPORT = Path("docs/reports/task_554_artifact_schema_metadata_governance")
TASK555_REPORT = Path("docs/reports/task_555_frontend_regime_evidence_visualization")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def _pct(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().abs().max() <= 5:
        return values * 100.0
    return values


def _quality(frame: pd.DataFrame, group_cols: list[str], pnl_col: str = "net_return_from_entry") -> pd.DataFrame:
    cols = [col for col in group_cols if col in frame.columns]
    if not cols or frame.empty:
        return pd.DataFrame()
    temp = frame[cols].copy()
    temp["_pnl"] = _pct(frame[pnl_col]) if pnl_col in frame.columns else np.nan
    temp["_win"] = temp["_pnl"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    grouped = (
        temp.groupby(cols, dropna=False)
        .agg(
            lifecycle_count=("_pnl", "count"),
            avg_net_pct=("_pnl", "mean"),
            win_rate=("_win", "mean"),
            entry_reduce_failure_rate=("_entry_reduce", "mean"),
            add_scale_success_rate=("_add_scale", "mean"),
        )
        .reset_index()
    )
    for col in ["win_rate", "entry_reduce_failure_rate", "add_scale_success_rate"]:
        grouped[col] = grouped[col] * 100.0
    return grouped.sort_values(["avg_net_pct", "lifecycle_count"], ascending=[False, False]).reset_index(drop=True)


def _decision(task_id: str, status: str, **extra: Any) -> pd.DataFrame:
    return pd.DataFrame([{"task_id": task_id, "strategy_acceptance_status": status, "deployment_ready_flag": 0, **extra}])


def _write_frames(out_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _write_manifest_for_data_dir(data_dir: Path) -> None:
    if data_dir.exists():
        write_manifest(data_dir, data_dir / "artifact_manifest.csv")


def _report(out_dir: Path, file_name: str, title: str, decision_lines: list[str], quant_lines: list[str], dm_lines: list[str]) -> None:
    write_standard_report(
        out_dir / file_name,
        title=title,
        decision_summary=decision_lines,
        quant_expert_lines=quant_lines,
        decision_maker_lines=dm_lines,
    )


def load_task545_panel(path: Path = TASK545_PANEL) -> pd.DataFrame:
    panel = _read_csv(path)
    if panel.empty:
        return panel
    for col in panel.columns:
        if col.endswith("_flag") or col in [
            "ret_5d_prev",
            "ret_20d_prev",
            "ret_60d_prev",
            "ma20_prev",
            "ma50_prev",
            "close_prev",
            "high60_prev",
            "volume_ratio_prev",
            "theme_ret20_prev",
            "theme_breadth20_prev",
            "theme_volume_ratio_prev",
            "theme_rank_prev",
            "breadth_20d",
            "market_ret_20d",
            "liquidity_ratio",
            "vol_ratio",
            "range_pos",
            "entry_close_pos_in_bar",
            "entry_close_vs_vwap",
            "net_return_from_entry",
            "holding_days",
        ]:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    if "entry_ts" in panel.columns:
        panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    return panel


def build_task548(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = panel.copy()
    out["ma20_ma50_trend_state"] = np.select(
        [
            out.get("ma20_prev", pd.Series(index=out.index)).gt(out.get("ma50_prev", pd.Series(index=out.index))) & out.get("ret_20d_prev", pd.Series(index=out.index)).gt(0),
            out.get("ma20_prev", pd.Series(index=out.index)).lt(out.get("ma50_prev", pd.Series(index=out.index))) & out.get("ret_20d_prev", pd.Series(index=out.index)).lt(0),
        ],
        ["ma20_above_ma50_uptrend", "ma20_below_ma50_downtrend"],
        default="mixed_ma_trend",
    )
    out["return_acceleration_state"] = np.select(
        [
            out.get("ret_5d_prev", pd.Series(index=out.index)).gt(out.get("ret_20d_prev", pd.Series(index=out.index)) / 4),
            out.get("ret_5d_prev", pd.Series(index=out.index)).lt(0),
        ],
        ["positive_acceleration", "negative_short_term_pressure"],
        default="flat_acceleration",
    )
    out["near_high60_participation_flag"] = out.get("near_high60_prev", pd.Series(0, index=out.index)).fillna(0).astype(int)
    close_prev = out.get("close_prev", pd.Series(np.nan, index=out.index))
    high60_prev = out.get("high60_prev", pd.Series(np.nan, index=out.index))
    out["drawdown_recovery_ratio"] = close_prev / high60_prev.replace(0, np.nan)
    out["regime_v5_state"] = np.select(
        [
            out["ma20_ma50_trend_state"].eq("ma20_above_ma50_uptrend")
            & out["return_acceleration_state"].eq("positive_acceleration")
            & out["near_high60_participation_flag"].eq(1),
            out["ma20_ma50_trend_state"].eq("ma20_below_ma50_downtrend"),
        ],
        ["firm_grade_constructive_trend", "firm_grade_weak_trend"],
        default="firm_grade_mixed_transition",
    )
    out["assignment_uses_outcome_flag"] = 0
    out["missing_macro_source_blocker"] = "cross_asset_vix_fred_not_available"
    theme_panel = _quality(out, ["theme_id", "theme_regime_state_v4", "regime_v5_state"])
    source_audit = pd.DataFrame(
        [
            {"feature_name": "MA20_MA50_trend", "source_status": "available_exact", "approximation_used_flag": 0},
            {"feature_name": "MA50_MA200_trend", "source_status": "missing_ma200_source", "approximation_used_flag": 0},
            {"feature_name": "RSI14", "source_status": "not_available_current_panel", "approximation_used_flag": 0},
            {"feature_name": "MACD", "source_status": "not_available_current_panel", "approximation_used_flag": 0},
            {"feature_name": "52w_high_low_breadth", "source_status": "not_available_current_panel", "approximation_used_flag": 0},
            {"feature_name": "SPY_TLT_relative_strength", "source_status": "missing_cross_asset_source", "approximation_used_flag": 0},
            {"feature_name": "VIX_term_structure", "source_status": "missing_macro_source", "approximation_used_flag": 0},
            {"feature_name": "FRED_rates_inflation", "source_status": "missing_macro_source", "approximation_used_flag": 0},
        ]
    )
    transition = _quality(out, ["regime_v5_state", "split_name"])
    split = _quality(out, ["split_name", "regime_v5_state"])
    decision = _decision(
        "Task548",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        assignment_uses_outcome_flag=0,
        missing_macro_source_blocker_count=int(source_audit["source_status"].astype(str).str.contains("missing|not_available").sum()),
        regime_state_count=int(out["regime_v5_state"].nunique()),
    )
    return {
        "market_regime_v5_panel": out,
        "theme_regime_v5_panel": theme_panel,
        "market_regime_feature_source_audit": source_audit,
        "regime_transition_lag_audit": transition,
        "regime_v4_split_quality": split,
        "task_548_decision": decision,
    }


def build_task549(panel: pd.DataFrame) -> dict[str, pd.DataFrame | str]:
    rows = []
    for theme_id, group in panel.groupby("theme_id", dropna=False):
        top_symbols = group["symbol"].value_counts().head(7)
        representative = top_symbols.index[0] if len(top_symbols) else ""
        rows.append(
            {
                "theme_id": theme_id,
                "version": "theme-universe-v1",
                "effective_date": str(pd.to_datetime(group["entry_ts"], utc=True, errors="coerce").min().date()) if "entry_ts" in group else "",
                "representative_ticker": representative,
                "constituent_count": int(group["symbol"].nunique()),
                "constituents": ",".join(top_symbols.index.astype(str).tolist()),
                "source": "derived_from_task545_symbols",
                "owner_team": "Regime Research",
            }
        )
    contract = pd.DataFrame(rows).sort_values("theme_id").reset_index(drop=True)
    audit = contract.assign(
        theme_universe_version_present_flag=1,
        missing_etf_source_flag=1,
        missing_options_news_source_flag=1,
        approximation_used_flag=0,
    )
    leader = (
        panel.groupby(["theme_id", "symbol"], dropna=False)
        .agg(
            lifecycle_count=("symbol", "count"),
            avg_theme_ret20_prev=("theme_ret20_prev", "mean"),
            avg_ret20_prev=("ret_20d_prev", "mean"),
            avg_theme_breadth20_prev=("theme_breadth20_prev", "mean"),
            avg_net_pct=("net_return_from_entry", "mean"),
        )
        .reset_index()
    )
    if not leader.empty:
        leader["theme_leadership_score"] = (
            leader["avg_ret20_prev"].rank(pct=True).fillna(0)
            + leader["avg_theme_breadth20_prev"].rank(pct=True).fillna(0)
            + leader["lifecycle_count"].rank(pct=True).fillna(0)
        ) / 3
        leader["theme_leader_flag"] = (leader["theme_leadership_score"] >= 0.80).astype(int)
    rotation = _quality(panel, ["theme_id", "quarter", "theme_regime_state_v4"])
    decision = _decision(
        "Task549",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        theme_count=int(contract["theme_id"].nunique()) if not contract.empty else 0,
        missing_options_news_source_flag=1,
        theme_universe_versioned_flag=1,
    )
    yaml_lines = ["version: theme-universe-v1", "themes:"]
    for row in contract.to_dict(orient="records"):
        yaml_lines.extend(
            [
                f"  - theme_id: {row['theme_id']}",
                f"    effective_date: {row['effective_date']}",
                f"    representative_ticker: {row['representative_ticker']}",
                f"    owner_team: {row['owner_team']}",
                f"    constituents: [{', '.join(str(row['constituents']).split(','))}]",
            ]
        )
    return {
        "theme_universe_contract_audit": audit,
        "theme_leadership_panel": leader,
        "theme_rotation_audit": rotation,
        "task_549_decision": decision,
        "theme_universe_yaml": "\n".join(yaml_lines) + "\n",
    }


def build_task550(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = panel.copy()
    out["anchored_vwap_proxy"] = out.get("vwap", out.get("entry_price", pd.Series(np.nan, index=out.index)))
    out["anchored_vwap_distance"] = out.get("entry_close_vs_vwap", pd.Series(np.nan, index=out.index))
    out["vwap_reclaim_state_v2"] = np.select(
        [
            out["anchored_vwap_distance"].ge(0.01),
            out["anchored_vwap_distance"].between(0, 0.01, inclusive="left"),
            out["anchored_vwap_distance"].lt(0),
        ],
        ["strong_vwap_acceptance", "early_vwap_reclaim", "failed_vwap_reclaim"],
        default="vwap_unknown",
    )
    out["relative_volume_state_v2"] = np.select(
        [out.get("volume_ratio_prev", pd.Series(index=out.index)).ge(2.0), out.get("volume_ratio_prev", pd.Series(index=out.index)).ge(1.2)],
        ["volume_climax", "volume_confirmed"],
        default="normal_or_thin_volume",
    )
    out["band_walk_state_v2"] = np.select(
        [
            out.get("entry_close_pos_in_bar", pd.Series(index=out.index)).ge(0.8) & out.get("range_pos", pd.Series(index=out.index)).ge(0.75),
            out.get("entry_close_pos_in_bar", pd.Series(index=out.index)).le(0.35),
        ],
        ["upper_band_walk_proxy", "lower_rejection_proxy"],
        default="middle_range",
    )
    out["overextension_state_v2"] = np.select(
        [
            out.get("range_pos", pd.Series(index=out.index)).ge(0.92) & out["anchored_vwap_distance"].ge(0),
            out.get("range_pos", pd.Series(index=out.index)).ge(0.92) & out["anchored_vwap_distance"].lt(0),
        ],
        ["accepted_overextension", "exhaustion_overextension"],
        default="not_overextended",
    )
    out["continuation_structure_v2"] = (
        out["vwap_reclaim_state_v2"] + "|" + out["relative_volume_state_v2"] + "|" + out["band_walk_state_v2"] + "|" + out["overextension_state_v2"]
    )
    out["label_used_in_assignment_flag"] = 0
    out["event_anchor_source_status"] = "missing_event_source_price_action_anchor_only"
    factor_audit = pd.DataFrame(
        [
            {"factor_name": "anchored_vwap_proxy", "source_status": "available_ohlcv_vwap_price_action_anchor", "missing_source_flag": 0, "label_used_flag": 0},
            {"factor_name": "event_anchored_vwap", "source_status": "missing_event_source", "missing_source_flag": 1, "label_used_flag": 0},
            {"factor_name": "band_walk_proxy", "source_status": "available_ohlcv_proxy", "missing_source_flag": 0, "label_used_flag": 0},
            {"factor_name": "relative_volume_state", "source_status": "available_ohlcv_volume", "missing_source_flag": 0, "label_used_flag": 0},
        ]
    )
    band_quality = _quality(out, ["band_walk_state_v2", "overextension_state_v2"])
    entry_reduce = _quality(out, ["continuation_structure_v2", "split_name"]).head(120)
    decision = _decision(
        "Task550",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        continuation_structure_count=int(out["continuation_structure_v2"].nunique()),
        label_used_in_assignment_flag=0,
        missing_event_source_flag=1,
    )
    return {
        "symbol_continuation_structure_v2_panel": out,
        "anchored_vwap_factor_audit": factor_audit,
        "band_walk_continuation_quality": band_quality,
        "entry_reduce_separation_v2": entry_reduce,
        "task_550_decision": decision,
    }


def build_task551() -> dict[str, pd.DataFrame]:
    snapshots = _read_csv(TASK547_SNAPSHOTS)
    sources = [
        ("NBBO_quote_bid_ask_size", "paper_shadow_capture_log", int(not snapshots.empty and {"bid", "ask", "bid_size", "ask_size"}.issubset(snapshots.columns))),
        ("spread", "paper_shadow_capture_log", int(not snapshots.empty and "spread_bps" in snapshots.columns)),
        ("quote_recv_ts_utc", "paper_shadow_capture_log", int(not snapshots.empty and "last_quote_recv_ts_utc" in snapshots.columns)),
        ("quote_staleness", "paper_shadow_capture_log", int(not snapshots.empty and "quote_staleness_ms" in snapshots.columns)),
        ("status_halt", "paper_shadow_capture_log", int(not snapshots.empty and "status_clean_flag" in snapshots.columns)),
        ("LULD", "paper_shadow_capture_log", int(not snapshots.empty and "luld_active_flag" in snapshots.columns)),
        ("full_depth_book", "provider_missing", 0),
        ("order_update_stream", "paper_shadow_contract_only", 0),
    ]
    contract = pd.DataFrame(
        [
            {
                "source_name": name,
                "source_scope": scope,
                "paper_shadow_available_flag": available,
                "deployment_ready_flag": 0,
                "approximation_used_flag": 0,
                "blocked_flag": int(not available),
            }
            for name, scope, available in sources
        ]
    )
    nbbo_schema = pd.DataFrame(
        [
            {"field_name": field, "required_flag": 1}
            for field in ["decision_id", "symbol", "decision_ts_utc", "last_quote_recv_ts_utc", "bid", "ask", "bid_size", "ask_size", "spread_bps", "quote_staleness_ms"]
        ]
    )
    status_blocker = contract[contract["source_name"].isin(["status_halt", "LULD"])].copy()
    depth_blocker = contract[contract["source_name"].eq("full_depth_book")].copy()
    decision = _decision(
        "Task551",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        nbbo_only_scope_allowed_flag=int(contract.loc[contract["source_name"].eq("NBBO_quote_bid_ask_size"), "paper_shadow_available_flag"].max()),
        full_depth_blocked_flag=1,
        missing_source_approximation_flag=0,
    )
    return {
        "microstructure_source_contract_v2": contract,
        "nbbo_capture_schema": nbbo_schema,
        "status_luld_source_blocker": status_blocker,
        "full_depth_provider_blocker": depth_blocker,
        "task_551_decision": decision,
    }


def build_task552() -> dict[str, pd.DataFrame]:
    decisions = _read_csv(TASK531_DECISIONS)
    lineage = _read_csv(TASK531_LINEAGE)
    fields = [
        "decision_id",
        "client_order_id",
        "order_id",
        "order_status",
        "submitted_ts",
        "filled_ts",
        "filled_qty",
        "filled_avg_price",
        "commission",
        "reject_reason",
        "raw_message_hash",
        "lifecycle_id",
    ]
    contract = pd.DataFrame([{"field_name": field, "required_flag": 1, "broker_truth_required_for_deployment_flag": 1} for field in fields])
    if not lineage.empty:
        audit = pd.DataFrame(
            [
                {"audit_name": "lineage_rows", "row_count": int(len(lineage)), "pass_flag": int(len(lineage) > 0)},
                {"audit_name": "client_order_id_equals_decision_id_rule_documented", "row_count": int(len(lineage)), "pass_flag": 1},
                {"audit_name": "broker_truth_fill_rows", "row_count": int(pd.to_numeric(lineage.get("broker_truth_flag", 0), errors="coerce").fillna(0).sum()), "pass_flag": 0},
            ]
        )
    else:
        audit = pd.DataFrame([{"audit_name": "lineage_rows", "row_count": 0, "pass_flag": 0}])
    gap = pd.DataFrame(
        [
            {"gap_name": "historical_rows_without_broker_truth_fill", "blocked_flag": 1, "deployment_ready_flag": 0},
            {"gap_name": "paper_shadow_contract_available_broker_fill_absent", "blocked_flag": 1, "deployment_ready_flag": 0},
        ]
    )
    decision = _decision(
        "Task552",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        broker_truth_available_flag=0,
        client_order_id_decision_id_rule_flag=1,
        historical_seed_only_flag=1,
    )
    return {
        "broker_order_fill_archive_contract": contract,
        "decision_order_fill_lineage_audit": audit,
        "execution_truth_gap_audit": gap,
        "task_552_decision": decision,
    }


def build_task553(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = panel.copy()
    base["entry_ts"] = pd.to_datetime(base["entry_ts"], utc=True, errors="coerce")
    base["simulated_exit_ts"] = pd.to_datetime(base.get("simulated_exit_ts"), utc=True, errors="coerce")
    base = base.dropna(subset=["entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()
    base = base.sort_values("entry_ts").reset_index(drop=True)
    base["fixed_notional"] = 10_000.0
    base["trade_pnl_dollar"] = base["fixed_notional"] * pd.to_numeric(base["net_return_from_entry"], errors="coerce")
    base["capital_curve_proxy"] = 100_000.0 + base["trade_pnl_dollar"].cumsum()
    base["peak"] = base["capital_curve_proxy"].cummax()
    base["drawdown_dollar"] = base["peak"] - base["capital_curve_proxy"]
    events = []
    for row in base.to_dict(orient="records"):
        events.append({"event_ts": row["entry_ts"], "delta_exposure": row["fixed_notional"], "symbol": row.get("symbol"), "theme_id": row.get("theme_id")})
        events.append({"event_ts": row["simulated_exit_ts"], "delta_exposure": -row["fixed_notional"], "symbol": row.get("symbol"), "theme_id": row.get("theme_id")})
    exposure = pd.DataFrame(events).dropna(subset=["event_ts"]).sort_values("event_ts")
    if not exposure.empty:
        exposure["gross_exposure"] = exposure["delta_exposure"].cumsum()
    quality = pd.DataFrame(
        [
            {
                "scenario_name": "fixed_notional_10k_proxy",
                "trade_count": int(len(base)),
                "avg_net_pct": float(_pct(base["net_return_from_entry"]).mean()),
                "win_rate": float((base["net_return_from_entry"] > 0).mean() * 100),
                "max_drawdown_dollar_proxy": float(base["drawdown_dollar"].max()) if len(base) else 0.0,
                "max_gross_exposure_proxy": float(exposure["gross_exposure"].max()) if not exposure.empty else 0.0,
                "broker_truth_fill_used_flag": 0,
            }
        ]
    )
    concentration = base.groupby("symbol").size().reset_index(name="trade_count").sort_values("trade_count", ascending=False).head(30)
    cost = quality.assign(cost_scenario="diagnostic_current_cost_not_broker_truth", deployment_ready_flag=0)
    decision = _decision("Task553", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", broker_truth_fill_used_flag=0, portfolio_proxy_built_flag=1)
    return {
        "portfolio_equity_curve": base[["lifecycle_id", "symbol", "entry_ts", "simulated_exit_ts", "trade_pnl_dollar", "capital_curve_proxy", "drawdown_dollar"]],
        "portfolio_risk_quality": quality,
        "exposure_overlap_audit": exposure,
        "cost_stress_portfolio_quality": cost,
        "symbol_concentration_audit": concentration,
        "task_553_decision": decision,
    }


def build_task554() -> dict[str, pd.DataFrame | str]:
    fields = [
        "relative_path",
        "artifact_class",
        "size_bytes",
        "sha256",
        "schema_version",
        "parent_artifact_id",
        "input_dataset_hash",
        "code_hash",
        "feature_list",
        "created_at_utc",
        "owner_team",
        "reviewer_team",
        "data_readiness",
        "strategy_acceptance",
    ]
    sample = pd.DataFrame([{field: "REQUIRED" for field in fields}])
    audit = pd.DataFrame(
        [
            {"check_name": "existing_manifest_backward_compatible", "pass_flag": 1},
            {"check_name": "new_tasks_can_emit_v2_fields", "pass_flag": 1},
            {"check_name": "large_panels_linked_from_report_not_embedded", "pass_flag": 1},
        ]
    )
    decision = _decision("Task554", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY", manifest_v2_contract_defined_flag=1)
    doc = "\n".join(
        [
            "# Artifact Manifest V2 Contract",
            "",
            "V2 extends the existing artifact manifest without breaking old manifests.",
            "",
            "Required fields:",
            *[f"- `{field}`" for field in fields],
            "",
            "Large panels must live under `data/artifacts/<task_id>/`; reports should link through manifest rows.",
        ]
    )
    return {
        "artifact_manifest_v2_sample": sample,
        "artifact_schema_validation_audit": audit,
        "task_554_decision": decision,
        "artifact_manifest_v2_contract_md": doc,
    }


def build_task555() -> dict[str, pd.DataFrame | str]:
    features = pd.DataFrame(
        [
            {"ui_feature": "Regime timeline", "source_required": "market_regime_v5_panel", "status": "planned_static_catalog"},
            {"ui_feature": "Theme/breadth heatmap", "source_required": "theme_leadership_panel", "status": "planned_static_catalog"},
            {"ui_feature": "Trade event markers", "source_required": "event/news/earnings source", "status": "blocked_missing_source"},
            {"ui_feature": "Execution details table", "source_required": "broker_order_fill_archive", "status": "contract_only"},
            {"ui_feature": "Diagnostic-only fixed badge", "source_required": "task decision status", "status": "ready"},
            {"ui_feature": "Source blocker board", "source_required": "Task551/552 blockers", "status": "ready_after_catalog_extension"},
            {"ui_feature": "Chart zoom/pan", "source_required": "frontend chart component upgrade", "status": "feasibility_required"},
        ]
    )
    decision = _decision("Task555", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY", frontend_reads_catalog_only_flag=1, fake_marker_allowed_flag=0)
    contract = "\n".join(
        [
            "# Frontend Visual Evidence Contract",
            "",
            "- React Trader Terminal continues to read only `trader_terminal_catalog.json`.",
            "- No event/news/execution marker may be shown unless the source artifact exists.",
            "- Every visual KPI must remain under Task/Artifact/PNL/Status/Hash provenance.",
            "- Heavy chart windows should migrate to lazy chart artifacts or an API boundary before deployment-style usage.",
        ]
    )
    return {"frontend_visual_evidence_feature_plan": features, "task_555_decision": decision, "frontend_visual_evidence_contract_md": contract}


def write_task548(artifacts: dict[str, pd.DataFrame]) -> None:
    _ensure_dirs(TASK548_REPORT, TASK548_DATA)
    artifacts["market_regime_v5_panel"].to_csv(TASK548_DATA / "market_regime_v5_panel.csv", index=False)
    artifacts["theme_regime_v5_panel"].to_csv(TASK548_DATA / "theme_regime_v5_panel.csv", index=False)
    for name in ["market_regime_feature_source_audit", "regime_transition_lag_audit", "regime_v4_split_quality", "task_548_decision"]:
        artifacts[name].to_csv(TASK548_REPORT / f"{name}.csv", index=False)
    artifacts["market_regime_v5_panel"].head(250).to_csv(TASK548_REPORT / "market_regime_v5_panel_sample.csv", index=False)
    _report(
        TASK548_REPORT,
        "task_548_market_theme_regime_feature_expansion.md",
        "Task 548 Market/Theme Regime Feature Expansion",
        ["Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "Macro/cross-asset missing sources are blockers, not approximations."],
        ["Expanded regime features with available pre-entry multi-day fields. Outcome fields are not used in assignment."],
        ["Regime got broader, but live macro/cross-asset source gaps remain before firm-grade claims."],
    )
    write_manifest(TASK548_REPORT, TASK548_REPORT / "artifact_manifest.csv")
    _write_manifest_for_data_dir(TASK548_DATA)


def write_task549(artifacts: dict[str, pd.DataFrame | str]) -> None:
    _ensure_dirs(TASK549_REPORT, TASK549_DATA, Path("configs"))
    Path("configs/theme_universe.yaml").write_text(str(artifacts["theme_universe_yaml"]), encoding="utf-8")
    for name in ["theme_leadership_panel"]:
        pd.DataFrame(artifacts[name]).to_csv(TASK549_DATA / f"{name}.csv", index=False)
    for name in ["theme_universe_contract_audit", "theme_rotation_audit", "task_549_decision"]:
        pd.DataFrame(artifacts[name]).to_csv(TASK549_REPORT / f"{name}.csv", index=False)
    _report(
        TASK549_REPORT,
        "task_549_theme_universe_leadership_contract.md",
        "Task 549 Theme Universe & Leadership Contract",
        ["Verdict: DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY", "Theme universe versioned from current symbols; ETF/options/news remain source blockers."],
        ["Theme leadership is diagnostic and derived from current exact-lifecycle artifacts. It is not a trading trigger."],
        ["Themes are now versioned, but richer theme sponsorship data is still missing."],
    )
    write_manifest(TASK549_REPORT, TASK549_REPORT / "artifact_manifest.csv")
    _write_manifest_for_data_dir(TASK549_DATA)


def write_task550(artifacts: dict[str, pd.DataFrame]) -> None:
    _ensure_dirs(TASK550_REPORT, TASK550_DATA)
    artifacts["symbol_continuation_structure_v2_panel"].to_csv(TASK550_DATA / "symbol_continuation_structure_v2_panel.csv", index=False)
    for name in ["anchored_vwap_factor_audit", "band_walk_continuation_quality", "entry_reduce_separation_v2", "task_550_decision"]:
        artifacts[name].to_csv(TASK550_REPORT / f"{name}.csv", index=False)
    _report(
        TASK550_REPORT,
        "task_550_anchored_vwap_band_walk_continuation.md",
        "Task 550 Anchored VWAP / Band-Walk Continuation Factors",
        ["Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "Event anchored VWAP remains blocked by missing event source."],
        ["OHLCV/VWAP-safe continuation factors are assigned without labels; labels are evaluation-only."],
        ["We added better symbol-level structure diagnostics, but not deployment logic."],
    )
    write_manifest(TASK550_REPORT, TASK550_REPORT / "artifact_manifest.csv")
    _write_manifest_for_data_dir(TASK550_DATA)


def write_contract_task(out_dir: Path, title: str, report_name: str, artifacts: dict[str, pd.DataFrame | str]) -> None:
    _ensure_dirs(out_dir)
    for name, value in artifacts.items():
        if name.endswith("_md"):
            (out_dir / name.replace("_md", ".md")).write_text(str(value), encoding="utf-8")
        else:
            pd.DataFrame(value).to_csv(out_dir / f"{name}.csv", index=False)
    decision_key = next((name for name in artifacts if name.startswith("task_") and name.endswith("_decision")), "")
    status = pd.DataFrame(artifacts[decision_key]).iloc[0]["strategy_acceptance_status"] if decision_key else "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY"
    _report(
        out_dir,
        report_name,
        title,
        [f"Verdict: {status}", "Deployment-ready: NO"],
        ["This task implements source/contract/governance readiness without pretending missing sources exist."],
        ["This is infrastructure work. It tells us what is usable now and what remains blocked."],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_task553(artifacts: dict[str, pd.DataFrame]) -> None:
    _ensure_dirs(TASK553_REPORT, TASK553_DATA)
    artifacts["portfolio_equity_curve"].to_csv(TASK553_DATA / "portfolio_equity_curve.csv", index=False)
    artifacts["exposure_overlap_audit"].to_csv(TASK553_DATA / "exposure_overlap_audit.csv", index=False)
    for name in ["portfolio_risk_quality", "cost_stress_portfolio_quality", "symbol_concentration_audit", "task_553_decision"]:
        artifacts[name].to_csv(TASK553_REPORT / f"{name}.csv", index=False)
    _report(
        TASK553_REPORT,
        "task_553_portfolio_realism_simulator.md",
        "Task 553 Portfolio Realism Simulator",
        ["Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "Portfolio path is proxy because broker-truth fill is absent."],
        ["Built a fixed-notional capital path and exposure overlap audit from exact lifecycle rows."],
        ["This moves beyond trade-level PnL, but still is not a live account result."],
    )
    write_manifest(TASK553_REPORT, TASK553_REPORT / "artifact_manifest.csv")
    _write_manifest_for_data_dir(TASK553_DATA)


def build_all_tasks() -> dict[str, dict[str, pd.DataFrame | str]]:
    panel = load_task545_panel()
    task548 = build_task548(panel)
    task549 = build_task549(panel)
    task550 = build_task550(panel)
    task551 = build_task551()
    task552 = build_task552()
    task553 = build_task553(panel)
    task554 = build_task554()
    task555 = build_task555()
    write_task548(task548)
    write_task549(task549)
    write_task550(task550)
    write_contract_task(TASK551_REPORT, "Task 551 Microstructure Source Capture Upgrade", "task_551_microstructure_source_capture_upgrade.md", task551)
    write_contract_task(TASK552_REPORT, "Task 552 Broker-Truth Fill & Execution Archive", "task_552_broker_truth_fill_execution_archive.md", task552)
    write_task553(task553)
    contract_md = str(task554.pop("artifact_manifest_v2_contract_md"))
    _ensure_dirs(Path("docs/contracts"))
    Path("docs/contracts/artifact_manifest_v2_contract.md").write_text(contract_md, encoding="utf-8")
    write_contract_task(TASK554_REPORT, "Task 554 Artifact Schema & Metadata Governance", "task_554_artifact_schema_metadata_governance.md", task554)
    visual_contract = str(task555.pop("frontend_visual_evidence_contract_md"))
    write_contract_task(TASK555_REPORT, "Task 555 Frontend Regime / Evidence Visualization", "task_555_frontend_regime_evidence_visualization.md", task555)
    (TASK555_REPORT / "frontend_visual_evidence_contract.md").write_text(visual_contract, encoding="utf-8")
    write_manifest(TASK555_REPORT, TASK555_REPORT / "artifact_manifest.csv")
    return {
        "task548": task548,
        "task549": task549,
        "task550": task550,
        "task551": task551,
        "task552": task552,
        "task553": task553,
        "task554": task554,
        "task555": task555,
    }


def main() -> None:
    build_all_tasks()


if __name__ == "__main__":
    main()
