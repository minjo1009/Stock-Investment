from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK573_PANEL = Path("data/artifacts/task_573_historical_nbbo_feature_rebuild/historical_nbbo_feature_panel.csv")
TASK576_PANEL = Path("data/artifacts/task_576_microstructure_aware_continuation_backtest/task576_microstructure_assignment_panel.csv")
QUOTE_DIR = Path("data/raw/alpaca_historical_microstructure/feed=sip/quotes")

TASK577_REPORT = Path("docs/reports/task_577_historical_nbbo_trajectory_factor_rebuild")
TASK578_REPORT = Path("docs/reports/task_578_regime_vwap_nbbo_trajectory_backtest")
TASK579_REPORT = Path("docs/reports/task_579_live_paper_capture_readiness_upgrade")
TASK580_REPORT = Path("docs/reports/task_580_nbbo_trajectory_firm_grade_gate")
TASK577_ARTIFACT = Path("data/artifacts/task_577_historical_nbbo_trajectory_factor_rebuild")
TASK578_ARTIFACT = Path("data/artifacts/task_578_regime_vwap_nbbo_trajectory_backtest")


def _decision(task_id: str, status: str, **extra: object) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": task_id,
                "strategy_acceptance_status": status,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
                **extra,
            }
        ]
    )


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_candidate_panel() -> pd.DataFrame:
    panel_path = TASK576_PANEL if TASK576_PANEL.exists() else TASK573_PANEL
    panel = pd.read_csv(panel_path)
    panel["symbol"] = panel["symbol"].astype(str).str.upper()
    panel["entry_ts_dt"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    return panel.dropna(subset=["symbol", "entry_ts_dt"]).copy()


def _load_symbol_quotes(symbol: str, quote_dir: Path | None = None) -> tuple[pd.DataFrame, str]:
    quote_dir = quote_dir or QUOTE_DIR
    path = quote_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        return pd.DataFrame(), ""
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame(), _file_hash(path)
    frame["quote_ts_dt"] = pd.to_datetime(frame["quote_ts"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["quote_ts_dt"]).sort_values("quote_ts_dt").reset_index(drop=True)
    for col in ["bid", "ask", "bid_size", "ask_size", "mid", "spread_bps", "nbbo_size_dollar", "nbbo_imbalance"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame, _file_hash(path)


def _window_stats(quotes: pd.DataFrame, entry_ts: pd.Timestamp, seconds: int) -> dict[str, object]:
    if quotes.empty:
        return _empty_stats(seconds)
    qts = quotes["quote_ts_dt"].astype("int64").to_numpy()
    start = entry_ts - pd.Timedelta(seconds=seconds)
    left = np.searchsorted(qts, start.value, side="left")
    right = np.searchsorted(qts, entry_ts.value, side="right")
    window = quotes.iloc[left:right]
    if window.empty:
        return _empty_stats(seconds)
    first = window.iloc[0]
    last = window.iloc[-1]
    spread = pd.to_numeric(window["spread_bps"], errors="coerce")
    size = pd.to_numeric(window["nbbo_size_dollar"], errors="coerce")
    imbalance = pd.to_numeric(window["nbbo_imbalance"], errors="coerce")
    bid_size = pd.to_numeric(window["bid_size"], errors="coerce")
    ask_size = pd.to_numeric(window["ask_size"], errors="coerce")
    mid = pd.to_numeric(window["mid"], errors="coerce")
    return {
        f"q{seconds}_quote_count": int(len(window)),
        f"q{seconds}_first_quote_ts": str(first["quote_ts"]),
        f"q{seconds}_last_quote_ts": str(last["quote_ts"]),
        f"q{seconds}_last_quote_age_sec": float((entry_ts - pd.to_datetime(last["quote_ts"], utc=True)).total_seconds()),
        f"q{seconds}_spread_first": float(first.get("spread_bps", np.nan)),
        f"q{seconds}_spread_last": float(last.get("spread_bps", np.nan)),
        f"q{seconds}_spread_mean": float(spread.mean()),
        f"q{seconds}_spread_delta": float(last.get("spread_bps", np.nan) - first.get("spread_bps", np.nan)),
        f"q{seconds}_size_first": float(first.get("nbbo_size_dollar", np.nan)),
        f"q{seconds}_size_last": float(last.get("nbbo_size_dollar", np.nan)),
        f"q{seconds}_size_delta_pct": _pct_change(first.get("nbbo_size_dollar", np.nan), last.get("nbbo_size_dollar", np.nan)),
        f"q{seconds}_imbalance_first": float(first.get("nbbo_imbalance", np.nan)),
        f"q{seconds}_imbalance_last": float(last.get("nbbo_imbalance", np.nan)),
        f"q{seconds}_imbalance_mean": float(imbalance.mean()),
        f"q{seconds}_imbalance_persistence": float((imbalance > 0.25).mean()),
        f"q{seconds}_ask_heavy_persistence": float((imbalance < -0.25).mean()),
        f"q{seconds}_bid_size_delta_pct": _pct_change(first.get("bid_size", np.nan), last.get("bid_size", np.nan)),
        f"q{seconds}_ask_size_delta_pct": _pct_change(first.get("ask_size", np.nan), last.get("ask_size", np.nan)),
        f"q{seconds}_mid_delta_pct": _pct_change(first.get("mid", np.nan), last.get("mid", np.nan)),
        f"q{seconds}_spread_cv": float(spread.std(ddof=0) / spread.mean()) if spread.mean() and not np.isnan(spread.mean()) else np.nan,
        f"q{seconds}_size_mean": float(size.mean()),
        f"q{seconds}_bid_size_mean": float(bid_size.mean()),
        f"q{seconds}_ask_size_mean": float(ask_size.mean()),
        f"q{seconds}_mid_mean": float(mid.mean()),
    }


def _empty_stats(seconds: int) -> dict[str, object]:
    return {
        f"q{seconds}_quote_count": 0,
        f"q{seconds}_first_quote_ts": "",
        f"q{seconds}_last_quote_ts": "",
        f"q{seconds}_last_quote_age_sec": np.nan,
        f"q{seconds}_spread_first": np.nan,
        f"q{seconds}_spread_last": np.nan,
        f"q{seconds}_spread_mean": np.nan,
        f"q{seconds}_spread_delta": np.nan,
        f"q{seconds}_size_first": np.nan,
        f"q{seconds}_size_last": np.nan,
        f"q{seconds}_size_delta_pct": np.nan,
        f"q{seconds}_imbalance_first": np.nan,
        f"q{seconds}_imbalance_last": np.nan,
        f"q{seconds}_imbalance_mean": np.nan,
        f"q{seconds}_imbalance_persistence": np.nan,
        f"q{seconds}_ask_heavy_persistence": np.nan,
        f"q{seconds}_bid_size_delta_pct": np.nan,
        f"q{seconds}_ask_size_delta_pct": np.nan,
        f"q{seconds}_mid_delta_pct": np.nan,
        f"q{seconds}_spread_cv": np.nan,
        f"q{seconds}_size_mean": np.nan,
        f"q{seconds}_bid_size_mean": np.nan,
        f"q{seconds}_ask_size_mean": np.nan,
        f"q{seconds}_mid_mean": np.nan,
    }


def _pct_change(first: object, last: object) -> float:
    first_num = pd.to_numeric(pd.Series([first]), errors="coerce").iloc[0]
    last_num = pd.to_numeric(pd.Series([last]), errors="coerce").iloc[0]
    if pd.isna(first_num) or pd.isna(last_num) or float(first_num) == 0:
        return np.nan
    return float((last_num - first_num) / abs(first_num))


def build_task577() -> dict[str, pd.DataFrame]:
    panel = _load_candidate_panel()
    panel = panel.reset_index(drop=True).copy()
    panel["task577_row_id"] = np.arange(len(panel))
    records: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    for symbol, group in panel.groupby("symbol", sort=True):
        quotes, source_hash = _load_symbol_quotes(symbol)
        source_rows.append(
            {
                "symbol": symbol,
                "quote_file_exists_flag": int(not quotes.empty),
                "quote_row_count": int(len(quotes)),
                "quote_source_hash": source_hash[:12],
                "receive_ts_available_flag": 0,
                "historical_quote_live_ready_flag": 0,
            }
        )
        for row in group.itertuples(index=False):
            entry_ts = getattr(row, "entry_ts_dt")
            stats: dict[str, object] = {
                "task577_row_id": getattr(row, "task577_row_id"),
                "lifecycle_id": getattr(row, "lifecycle_id"),
                "symbol": symbol,
                "entry_ts": getattr(row, "entry_ts"),
                "quote_source_hash": source_hash[:12],
                "trajectory_assignment_used_outcome_flag": 0,
                "future_quote_used_flag": 0,
                "receive_ts_live_ready_flag": 0,
            }
            for seconds in [60, 30, 10]:
                stats.update(_window_stats(quotes, entry_ts, seconds))
            records.append(stats)
    trajectory = panel.merge(pd.DataFrame(records), on=["task577_row_id", "lifecycle_id", "symbol", "entry_ts"], how="left", validate="one_to_one")
    trajectory = _assign_trajectory_states(trajectory)
    coverage = _trajectory_coverage(trajectory)
    source_audit = pd.DataFrame(source_rows)
    decision = _decision(
        "Task577",
        "DIAGNOSTIC_PASS_NBBO_TRAJECTORY_BUILT",
        total_rows=int(len(trajectory)),
        q60_covered_rows=int((trajectory["q60_quote_count"] > 0).sum()),
        q30_covered_rows=int((trajectory["q30_quote_count"] > 0).sum()),
        q10_covered_rows=int((trajectory["q10_quote_count"] > 0).sum()),
        receive_ts_live_ready_flag=0,
        missing_source_approximated_flag=0,
    )
    return {
        "nbbo_trajectory_feature_panel.csv": trajectory,
        "nbbo_trajectory_source_audit.csv": source_audit,
        "nbbo_trajectory_coverage_audit.csv": coverage,
        "task_577_decision.csv": decision,
    }


def _assign_trajectory_states(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["spread_trajectory_state"] = "spread_missing"
    out.loc[out["q30_spread_delta"] <= -1.0, "spread_trajectory_state"] = "spread_tightening"
    out.loc[out["q30_spread_delta"].between(-1.0, 1.0, inclusive="both"), "spread_trajectory_state"] = "spread_stable"
    out.loc[out["q30_spread_delta"] > 1.0, "spread_trajectory_state"] = "spread_widening"
    out["book_pressure_state"] = "book_missing"
    out.loc[(out["q30_imbalance_persistence"] >= 0.4) & (out["q30_bid_size_delta_pct"] >= -0.5), "book_pressure_state"] = "bid_support_persistent"
    out.loc[(out["q30_ask_heavy_persistence"] >= 0.4) & (out["q30_ask_size_delta_pct"] >= -0.5), "book_pressure_state"] = "ask_pressure_persistent"
    out.loc[out["book_pressure_state"].eq("book_missing") & out["q30_imbalance_mean"].between(-0.25, 0.25, inclusive="both"), "book_pressure_state"] = "balanced_book"
    out["quote_activity_state"] = "quote_activity_missing"
    out.loc[out["q30_quote_count"] >= 30, "quote_activity_state"] = "active_quote_stream"
    out.loc[out["q30_quote_count"].between(1, 29, inclusive="both"), "quote_activity_state"] = "thin_quote_stream"
    out["nbbo_trajectory_state_v1"] = (
        out["spread_trajectory_state"].astype(str)
        + "|"
        + out["book_pressure_state"].astype(str)
        + "|"
        + out["quote_activity_state"].astype(str)
    )
    return out


def _trajectory_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    total = len(frame)
    return pd.DataFrame(
        [
            {
                "window_seconds": seconds,
                "covered_rows": int((frame[f"q{seconds}_quote_count"] > 0).sum()),
                "coverage_rate": 0.0 if total == 0 else float((frame[f"q{seconds}_quote_count"] > 0).mean()),
                "median_quote_count": float(frame[f"q{seconds}_quote_count"].median()) if total else 0.0,
                "receive_ts_live_ready_flag": 0,
            }
            for seconds in [60, 30, 10]
        ]
    )


def _quality(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
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
                "median_holding_days": float(pd.to_numeric(group.get("holding_days"), errors="coerce").median()) if "holding_days" in group else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["avg_net", "count"], ascending=[False, False]).reset_index(drop=True)


def build_task578(task577_panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    panel = task577_panel.copy() if task577_panel is not None else build_task577()["nbbo_trajectory_feature_panel.csv"]
    panel = _assign_task578_sets(panel)
    selected = panel[panel["task578_candidate_set"].ne("not_selected")].copy()
    quality = _quality(selected, ["task578_candidate_set"])
    split_quality = _quality(selected, ["task578_candidate_set", "split_name"]) if "split_name" in selected.columns else pd.DataFrame()
    quarter_quality = _quality(selected, ["task578_candidate_set", "quarter"]) if "quarter" in selected.columns else pd.DataFrame()
    trajectory_quality = _quality(panel[panel["q30_quote_count"] > 0], ["nbbo_trajectory_state_v1"])
    best = quality.iloc[0].to_dict() if not quality.empty else {}
    decision = _decision(
        "Task578",
        "DIAGNOSTIC_PASS_TRAJECTORY_BACKTESTED" if not quality.empty else "DATA_BLOCKED_NO_TRAJECTORY_CANDIDATES",
        selected_rows=int(len(selected)),
        candidate_set_count=int(quality["task578_candidate_set"].nunique()) if not quality.empty else 0,
        best_candidate_set=best.get("task578_candidate_set", ""),
        best_count=best.get("count", 0),
        best_avg_net=best.get("avg_net", np.nan),
        best_win_rate=best.get("win_rate", np.nan),
        best_entry_reduce_rate=best.get("entry_reduce_rate", np.nan),
        assignment_used_outcome_flag=0,
        missing_source_approximated_flag=0,
    )
    return {
        "nbbo_trajectory_backtest_panel.csv": panel,
        "nbbo_trajectory_candidate_set_quality.csv": quality,
        "nbbo_trajectory_split_quality.csv": split_quality,
        "nbbo_trajectory_quarter_quality.csv": quarter_quality,
        "nbbo_trajectory_state_quality.csv": trajectory_quality,
        "task_578_decision.csv": decision,
    }


def _assign_task578_sets(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["task578_candidate_set"] = "not_selected"
    capital = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).eq("capital_flow_expansion")
    constructive = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).isin(
        ["capital_flow_expansion", "constructive_persistence"]
    )
    pullback = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("controlled_pullback_only")
    absorption = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("near_high_absorption_only")
    support = out["book_pressure_state"].isin(["bid_support_persistent", "balanced_book"])
    no_widening = out["spread_trajectory_state"].isin(["spread_tightening", "spread_stable"])
    active = out["quote_activity_state"].eq("active_quote_stream")
    out.loc[constructive & pullback & support & no_widening, "task578_candidate_set"] = "trajectory_supported_pullback"
    out.loc[constructive & absorption & support & no_widening, "task578_candidate_set"] = "trajectory_supported_absorption"
    out.loc[capital & support & no_widening & active, "task578_candidate_set"] = "capital_flow_active_quote_support"
    out.loc[capital & pullback & support & no_widening & active, "task578_candidate_set"] = "capital_flow_active_pullback_support"
    out.loc[out["book_pressure_state"].eq("ask_pressure_persistent") | out["spread_trajectory_state"].eq("spread_widening"), "task578_candidate_set"] = "diagnostic_pressure_or_widening"
    out["trajectory_assignment_used_outcome_flag_v2"] = 0
    return out


def build_task579() -> dict[str, pd.DataFrame]:
    snapshot_contract = pd.DataFrame(
        [
            {"field": "decision_id", "required_flag": 1, "source": "strategy_clock", "live_ready_required_flag": 1},
            {"field": "feature_cutoff_recv_ts_utc", "required_flag": 1, "source": "local_collector", "live_ready_required_flag": 1},
            {"field": "last_quote_recv_ts_utc", "required_flag": 1, "source": "quote_stream", "live_ready_required_flag": 1},
            {"field": "bid/ask/bid_size/ask_size", "required_flag": 1, "source": "quote_stream", "live_ready_required_flag": 1},
            {"field": "client_order_id", "required_flag": 1, "source": "paper_order_or_shadow_action", "live_ready_required_flag": 1},
            {"field": "lifecycle_id", "required_flag": 1, "source": "canonical_lifecycle", "live_ready_required_flag": 1},
        ]
    )
    checklist = pd.DataFrame(
        [
            {"check": "historical_nbbo_diagnostic_available", "status": "PASS", "blocking_flag": 0},
            {"check": "receive_ts_capture_available", "status": "DATA_BLOCKED_LIVE_CAPTURE_REQUIRED", "blocking_flag": 1},
            {"check": "broker_truth_fill_available", "status": "DATA_BLOCKED_PAPER_OR_LIVE_ORDER_ARCHIVE_REQUIRED", "blocking_flag": 1},
            {"check": "status_luld_available", "status": "DATA_BLOCKED_STATUS_LULD_CAPTURE_REQUIRED", "blocking_flag": 1},
        ]
    )
    decision = _decision(
        "Task579",
        "PAPER_SHADOW_CAPTURE_PLAN_READY_NOT_LIVE_READY",
        blocking_check_count=int(checklist["blocking_flag"].sum()),
        historical_nbbo_live_ready_flag=0,
        broker_truth_ready_flag=0,
    )
    return {
        "live_paper_snapshot_contract.csv": snapshot_contract,
        "live_paper_capture_readiness_checklist.csv": checklist,
        "task_579_decision.csv": decision,
    }


def build_task580(task577: dict[str, pd.DataFrame], task578: dict[str, pd.DataFrame], task579: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    d577 = task577["task_577_decision.csv"].iloc[0].to_dict()
    d578 = task578["task_578_decision.csv"].iloc[0].to_dict()
    d579 = task579["task_579_decision.csv"].iloc[0].to_dict()
    gates = pd.DataFrame(
        [
            {"gate": "nbbo_trajectory_built", "status": d577["strategy_acceptance_status"], "pass_flag": int("BUILT" in str(d577["strategy_acceptance_status"]))},
            {"gate": "trajectory_backtest_done", "status": d578["strategy_acceptance_status"], "pass_flag": int("BACKTESTED" in str(d578["strategy_acceptance_status"]))},
            {"gate": "live_capture_ready", "status": d579["strategy_acceptance_status"], "pass_flag": 0},
            {"gate": "broker_truth_ready", "status": "DATA_BLOCKED", "pass_flag": 0},
            {"gate": "deployment_ready", "status": "FORBIDDEN_DIAGNOSTIC_ONLY", "pass_flag": 0},
        ]
    )
    best_er = pd.to_numeric(pd.Series([d578.get("best_entry_reduce_rate")]), errors="coerce").iloc[0]
    if gates["pass_flag"].iloc[:2].sum() == 2 and pd.notna(best_er) and best_er <= 0.27:
        status = "CONTINUE_WITH_NBBO_TRAJECTORY_AND_LIVE_CAPTURE"
        next_action = "run_task581_live_paper_nbbo_trajectory_capture"
    elif gates["pass_flag"].iloc[:2].sum() == 2:
        status = "DIAGNOSTIC_ONLY_TRAJECTORY_NOT_SUFFICIENT_YET"
        next_action = "refine_quote_pressure_factor_or_add_live_capture"
    else:
        status = "DATA_BLOCKED_NBBO_TRAJECTORY_INCOMPLETE"
        next_action = "repair_task577_578_inputs"
    decision = _decision(
        "Task580",
        status,
        next_action=next_action,
        best_entry_reduce_rate=best_er,
        deployment_ready_flag=0,
        paid_depth_required_now_flag=0,
        missing_source_approximated_flag=0,
    )
    return {
        "nbbo_trajectory_firm_grade_gate.csv": gates,
        "task_580_decision.csv": decision,
    }


def _write_bundle(report_dir: Path, artifacts: dict[str, pd.DataFrame], title: str, decision_key: str, quant: list[str], maker: list[str]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        if name.endswith("_panel.csv") and name.startswith("nbbo_trajectory_feature"):
            TASK577_ARTIFACT.mkdir(parents=True, exist_ok=True)
            frame.to_csv(TASK577_ARTIFACT / name, index=False, encoding="utf-8-sig")
        elif name.endswith("_panel.csv") and name.startswith("nbbo_trajectory_backtest"):
            TASK578_ARTIFACT.mkdir(parents=True, exist_ok=True)
            frame.to_csv(TASK578_ARTIFACT / name, index=False, encoding="utf-8-sig")
        else:
            frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")
    decision = artifacts[decision_key].iloc[0].to_dict()
    write_standard_report(
        report_dir / f"{report_dir.name}.md",
        title=title,
        decision_summary=[f"{k}: {v}" for k, v in decision.items()],
        quant_expert_lines=quant,
        decision_maker_lines=maker,
    )
    write_manifest(report_dir, report_dir / "artifact_manifest.csv")


def run_all_tasks() -> dict[str, dict[str, pd.DataFrame]]:
    task577 = build_task577()
    task578 = build_task578(task577["nbbo_trajectory_feature_panel.csv"])
    task579 = build_task579()
    task580 = build_task580(task577, task578, task579)
    _write_bundle(
        TASK577_REPORT,
        task577,
        "Task 577 - Historical NBBO Trajectory Factor Rebuild",
        "task_577_decision.csv",
        [
            "Entry-before-only quote windows are used to compute spread, size, imbalance, and quote activity trajectory.",
            "Historical quotes do not provide receive timestamp and are not marked live-ready.",
        ],
        [
            "진입 직전 호가 흐름을 계산했습니다.",
            "진입 이후 호가나 결과 라벨로 신호를 만들지 않았습니다.",
        ],
    )
    _write_bundle(
        TASK578_REPORT,
        task578,
        "Task 578 - Regime VWAP NBBO Trajectory Backtest",
        "task_578_decision.csv",
        [
            "Capital-flow regime, VWAP sleeve, and NBBO trajectory states are combined into diagnostic candidate sets.",
            "Labels are used only for evaluation.",
        ],
        [
            "좋은 장/테마와 VWAP 구조에 호가 흐름을 붙여 fake continuation이 줄어드는지 확인했습니다.",
            "아직 실전 투입 판단은 아닙니다.",
        ],
    )
    _write_bundle(
        TASK579_REPORT,
        task579,
        "Task 579 - Live Paper Capture Readiness Upgrade",
        "task_579_decision.csv",
        [
            "Historical diagnostics are separated from receive-timestamp live capture and broker-truth fill readiness.",
        ],
        [
            "과거 호가 분석과 실시간 검증을 분리했습니다.",
            "실전 검증에는 장중 수신시각과 주문/체결 연결이 필요합니다.",
        ],
    )
    _write_bundle(
        TASK580_REPORT,
        task580,
        "Task 580 - NBBO Trajectory Firm Grade Gate",
        "task_580_decision.csv",
        [
            "The gate decides whether NBBO trajectory warrants continued live capture or further factor refinement.",
        ],
        [
            "이번 결과가 다음 단계로 갈 가치가 있는지 게이트로 판정합니다.",
            "유료 depth 데이터는 아직 즉시 필수로 판정하지 않습니다.",
        ],
    )
    return {"task577": task577, "task578": task578, "task579": task579, "task580": task580}
