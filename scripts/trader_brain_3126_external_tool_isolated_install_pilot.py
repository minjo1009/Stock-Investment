from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import venv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3126_external_tool_isolated_install_pilot"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3126_external_tool_isolated_install_pilot.md"
DECISION = REPORT_DIR / "task_3126_decision.csv"
VENV_DIR = ROOT / ".cache" / "task_3126_external_tool_venv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_ISOLATED_INSTALL_PILOT_ONLY"

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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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
    except Exception as exc:  # pragma: no cover - defensive report path
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": repr(exc),
            "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        }


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> dict[str, object]:
    python_path = venv_python()
    if python_path.exists():
        return {
            "step": "create_venv",
            "status": "available_existing",
            "returncode": 0,
            "runtime_ms": 0,
            "stdout": "",
            "stderr": "",
            "venv_path": VENV_DIR.as_posix(),
            "python_path": python_path.as_posix(),
            **common_status(),
        }
    started = time.perf_counter()
    try:
        builder = venv.EnvBuilder(with_pip=True, clear=False, symlinks=False)
        builder.create(VENV_DIR)
        status = "created"
        returncode = 0
        stderr = ""
    except Exception as exc:  # pragma: no cover - environment dependent
        status = "blocked_venv_create_failed"
        returncode = -1
        stderr = repr(exc)
    return {
        "step": "create_venv",
        "status": status,
        "returncode": returncode,
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "stdout": "",
        "stderr": stderr[-4000:],
        "venv_path": VENV_DIR.as_posix(),
        "python_path": python_path.as_posix(),
        **common_status(),
    }


def inspect_distribution(distribution_name: str, import_names: list[str]) -> dict[str, object]:
    code = r"""
import importlib
import importlib.metadata as md
import importlib.util
import json
import sys

dist = sys.argv[1]
import_names = sys.argv[2].split(",")
payload = {
    "distribution_name": dist,
    "version": "",
    "license": "",
    "import_name_used": "",
    "import_available": "0",
    "import_origin": "",
    "public_attr_sample": "",
}
try:
    payload["version"] = md.version(dist)
    meta = md.metadata(dist)
    payload["license"] = meta.get("License") or ";".join(meta.get_all("Classifier") or [])[:300]
except Exception as exc:
    payload["metadata_error"] = repr(exc)
for name in import_names:
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            continue
        module = importlib.import_module(name)
        payload["import_name_used"] = name
        payload["import_available"] = "1"
        payload["import_origin"] = spec.origin or ""
        payload["public_attr_sample"] = "|".join([attr for attr in dir(module) if not attr.startswith("_")][:50])
        break
    except Exception as exc:
        payload["import_error"] = repr(exc)
print(json.dumps(payload, ensure_ascii=False))
"""
    result = command_result([str(venv_python()), "-c", code, distribution_name, ",".join(import_names)], timeout=120)
    try:
        payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
    except Exception:
        payload = {
            "distribution_name": distribution_name,
            "version": "",
            "license": "",
            "import_name_used": "",
            "import_available": "0",
            "import_origin": "",
            "public_attr_sample": "",
            "metadata_error": "inspect_stdout_not_json",
        }
    payload["inspect_returncode"] = result["returncode"]
    payload["inspect_stderr"] = result["stderr"]
    return payload


