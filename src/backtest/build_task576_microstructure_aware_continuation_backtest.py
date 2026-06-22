from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK573_PANEL = Path("data/artifacts/task_573_historical_nbbo_feature_rebuild/historical_nbbo_feature_panel.csv")
TASK567_PANEL = Path("data/artifacts/task_567_capital_flow_regime_v6/capital_flow_regime_v6_panel.csv")
REPORT_DIR = Path("docs/reports/task_576_microstructure_aware_continuation_backtest")
ARTIFACT_DIR = Path("data/artifacts/task_576_microstructure_aware_continuation_backtest")


def _decision(status: str, **extra: object) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task576",
                "strategy_acceptance_status": status,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
                **extra,
            }
        ]
    )


def _load_panel(task573_panel: Path = TASK573_PANEL, task567_panel: Path = TASK567_PANEL) -> pd.DataFrame:
    panel = pd.read_csv(task573_panel)
    if task567_panel.exists() and "capital_flow_regime_v6" not in panel.columns:
        regime = pd.read_csv(task567_panel, usecols=lambda c: c in {"lifecycle_id", "capital_flow_regime_v6", "capital_flow_score_v6"})
        regime = regime.drop_duplicates("lifecycle_id", keep="first")
        panel = panel.merge(regime, on="lifecycle_id", how="left", validate="many_to_one")
    return panel


def _add_micro_buckets(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["spread_bucket_task576"] = pd.cut(
        pd.to_numeric(out["spread_bps"], errors="coerce"),
        bins=[-float("inf"), 5, 15, 40, float("inf")],
        labels=["tight_spread", "normal_spread", "wide_spread", "very_wide_spread"],
    ).astype(str)
    size = pd.to_numeric(out["nbbo_size_dollar"], errors="coerce")
    matched = out["quote_match_available_flag"].eq(1) if "quote_match_available_flag" in out.columns else size.notna()
    out["nbbo_size_bucket_task576"] = "missing_nbbo"
    if matched.sum() >= 3:
        out.loc[matched, "nbbo_size_bucket_task576"] = pd.qcut(
            size[matched].rank(method="first"),
            q=3,
            labels=["thin_nbbo", "normal_nbbo", "deep_nbbo"],
        ).astype(str)
    out["imbalance_bucket_task576"] = pd.cut(
        pd.to_numeric(out["nbbo_imbalance"], errors="coerce"),
        bins=[-float("inf"), -0.25, 0.25, float("inf")],
        labels=["ask_heavy", "balanced", "bid_heavy"],
    ).astype(str)
    out["microstructure_clean_state_v1"] = "micro_missing"
    out.loc[
        matched
        & out["spread_bucket_task576"].isin(["tight_spread", "normal_spread"])
        & out["nbbo_size_bucket_task576"].isin(["normal_nbbo", "deep_nbbo"])
        & out["imbalance_bucket_task576"].isin(["balanced", "bid_heavy"]),
        "microstructure_clean_state_v1",
    ] = "micro_clean"
    out.loc[
        matched
        & (
            out["spread_bucket_task576"].isin(["wide_spread", "very_wide_spread"])
            | out["nbbo_size_bucket_task576"].eq("thin_nbbo")
            | out["imbalance_bucket_task576"].eq("ask_heavy")
        ),
        "microstructure_clean_state_v1",
    ] = "micro_friction_or_pressure"
    out["microstructure_assignment_used_outcome_flag"] = 0
    out["historical_microstructure_live_ready_flag"] = 0
    return out


def _assign_candidate_sets(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["task576_candidate_set"] = "not_selected"
    capital = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).eq("capital_flow_expansion")
    constructive = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).isin(
        ["capital_flow_expansion", "constructive_persistence"]
    )
    clean = out["microstructure_clean_state_v1"].eq("micro_clean")
    pullback = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("controlled_pullback_only")
    absorption = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("near_high_absorption_only")
    out.loc[constructive & pullback & clean, "task576_candidate_set"] = "clean_controlled_pullback"
    out.loc[constructive & absorption & clean, "task576_candidate_set"] = "clean_near_high_absorption"
    out.loc[capital & clean, "task576_candidate_set"] = "capital_flow_micro_clean"
    out.loc[capital & pullback & clean, "task576_candidate_set"] = "capital_flow_clean_pullback"
    out.loc[capital & absorption & clean, "task576_candidate_set"] = "capital_flow_clean_absorption"
    out.loc[
        out["microstructure_clean_state_v1"].eq("micro_friction_or_pressure")
        & out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).isin(
            ["controlled_pullback_only", "near_high_absorption_only"]
        ),
        "task576_candidate_set",
    ] = "diagnostic_micro_friction_sleeve"
    return out


