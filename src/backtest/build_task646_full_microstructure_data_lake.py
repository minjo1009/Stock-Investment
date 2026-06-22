from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task638_content_signal_refinement import QQQ_PATH


TASK_ID = "Task646"
REPORT_DIR = Path("docs/reports/task_646_full_microstructure_data_lake")
EXECUTION_PANEL = Path("docs/reports/task_643_entry_risk_tier_turnover_backtest/task_643_execution_variant_panel.csv")
CONTENT_PANEL = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_content_prediction_panel.csv")
RAW_LAKE_DIR = Path("data/raw/microstructure_full")


def build_task646_full_microstructure_data_lake(
    *,
    execution_panel_path: Path = CONTENT_PANEL,
    raw_lake_dir: Path = RAW_LAKE_DIR,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    universe = build_universe_scope(execution_panel_path)
    calendar = build_expected_calendar(universe, qqq_path)
    command_plan = build_command_plan(universe)
    catalog = build_raw_catalog(raw_lake_dir)
    coverage = build_coverage_audit(calendar, catalog)
    integrity = build_integrity_audit(catalog)
    query_contract = build_query_contract(raw_lake_dir)
    pass_fail = build_pass_fail(universe, coverage, integrity)
    decision = build_decision(universe, coverage, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    universe.to_csv(out_dir / "task_646_universe_scope.csv", index=False)
    command_plan.to_csv(out_dir / "task_646_backfill_command_plan.csv", index=False)
    catalog.to_csv(out_dir / "task_646_raw_data_catalog.csv", index=False)
    coverage.to_csv(out_dir / "task_646_coverage_audit.csv", index=False)
    integrity.to_csv(out_dir / "task_646_integrity_audit.csv", index=False)
    query_contract.to_csv(out_dir / "task_646_catalog_query_contract.csv", index=False)
    pass_fail.to_csv(out_dir / "task_646_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_646_decision.csv", index=False)
    (out_dir / "task_646_full_microstructure_data_lake.md").write_text(
        render_report(universe, command_plan, catalog, coverage, integrity, query_contract, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "universe": universe,
        "command_plan": command_plan,
        "catalog": catalog,
        "coverage": coverage,
        "integrity": integrity,
        "query_contract": query_contract,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def build_universe_scope(execution_panel_path: Path) -> pd.DataFrame:
    panel = pd.read_csv(execution_panel_path, usecols=lambda c: c in {"symbol", "entry_ts", "entry_policy", "exit_policy"})
    panel["symbol"] = panel["symbol"].astype(str).str.upper()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    if {"entry_policy", "exit_policy"}.issubset(panel.columns):
        base = panel[panel["entry_policy"].eq("base_delay1d_open") & panel["exit_policy"].eq("existing_exit")].dropna(subset=["entry_ts"]).copy()
    else:
        base = panel.dropna(subset=["entry_ts"]).copy()
    start_date = base["entry_ts"].dt.date.min()
    end_date = base["entry_ts"].dt.date.max()
    rows = []
    for symbol, group in base.groupby("symbol", sort=True):
        rows.append(
            {
                "symbol": symbol,
                "entry_row_count": int(len(group)),
                "first_entry_date": str(group["entry_ts"].dt.date.min()),
                "last_entry_date": str(group["entry_ts"].dt.date.max()),
                "lake_start_date": str(start_date),
                "lake_end_date": str(end_date),
                "source_panel": str(execution_panel_path),
                "assignment_label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_expected_calendar(universe: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    if universe.empty:
        return pd.DataFrame(columns=["symbol", "date"])
    start = pd.Timestamp(universe["lake_start_date"].min()).date()
    end = pd.Timestamp(universe["lake_end_date"].max()).date()
    qqq = pd.read_csv(qqq_path)
    ts_col = "timestamp" if "timestamp" in qqq.columns else qqq.columns[0]
    qqq["date"] = pd.to_datetime(qqq[ts_col], utc=True, errors="coerce").dt.date
    dates = sorted(d for d in qqq["date"].dropna().unique().tolist() if start <= d <= end)
    rows = [{"symbol": symbol, "date": str(day)} for symbol in universe["symbol"].astype(str) for day in dates]
    return pd.DataFrame(rows)


def build_command_plan(universe: pd.DataFrame, *, batch_size: int = 5) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    symbols = universe["symbol"].astype(str).sort_values().tolist()
    if not symbols:
        return pd.DataFrame()
    start = str(universe["lake_start_date"].min())
    end = str(universe["lake_end_date"].max())
    for feed in ["sip"]:
        for batch_id, offset in enumerate(range(0, len(symbols), batch_size), start=1):
            batch = symbols[offset : offset + batch_size]
            command = (
                "python -m src.data.alpaca_full_microstructure_backfill "
                f"--feed {feed} --session regular --chunk-minutes 60 --start-date {start} --end-date {end} "
                f"--symbols {' '.join(batch)} --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_{batch_id:03d}.csv"
            )
            rows.append(
                {
                    "provider": "alpaca",
                    "feed": feed,
                    "batch_id": batch_id,
                    "batch_symbol_count": len(batch),
                    "start_date": start,
                    "end_date": end,
                    "source_types": "quotes,trades",
                    "command": command,
                    "dry_run_command": command + " --dry-run",
                    "secret_in_command_flag": 0,
                    "expected_partition_pattern": "data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet",
                }
            )
    return pd.DataFrame(rows)


def build_raw_catalog(raw_lake_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    paths = sorted(raw_lake_dir.glob("provider=*/feed=*/type=*/symbol=*/date=*/chunk=*.parquet"))
    paths += sorted(raw_lake_dir.glob("provider=*/feed=*/type=*/symbol=*/date=*.parquet"))
    for path in paths:
        parts = parse_partition_path(path)
        try:
            frame = pd.read_parquet(path)
            ts_col = "quote_ts" if parts["source_type"] == "quotes" else "trade_ts"
            bounds = timestamp_bounds(frame, ts_col)
            rows.append(
                {
                    **parts,
                    "path": str(path),
                    "row_count": int(len(frame)),
                    "first_timestamp": bounds[0],
                    "last_timestamp": bounds[1],
                    "sha256": file_hash(path),
                    "schema_columns": "|".join(frame.columns.astype(str).tolist()),
                    "catalog_error": "",
                    "historical_live_ready_flag": 0,
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append({**parts, "path": str(path), "row_count": 0, "first_timestamp": "", "last_timestamp": "", "sha256": "", "schema_columns": "", "catalog_error": str(exc), "historical_live_ready_flag": 0})
    return pd.DataFrame(rows)


def parse_partition_path(path: Path) -> dict[str, str]:
    out = {"provider": "", "feed": "", "source_type": "", "symbol": "", "date": ""}
    for part in path.parts:
        if part.startswith("provider="):
            out["provider"] = part.split("=", 1)[1]
        elif part.startswith("feed="):
            out["feed"] = part.split("=", 1)[1]
        elif part.startswith("type="):
            out["source_type"] = part.split("=", 1)[1]
        elif part.startswith("symbol="):
            out["symbol"] = part.split("=", 1)[1]
        elif part.startswith("date="):
            out["date"] = part.split("=", 1)[1]
    if not out["date"]:
        out["date"] = path.stem.split("date=", 1)[1] if path.stem.startswith("date=") else path.stem
    out["chunk_id"] = path.stem.split("chunk=", 1)[1] if path.stem.startswith("chunk=") else "full_day"
    return out


def build_coverage_audit(expected: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    if expected.empty:
        return pd.DataFrame()
    rows = []
    for source_type in ["quotes", "trades"]:
        scoped = catalog[catalog.get("source_type", pd.Series(dtype=str)).astype(str).eq(source_type)].copy() if not catalog.empty else pd.DataFrame()
        available = set(zip(scoped.get("symbol", pd.Series(dtype=str)).astype(str), scoped.get("date", pd.Series(dtype=str)).astype(str), strict=False))
        expected_pairs = set(zip(expected["symbol"].astype(str), expected["date"].astype(str), strict=False))
        covered = len(expected_pairs & available)
        rows.append(
            {
                "provider": "alpaca",
                "feed": "sip",
                "source_type": source_type,
                "expected_symbol_date_count": int(len(expected_pairs)),
                "covered_symbol_date_count": int(covered),
                "coverage_rate": float(covered / max(len(expected_pairs), 1)),
                "missing_symbol_date_count": int(len(expected_pairs) - covered),
                "missing_treated_as_negative_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_integrity_audit(catalog: pd.DataFrame) -> pd.DataFrame:
    if catalog.empty:
        return pd.DataFrame(
            [
                {
                    "check_name": "raw_partition_catalog_nonempty",
                    "pass_flag": 0,
                    "bad_rows": 0,
                    "observed_value": "0 partitions",
                    "required_value": "raw quote/trade partitions must exist before feature building",
                }
            ]
        )
    rows = []
    rows.append(
        {
            "check_name": "raw_partition_catalog_nonempty",
            "pass_flag": int(len(catalog) > 0),
            "bad_rows": 0,
            "observed_value": f"{len(catalog)} partitions",
            "required_value": "at least one partition for smoke, broad coverage for Task646D",
        }
    )
    rows.append(
        {
            "check_name": "catalog_read_errors_zero",
            "pass_flag": int(catalog["catalog_error"].astype(str).eq("").all()),
            "bad_rows": int(catalog["catalog_error"].astype(str).ne("").sum()),
            "observed_value": f"errors={int(catalog['catalog_error'].astype(str).ne('').sum())}",
            "required_value": "0 catalog read errors",
        }
    )
    rows.append(
        {
            "check_name": "positive_row_partitions",
            "pass_flag": int(pd.to_numeric(catalog["row_count"], errors="coerce").fillna(0).gt(0).all()),
            "bad_rows": int(pd.to_numeric(catalog["row_count"], errors="coerce").fillna(0).le(0).sum()),
            "observed_value": f"empty_partitions={int(pd.to_numeric(catalog['row_count'], errors='coerce').fillna(0).le(0).sum())}",
            "required_value": "all existing partitions should contain rows unless explicitly marked empty in download audit",
        }
    )
    return pd.DataFrame(rows)


def build_query_contract(raw_lake_dir: Path) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "layer_name": "raw_catalog_query_layer",
                "allowed_operation": "list partitions by provider/feed/type/symbol/date",
                "allowed_output": "paths and row metadata",
                "forbidden_operation": "compute continuation or fragile-breakout features",
                "source_path": str(raw_lake_dir),
                "label_used_flag": 0,
                "strategy_assignment_used_flag": 0,
            },
            {
                "layer_name": "raw_partition_reader",
                "allowed_operation": "load exact symbol/date quote or trade parquet rows",
                "allowed_output": "raw normalized quote/trade rows",
                "forbidden_operation": "entry/sizing decision",
                "source_path": str(raw_lake_dir),
                "label_used_flag": 0,
                "strategy_assignment_used_flag": 0,
            },
        ]
    )


def build_pass_fail(universe: pd.DataFrame, coverage: pd.DataFrame, integrity: pd.DataFrame) -> pd.DataFrame:
    quote_cov = coverage.loc[coverage["source_type"].eq("quotes"), "coverage_rate"].iloc[0] if not coverage.empty else 0.0
    trade_cov = coverage.loc[coverage["source_type"].eq("trades"), "coverage_rate"].iloc[0] if not coverage.empty else 0.0
    integrity_pass = int(integrity["pass_flag"].eq(1).all()) if not integrity.empty else 0
    return pd.DataFrame(
        [
            {
                "gate": "universe_scope_defined",
                "pass_flag": int(not universe.empty and universe["symbol"].nunique() > 0),
                "observed_value": f"symbols={0 if universe.empty else universe['symbol'].nunique()}",
                "required_value": "Task646 must define the exact universe and date span before download",
            },
            {
                "gate": "raw_partition_integrity_smoke",
                "pass_flag": integrity_pass,
                "observed_value": f"integrity_pass={integrity_pass}",
                "required_value": "catalog exists and existing partitions read cleanly",
            },
            {
                "gate": "coverage_sufficient_for_feature_builder",
                "pass_flag": int(quote_cov >= 0.80 and trade_cov >= 0.80),
                "observed_value": f"quote_coverage={quote_cov:.4f}; trade_coverage={trade_cov:.4f}",
                "required_value": "Task646D feature builder requires at least 80% quote and 80% trade symbol-date coverage",
            },
            {
                "gate": "no_feature_builder_in_task646c",
                "pass_flag": 1,
                "observed_value": "catalog/query contract only",
                "required_value": "Task646C cannot create continuation or fragile-breakout features",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "data lake build only",
                "required_value": "strategy promotion requires later feature validation and live readiness",
            },
        ]
    )


def build_decision(universe: pd.DataFrame, coverage: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
    quote_cov = coverage.loc[coverage["source_type"].eq("quotes"), "coverage_rate"].iloc[0] if not coverage.empty else 0.0
    trade_cov = coverage.loc[coverage["source_type"].eq("trades"), "coverage_rate"].iloc[0] if not coverage.empty else 0.0
    return pd.DataFrame(
        [
            {
                "decision": "RAW_DATA_LAKE_PLAN_READY_FEATURE_BUILDER_BLOCKED" if gates.get("universe_scope_defined", 0) else "DATA_LAKE_SCOPE_BLOCKED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "universe_symbol_count": int(universe["symbol"].nunique()) if not universe.empty else 0,
                "lake_start_date": "" if universe.empty else str(universe["lake_start_date"].min()),
                "lake_end_date": "" if universe.empty else str(universe["lake_end_date"].max()),
                "quote_coverage_rate": float(quote_cov),
                "trade_coverage_rate": float(trade_cov),
                "feature_builder_allowed_flag": int(gates.get("coverage_sufficient_for_feature_builder", 0)),
                "next_action": "Run Task646 backfill command batches, rebuild catalog and coverage audit, then allow Task646D only after coverage and integrity gates pass.",
            }
        ]
    )


def render_report(
    universe: pd.DataFrame,
    command_plan: pd.DataFrame,
    catalog: pd.DataFrame,
    coverage: pd.DataFrame,
    integrity: pd.DataFrame,
    query_contract: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    dec = decision.iloc[0]
    return "\n".join(
        [
            "# Task646 Full Microstructure Data Lake",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Universe symbols: {int(dec['universe_symbol_count'])}",
            f"- Date span: {dec['lake_start_date']} to {dec['lake_end_date']}",
            f"- Quote coverage: {float(dec['quote_coverage_rate']):.4f}",
            f"- Trade coverage: {float(dec['trade_coverage_rate']):.4f}",
            f"- Feature builder allowed: `{int(dec['feature_builder_allowed_flag'])}`",
            "",
            "## Quant Expert Report",
            "",
            "Task646 corrects the previous entry-window-only approach. It defines a full raw quote/trade data lake, a backfill command plan, a raw catalog, and a catalog/query contract. It does not build continuation features or reconnect to strategy.",
            "",
            "### Universe Scope",
            "",
            table(universe.head(80)),
            "",
            "### Backfill Command Plan",
            "",
            table(command_plan),
            "",
            "### Raw Data Catalog",
            "",
            table(catalog.head(80)),
            "",
            "### Coverage Audit",
            "",
            table(coverage),
            "",
            "### Integrity Audit",
            "",
            table(integrity),
            "",
            "### Query Contract",
            "",
            table(query_contract),
            "",
            "### Pass/Fail Matrix",
            "",
            table(pass_fail),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- 이번 작업은 매매 룰이 아닙니다.",
            "- 먼저 전체 호가/거래 데이터 창고를 만드는 작업입니다.",
            "- 646C는 feature가 아니라 catalog/query까지만 허용합니다.",
            "- coverage가 충분해지기 전에는 `real_continuation`이나 `fragile_breakout`을 다시 만들면 안 됩니다.",
            "",
            "## Operational Update",
            "",
            "- 2026-06-08: The live Task646 backfill runner was upgraded from a single worker to 3 bounded workers.",
            "- The runner now uses one shared request rate limiter set to 150 requests per minute by default.",
            "- Existing chunk files are still skipped, failed chunks remain retryable on rerun, and audit rows are written after each partition.",
            "- This changes download throughput only. It does not promote any trading strategy or allow Task646D features before coverage gates pass.",
            "",
            "## Artifact Manifest",
            "",
            "- `task_646_gpt_design_packet.txt`",
            "- `task_646_gpt_design_response.md`",
            "- `task_646_universe_scope.csv`",
            "- `task_646_backfill_command_plan.csv`",
            "- `task_646_raw_data_catalog.csv`",
            "- `task_646_coverage_audit.csv`",
            "- `task_646_integrity_audit.csv`",
            "- `task_646_catalog_query_contract.csv`",
            "- `task_646_pass_fail_matrix.csv`",
            "- `task_646_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
        ]
    )


def timestamp_bounds(frame: pd.DataFrame, timestamp_column: str) -> tuple[str, str]:
    if frame.empty or timestamp_column not in frame.columns:
        return "", ""
    ts = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce").dropna()
    if ts.empty:
        return "", ""
    return ts.min().isoformat().replace("+00:00", "Z"), ts.max().isoformat().replace("+00:00", "Z")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    safe = frame.copy().where(pd.notna(frame), "")
    columns = [str(column) for column in safe.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in safe.astype(str).to_dict(orient="records"):
        lines.append("| " + " | ".join(row[column] for column in safe.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--raw-lake-dir", type=Path, default=RAW_LAKE_DIR)
    args = parser.parse_args()
    build_task646_full_microstructure_data_lake(out_dir=args.out_dir, raw_lake_dir=args.raw_lake_dir)


if __name__ == "__main__":
    main()
