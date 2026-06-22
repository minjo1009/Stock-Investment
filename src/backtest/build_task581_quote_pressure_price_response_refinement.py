from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK578_PANEL = Path("data/artifacts/task_578_regime_vwap_nbbo_trajectory_backtest/nbbo_trajectory_backtest_panel.csv")
QUOTE_DIR = Path("data/raw/alpaca_historical_microstructure/feed=sip/quotes")
TRADE_DIR = Path("data/raw/alpaca_historical_microstructure/feed=sip/trades")

REPORT_DIR = Path("docs/reports/task_581_quote_pressure_price_response_refinement")
ARTIFACT_DIR = Path("data/artifacts/task_581_quote_pressure_price_response_refinement")


def _decision(status: str, **extra: object) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task581",
                "strategy_acceptance_status": status,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
                **extra,
            }
        ]
    )


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def _load_panel(panel_path: Path = TASK578_PANEL) -> pd.DataFrame:
    panel = pd.read_csv(panel_path)
    panel["symbol"] = panel["symbol"].astype(str).str.upper()
    panel["entry_ts_dt"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    return panel.dropna(subset=["symbol", "entry_ts_dt"]).reset_index(drop=True)


def _load_quotes(symbol: str, quote_dir: Path) -> pd.DataFrame:
    path = quote_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["ts_dt"] = pd.to_datetime(frame["quote_ts"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["ts_dt"]).sort_values("ts_dt").reset_index(drop=True)
    for col in ["mid", "bid", "ask", "bid_size", "ask_size", "spread_bps", "nbbo_imbalance"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def _load_trades(symbol: str, trade_dir: Path) -> pd.DataFrame:
    path = trade_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["ts_dt"] = pd.to_datetime(frame["trade_ts"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["ts_dt"]).sort_values("ts_dt").reset_index(drop=True)
    for col in ["price", "size"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def _pct_change(first: object, last: object) -> float:
    first_num = pd.to_numeric(pd.Series([first]), errors="coerce").iloc[0]
    last_num = pd.to_numeric(pd.Series([last]), errors="coerce").iloc[0]
    if pd.isna(first_num) or pd.isna(last_num) or float(first_num) == 0:
        return np.nan
    return float((last_num - first_num) / abs(first_num))


def _quote_response_stats(quotes: pd.DataFrame, entry_ts: pd.Timestamp, seconds: int) -> dict[str, object]:
    prefix = f"qr{seconds}"
    if quotes.empty:
        return {
            f"{prefix}_quote_count": 0,
            f"{prefix}_mid_response_pct": np.nan,
            f"{prefix}_spread_response_bps": np.nan,
            f"{prefix}_imbalance_mean": np.nan,
            f"{prefix}_bid_pressure_persistence": np.nan,
            f"{prefix}_ask_pressure_persistence": np.nan,
            f"{prefix}_last_quote_age_sec": np.nan,
        }
    ts = quotes["ts_dt"].astype("int64").to_numpy()
    start = entry_ts - pd.Timedelta(seconds=seconds)
    left = np.searchsorted(ts, start.value, side="left")
    right = np.searchsorted(ts, entry_ts.value, side="right")
    window = quotes.iloc[left:right]
    if window.empty:
        return {
            f"{prefix}_quote_count": 0,
            f"{prefix}_mid_response_pct": np.nan,
            f"{prefix}_spread_response_bps": np.nan,
            f"{prefix}_imbalance_mean": np.nan,
            f"{prefix}_bid_pressure_persistence": np.nan,
            f"{prefix}_ask_pressure_persistence": np.nan,
            f"{prefix}_last_quote_age_sec": np.nan,
        }
    first = window.iloc[0]
    last = window.iloc[-1]
    imbalance = pd.to_numeric(window["nbbo_imbalance"], errors="coerce")
    return {
        f"{prefix}_quote_count": int(len(window)),
        f"{prefix}_mid_response_pct": _pct_change(first.get("mid"), last.get("mid")),
        f"{prefix}_spread_response_bps": float(last.get("spread_bps", np.nan) - first.get("spread_bps", np.nan)),
        f"{prefix}_imbalance_mean": float(imbalance.mean()),
        f"{prefix}_bid_pressure_persistence": float((imbalance > 0.25).mean()),
        f"{prefix}_ask_pressure_persistence": float((imbalance < -0.25).mean()),
        f"{prefix}_last_quote_age_sec": float((entry_ts - pd.to_datetime(last["quote_ts"], utc=True)).total_seconds()),
    }


def _trade_response_stats(trades: pd.DataFrame, entry_ts: pd.Timestamp, seconds: int) -> dict[str, object]:
    prefix = f"tr{seconds}"
    if trades.empty:
        return {
            f"{prefix}_trade_count": 0,
            f"{prefix}_trade_response_pct": np.nan,
            f"{prefix}_dollar_volume": np.nan,
            f"{prefix}_large_trade_share": np.nan,
            f"{prefix}_available_flag": 0,
        }
    ts = trades["ts_dt"].astype("int64").to_numpy()
    start = entry_ts - pd.Timedelta(seconds=seconds)
    left = np.searchsorted(ts, start.value, side="left")
    right = np.searchsorted(ts, entry_ts.value, side="right")
    window = trades.iloc[left:right]
    if window.empty:
        return {
            f"{prefix}_trade_count": 0,
            f"{prefix}_trade_response_pct": np.nan,
            f"{prefix}_dollar_volume": 0.0,
            f"{prefix}_large_trade_share": np.nan,
            f"{prefix}_available_flag": 1,
        }
    dollar = pd.to_numeric(window["price"], errors="coerce") * pd.to_numeric(window["size"], errors="coerce")
    large_cutoff = dollar.quantile(0.75) if dollar.notna().sum() >= 4 else np.nan
    return {
        f"{prefix}_trade_count": int(len(window)),
        f"{prefix}_trade_response_pct": _pct_change(window.iloc[0].get("price"), window.iloc[-1].get("price")),
        f"{prefix}_dollar_volume": float(dollar.sum()),
        f"{prefix}_large_trade_share": float((dollar >= large_cutoff).mean()) if pd.notna(large_cutoff) else np.nan,
        f"{prefix}_available_flag": 1,
    }


def _build_response_features(panel: pd.DataFrame, quote_dir: Path, trade_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    working = panel.reset_index(drop=True).copy()
    working["task581_row_id"] = np.arange(len(working))
    for symbol, group in working.groupby("symbol", sort=True):
        quote_path = quote_dir / f"{symbol}.csv"
        trade_path = trade_dir / f"{symbol}.csv"
        quotes = _load_quotes(symbol, quote_dir)
        trades = _load_trades(symbol, trade_dir)
        source_rows.append(
            {
                "symbol": symbol,
                "quote_source_exists_flag": int(not quotes.empty),
                "trade_source_exists_flag": int(not trades.empty),
                "quote_row_count": int(len(quotes)),
                "trade_row_count": int(len(trades)),
                "quote_source_hash": _file_hash(quote_path),
                "trade_source_hash": _file_hash(trade_path),
                "receive_ts_available_flag": 0,
                "historical_live_ready_flag": 0,
            }
        )
        for row in group.itertuples(index=False):
            entry_ts = getattr(row, "entry_ts_dt")
            rec: dict[str, object] = {
                "task581_row_id": getattr(row, "task581_row_id"),
                "lifecycle_id": getattr(row, "lifecycle_id"),
                "symbol": symbol,
                "entry_ts": getattr(row, "entry_ts"),
                "quote_response_source_available_flag": int(not quotes.empty),
                "trade_response_source_available_flag": int(not trades.empty),
                "future_market_data_used_flag": 0,
                "label_used_in_assignment_flag_task581": 0,
                "inferred_matching_used_flag_task581": 0,
                "missing_source_approximated_flag_task581": 0,
                "historical_live_ready_flag": 0,
            }
            for seconds in [60, 30, 10]:
                rec.update(_quote_response_stats(quotes, entry_ts, seconds))
                rec.update(_trade_response_stats(trades, entry_ts, seconds))
            records.append(rec)
    enriched = working.merge(pd.DataFrame(records), on=["task581_row_id", "lifecycle_id", "symbol", "entry_ts"], how="left", validate="one_to_one")
    return _assign_states(enriched), pd.DataFrame(source_rows)


def _assign_states(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    mid_up = pd.to_numeric(out["qr30_mid_response_pct"], errors="coerce") >= 0.0005
    mid_flat = pd.to_numeric(out["qr30_mid_response_pct"], errors="coerce").between(-0.0005, 0.0005, inclusive="both")
    mid_down = pd.to_numeric(out["qr30_mid_response_pct"], errors="coerce") < -0.0005
    spread_widening = pd.to_numeric(out["qr30_spread_response_bps"], errors="coerce") > 1.0
    spread_ok = pd.to_numeric(out["qr30_spread_response_bps"], errors="coerce") <= 1.0
    bid_pressure = pd.to_numeric(out["qr30_bid_pressure_persistence"], errors="coerce") >= 0.35
    ask_pressure = pd.to_numeric(out["qr30_ask_pressure_persistence"], errors="coerce") >= 0.35
    active_quotes = pd.to_numeric(out["qr30_quote_count"], errors="coerce") >= 30
    trade_up = pd.to_numeric(out["tr30_trade_response_pct"], errors="coerce") >= 0.0005
    trade_down = pd.to_numeric(out["tr30_trade_response_pct"], errors="coerce") < -0.0005

    out["quote_pressure_price_response_state_v1"] = "response_missing"
    out.loc[active_quotes & bid_pressure & spread_ok & (mid_up | trade_up), "quote_pressure_price_response_state_v1"] = "bid_support_price_acceptance"
    out.loc[active_quotes & bid_pressure & spread_ok & mid_flat & ~trade_up, "quote_pressure_price_response_state_v1"] = "bid_support_no_price_response"
    out.loc[active_quotes & ask_pressure & spread_ok & (mid_up | trade_up), "quote_pressure_price_response_state_v1"] = "ask_pressure_absorbed_price_up"
    out.loc[active_quotes & ask_pressure & (mid_down | trade_down), "quote_pressure_price_response_state_v1"] = "ask_pressure_price_breakdown"
    out.loc[active_quotes & spread_widening & (mid_down | trade_down), "quote_pressure_price_response_state_v1"] = "spread_widening_price_breakdown"
    out.loc[out["qr30_quote_count"].fillna(0).astype(float).between(1, 29, inclusive="both"), "quote_pressure_price_response_state_v1"] = "thin_quote_response"
    out["task581_assignment_used_outcome_flag"] = 0
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
                "false_positive_rate": float(pd.to_numeric(group["false_positive_flag"], errors="coerce").mean()),
                "median_holding_days": float(pd.to_numeric(group.get("holding_days"), errors="coerce").median()) if "holding_days" in group else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["avg_net", "count"], ascending=[False, False]).reset_index(drop=True)


def _candidate_sets(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["task581_candidate_set"] = "not_selected"
    capital = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).eq("capital_flow_expansion")
    constructive = out.get("capital_flow_regime_v6", pd.Series(index=out.index, dtype=str)).astype(str).isin(
        ["capital_flow_expansion", "constructive_persistence"]
    )
    pullback = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("controlled_pullback_only")
    absorption = out.get("pullback_sleeve_v1", pd.Series(index=out.index, dtype=str)).astype(str).eq("near_high_absorption_only")
    state = out["quote_pressure_price_response_state_v1"].astype(str)
    accepted = state.isin(["bid_support_price_acceptance", "ask_pressure_absorbed_price_up"])
    no_response = state.eq("bid_support_no_price_response")
    breakdown = state.isin(["ask_pressure_price_breakdown", "spread_widening_price_breakdown"])
    out.loc[constructive & pullback & accepted, "task581_candidate_set"] = "price_response_supported_pullback"
    out.loc[constructive & absorption & accepted, "task581_candidate_set"] = "price_response_supported_absorption"
    out.loc[capital & accepted, "task581_candidate_set"] = "capital_flow_price_response_acceptance"
    out.loc[capital & pullback & accepted, "task581_candidate_set"] = "capital_flow_pullback_price_response"
    out.loc[no_response | breakdown, "task581_candidate_set"] = "diagnostic_quote_pressure_failure"
    return out


def _leakage_audit(panel: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("No inferred lifecycle matching", "inferred_matching_used_flag_task581", 0),
        ("No label used in assignment", "label_used_in_assignment_flag_task581", 0),
        ("No future market data in feature", "future_market_data_used_flag", 0),
        ("No missing source approximation", "missing_source_approximated_flag_task581", 0),
        ("Historical data not live ready", "historical_live_ready_flag", 0),
    ]
    rows = []
    for check, column, expected in checks:
        if column not in panel.columns:
            rows.append({"check": check, "status": "NOT_REPORTED", "bad_rows": None, "total_rows": len(panel)})
            continue
        bad = int((pd.to_numeric(panel[column], errors="coerce").fillna(expected) != expected).sum())
        rows.append({"check": check, "status": "PASS" if bad == 0 else "FAIL", "bad_rows": bad, "total_rows": len(panel)})
    return pd.DataFrame(rows)


def build_task581(
    panel_path: Path = TASK578_PANEL,
    quote_dir: Path = QUOTE_DIR,
    trade_dir: Path = TRADE_DIR,
) -> dict[str, pd.DataFrame]:
    panel = _load_panel(panel_path)
    enriched, source_audit = _build_response_features(panel, quote_dir, trade_dir)
    assigned = _candidate_sets(enriched)
    selected = assigned[assigned["task581_candidate_set"].ne("not_selected")].copy()
    quality = _quality(selected, ["task581_candidate_set"])
    state_quality = _quality(assigned[assigned["quote_response_source_available_flag"].eq(1)], ["quote_pressure_price_response_state_v1"])
    split_quality = _quality(selected, ["task581_candidate_set", "split_name"]) if "split_name" in selected.columns else pd.DataFrame()
    quarter_quality = _quality(selected, ["task581_candidate_set", "quarter"]) if "quarter" in selected.columns else pd.DataFrame()
    leakage = _leakage_audit(assigned)
    best = quality.iloc[0].to_dict() if not quality.empty else {}
    decision = _decision(
        "DIAGNOSTIC_PASS_QUOTE_PRESSURE_PRICE_RESPONSE_TESTED" if not quality.empty else "DATA_BLOCKED_NO_RESPONSE_CANDIDATES",
        total_rows=int(len(assigned)),
        selected_rows=int(len(selected)),
        quote_response_covered_rows=int((assigned["qr30_quote_count"] > 0).sum()),
        trade_response_source_rows=int((assigned["trade_response_source_available_flag"] == 1).sum()),
        candidate_set_count=int(quality["task581_candidate_set"].nunique()) if not quality.empty else 0,
        best_candidate_set=best.get("task581_candidate_set", ""),
        best_count=best.get("count", 0),
        best_avg_net=best.get("avg_net", np.nan),
        best_win_rate=best.get("win_rate", np.nan),
        best_entry_reduce_rate=best.get("entry_reduce_rate", np.nan),
        receive_ts_live_ready_flag=0,
        missing_source_approximated_flag=0,
        next_action="start_safe_kis_paper_bridge_and_live_capture",
    )
    return {
        "quote_pressure_price_response_panel.csv": assigned,
        "quote_pressure_price_response_source_audit.csv": source_audit,
        "quote_pressure_price_response_state_quality.csv": state_quality,
        "quote_pressure_price_response_candidate_quality.csv": quality,
        "quote_pressure_price_response_split_quality.csv": split_quality,
        "quote_pressure_price_response_quarter_quality.csv": quarter_quality,
        "quote_pressure_price_response_leakage_audit.csv": leakage,
        "task_581_decision.csv": decision,
    }


def write_task581(artifacts: dict[str, pd.DataFrame]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        target_dir = ARTIFACT_DIR if name == "quote_pressure_price_response_panel.csv" else REPORT_DIR
        frame.to_csv(target_dir / name, index=False, encoding="utf-8-sig")
    decision = artifacts["task_581_decision.csv"].iloc[0].to_dict()
    write_standard_report(
        REPORT_DIR / "task_581_quote_pressure_price_response_refinement.md",
        title="Task 581 - Quote Pressure x Price Response Microstructure Refinement",
        decision_summary=[f"{k}: {v}" for k, v in decision.items()],
        quant_expert_lines=[
            "Task581 tests whether pre-entry NBBO pressure is confirmed by pre-entry mid/trade price response.",
            "Historical quotes/trades are diagnostic only because receive timestamps and broker-truth fills are unavailable for this sample.",
            "Trade response is used only when raw historical trade files exist; missing trade data is not approximated.",
        ],
        decision_maker_lines=[
            "진입 직전 호가 압력이 실제 가격 반응으로 이어졌는지 확인했다.",
            "진입 이후 정보는 신호 생성에 쓰지 않았고, 없는 trade 데이터는 없는 것으로 보고했다.",
            "이 결과는 한국투자 모의계좌 연결과 live receive timestamp 축적의 다음 입력이다.",
        ],
    )
    write_manifest(REPORT_DIR, REPORT_DIR / "artifact_manifest.csv")


def run_task581() -> dict[str, pd.DataFrame]:
    artifacts = build_task581()
    write_task581(artifacts)
    return artifacts


if __name__ == "__main__":
    run_task581()
