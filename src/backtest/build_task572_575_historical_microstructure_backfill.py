from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


RAW_MICRO_DIR = Path("data/raw/alpaca_historical_microstructure")
TASK568_PANEL = Path("data/artifacts/task_568_vwap_pullback_sleeve_robustness/vwap_pullback_sleeve_assignment_panel.csv")

TASK572_REPORT = Path("docs/reports/task_572_historical_quote_trade_source_acquisition")
TASK573_REPORT = Path("docs/reports/task_573_historical_nbbo_feature_rebuild")
TASK574_REPORT = Path("docs/reports/task_574_historical_microstructure_failure_separation")
TASK575_REPORT = Path("docs/reports/task_575_microstructure_download_integration_gate")
TASK573_ARTIFACT = Path("data/artifacts/task_573_historical_nbbo_feature_rebuild")


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _read_candidate_panel(path: Path = TASK568_PANEL, nrows: int | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, nrows=nrows)


def _required_window(candidate: pd.DataFrame) -> tuple[str, str, int, int]:
    if candidate.empty or "entry_ts" not in candidate.columns:
        return "", "", 0, 0
    ts = pd.to_datetime(candidate["entry_ts"], utc=True, errors="coerce").dropna()
    if ts.empty:
        return "", "", 0, 0
    return (
        ts.min().isoformat().replace("+00:00", "Z"),
        ts.max().isoformat().replace("+00:00", "Z"),
        int(candidate.get("symbol", pd.Series(dtype=str)).astype(str).str.upper().nunique()),
        int(len(candidate)),
    )


def _source_contract() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_name": "historical_quotes_nbbo",
                "provider": "alpaca",
                "download_possible_flag": 1,
                "firm_grade_role": "entry_time_spread_bid_ask_size_quote_imbalance",
                "receive_ts_available_flag": 0,
                "deployment_live_ready_flag": 0,
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "historical_trades",
                "provider": "alpaca",
                "download_possible_flag": 1,
                "firm_grade_role": "trade_print_intensity_and_price_validation",
                "receive_ts_available_flag": 0,
                "deployment_live_ready_flag": 0,
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "historical_status_luld",
                "provider": "alpaca_or_exchange_vendor",
                "download_possible_flag": 0,
                "firm_grade_role": "halt_luld_status_filter",
                "receive_ts_available_flag": 0,
                "deployment_live_ready_flag": 0,
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "full_depth_book",
                "provider": "direct_depth_vendor_required",
                "download_possible_flag": 0,
                "firm_grade_role": "depth_resiliency_and_capacity",
                "receive_ts_available_flag": 0,
                "deployment_live_ready_flag": 0,
                "approximation_allowed_flag": 0,
            },
        ]
    )


def _download_command_contract(candidate: pd.DataFrame, feed: str = "sip") -> pd.DataFrame:
    start, end, symbol_count, row_count = _required_window(candidate)
    symbols = []
    if not candidate.empty and "symbol" in candidate.columns:
        symbols = sorted(candidate["symbol"].astype(str).str.upper().dropna().unique().tolist())
    if not symbols:
        symbols = ["AAPL", "NVDA", "AMD"]
    rows: list[dict[str, object]] = []
    for row_feed, contract_name in [(feed, "historical_quotes_trades_primary_download"), ("iex", "scope_limited_iex_diagnostic_download")]:
        for batch_id, start_idx in enumerate(range(0, len(symbols), 20), start=1):
            batch_symbols = symbols[start_idx : start_idx + 20]
            command = (
                "python -m src.data.alpaca_historical_microstructure_export "
                f"--feed {row_feed} --entry-panel {TASK568_PANEL.as_posix()} "
                f"--window-before-minutes 1 --window-after-minutes 0 --symbols {' '.join(batch_symbols)}"
            )
            rows.append(
                {
                "contract_name": "historical_quotes_trades_primary_download",
                "feed": row_feed,
                "batch_id": batch_id,
                "batch_symbol_count": len(batch_symbols),
                "candidate_symbol_count": symbol_count,
                "candidate_row_count": row_count,
                "required_start": start,
                "required_end": end,
                "window_before_minutes": 1,
                "window_after_minutes": 0,
                "download_scope": "entry_window_targeted_not_full_range",
                "command": command,
                "secret_in_command_flag": 0,
                "expected_output_dir": str(RAW_MICRO_DIR / f"feed={row_feed}"),
            }
            )
            rows[-1]["contract_name"] = contract_name
    return pd.DataFrame(rows)


