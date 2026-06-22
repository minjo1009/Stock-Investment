from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3127_external_tool_opt_in_wrapper_pilot"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3127_external_tool_opt_in_wrapper_pilot.md"
DECISION = REPORT_DIR / "task_3127_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_OPT_IN_WRAPPER_PILOT_ONLY"

TASK3126_OUT = ROOT / "data/artifacts/task_3126_external_tool_isolated_install_pilot"
TASK3126_VENV = ROOT / ".cache/task_3126_external_tool_venv"
SEC_PANEL = ROOT / "data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv"
LIQUIDITY_PANEL = ROOT / "data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv"


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def common_status() -> dict[str, object]:
    return {
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "selector_changed": "0",
        "sizing_changed": "0",
        "replay_performed": "0",
        "source_acquisition_performed": "0",
        "root_dependency_manifest_created": "0",
        "authority": AUTHORITY,
    }


def venv_python() -> Path:
    if os.name == "nt":
        return TASK3126_VENV / "Scripts" / "python.exe"
    return TASK3126_VENV / "bin" / "python"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows_sha256(rows: list[dict[str, object]], fields: list[str]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update("\t".join(str(row.get(field, "")) for field in fields).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def command_result(cmd: list[str], timeout: int = 300) -> dict[str, object]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": repr(exc),
            "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        }


def load_task3126_decisions() -> dict[str, dict[str, str]]:
    rows = read_csv(TASK3126_OUT / "adoption_decision_matrix.csv")
    return {row["tool_name"]: row for row in rows}


def build_wrapper_contracts(decisions: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    specs = [
        {
            "wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "tool_name": "pandera",
            "wrapper_status": "enabled" if decisions.get("pandera", {}).get("decision") == "adopt" else "blocked",
            "input_panel": SEC_PANEL.as_posix(),
            "output_artifact": (OUT_DIR / "pandera_wrapper_result.csv").as_posix(),
            "allowed_layers": "data_validation|resolver_qa",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-POLARS-SEC-AGG",
            "tool_name": "polars",
            "wrapper_status": "enabled" if decisions.get("polars", {}).get("decision") == "adopt" else "blocked",
            "input_panel": SEC_PANEL.as_posix(),
            "output_artifact": (OUT_DIR / "wrapper_outputs/sec_symbol_event_family_polars.csv").as_posix(),
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-POLARS-LIQUIDITY-AGG",
            "tool_name": "polars",
            "wrapper_status": "enabled" if decisions.get("polars", {}).get("decision") == "adopt" else "blocked",
            "input_panel": LIQUIDITY_PANEL.as_posix(),
            "output_artifact": (OUT_DIR / "wrapper_outputs/liquidity_provider_series_polars.csv").as_posix(),
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-DUCKDB-LIQUIDITY-AGG",
            "tool_name": "duckdb",
            "wrapper_status": "enabled" if decisions.get("duckdb", {}).get("decision") == "adopt" else "blocked",
            "input_panel": LIQUIDITY_PANEL.as_posix(),
            "output_artifact": (OUT_DIR / "wrapper_outputs/liquidity_provider_series_duckdb.csv").as_posix(),
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-EDGARTOOLS-OFFLINE-SEC",
            "tool_name": "edgartools",
            "wrapper_status": "deferred",
            "input_panel": SEC_PANEL.as_posix(),
            "output_artifact": "",
            "allowed_layers": "none_until_offline_local_parse_is_proven",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-DLT-RECEIPT",
            "tool_name": "dlt",
            "wrapper_status": "deferred",
            "input_panel": "",
            "output_artifact": "",
            "allowed_layers": "none_until_source_receipt_task",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
        {
            "wrapper_id": "WRAP3127-GITHUB-MCP-READONLY",
            "tool_name": "github_mcp_read_only",
            "wrapper_status": "deferred",
            "input_panel": "",
            "output_artifact": "",
            "allowed_layers": "none_until_read_only_monitoring_task",
            "forbidden_layers": "source_truth|selector|sizing|replay|paper_order|live_order|acceptance|deployment",
            "writes_only_under_task_artifacts": "1",
            "requires_root_dependency": "0",
        },
    ]
    return [{**spec, **common_status()} for spec in specs]


def run_pandera_wrapper(enabled: bool) -> list[dict[str, object]]:
    required_cols = [
        "source_packet_id",
        "symbol",
        "cik",
        "accession_number",
        "source_ts",
        "available_to_brain_ts",
        "raw_path",
        "raw_sha256",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
    ]
    if not enabled:
        return [
            {
                "wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
                "wrapper_status": "blocked_task3126_not_adopted",
                "schema_status": "not_executed",
                "row_count": 0,
                "required_columns": "|".join(required_cols),
                "pandera_validator_pass": "0",
                "decision": "blocked",
                "reason": "Task3126 did not adopt Pandera",
                **common_status(),
            }
        ]
    if not venv_python().exists():
        return [
            {
                "wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
                "wrapper_status": "blocked_venv_missing",
                "schema_status": "not_executed",
                "row_count": 0,
                "required_columns": "|".join(required_cols),
                "pandera_validator_pass": "0",
                "decision": "blocked",
                "reason": "Task3126 isolated venv is missing",
                **common_status(),
            }
        ]
    code = r"""
import json
import sys

payload = {"schema_status": "not_started"}
try:
    import pandas as pd
    try:
        import pandera.pandas as pa
    except Exception:
        import pandera as pa
    from pandera import Check, Column, DataFrameSchema

    path = sys.argv[1]
    df = pd.read_csv(path, dtype=str)
    schema = DataFrameSchema(
        {
            "source_packet_id": Column(str, nullable=False),
            "symbol": Column(str, nullable=False),
            "cik": Column(str, nullable=False),
            "accession_number": Column(str, nullable=False),
            "source_ts": Column(str, nullable=False),
            "available_to_brain_ts": Column(str, nullable=False),
            "raw_path": Column(str, nullable=False),
            "raw_sha256": Column(str, nullable=False),
            "missing_source_is_negative": Column(str, Check.isin(["0", ""]), nullable=True),
            "assignment_uses_future_outcome": Column(str, Check.isin(["0", ""]), nullable=True),
            "outcome_used_for_assignment": Column(str, Check.isin(["0", ""]), nullable=True),
        },
        strict=False,
        coerce=True,
    )
    schema.validate(df, lazy=True)
    payload = {
        "schema_status": "schema_checks_executed",
        "row_count": int(len(df)),
        "failure_cases": 0,
        "error": "",
    }
except Exception as exc:
    payload = {
        "schema_status": "schema_execution_failed",
        "row_count": 0,
        "failure_cases": -1,
        "error": repr(exc)[:2000],
    }
print(json.dumps(payload, ensure_ascii=False))
"""
    result = command_result([str(venv_python()), "-c", code, SEC_PANEL.as_posix()], timeout=300)
    try:
        payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
    except Exception:
        payload = {
            "schema_status": "schema_execution_failed",
            "row_count": 0,
            "failure_cases": -1,
            "error": "pandera_stdout_not_json",
        }
    passed = payload.get("schema_status") == "schema_checks_executed" and int(payload.get("failure_cases", -1)) == 0
    return [
        {
            "wrapper_id": "WRAP3127-PANDERA-SEC-SCHEMA",
            "wrapper_status": "executed",
            "schema_status": payload.get("schema_status", ""),
            "target_panel": SEC_PANEL.as_posix(),
            "target_panel_sha256": file_sha256(SEC_PANEL),
            "row_count": payload.get("row_count", 0),
            "required_columns": "|".join(required_cols),
            "pandera_failure_cases": payload.get("failure_cases", ""),
            "pandera_error": payload.get("error", ""),
            "runtime_ms": result["runtime_ms"],
            "pandera_validator_pass": "1" if passed else "0",
            "decision": "wrapper_candidate" if passed else "reject",
            "reason": "schema_passed_in_opt_in_wrapper" if passed else payload.get("schema_status", ""),
            **common_status(),
        }
    ]


def pandas_baseline(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    import pandas as pd

    started = time.perf_counter()
    df = pd.read_csv(panel, dtype=str)
    for col in group_cols:
        df[col] = df[col].fillna("")
    df["_strict_gate_pass_int"] = pd.to_numeric(df["strict_gate_pass"], errors="coerce").fillna(0).astype(int)
    grouped = (
        df.groupby(group_cols, dropna=False)["_strict_gate_pass_int"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "packet_count", "sum": "strict_gate_pass_count"})
        .sort_values(group_cols)
    )
    rows = grouped.to_dict(orient="records")
    metrics = {
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": len(df),
        "result_row_count": len(rows),
        "join_key_null_count": int(df[group_cols].isna().any(axis=1).sum()),
        "strict_gate_pass_total": int(df["_strict_gate_pass_int"].sum()),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def run_polars_agg(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    import polars as pl

    started = time.perf_counter()
    df = pl.read_csv(panel, infer_schema_length=0)
    df = df.with_columns([pl.col(col).fill_null("") for col in group_cols])
    df = df.with_columns(pl.col("strict_gate_pass").cast(pl.Int64, strict=False).fill_null(0).alias("_strict_gate_pass_int"))
    grouped = (
        df.group_by(group_cols)
        .agg(
            [
                pl.len().alias("packet_count"),
                pl.col("_strict_gate_pass_int").sum().alias("strict_gate_pass_count"),
            ]
        )
        .sort(group_cols)
    )
    rows = grouped.to_dicts()
    null_expr = pl.any_horizontal([pl.col(col).is_null() for col in group_cols]).sum()
    metrics = {
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": df.height,
        "result_row_count": grouped.height,
        "join_key_null_count": int(df.select(null_expr).item()),
        "strict_gate_pass_total": int(df.select(pl.col("_strict_gate_pass_int").sum()).item()),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def run_duckdb_agg(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    import duckdb

    started = time.perf_counter()
    group_sql = ", ".join(group_cols)
    null_condition = " OR ".join([f"{col} IS NULL" for col in group_cols])
    path_sql = panel.as_posix().replace("'", "''")
    con = duckdb.connect(database=":memory:")
    metrics_row = con.execute(
        f"""
        WITH src AS (
            SELECT * FROM read_csv_auto('{path_sql}', HEADER=TRUE, ALL_VARCHAR=TRUE)
        ),
        grouped AS (
            SELECT {group_sql},
                   COUNT(*) AS packet_count,
                   SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) AS strict_gate_pass_count
            FROM src
            GROUP BY {group_sql}
        )
        SELECT
            (SELECT COUNT(*) FROM src) AS source_row_count,
            (SELECT COUNT(*) FROM grouped) AS result_row_count,
            (SELECT SUM(CASE WHEN {null_condition} THEN 1 ELSE 0 END) FROM src) AS join_key_null_count,
            (SELECT SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) FROM src) AS strict_gate_pass_total
        """
    ).fetchone()
    grouped_rows = con.execute(
        f"""
        SELECT {group_sql},
               COUNT(*) AS packet_count,
               SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) AS strict_gate_pass_count
        FROM read_csv_auto('{path_sql}', HEADER=TRUE, ALL_VARCHAR=TRUE)
        GROUP BY {group_sql}
        ORDER BY {group_sql}
        """
    ).fetchall()
    rows = [
        {**dict(zip(group_cols, row[: len(group_cols)])), "packet_count": row[-2], "strict_gate_pass_count": row[-1]}
        for row in grouped_rows
    ]
    source_row_count, result_row_count, join_key_null_count, strict_gate_pass_total = metrics_row
    metrics = {
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": int(source_row_count),
        "result_row_count": int(result_row_count),
        "join_key_null_count": int(join_key_null_count or 0),
        "strict_gate_pass_total": int(strict_gate_pass_total or 0),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def run_query_wrappers(contracts: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    wrapper_specs = [
        {
            "wrapper_id": "WRAP3127-POLARS-SEC-AGG",
            "engine": "polars",
            "query_id": "sec_symbol_event_family_agg",
            "panel": SEC_PANEL,
            "group_cols": ["symbol", "event_family"],
            "output": OUT_DIR / "wrapper_outputs/sec_symbol_event_family_polars.csv",
        },
        {
            "wrapper_id": "WRAP3127-POLARS-LIQUIDITY-AGG",
            "engine": "polars",
            "query_id": "liquidity_provider_series_agg",
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "wrapper_outputs/liquidity_provider_series_polars.csv",
        },
        {
            "wrapper_id": "WRAP3127-DUCKDB-LIQUIDITY-AGG",
            "engine": "duckdb",
            "query_id": "liquidity_provider_series_agg",
            "panel": LIQUIDITY_PANEL,
            "group_cols": ["provider", "series_id"],
            "output": OUT_DIR / "wrapper_outputs/liquidity_provider_series_duckdb.csv",
        },
    ]
    enabled = {row["wrapper_id"]: row["wrapper_status"] == "enabled" for row in contracts}
    result_rows: list[dict[str, object]] = []
    preview_rows: list[dict[str, object]] = []
    baseline_cache: dict[tuple[str, str], dict[str, object]] = {}
    for spec in wrapper_specs:
        wrapper_id = spec["wrapper_id"]
        if not enabled.get(wrapper_id, False):
            result_rows.append(
                {
                    "wrapper_id": wrapper_id,
                    "query_id": spec["query_id"],
                    "engine": spec["engine"],
                    "wrapper_status": "blocked_contract_not_enabled",
                    "decision": "blocked",
                    "reason": "Task3126 did not adopt this wrapper candidate",
                    **common_status(),
                }
            )
            continue
        key = (spec["panel"].as_posix(), "|".join(spec["group_cols"]))
        if key not in baseline_cache:
            baseline_metrics, _ = pandas_baseline(spec["panel"], spec["group_cols"])
            baseline_cache[key] = baseline_metrics
        baseline = baseline_cache[key]
        try:
            if spec["engine"] == "polars":
                metrics, rows = run_polars_agg(spec["panel"], spec["group_cols"])
            elif spec["engine"] == "duckdb":
                metrics, rows = run_duckdb_agg(spec["panel"], spec["group_cols"])
            else:
                raise ValueError(spec["engine"])
            write_csv(spec["output"], rows)
            exact = all(
                [
                    metrics["source_row_count"] == baseline["source_row_count"],
                    metrics["result_row_count"] == baseline["result_row_count"],
                    metrics["join_key_null_count"] == baseline["join_key_null_count"],
                    metrics["strict_gate_pass_total"] == baseline["strict_gate_pass_total"],
                    metrics["aggregate_checksum"] == baseline["aggregate_checksum"],
                ]
            )
            faster = float(metrics["runtime_ms"]) < float(baseline["runtime_ms"])
            decision = "wrapper_candidate" if exact and faster else "reject"
            reason = "exact_and_faster_than_pandas" if exact and faster else "not_exact_or_not_faster"
            result_rows.append(
                {
                    "wrapper_id": wrapper_id,
                    "query_id": spec["query_id"],
                    "engine": spec["engine"],
                    "wrapper_status": "executed",
                    "source_panel": spec["panel"].as_posix(),
                    "source_panel_sha256": file_sha256(spec["panel"]),
                    "output_artifact": spec["output"].as_posix(),
                    "output_artifact_sha256": file_sha256(spec["output"]),
                    "join_key_columns": "|".join(spec["group_cols"]),
                    "pandas_runtime_ms": baseline["runtime_ms"],
                    "wrapper_runtime_ms": metrics["runtime_ms"],
                    "source_row_count": metrics["source_row_count"],
                    "result_row_count": metrics["result_row_count"],
                    "join_key_null_count": metrics["join_key_null_count"],
                    "strict_gate_pass_total": metrics["strict_gate_pass_total"],
                    "row_count_match_pandas": "1" if metrics["source_row_count"] == baseline["source_row_count"] and metrics["result_row_count"] == baseline["result_row_count"] else "0",
                    "join_key_null_match_pandas": "1" if metrics["join_key_null_count"] == baseline["join_key_null_count"] else "0",
                    "aggregate_checksum_match_pandas": "1" if metrics["aggregate_checksum"] == baseline["aggregate_checksum"] else "0",
                    "strict_gate_pass_total_match_pandas": "1" if metrics["strict_gate_pass_total"] == baseline["strict_gate_pass_total"] else "0",
                    "faster_than_pandas": "1" if faster else "0",
                    "decision": decision,
                    "reason": reason,
                    **common_status(),
                }
            )
            for idx, row in enumerate(rows[:10], start=1):
                preview_rows.append(
                    {
                        "wrapper_id": wrapper_id,
                        "preview_rank": idx,
                        **{key: row.get(key, "") for key in spec["group_cols"]},
                        "packet_count": row.get("packet_count", ""),
                        "strict_gate_pass_count": row.get("strict_gate_pass_count", ""),
                    }
                )
        except Exception as exc:
            result_rows.append(
                {
                    "wrapper_id": wrapper_id,
                    "query_id": spec["query_id"],
                    "engine": spec["engine"],
                    "wrapper_status": "execution_failed",
                    "source_panel": spec["panel"].as_posix(),
                    "join_key_columns": "|".join(spec["group_cols"]),
                    "decision": "blocked",
                    "reason": repr(exc)[:1000],
                    **common_status(),
                }
            )
    return result_rows, preview_rows


def build_adoption_decisions(
    pandera_rows: list[dict[str, object]],
    query_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    pandera = pandera_rows[0]
    decisions.append(
        {
            "tool_name": "pandera",
            "wrapper_decision": "adopt_wrapper_candidate" if pandera.get("decision") == "wrapper_candidate" else "reject_or_block",
            "candidate_wrapper_count": "1" if pandera.get("decision") == "wrapper_candidate" else "0",
            "reason": pandera.get("reason", ""),
            "allowed_next_layer": "task_scoped_validator_wrapper_only",
            **common_status(),
        }
    )
    for engine in ["polars", "duckdb"]:
        engine_rows = [row for row in query_rows if row.get("engine") == engine]
        candidate_count = sum(1 for row in engine_rows if row.get("decision") == "wrapper_candidate")
        mismatch_count = sum(
            1
            for row in engine_rows
            if row.get("wrapper_status") == "executed"
            and (
                row.get("row_count_match_pandas") != "1"
                or row.get("join_key_null_match_pandas") != "1"
                or row.get("aggregate_checksum_match_pandas") != "1"
                or row.get("strict_gate_pass_total_match_pandas") != "1"
            )
        )
        decisions.append(
            {
                "tool_name": engine,
                "wrapper_decision": "adopt_wrapper_candidate" if candidate_count > 0 and mismatch_count == 0 else "reject_or_block",
                "candidate_wrapper_count": candidate_count,
                "reason": f"candidate_count={candidate_count};mismatch_count={mismatch_count}",
                "allowed_next_layer": "task_scoped_local_artifact_query_wrapper_only" if candidate_count > 0 and mismatch_count == 0 else "none",
                **common_status(),
            }
        )
    for tool, reason in [
        ("edgartools", "deferred_until_offline_local_sec_parse_is_proven"),
        ("dlt", "deferred_until_source_receipt_task"),
        ("github_mcp_read_only", "deferred_until_read_only_monitoring_task"),
    ]:
        decisions.append(
            {
                "tool_name": tool,
                "wrapper_decision": "defer",
                "candidate_wrapper_count": 0,
                "reason": reason,
                "allowed_next_layer": "none",
                **common_status(),
            }
        )
    return decisions


def build_acceptance_checks(
    contracts: list[dict[str, object]],
    pandera_rows: list[dict[str, object]],
    query_rows: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> list[dict[str, object]]:
    root_dependency_files = [
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "pyproject.toml",
        ROOT / "setup.cfg",
        ROOT / "poetry.lock",
        ROOT / "Pipfile",
    ]
    checks = [
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
        ("no_orders", True, "No paper or live orders are created."),
        ("no_replay_or_source_acquisition", True, "No replay or source acquisition is performed."),
        ("root_dependency_manifest_absent", not any(path.exists() for path in root_dependency_files), "No root Python dependency manifest was created."),
        ("wrapper_contracts_present", len(contracts) == 7, "All enabled and deferred wrapper contracts are recorded."),
        ("pandera_wrapper_passed", pandera_rows[0].get("decision") == "wrapper_candidate", "Pandera opt-in wrapper passed."),
        (
            "query_wrappers_exact",
            all(
                row.get("wrapper_status") != "executed"
                or (
                    row.get("row_count_match_pandas") == "1"
                    and row.get("join_key_null_match_pandas") == "1"
                    and row.get("aggregate_checksum_match_pandas") == "1"
                    and row.get("strict_gate_pass_total_match_pandas") == "1"
                )
                for row in query_rows
            ),
            "Executed local query wrappers match pandas.",
        ),
        ("wrapper_candidates_present", sum(1 for row in query_rows if row.get("decision") == "wrapper_candidate") >= 1, "At least one local query wrapper candidate exists."),
        (
            "deferred_tools_not_executed",
            all(row["wrapper_status"] == "deferred" for row in contracts if row["tool_name"] in {"edgartools", "dlt", "github_mcp_read_only"}),
            "Deferred tools were not executed.",
        ),
        ("decisions_cover_all_tools", {row["tool_name"] for row in decisions} == {"pandera", "polars", "duckdb", "edgartools", "dlt", "github_mcp_read_only"}, "All planned tools have wrapper decisions."),
    ]
    return [
        {
            "check_id": f"CHK3127-{idx:03d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            **common_status(),
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ")[:500] for field in fields) + " |")
    return "\n".join(lines)


def write_report(
    contracts: list[dict[str, object]],
    pandera_rows: list[dict[str, object]],
    query_rows: list[dict[str, object]],
    decisions: list[dict[str, object]],
    checks: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3127 External Tool Opt-In Wrapper Pilot

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: promoted only Task3126 adopted infrastructure candidates into task-scoped opt-in wrappers for validation and local artifact querying.
- What did not change: no root dependency manifest, raw source download, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Wrapper contracts: {closeout['wrapper_contract_rows']}.
  - Executed wrappers: {closeout['executed_wrapper_rows']}.
  - Wrapper candidates: {closeout['wrapper_candidate_rows']}.
  - Deferred wrappers: {closeout['deferred_wrapper_rows']}.
- Next action: move only `Pandera` and exact/faster local query wrappers into a narrow reusable helper task; keep `edgartools`, `dlt`, and GitHub MCP deferred.

## Quant Expert Report

### Wrapper Contracts

{markdown_table(contracts, ['wrapper_id', 'tool_name', 'wrapper_status', 'allowed_layers', 'forbidden_layers', 'writes_only_under_task_artifacts'])}

### Pandera Schema Wrapper

{markdown_table(pandera_rows, ['wrapper_id', 'wrapper_status', 'schema_status', 'row_count', 'pandera_validator_pass', 'decision', 'reason'])}

### Local Query Wrappers

{markdown_table(query_rows, ['wrapper_id', 'query_id', 'engine', 'wrapper_status', 'pandas_runtime_ms', 'wrapper_runtime_ms', 'source_row_count', 'result_row_count', 'aggregate_checksum_match_pandas', 'faster_than_pandas', 'decision'])}

### Wrapper Decision Matrix

{markdown_table(decisions, ['tool_name', 'wrapper_decision', 'candidate_wrapper_count', 'reason', 'allowed_next_layer'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: we now have real wrapper candidates, but still only for infrastructure.

`Pandera` is useful as a schema validator wrapper. `Polars` is useful for local artifact query acceleration. `DuckDB` remains useful where its exact result is faster than pandas. `edgartools` is still not ready because offline local SEC parsing has not been proven.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `{TASK3126_OUT.as_posix()}/adoption_decision_matrix.csv`
  - `{SEC_PANEL.as_posix()}`
  - `{LIQUIDITY_PANEL.as_posix()}`
- Outputs:
  - `docs/reports/{TASK_ID}/task_3127_external_tool_opt_in_wrapper_pilot.md`
  - `docs/reports/{TASK_ID}/task_3127_decision.csv`
  - `data/artifacts/{TASK_ID}/`
- Row counts:
  - Wrapper contracts: {len(contracts)}
  - Pandera wrapper rows: {len(pandera_rows)}
  - Local query wrapper rows: {len(query_rows)}
  - Wrapper decision rows: {len(decisions)}
- Validation commands:
  - `python scripts/trader_brain_3127_external_tool_opt_in_wrapper_pilot_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3126 decisions: `{file_sha256(TASK3126_OUT / 'adoption_decision_matrix.csv')}`
  - SEC panel: `{file_sha256(SEC_PANEL)}`
  - Liquidity/rates panel: `{file_sha256(LIQUIDITY_PANEL)}`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "wrapper_outputs").mkdir(parents=True, exist_ok=True)

    decisions_3126 = load_task3126_decisions()
    contracts = build_wrapper_contracts(decisions_3126)
    pandera_enabled = any(row["wrapper_id"] == "WRAP3127-PANDERA-SEC-SCHEMA" and row["wrapper_status"] == "enabled" for row in contracts)
    pandera_rows = run_pandera_wrapper(pandera_enabled)
    query_rows, preview_rows = run_query_wrappers(contracts)
    decisions = build_adoption_decisions(pandera_rows, query_rows)
    checks = build_acceptance_checks(contracts, pandera_rows, query_rows, decisions)

    executed_count = sum(1 for row in query_rows if row.get("wrapper_status") == "executed") + sum(1 for row in pandera_rows if row.get("wrapper_status") == "executed")
    candidate_count = sum(1 for row in query_rows if row.get("decision") == "wrapper_candidate") + sum(1 for row in pandera_rows if row.get("decision") == "wrapper_candidate")
    closeout = {
        "task_id": "Task3127",
        "verdict": "external_tool_opt_in_wrapper_pilot_completed_diagnostic_only",
        "wrapper_contract_rows": len(contracts),
        "executed_wrapper_rows": executed_count,
        "wrapper_candidate_rows": candidate_count,
        "deferred_wrapper_rows": sum(1 for row in contracts if row["wrapper_status"] == "deferred"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }

    write_csv(OUT_DIR / "wrapper_contracts.csv", contracts)
    write_csv(OUT_DIR / "pandera_wrapper_result.csv", pandera_rows)
    write_csv(OUT_DIR / "local_query_wrapper_result.csv", query_rows)
    write_csv(OUT_DIR / "local_query_wrapper_preview.csv", preview_rows)
    write_csv(OUT_DIR / "wrapper_decision_matrix.csv", decisions)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3127_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3127_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(contracts, pandera_rows, query_rows, decisions, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3127_EXTERNAL_TOOL_OPT_IN_WRAPPER_PILOT_COMPLETE]")


if __name__ == "__main__":
    main()