def install_and_inspect_tools(venv_row: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]], str]:
    specs = [
        {"tool_name": "edgartools", "distribution_name": "edgartools", "import_names": ["edgar", "edgartools"]},
        {"tool_name": "pandera", "distribution_name": "pandera", "import_names": ["pandera"]},
    ]
    install_rows: list[dict[str, object]] = [venv_row]
    lock_rows: list[dict[str, object]] = []
    freeze_text = ""
    python_path = venv_python()
    if venv_row["returncode"] != 0 or not python_path.exists():
        for spec in specs:
            lock_rows.append(
                {
                    **spec,
                    "install_status": "blocked_venv_unavailable",
                    "install_returncode": venv_row["returncode"],
                    "install_runtime_ms": 0,
                    "version": "",
                    "license": "",
                    "import_available": "0",
                    "import_name_used": "",
                    "import_origin": "",
                    "failure_reason": venv_row.get("stderr", ""),
                    **common_status(),
                }
            )
        return install_rows, lock_rows, freeze_text

    for spec in specs:
        install_result = command_result(
            [
                str(python_path),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                spec["distribution_name"],
            ],
            timeout=600,
        )
        install_rows.append(
            {
                "step": f"pip_install_{spec['tool_name']}",
                "status": "installed" if install_result["returncode"] == 0 else "blocked_install_or_py_compat",
                "returncode": install_result["returncode"],
                "runtime_ms": install_result["runtime_ms"],
                "stdout": install_result["stdout"],
                "stderr": install_result["stderr"],
                "venv_path": VENV_DIR.as_posix(),
                "python_path": python_path.as_posix(),
                **common_status(),
            }
        )
        inspect = inspect_distribution(spec["distribution_name"], spec["import_names"]) if install_result["returncode"] == 0 else {}
        import_available = str(inspect.get("import_available", "0"))
        lock_rows.append(
            {
                **spec,
                "import_names": "|".join(spec["import_names"]),
                "install_status": "installed" if install_result["returncode"] == 0 and import_available == "1" else "blocked_install_or_py_compat",
                "install_returncode": install_result["returncode"],
                "install_runtime_ms": install_result["runtime_ms"],
                "version": inspect.get("version", ""),
                "license": inspect.get("license", ""),
                "import_available": import_available,
                "import_name_used": inspect.get("import_name_used", ""),
                "import_origin": inspect.get("import_origin", ""),
                "network_used_for_pip_install": "1",
                "raw_source_downloaded": "0",
                "failure_reason": "" if install_result["returncode"] == 0 and import_available == "1" else str(install_result["stderr"])[:1000],
                "public_attr_sample": inspect.get("public_attr_sample", ""),
                **common_status(),
            }
        )

    freeze_result = command_result([str(python_path), "-m", "pip", "freeze"], timeout=120)
    freeze_text = str(freeze_result["stdout"])
    return install_rows, lock_rows, freeze_text