def _raw_file_audit(raw_dir: Path = RAW_MICRO_DIR) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(raw_dir.glob("feed=*/quotes/*.csv")) + sorted(raw_dir.glob("feed=*/trades/*.csv")):
        try:
            header = pd.read_csv(path, nrows=0)
            with path.open("r", encoding="utf-8-sig") as handle:
                count = sum(1 for _ in handle) - 1
            source_kind = "quotes" if "\\quotes\\" in str(path) or "/quotes/" in str(path).replace("\\", "/") else "trades"
            feed = next((part.split("=", 1)[1] for part in path.parts if part.startswith("feed=")), "")
            rows.append(
                {
                    "source_kind": source_kind,
                    "feed": feed,
                    "symbol": path.stem.upper(),
                    "path": str(path),
                    "row_count": max(int(count), 0),
                    "columns": "|".join(header.columns.astype(str).tolist()),
                    "sha256": _file_hash(path),
                    "receive_ts_available_flag": 0,
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "source_kind": "unknown",
                    "feed": "",
                    "symbol": path.stem.upper(),
                    "path": str(path),
                    "row_count": 0,
                    "columns": "",
                    "sha256": "",
                    "receive_ts_available_flag": 0,
                    "error": str(exc),
                }
            )
    return pd.DataFrame(rows)


def build_task572(*, raw_dir: Path = RAW_MICRO_DIR, candidate_path: Path = TASK568_PANEL) -> dict[str, pd.DataFrame]:
    candidate = _read_candidate_panel(candidate_path)
    contract = _source_contract()
    command = _download_command_contract(candidate)
    files = _raw_file_audit(raw_dir)
    quote_rows = int(files.loc[files.get("source_kind", pd.Series(dtype=str)).eq("quotes"), "row_count"].sum()) if not files.empty else 0
    trade_rows = int(files.loc[files.get("source_kind", pd.Series(dtype=str)).eq("trades"), "row_count"].sum()) if not files.empty else 0
    candidate_symbol_count = int(candidate.get("symbol", pd.Series(dtype=str)).astype(str).str.upper().nunique()) if not candidate.empty else 0
    quote_symbol_count = int(files.loc[files.get("source_kind", pd.Series(dtype=str)).eq("quotes"), "symbol"].nunique()) if not files.empty else 0
    trade_symbol_count = int(files.loc[files.get("source_kind", pd.Series(dtype=str)).eq("trades"), "symbol"].nunique()) if not files.empty else 0
    if quote_symbol_count >= candidate_symbol_count and candidate_symbol_count > 0 and trade_symbol_count >= candidate_symbol_count:
        status = "HISTORICAL_QUOTES_TRADES_AVAILABLE"
    elif quote_symbol_count >= candidate_symbol_count and candidate_symbol_count > 0:
        status = "HISTORICAL_QUOTES_AVAILABLE_TRADES_PARTIAL"
    elif quote_rows > 0:
        status = "HISTORICAL_QUOTES_PARTIAL_TRADES_OPTIONAL"
    else:
        status = "DATA_BLOCKED_HISTORICAL_QUOTES_MISSING"
    decision = _decision(
        "Task572",
        status,
        candidate_symbol_count=candidate_symbol_count,
        quote_symbol_count=quote_symbol_count,
        trade_symbol_count=trade_symbol_count,
        quote_row_count=quote_rows,
        trade_row_count=trade_rows,
        missing_source_approximated_flag=0,
        receive_ts_live_ready_flag=0,
    )
    return {
        "historical_microstructure_source_contract.csv": contract,
        "historical_microstructure_download_command_contract.csv": command,
        "historical_microstructure_raw_file_audit.csv": files,
        "task_572_decision.csv": decision,
    }