def _quality(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if frame.empty:
        return pd.DataFrame()
    for key, group in frame.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        rows.append(
            {
                **dict(zip(group_cols, key)),
                "count": int(len(group)),
                "avg_net": float(pd.to_numeric(group["net_return_from_entry"], errors="coerce").mean()),
                "win_rate": float(pd.to_numeric(group["win_flag"], errors="coerce").mean()),
                "entry_reduce_rate": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").mean()),
                "add_scale_rate": float(pd.to_numeric(group["add_scale_success_flag"], errors="coerce").mean()),
                "same_day_exit_rate": float(pd.to_numeric(group.get("same_day_exit_flag"), errors="coerce").mean()) if "same_day_exit_flag" in group else float("nan"),
                "median_holding_days": float(pd.to_numeric(group.get("holding_days"), errors="coerce").median()) if "holding_days" in group else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values(["avg_net", "count"], ascending=[False, False]).reset_index(drop=True)


def _leakage_audit(panel: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("No inferred lifecycle matching", "inferred_lifecycle_matching_used_flag_micro", 0),
        ("No symbol/date/price/time fallback", "symbol_date_price_time_fallback_used_flag", 0),
        ("No outcome in microstructure assignment", "microstructure_assignment_used_outcome_flag", 0),
        ("Historical microstructure not live-ready", "historical_microstructure_live_ready_flag", 0),
    ]
    rows = []
    for name, column, expected in checks:
        if column not in panel.columns:
            rows.append({"check": name, "status": "NOT_REPORTED", "bad_rows": None, "total_rows": len(panel)})
            continue
        bad = int((pd.to_numeric(panel[column], errors="coerce").fillna(expected) != expected).sum())
        rows.append({"check": name, "status": "PASS" if bad == 0 else "FAIL", "bad_rows": bad, "total_rows": len(panel)})
    return pd.DataFrame(rows)


def build_task576(task573_panel: Path = TASK573_PANEL, task567_panel: Path = TASK567_PANEL) -> dict[str, pd.DataFrame]:
    panel = _assign_candidate_sets(_add_micro_buckets(_load_panel(task573_panel, task567_panel)))
    matched = panel[panel.get("quote_match_available_flag", pd.Series(dtype=int)).eq(1)].copy()
    selected = matched[matched["task576_candidate_set"].ne("not_selected")].copy()
    quality = _quality(selected, ["task576_candidate_set"])
    split_quality = _quality(selected, ["task576_candidate_set", "split_name"]) if "split_name" in selected.columns else pd.DataFrame()
    quarter_quality = _quality(selected, ["task576_candidate_set", "quarter"]) if "quarter" in selected.columns else pd.DataFrame()
    micro_state_quality = _quality(matched, ["microstructure_clean_state_v1", "spread_bucket_task576", "nbbo_size_bucket_task576", "imbalance_bucket_task576"])
    leakage = _leakage_audit(panel)
    best = quality.iloc[0].to_dict() if not quality.empty else {}
    status = "DIAGNOSTIC_PASS_MICROSTRUCTURE_AWARE_BACKTESTED" if not quality.empty else "DATA_BLOCKED_NO_MICROSTRUCTURE_CANDIDATES"
    decision = _decision(
        status,
        total_rows=int(len(panel)),
        quote_matched_rows=int(len(matched)),
        selected_rows=int(len(selected)),
        candidate_set_count=int(quality["task576_candidate_set"].nunique()) if not quality.empty else 0,
        best_candidate_set=best.get("task576_candidate_set", ""),
        best_count=best.get("count", 0),
        best_avg_net=best.get("avg_net", pd.NA),
        best_win_rate=best.get("win_rate", pd.NA),
        best_entry_reduce_rate=best.get("entry_reduce_rate", pd.NA),
        missing_source_approximated_flag=0,
        live_ready_flag=0,
    )
    return {
        "task576_microstructure_assignment_panel.csv": panel,
        "task576_candidate_set_quality.csv": quality,
        "task576_candidate_set_split_quality.csv": split_quality,
        "task576_candidate_set_quarter_quality.csv": quarter_quality,
        "task576_microstructure_state_quality.csv": micro_state_quality,
        "task576_leakage_audit.csv": leakage,
        "task_576_decision.csv": decision,
    }


def write_task576(artifacts: dict[str, pd.DataFrame]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        target_dir = ARTIFACT_DIR if name == "task576_microstructure_assignment_panel.csv" else REPORT_DIR
        frame.to_csv(target_dir / name, index=False, encoding="utf-8-sig")
    decision = artifacts["task_576_decision.csv"].iloc[0].to_dict()
    write_standard_report(
        REPORT_DIR / "task_576_microstructure_aware_continuation_backtest.md",
        title="Task 576 - Microstructure-Aware Continuation Backtest",
        decision_summary=[f"{k}: {v}" for k, v in decision.items()],
        quant_expert_lines=[
            "Historical SIP NBBO is used as an entry-time diagnostic layer over exact canonical lifecycle rows.",
            "Candidate sets combine capital-flow regime, VWAP pullback sleeve, and quote-derived spread/depth/imbalance buckets.",
            "Historical quote data is not receive-timestamp live evidence and is not promoted to deployment readiness.",
        ],
        decision_maker_lines=[
            "이번 작업은 '좋은 regime + 좋은 intraday 구조'에 실제 bid/ask 상태를 붙여 가짜 continuation을 줄일 수 있는지 보는 단계입니다.",
            "결과가 좋아도 실전 투입은 아니며, live 수신시각과 broker fill 기록이 필요합니다.",
        ],
    )
    write_manifest(REPORT_DIR, REPORT_DIR / "artifact_manifest.csv")