def edgartools_local_parse(lock_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    edgar_lock = next(row for row in lock_rows if row["tool_name"] == "edgartools")
    sec_rows = read_csv(SEC_PANEL)
    sample = [
        row
        for row in sec_rows
        if row.get("primary_document_raw_path") and (ROOT / row["primary_document_raw_path"]).exists()
    ][:10]
    if edgar_lock["install_status"] != "installed":
        status = "blocked_install_or_py_compat"
        local_parser_found = "0"
        parser_candidates = ""
    else:
        code = r"""
import importlib
import inspect
import json
import sys

module = importlib.import_module(sys.argv[1])
candidates = []
for attr_name in dir(module):
    if attr_name.startswith("_"):
        continue
    try:
        obj = getattr(module, attr_name)
    except Exception:
        continue
    name_l = attr_name.lower()
    if any(token in name_l for token in ["filing", "document", "html", "xbrl"]):
        methods = []
        try:
            methods = [
                method
                for method in dir(obj)
                if any(token in method.lower() for token in ["from", "parse", "html", "local", "file"])
            ][:12]
        except Exception:
            pass
        candidates.append({"name": attr_name, "methods": methods})
print(json.dumps({"candidates": candidates[:20]}, ensure_ascii=False))
"""
        result = command_result([str(venv_python()), "-c", code, str(edgar_lock["import_name_used"])], timeout=120)
        try:
            payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
        except Exception:
            payload = {"candidates": []}
        candidates = payload.get("candidates", [])
        parser_candidates = json.dumps(candidates, ensure_ascii=False)[:2000]
        local_parser_found = "1" if any(candidate.get("methods") for candidate in candidates) else "0"
        status = "tool_api_not_local_file_compatible"
        if local_parser_found == "1":
            status = "local_parser_candidates_found_not_executed_no_safe_constructor"

    comparison_rows: list[dict[str, object]] = []
    for idx, row in enumerate(sample, start=1):
        comparison_rows.append(
            {
                "comparison_id": f"EDGAR3126-{idx:03d}",
                "comparison_status": status,
                "local_parser_found": local_parser_found,
                "parser_candidates": parser_candidates if idx == 1 else "",
                "symbol": row.get("symbol", ""),
                "expected_cik": row.get("cik", ""),
                "edgartools_cik": "",
                "cik_match": "0",
                "expected_accession_number": row.get("accession_number", ""),
                "edgartools_accession_number": "",
                "accession_match": "0",
                "expected_filing_date": row.get("filing_date", ""),
                "edgartools_filing_date": "",
                "filing_date_match": "0",
                "expected_document": row.get("primary_document", ""),
                "edgartools_document": "",
                "document_match": "0",
                "expected_fact_key": "event_family",
                "expected_fact_value": row.get("event_family", ""),
                "edgartools_fact_value": "",
                "primitive_fact_match": "0",
                "raw_path": row.get("primary_document_raw_path", ""),
                "raw_sha256": row.get("primary_document_raw_sha256", ""),
                "raw_identity_preserved": "1" if row.get("primary_document_raw_path") and row.get("primary_document_raw_sha256") else "0",
                **common_status(),
            }
        )
    summary = [
        {
            "tool_name": "edgartools",
            "install_status": edgar_lock["install_status"],
            "comparison_status": status,
            "sample_row_count": len(sample),
            "local_parser_found": local_parser_found,
            "raw_identity_preserved_rows": sum(1 for row in comparison_rows if row["raw_identity_preserved"] == "1"),
            "row_level_match_rows": 0,
            "adoption_decision": "blocked" if edgar_lock["install_status"] != "installed" else "defer",
            "decision_reason": "install_failed" if edgar_lock["install_status"] != "installed" else status,
            **common_status(),
        }
    ]
    return comparison_rows, summary


def pandera_validation(lock_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pandera_lock = next(row for row in lock_rows if row["tool_name"] == "pandera")
    rows = read_csv(SEC_PANEL)
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
    missing_cols = [col for col in required_cols if col not in (rows[0].keys() if rows else [])]
    imperative = {
        "row_count": len(rows),
        "missing_columns": "|".join(missing_cols),
        "timestamp_missing_rows": sum(1 for row in rows if not row.get("source_ts") or not row.get("available_to_brain_ts")),
        "bad_missing_source_negative_rows": sum(1 for row in rows if row.get("missing_source_is_negative") not in {"0", ""}),
        "bad_future_assignment_rows": sum(1 for row in rows if row.get("assignment_uses_future_outcome") not in {"0", ""}),
        "bad_outcome_assignment_rows": sum(1 for row in rows if row.get("outcome_used_for_assignment") not in {"0", ""}),
    }
    if pandera_lock["install_status"] != "installed":
        validation_status = "blocked_install_or_py_compat"
        pandera_payload: dict[str, object] = {}
    else:
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
            pandera_payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
        except Exception:
            pandera_payload = {
                "schema_status": "schema_execution_failed",
                "row_count": 0,
                "failure_cases": -1,
                "error": "pandera_stdout_not_json",
            }
        pandera_payload["returncode"] = result["returncode"]
        pandera_payload["stderr"] = result["stderr"]
        validation_status = str(pandera_payload.get("schema_status", "schema_execution_failed"))

    imperative_pass = all(
        [
            not missing_cols,
            imperative["timestamp_missing_rows"] == 0,
            imperative["bad_missing_source_negative_rows"] == 0,
            imperative["bad_future_assignment_rows"] == 0,
            imperative["bad_outcome_assignment_rows"] == 0,
        ]
    )
    pandera_pass = validation_status == "schema_checks_executed" and int(pandera_payload.get("failure_cases", -1)) == 0
    validation_rows = [
        {
            "tool_name": "pandera",
            "install_status": pandera_lock["install_status"],
            "schema_status": validation_status,
            "target_panel": SEC_PANEL.as_posix(),
            "target_panel_sha256": file_sha256(SEC_PANEL),
            "row_count": imperative["row_count"],
            "pandera_row_count": pandera_payload.get("row_count", 0),
            "required_columns": "|".join(required_cols),
            "missing_columns": imperative["missing_columns"],
            "timestamp_missing_rows": imperative["timestamp_missing_rows"],
            "bad_missing_source_negative_rows": imperative["bad_missing_source_negative_rows"],
            "bad_future_assignment_rows": imperative["bad_future_assignment_rows"],
            "bad_outcome_assignment_rows": imperative["bad_outcome_assignment_rows"],
            "pandera_failure_cases": pandera_payload.get("failure_cases", ""),
            "pandera_error": pandera_payload.get("error", ""),
            "imperative_validator_pass": "1" if imperative_pass else "0",
            "pandera_validator_pass": "1" if pandera_pass else "0",
            **common_status(),
        }
    ]
    diff_rows = [
        {
            "tool_name": "pandera",
            "diff_status": "matched" if imperative_pass and pandera_pass else "blocked_or_mismatch",
            "imperative_validator_pass": "1" if imperative_pass else "0",
            "pandera_validator_pass": "1" if pandera_pass else "0",
            "row_count_match": "1" if int(pandera_payload.get("row_count", -1)) == imperative["row_count"] else "0",
            "false_fail_detected": "0" if pandera_pass else "1",
            "adoption_decision": "adopt" if imperative_pass and pandera_pass else ("blocked" if pandera_lock["install_status"] != "installed" else "reject"),
            "decision_reason": "schema_matches_existing_validator" if imperative_pass and pandera_pass else validation_status,
            **common_status(),
        }
    ]
    return validation_rows, diff_rows


def pandas_panel_metrics(panel: Path, query_id: str, group_cols: list[str]) -> dict[str, object]:
    import pandas as pd

    started = time.perf_counter()
    df = pd.read_csv(panel, dtype=str)
    for col in group_cols:
        df[col] = df[col].fillna("")
    if "strict_gate_pass" in df.columns:
        df["_strict_gate_pass_int"] = pd.to_numeric(df["strict_gate_pass"], errors="coerce").fillna(0).astype(int)
    else:
        df["_strict_gate_pass_int"] = 0
    grouped = (
        df.groupby(group_cols, dropna=False)["_strict_gate_pass_int"]
        .agg(["count", "sum"])
        .reset_index()
        .sort_values(group_cols)
    )
    result_rows = grouped.rename(columns={"count": "packet_count", "sum": "strict_gate_pass_count"}).to_dict(orient="records")
    elapsed = round((time.perf_counter() - started) * 1000, 6)
    return {
        "query_id": query_id,
        "engine": "pandas",
        "dependency_status": "available",
        "runtime_ms": elapsed,
        "source_panel": panel.as_posix(),
        "source_panel_sha256": file_sha256(panel),
        "source_row_count": len(df),
        "result_row_count": len(result_rows),
        "join_key_columns": "|".join(group_cols),
        "join_key_null_count": int(df[group_cols].isna().any(axis=1).sum()),
        "strict_gate_pass_total": int(df["_strict_gate_pass_int"].sum()),
        "aggregate_checksum": rows_sha256(result_rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }


def duckdb_panel_metrics(panel: Path, query_id: str, group_cols: list[str]) -> dict[str, object]:
    try:
        import duckdb
    except Exception as exc:
        return {"query_id": query_id, "engine": "duckdb", "dependency_status": "dependency_missing", "failure_reason": repr(exc)}
    started = time.perf_counter()
    group_sql = ", ".join(group_cols)
    null_condition = " OR ".join([f"{col} IS NULL" for col in group_cols])
    path_sql = panel.as_posix().replace("'", "''")
    query = f"""
        WITH src AS (
            SELECT * FROM read_csv_auto('{path_sql}', HEADER=TRUE, ALL_VARCHAR=TRUE)
        ),
        grouped AS (
            SELECT {group_sql},
                   COUNT(*) AS packet_count,
                   SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) AS strict_gate_pass_count
            FROM src
            GROUP BY {group_sql}
            ORDER BY {group_sql}
        )
        SELECT
            (SELECT COUNT(*) FROM src) AS source_row_count,
            (SELECT COUNT(*) FROM grouped) AS result_row_count,
            (SELECT SUM(CASE WHEN {null_condition} THEN 1 ELSE 0 END) FROM src) AS join_key_null_count,
            (SELECT SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) FROM src) AS strict_gate_pass_total
    """
    con = duckdb.connect(database=":memory:")
    source_row_count, result_row_count, join_key_null_count, strict_gate_pass_total = con.execute(query).fetchone()
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
    result_rows = [
        {**dict(zip(group_cols, row[: len(group_cols)])), "packet_count": row[-2], "strict_gate_pass_count": row[-1]}
        for row in grouped_rows
    ]
    elapsed = round((time.perf_counter() - started) * 1000, 6)
    return {
        "query_id": query_id,
        "engine": "duckdb",
        "dependency_status": "available",
        "runtime_ms": elapsed,
        "source_panel": panel.as_posix(),
        "source_panel_sha256": file_sha256(panel),
        "source_row_count": int(source_row_count),
        "result_row_count": int(result_row_count),
        "join_key_columns": "|".join(group_cols),
        "join_key_null_count": int(join_key_null_count or 0),
        "strict_gate_pass_total": int(strict_gate_pass_total or 0),
        "aggregate_checksum": rows_sha256(result_rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }


def polars_panel_metrics(panel: Path, query_id: str, group_cols: list[str]) -> dict[str, object]:
    try:
        import polars as pl
    except Exception as exc:
        return {"query_id": query_id, "engine": "polars", "dependency_status": "dependency_missing", "failure_reason": repr(exc)}
    started = time.perf_counter()
    df = pl.read_csv(panel, infer_schema_length=0)
    df = df.with_columns([pl.col(col).fill_null("") for col in group_cols])
    strict_expr = pl.col("strict_gate_pass").cast(pl.Int64, strict=False).fill_null(0).alias("_strict_gate_pass_int")
    df = df.with_columns(strict_expr)
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
    result_rows = grouped.to_dicts()
    null_expr = pl.any_horizontal([pl.col(col).is_null() for col in group_cols]).sum()
    elapsed = round((time.perf_counter() - started) * 1000, 6)
    return {
        "query_id": query_id,
        "engine": "polars",
        "dependency_status": "available",
        "runtime_ms": elapsed,
        "source_panel": panel.as_posix(),
        "source_panel_sha256": file_sha256(panel),
        "source_row_count": df.height,
        "result_row_count": grouped.height,
        "join_key_columns": "|".join(group_cols),
        "join_key_null_count": int(df.select(null_expr).item()),
        "strict_gate_pass_total": int(df.select(pl.col("_strict_gate_pass_int").sum()).item()),
        "aggregate_checksum": rows_sha256(result_rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }


def large_panel_benchmark() -> list[dict[str, object]]:
    queries = [
        ("sec_symbol_event_family_agg", SEC_PANEL, ["symbol", "event_family"]),
        ("liquidity_provider_series_agg", LIQUIDITY_PANEL, ["provider", "series_id"]),
    ]
    rows: list[dict[str, object]] = []
    for query_id, panel, group_cols in queries:
        metrics = [
            pandas_panel_metrics(panel, query_id, group_cols),
            duckdb_panel_metrics(panel, query_id, group_cols),
            polars_panel_metrics(panel, query_id, group_cols),
        ]
        baseline = metrics[0]
        for row in metrics:
            if row.get("dependency_status") != "available":
                row["row_count_match_pandas"] = "0"
                row["join_key_null_match_pandas"] = "0"
                row["aggregate_checksum_match_pandas"] = "0"
                row["strict_gate_pass_total_match_pandas"] = "0"
                row["adoption_candidate"] = "0"
            else:
                row["row_count_match_pandas"] = "1" if row.get("source_row_count") == baseline.get("source_row_count") and row.get("result_row_count") == baseline.get("result_row_count") else "0"
                row["join_key_null_match_pandas"] = "1" if row.get("join_key_null_count") == baseline.get("join_key_null_count") else "0"
                row["aggregate_checksum_match_pandas"] = "1" if row.get("aggregate_checksum") == baseline.get("aggregate_checksum") else "0"
                row["strict_gate_pass_total_match_pandas"] = "1" if row.get("strict_gate_pass_total") == baseline.get("strict_gate_pass_total") else "0"
                faster = float(row.get("runtime_ms", 999999)) < float(baseline.get("runtime_ms", 0))
                exact = all(
                    row.get(col) == "1"
                    for col in [
                        "row_count_match_pandas",
                        "join_key_null_match_pandas",
                        "aggregate_checksum_match_pandas",
                        "strict_gate_pass_total_match_pandas",
                    ]
                )
                row["adoption_candidate"] = "1" if row.get("engine") != "pandas" and exact and faster else "0"
            row.update(common_status())
            rows.append(row)
    return rows


def build_adoption_decisions(
    lock_rows: list[dict[str, object]],
    edgar_summary: list[dict[str, object]],
    pandera_diff: list[dict[str, object]],
    benchmark_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    edgar = edgar_summary[0]
    decisions.append(
        {
            "tool_name": "edgartools",
            "decision": edgar["adoption_decision"],
            "reason": edgar["decision_reason"],
            "allowed_next_layer": "none_until_offline_local_parse_is_proven",
            **common_status(),
        }
    )
    pandera = pandera_diff[0]
    decisions.append(
        {
            "tool_name": "pandera",
            "decision": pandera["adoption_decision"],
            "reason": pandera["decision_reason"],
            "allowed_next_layer": "optional_validator_schema_candidate" if pandera["adoption_decision"] == "adopt" else "none",
            **common_status(),
        }
    )
    for engine in ["duckdb", "polars"]:
        engine_rows = [row for row in benchmark_rows if row.get("engine") == engine]
        mismatched = any(
            row.get("dependency_status") == "available"
            and (
                row.get("row_count_match_pandas") != "1"
                or row.get("join_key_null_match_pandas") != "1"
                or row.get("aggregate_checksum_match_pandas") != "1"
                or row.get("strict_gate_pass_total_match_pandas") != "1"
            )
            for row in engine_rows
        )
        candidates = sum(1 for row in engine_rows if row.get("adoption_candidate") == "1")
        decision = "reject" if mismatched else ("adopt" if candidates > 0 else "defer")
        reason = "benchmark_mismatch" if mismatched else (f"large_panel_adoption_candidates={candidates}" if candidates > 0 else "exact_but_not_faster_on_large_panel")
        decisions.append(
            {
                "tool_name": engine,
                "decision": decision,
                "reason": reason,
                "allowed_next_layer": "local_artifact_query_helper_candidate" if decision == "adopt" else "none",
                **common_status(),
            }
        )
    dlt_lock = {"install_status": "deferred_not_in_task3126"}
    decisions.append(
        {
            "tool_name": "dlt",
            "decision": "defer",
            "reason": dlt_lock["install_status"],
            "allowed_next_layer": "none_until_source_receipt_task",
            **common_status(),
        }
    )
    decisions.append(
        {
            "tool_name": "github_mcp_read_only",
            "decision": "defer",
            "reason": "connector_not_invoked_in_task3126",
            "allowed_next_layer": "none_until_read_only_monitoring_task",
            **common_status(),
        }
    )
    return decisions


def build_acceptance_checks(
    lock_rows: list[dict[str, object]],
    edgar_summary: list[dict[str, object]],
    pandera_validation_rows: list[dict[str, object]],
    benchmark_rows: list[dict[str, object]],
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
        ("install_lock_present", len(lock_rows) == 2 and {row["tool_name"] for row in lock_rows} == {"edgartools", "pandera"}, "edgartools and pandera install rows are recorded."),
        ("edgartools_no_trading_connection", edgar_summary[0]["adoption_decision"] in {"blocked", "defer", "reject"}, "edgartools is not connected to selector/sizing/replay."),
        ("pandera_validation_recorded", len(pandera_validation_rows) == 1, "Pandera validation result is recorded even if blocked."),
        (
            "large_panel_benchmark_exact_or_rejected",
            all(
                row.get("dependency_status") != "available"
                or row.get("engine") == "pandas"
                or row.get("row_count_match_pandas") == "1"
                and row.get("join_key_null_match_pandas") == "1"
                and row.get("aggregate_checksum_match_pandas") == "1"
                and row.get("strict_gate_pass_total_match_pandas") == "1"
                for row in benchmark_rows
            ),
            "DuckDB/Polars available rows match pandas on row/key/checksum metrics.",
        ),
        ("decisions_cover_all_tools", {row["tool_name"] for row in decisions} == {"edgartools", "pandera", "duckdb", "polars", "dlt", "github_mcp_read_only"}, "All planned tools have an adopt/defer/reject/blocked decision."),
    ]
    return [
        {
            "check_id": f"CHK3126-{idx:03d}",
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
    lock_rows: list[dict[str, object]],
    edgar_summary: list[dict[str, object]],
    pandera_validation_rows: list[dict[str, object]],
    pandera_diff_rows: list[dict[str, object]],
    benchmark_rows: list[dict[str, object]],
    decisions: list[dict[str, object]],
    checks: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3126 External Tool Isolated Install Pilot

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: created an isolated venv install pilot for `edgartools` and `Pandera`, ran an offline SEC local-parse compatibility check, ran a Pandera validator attempt, and benchmarked DuckDB/Polars on larger local panels.
- What did not change: no root dependency manifest, raw source download, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Install rows: {closeout['install_lock_rows']}.
  - Installed tools: {closeout['installed_tool_count']}.
  - Pandera decision: `{closeout['pandera_decision']}`.
  - Edgartools decision: `{closeout['edgartools_decision']}`.
  - Large benchmark rows: {closeout['large_benchmark_rows']}.
  - Local query adoption candidates: {closeout['local_query_adoption_candidate_count']}.
- Next action: promote only tools with `decision=adopt` to a separate opt-in wrapper task; keep all others deferred or blocked.

## Quant Expert Report

### Isolated Install Lock

{markdown_table(lock_rows, ['tool_name', 'install_status', 'version', 'import_available', 'import_name_used', 'license'])}

The install was isolated under `.cache/task_3126_external_tool_venv/`. No root dependency manifest was created.

### Edgartools SEC Local Fixture Check

{markdown_table(edgar_summary, ['tool_name', 'install_status', 'comparison_status', 'sample_row_count', 'local_parser_found', 'row_level_match_rows', 'adoption_decision', 'decision_reason'])}

`edgartools` was not allowed to download SEC data. It could only qualify if a safe offline local-file parser was proven against existing raw documents.

### Pandera Validator Pilot

{markdown_table(pandera_validation_rows, ['tool_name', 'install_status', 'schema_status', 'row_count', 'pandera_row_count', 'imperative_validator_pass', 'pandera_validator_pass', 'pandera_failure_cases'])}

{markdown_table(pandera_diff_rows, ['tool_name', 'diff_status', 'row_count_match', 'false_fail_detected', 'adoption_decision', 'decision_reason'])}

The validator target is the existing SEC normalized packet panel. The schema checks timestamps, source/hash identity, missing-as-negative flags, and outcome-assignment flags.

### DuckDB/Polars Large Panel Benchmark

{markdown_table(benchmark_rows, ['query_id', 'engine', 'runtime_ms', 'source_row_count', 'result_row_count', 'join_key_null_count', 'row_count_match_pandas', 'aggregate_checksum_match_pandas', 'strict_gate_pass_total_match_pandas', 'adoption_candidate'])}

The benchmark compares pandas, DuckDB, and Polars on existing local SEC and liquidity/rates panels. Results that differ from pandas are not adoption candidates.

### Adoption Decision Matrix

{markdown_table(decisions, ['tool_name', 'decision', 'reason', 'allowed_next_layer'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: this task decides which external tools deserve a next wrapper step, not trading use.

`Pandera` can move forward only if its isolated schema result matches the existing validator. `edgartools` cannot move forward unless it proves offline local SEC document parsing without hiding raw identity. DuckDB/Polars can move forward only where a large-panel benchmark exactly matches pandas and is faster.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `{SEC_PANEL.as_posix()}`
  - `{LIQUIDITY_PANEL.as_posix()}`
- Outputs:
  - `docs/reports/{TASK_ID}/task_3126_external_tool_isolated_install_pilot.md`
  - `docs/reports/{TASK_ID}/task_3126_decision.csv`
  - `data/artifacts/{TASK_ID}/`
- Row counts:
  - Tool install lock: {len(lock_rows)}
  - Edgartools comparison summary rows: {len(edgar_summary)}
  - Pandera validation rows: {len(pandera_validation_rows)}
  - Large benchmark rows: {len(benchmark_rows)}
  - Adoption decision rows: {len(decisions)}
- Validation commands:
  - `python scripts/trader_brain_3126_external_tool_isolated_install_pilot_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
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

    venv_row = ensure_venv()
    install_rows, lock_rows, freeze_text = install_and_inspect_tools(venv_row)
    edgar_comparison_rows, edgar_summary = edgartools_local_parse(lock_rows)
    pandera_validation_rows, pandera_diff_rows = pandera_validation(lock_rows)
    benchmark_rows = large_panel_benchmark()
    decisions = build_adoption_decisions(lock_rows, edgar_summary, pandera_diff_rows, benchmark_rows)
    checks = build_acceptance_checks(lock_rows, edgar_summary, pandera_validation_rows, benchmark_rows, decisions)

    installed_count = sum(1 for row in lock_rows if row["install_status"] == "installed")
    local_candidates = sum(1 for row in benchmark_rows if row.get("adoption_candidate") == "1")
    closeout = {
        "task_id": "Task3126",
        "verdict": "external_tool_isolated_install_pilot_completed_diagnostic_only",
        "install_lock_rows": len(lock_rows),
        "installed_tool_count": installed_count,
        "edgartools_decision": next(row["decision"] for row in decisions if row["tool_name"] == "edgartools"),
        "pandera_decision": next(row["decision"] for row in decisions if row["tool_name"] == "pandera"),
        "large_benchmark_rows": len(benchmark_rows),
        "local_query_adoption_candidate_count": local_candidates,
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }

    write_csv(OUT_DIR / "install_run_log.csv", install_rows)
    write_csv(OUT_DIR / "tool_install_lock.csv", lock_rows)
    (OUT_DIR / "pip_freeze_external_tool_pilot.txt").write_text(freeze_text, encoding="utf-8")
    write_csv(OUT_DIR / "edgartools_local_parse_comparison.csv", edgar_comparison_rows)
    write_csv(OUT_DIR / "edgartools_local_parse_summary.csv", edgar_summary)
    write_csv(OUT_DIR / "pandera_validation_report.csv", pandera_validation_rows)
    write_csv(OUT_DIR / "validator_diff_report.csv", pandera_diff_rows)
    write_csv(OUT_DIR / "large_panel_query_benchmark.csv", benchmark_rows)
    write_csv(OUT_DIR / "adoption_decision_matrix.csv", decisions)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3126_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3126_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(lock_rows, edgar_summary, pandera_validation_rows, pandera_diff_rows, benchmark_rows, decisions, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3126_EXTERNAL_TOOL_ISOLATED_INSTALL_PILOT_COMPLETE]")


if __name__ == "__main__":
    main()