def _load_quotes(raw_dir: Path = RAW_MICRO_DIR) -> pd.DataFrame:
    frames = []
    for path in sorted(raw_dir.glob("feed=*/quotes/*.csv")):
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame["raw_quote_source_path"] = str(path)
        frame["raw_quote_source_hash"] = _file_hash(path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    quotes = pd.concat(frames, ignore_index=True)
    quotes["symbol"] = quotes["symbol"].astype(str).str.upper()
    quotes["quote_ts"] = pd.to_datetime(quotes["quote_ts"], utc=True, errors="coerce")
    return quotes.dropna(subset=["symbol", "quote_ts"]).sort_values(["symbol", "quote_ts"]).reset_index(drop=True)


def _build_quote_features(candidate: pd.DataFrame, quotes: pd.DataFrame, tolerance_minutes: int = 30) -> pd.DataFrame:
    if candidate.empty:
        return pd.DataFrame()
    base = candidate.copy()
    base["symbol"] = base["symbol"].astype(str).str.upper()
    base["entry_ts_dt"] = pd.to_datetime(base["entry_ts"], utc=True, errors="coerce")
    quote_columns = set(quotes.columns)
    rows = []
    tolerance = pd.Timedelta(minutes=int(tolerance_minutes))
    for symbol, group in base.dropna(subset=["entry_ts_dt"]).groupby("symbol", sort=False):
        q = quotes[quotes["symbol"].eq(symbol)].sort_values("quote_ts") if {"symbol", "quote_ts"}.issubset(quote_columns) else pd.DataFrame()
        g = group.sort_values("entry_ts_dt")
        if q.empty:
            merged = g.copy()
            for column in [
                "quote_ts",
                "bid",
                "ask",
                "bid_size",
                "ask_size",
                "mid",
                "spread_bps",
                "nbbo_size_dollar",
                "nbbo_imbalance",
                "raw_quote_source_path",
                "raw_quote_source_hash",
            ]:
                merged[column] = pd.NA
        else:
            merged = pd.merge_asof(
                g,
                q,
                left_on="entry_ts_dt",
                right_on="quote_ts",
                by="symbol",
                direction="backward",
                tolerance=tolerance,
            )
        rows.append(merged)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["quote_ts"] = pd.to_datetime(out.get("quote_ts"), utc=True, errors="coerce")
    out["quote_match_available_flag"] = out["quote_ts"].notna().astype(int)
    out["quote_age_minutes"] = (out["entry_ts_dt"] - out["quote_ts"]).dt.total_seconds() / 60
    out["spread_to_intraday_range"] = out["spread_bps"] / ((out["range_pos"].abs() + 0.05) * 100).where(out.get("range_pos", 0).notna(), 100) if "range_pos" in out.columns else pd.NA
    out["historical_quote_used_as_live_ready_flag"] = 0
    out["receive_ts_available_flag"] = 0
    out["inferred_lifecycle_matching_used_flag_micro"] = 0
    out["symbol_date_price_time_fallback_used_flag"] = 0
    return out.drop(columns=["entry_ts_dt"], errors="ignore")


def build_task573(*, raw_dir: Path = RAW_MICRO_DIR, candidate_path: Path = TASK568_PANEL) -> dict[str, pd.DataFrame]:
    candidate = _read_candidate_panel(candidate_path)
    quotes = _load_quotes(raw_dir)
    features = _build_quote_features(candidate, quotes)
    matched = int(features.get("quote_match_available_flag", pd.Series(dtype=int)).sum()) if not features.empty else 0
    total = int(len(candidate))
    status = "HISTORICAL_NBBO_FEATURES_AVAILABLE" if matched > 0 else "DATA_BLOCKED_NO_HISTORICAL_QUOTE_MATCHES"
    lineage = pd.DataFrame(
        [
            {
                "factor_name": name,
                "required_source": "historical_quotes_nbbo",
                "exact_source_available_flag": int(matched > 0),
                "receive_ts_required_for_live_ready_flag": 1 if name in {"quote_staleness_ms"} else 0,
                "inferred_matching_used_flag": 0,
                "missing_source_approximated_flag": 0,
            }
            for name in ["spread_bps", "nbbo_size_dollar", "nbbo_imbalance", "quote_age_minutes", "spread_to_intraday_range"]
        ]
    )
    audit = pd.DataFrame(
        [
            {
                "candidate_rows": total,
                "quote_feature_rows": int(len(features)),
                "quote_matched_rows": matched,
                "quote_match_rate": 0.0 if total == 0 else matched / total,
                "historical_quote_used_as_live_ready_flag": 0,
                "missing_source_approximated_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
            }
        ]
    )
    decision = _decision(
        "Task573",
        status,
        candidate_rows=total,
        quote_matched_rows=matched,
        historical_quote_used_as_live_ready_flag=0,
        missing_source_approximated_flag=0,
    )
    return {
        "historical_nbbo_feature_panel.csv": features,
        "historical_nbbo_feature_lineage_audit.csv": lineage,
        "historical_nbbo_feature_coverage_audit.csv": audit,
        "task_573_decision.csv": decision,
    }


def _quality(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty or not set(group_cols).issubset(frame.columns):
        return pd.DataFrame(columns=group_cols + ["count", "avg_net", "win_rate", "entry_reduce_rate", "add_scale_rate"])
    rows = []
    for key, group in frame.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        rows.append(
            {
                **dict(zip(group_cols, key)),
                "count": int(len(group)),
                "avg_net": float(pd.to_numeric(group.get("net_return_from_entry"), errors="coerce").mean()),
                "win_rate": float(pd.to_numeric(group.get("win_flag"), errors="coerce").mean()),
                "entry_reduce_rate": float(pd.to_numeric(group.get("entry_reduce_failure_flag"), errors="coerce").mean()),
                "add_scale_rate": float(pd.to_numeric(group.get("add_scale_success_flag"), errors="coerce").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["count"], ascending=False).reset_index(drop=True)


def build_task574(*, feature_panel: pd.DataFrame | None = None, raw_dir: Path = RAW_MICRO_DIR, candidate_path: Path = TASK568_PANEL) -> dict[str, pd.DataFrame]:
    features = feature_panel if feature_panel is not None else build_task573(raw_dir=raw_dir, candidate_path=candidate_path)["historical_nbbo_feature_panel.csv"]
    if features.empty or int(features.get("quote_match_available_flag", pd.Series(dtype=int)).sum()) == 0:
        empty = pd.DataFrame()
        decision = _decision(
            "Task574",
            "DATA_BLOCKED_NO_HISTORICAL_NBBO_FEATURES",
            tested_bucket_count=0,
            missing_source_approximated_flag=0,
        )
        return {
            "historical_microstructure_bucket_quality.csv": empty,
            "historical_microstructure_failure_separation_audit.csv": empty,
            "task_574_decision.csv": decision,
        }
    tested = features[features["quote_match_available_flag"].eq(1)].copy()
    tested["spread_bucket"] = pd.cut(
        pd.to_numeric(tested["spread_bps"], errors="coerce"),
        bins=[-float("inf"), 5, 15, 40, float("inf")],
        labels=["tight_spread", "normal_spread", "wide_spread", "very_wide_spread"],
    ).astype(str)
    tested["nbbo_size_bucket"] = pd.qcut(
        pd.to_numeric(tested["nbbo_size_dollar"], errors="coerce").rank(method="first"),
        q=3,
        labels=["thin_nbbo", "normal_nbbo", "deep_nbbo"],
    ).astype(str)
    tested["imbalance_bucket"] = pd.cut(
        pd.to_numeric(tested["nbbo_imbalance"], errors="coerce"),
        bins=[-float("inf"), -0.25, 0.25, float("inf")],
        labels=["ask_heavy", "balanced", "bid_heavy"],
    ).astype(str)
    quality = _quality(tested, ["spread_bucket", "nbbo_size_bucket", "imbalance_bucket"])
    audit = _quality(tested, ["vwap_acceptance_state_v3", "spread_bucket"]) if "vwap_acceptance_state_v3" in tested.columns else pd.DataFrame()
    status = "DIAGNOSTIC_PASS_HISTORICAL_MICROSTRUCTURE_TESTED" if not quality.empty else "DATA_BLOCKED_NO_EVALUABLE_BUCKETS"
    decision = _decision(
        "Task574",
        status,
        tested_bucket_count=int(len(quality)),
        tested_lifecycle_count=int(len(tested)),
        missing_source_approximated_flag=0,
        live_ready_flag=0,
    )
    return {
        "historical_microstructure_bucket_quality.csv": quality,
        "historical_microstructure_failure_separation_audit.csv": audit,
        "task_574_decision.csv": decision,
    }


def build_task575(task572: dict[str, pd.DataFrame], task573: dict[str, pd.DataFrame], task574: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    d572 = task572["task_572_decision.csv"].iloc[0].to_dict()
    d573 = task573["task_573_decision.csv"].iloc[0].to_dict()
    d574 = task574["task_574_decision.csv"].iloc[0].to_dict()
    rows = [
        {"gate": "historical_quote_source_available", "status": d572["strategy_acceptance_status"], "pass_flag": int("QUOTES_AVAILABLE" in str(d572["strategy_acceptance_status"]))},
        {"gate": "historical_nbbo_feature_match_available", "status": d573["strategy_acceptance_status"], "pass_flag": int("AVAILABLE" in str(d573["strategy_acceptance_status"]))},
        {"gate": "historical_microstructure_failure_tested", "status": d574["strategy_acceptance_status"], "pass_flag": int("TESTED" in str(d574["strategy_acceptance_status"]))},
        {"gate": "receive_ts_live_ready", "status": "DATA_BLOCKED_HISTORICAL_ONLY", "pass_flag": 0},
        {"gate": "status_luld_historical_available", "status": "DATA_BLOCKED_NOT_APPROXIMATED", "pass_flag": 0},
    ]
    gate = pd.DataFrame(rows)
    if int(gate["pass_flag"].iloc[:3].sum()) == 3:
        status = "HISTORICAL_MICROSTRUCTURE_DIAGNOSTIC_READY_NOT_LIVE_READY"
        next_action = "run_historical_microstructure_failure_retest_then_live_capture"
    elif int(gate["pass_flag"].iloc[0]) == 0:
        status = "DATA_BLOCKED_DOWNLOAD_HISTORICAL_QUOTES_TRADES_FIRST"
        next_action = "run_alpaca_historical_microstructure_export"
    else:
        status = "DATA_BLOCKED_BUILD_HISTORICAL_NBBO_FEATURES"
        next_action = "rebuild_task573_after_quote_download"
    decision = _decision(
        "Task575",
        status,
        next_action=next_action,
        hard_live_ready_flag=0,
        deployment_ready_flag=0,
        missing_source_approximated_flag=0,
    )
    return {
        "historical_microstructure_integration_gate.csv": gate,
        "task_575_decision.csv": decision,
    }


def _write_bundle(report_dir: Path, artifacts: dict[str, pd.DataFrame], title: str, decision_key: str, quant: list[str], decision_maker: list[str]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")
    decision = artifacts[decision_key].iloc[0].to_dict()
    write_standard_report(
        report_dir / f"{report_dir.name}.md",
        title=title,
        decision_summary=[f"{key}: {value}" for key, value in decision.items()],
        quant_expert_lines=quant,
        decision_maker_lines=decision_maker,
    )
    write_manifest(report_dir, report_dir / "artifact_manifest.csv")


def run_all_tasks(*, raw_dir: Path = RAW_MICRO_DIR, candidate_path: Path = TASK568_PANEL) -> dict[str, dict[str, pd.DataFrame]]:
    task572 = build_task572(raw_dir=raw_dir, candidate_path=candidate_path)
    task573 = build_task573(raw_dir=raw_dir, candidate_path=candidate_path)
    feature_panel = task573["historical_nbbo_feature_panel.csv"]
    TASK573_ARTIFACT.mkdir(parents=True, exist_ok=True)
    feature_panel.to_csv(TASK573_ARTIFACT / "historical_nbbo_feature_panel.csv", index=False, encoding="utf-8-sig")
    task574 = build_task574(feature_panel=feature_panel, raw_dir=raw_dir, candidate_path=candidate_path)
    task575 = build_task575(task572, task573, task574)

    _write_bundle(
        TASK572_REPORT,
        task572,
        "Task 572 - Historical Quote/Trade Source Acquisition",
        "task_572_decision.csv",
        [
            "Historical Alpaca quotes/trades are treated as downloadable microstructure diagnostics, not live-ready evidence.",
            "Receive timestamp, status/LULD, and full depth are explicitly blocked when absent; no approximation is allowed.",
        ],
        [
            "과거 NBBO/체결 데이터는 다운로드해서 실패 원인 분석에 붙일 수 있습니다.",
            "하지만 이 데이터는 실제 수신시각과 주문체결 truth가 없으므로 실전 검증으로 승격하지 않습니다.",
        ],
    )
    _write_bundle(
        TASK573_REPORT,
        {k: v for k, v in task573.items() if k != "historical_nbbo_feature_panel.csv"},
        "Task 573 - Historical NBBO Feature Rebuild",
        "task_573_decision.csv",
        [
            "Entry-time quote features are aligned only by symbol plus quote timestamp before the existing exact lifecycle entry time.",
            "This is market-data feature alignment, not lifecycle identity reconstruction.",
        ],
        [
            "거래 진입 시점 이전에 실제로 존재했던 bid/ask/size만 붙입니다.",
            "quote가 없으면 빈칸으로 남기고, 좋은/나쁜 결과를 추정해서 채우지 않습니다.",
        ],
    )
    _write_bundle(
        TASK574_REPORT,
        task574,
        "Task 574 - Historical Microstructure Failure Separation",
        "task_574_decision.csv",
        [
            "Historical NBBO buckets are evaluated only after exact lifecycle labels already exist.",
            "The result remains diagnostic because historical quotes do not contain local receive timestamp or broker fill truth.",
        ],
        [
            "spread와 bid/ask size가 entry_reduce 실패를 줄이는지 검증하는 단계입니다.",
            "실전 주문 가능성 판단은 아직 아니며, live capture와 broker fill 기록이 필요합니다.",
        ],
    )
    _write_bundle(
        TASK575_REPORT,
        task575,
        "Task 575 - Microstructure Download Integration Gate",
        "task_575_decision.csv",
        [
            "The gate separates historical diagnostic readiness from live-ready hard evidence.",
            "If quotes are missing, the next action is data download, not threshold tuning.",
        ],
        [
            "이 게이트는 다음 액션을 자동으로 정합니다.",
            "데이터가 없으면 전략 조정이 아니라 historical quotes/trades 다운로드가 먼저입니다.",
        ],
    )
    return {"task572": task572, "task573": task573, "task574": task574, "task575": task575}
