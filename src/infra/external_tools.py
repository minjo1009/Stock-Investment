from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ToolStatus:
    tool_name: str
    import_name: str
    dependency_status: str
    import_origin: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_name": self.tool_name,
            "import_name": self.import_name,
            "dependency_status": self.dependency_status,
            "import_origin": self.import_origin,
        }


@dataclass(frozen=True)
class AggregateMetrics:
    engine: str
    dependency_status: str
    runtime_ms: float = 0.0
    source_row_count: int = 0
    result_row_count: int = 0
    join_key_null_count: int = 0
    strict_gate_pass_total: int = 0
    aggregate_checksum: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "dependency_status": self.dependency_status,
            "runtime_ms": self.runtime_ms,
            "source_row_count": self.source_row_count,
            "result_row_count": self.result_row_count,
            "join_key_null_count": self.join_key_null_count,
            "strict_gate_pass_total": self.strict_gate_pass_total,
            "aggregate_checksum": self.aggregate_checksum,
            "error": self.error,
        }


@dataclass(frozen=True)
class AggregateResult:
    metrics: AggregateMetrics
    rows: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        payload = self.metrics.to_dict()
        payload["row_payload_count"] = len(self.rows)
        return payload


@dataclass(frozen=True)
class SchemaValidationResult:
    schema_status: str
    dependency_status: str
    row_count: int = 0
    failure_cases: int = 0
    error: str = ""
    runtime_ms: float = 0.0
    required_columns: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_status": self.schema_status,
            "dependency_status": self.dependency_status,
            "row_count": self.row_count,
            "failure_cases": self.failure_cases,
            "error": self.error,
            "runtime_ms": self.runtime_ms,
            "required_columns": self.required_columns,
        }


@dataclass(frozen=True)
class MetricComparison:
    row_count_match_pandas: str
    join_key_null_match_pandas: str
    aggregate_checksum_match_pandas: str
    strict_gate_pass_total_match_pandas: str
    faster_than_pandas: str
    comparison_pass: str

    def to_dict(self) -> dict[str, object]:
        return {
            "row_count_match_pandas": self.row_count_match_pandas,
            "join_key_null_match_pandas": self.join_key_null_match_pandas,
            "aggregate_checksum_match_pandas": self.aggregate_checksum_match_pandas,
            "strict_gate_pass_total_match_pandas": self.strict_gate_pass_total_match_pandas,
            "faster_than_pandas": self.faster_than_pandas,
            "comparison_pass": self.comparison_pass,
        }


def aggregate_result_from_metrics(metrics: dict[str, object], rows: list[dict[str, object]]) -> AggregateResult:
    typed_metrics = AggregateMetrics(
        engine=str(metrics.get("engine", "")),
        dependency_status=str(metrics.get("dependency_status", "")),
        runtime_ms=float(metrics.get("runtime_ms") or 0),
        source_row_count=int(metrics.get("source_row_count") or 0),
        result_row_count=int(metrics.get("result_row_count") or 0),
        join_key_null_count=int(metrics.get("join_key_null_count") or 0),
        strict_gate_pass_total=int(metrics.get("strict_gate_pass_total") or 0),
        aggregate_checksum=str(metrics.get("aggregate_checksum", "")),
        error=str(metrics.get("error", "")),
    )
    return AggregateResult(metrics=typed_metrics, rows=tuple(rows))


def schema_result_from_payload(payload: dict[str, object]) -> SchemaValidationResult:
    return SchemaValidationResult(
        schema_status=str(payload.get("schema_status", "")),
        dependency_status=str(payload.get("dependency_status", "")),
        row_count=int(payload.get("row_count") or 0),
        failure_cases=int(payload.get("failure_cases") or 0),
        error=str(payload.get("error", "")),
        runtime_ms=float(payload.get("runtime_ms") or 0),
        required_columns=str(payload.get("required_columns", "")),
    )


def dependency_status(tool_name: str, import_names: Iterable[str] | None = None) -> ToolStatus:
    names = list(import_names or [tool_name])
    for name in names:
        spec = importlib.util.find_spec(name)
        if spec is not None:
            return ToolStatus(tool_name=tool_name, import_name=name, dependency_status="available", import_origin=spec.origin or "")
    return ToolStatus(tool_name=tool_name, import_name=names[0], dependency_status="dependency_missing")


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


def csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def missing_required_columns(path: Path, required_cols: Iterable[str]) -> list[str]:
    if not path.exists():
        return [f"missing_file:{path}"]
    header = set(csv_header(path))
    return [col for col in required_cols if col not in header]


def invalid_input_metrics(engine: str, error: str) -> dict[str, object]:
    return {
        "engine": engine,
        "dependency_status": "invalid_input",
        "runtime_ms": 0,
        "source_row_count": 0,
        "result_row_count": 0,
        "join_key_null_count": 0,
        "strict_gate_pass_total": 0,
        "aggregate_checksum": "",
        "error": error,
    }


def _strict_gate_required_columns(group_cols: list[str]) -> list[str]:
    return list(dict.fromkeys([*group_cols, "strict_gate_pass"]))


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _command_result(cmd: list[str], cwd: Path, timeout: int = 300) -> dict[str, object]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
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


def pandas_strict_gate_aggregate(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    status = dependency_status("pandas")
    if status.dependency_status != "available":
        return {"engine": "pandas", "dependency_status": status.dependency_status}, []
    required_cols = _strict_gate_required_columns(group_cols)
    missing_cols = missing_required_columns(panel, required_cols)
    if missing_cols:
        return invalid_input_metrics("pandas", "missing_columns:" + "|".join(missing_cols)), []

    import pandas as pd

    started = time.perf_counter()
    df = pd.read_csv(panel, dtype=str, usecols=required_cols)
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
        "engine": "pandas",
        "dependency_status": "available",
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": len(df),
        "result_row_count": len(rows),
        "join_key_null_count": int(df[group_cols].isna().any(axis=1).sum()),
        "strict_gate_pass_total": int(df["_strict_gate_pass_int"].sum()),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def polars_strict_gate_aggregate(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    status = dependency_status("polars")
    if status.dependency_status != "available":
        return {"engine": "polars", "dependency_status": status.dependency_status}, []
    required_cols = _strict_gate_required_columns(group_cols)
    missing_cols = missing_required_columns(panel, required_cols)
    if missing_cols:
        return invalid_input_metrics("polars", "missing_columns:" + "|".join(missing_cols)), []

    import polars as pl

    started = time.perf_counter()
    df = pl.read_csv(panel, infer_schema_length=0, columns=required_cols)
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
        "engine": "polars",
        "dependency_status": "available",
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": df.height,
        "result_row_count": grouped.height,
        "join_key_null_count": int(df.select(null_expr).item()),
        "strict_gate_pass_total": int(df.select(pl.col("_strict_gate_pass_int").sum()).item()),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def duckdb_strict_gate_aggregate(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    status = dependency_status("duckdb")
    if status.dependency_status != "available":
        return {"engine": "duckdb", "dependency_status": status.dependency_status}, []
    required_cols = _strict_gate_required_columns(group_cols)
    missing_cols = missing_required_columns(panel, required_cols)
    if missing_cols:
        return invalid_input_metrics("duckdb", "missing_columns:" + "|".join(missing_cols)), []

    import duckdb

    started = time.perf_counter()
    group_sql = ", ".join(group_cols)
    selected_sql = ", ".join(required_cols)
    null_condition = " OR ".join([f"{col} IS NULL" for col in group_cols])
    path_sql = panel.as_posix().replace("'", "''")
    con = duckdb.connect(database=":memory:")
    metrics_row = con.execute(
        f"""
        WITH src AS (
            SELECT {selected_sql}
            FROM read_csv_auto('{path_sql}', HEADER=TRUE, ALL_VARCHAR=TRUE)
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
        WITH src AS (
            SELECT {selected_sql}
            FROM read_csv_auto('{path_sql}', HEADER=TRUE, ALL_VARCHAR=TRUE)
        )
        SELECT {group_sql},
               COUNT(*) AS packet_count,
               SUM(COALESCE(TRY_CAST(strict_gate_pass AS INTEGER), 0)) AS strict_gate_pass_count
        FROM src
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
        "engine": "duckdb",
        "dependency_status": "available",
        "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
        "source_row_count": int(source_row_count),
        "result_row_count": int(result_row_count),
        "join_key_null_count": int(join_key_null_count or 0),
        "strict_gate_pass_total": int(strict_gate_pass_total or 0),
        "aggregate_checksum": rows_sha256(rows, group_cols + ["packet_count", "strict_gate_pass_count"]),
    }
    return metrics, rows


def compare_metrics(candidate: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    if candidate.get("dependency_status") != "available" or baseline.get("dependency_status") != "available":
        return {
            "row_count_match_pandas": "0",
            "join_key_null_match_pandas": "0",
            "aggregate_checksum_match_pandas": "0",
            "strict_gate_pass_total_match_pandas": "0",
            "faster_than_pandas": "0",
            "comparison_pass": "0",
        }
    checks = {
        "row_count_match_pandas": "1"
        if candidate.get("source_row_count") == baseline.get("source_row_count")
        and candidate.get("result_row_count") == baseline.get("result_row_count")
        else "0",
        "join_key_null_match_pandas": "1" if candidate.get("join_key_null_count") == baseline.get("join_key_null_count") else "0",
        "aggregate_checksum_match_pandas": "1" if candidate.get("aggregate_checksum") == baseline.get("aggregate_checksum") else "0",
        "strict_gate_pass_total_match_pandas": "1" if candidate.get("strict_gate_pass_total") == baseline.get("strict_gate_pass_total") else "0",
        "faster_than_pandas": "1" if float(candidate.get("runtime_ms", 999999)) < float(baseline.get("runtime_ms", 0)) else "0",
    }
    checks["comparison_pass"] = "1" if all(value == "1" for value in checks.values()) else "0"
    return checks


def compare_aggregate_results(candidate: AggregateResult, baseline: AggregateResult) -> MetricComparison:
    if candidate.metrics.dependency_status != "available" or baseline.metrics.dependency_status != "available":
        return MetricComparison(
            row_count_match_pandas="0",
            join_key_null_match_pandas="0",
            aggregate_checksum_match_pandas="0",
            strict_gate_pass_total_match_pandas="0",
            faster_than_pandas="0",
            comparison_pass="0",
        )
    row_match = (
        candidate.metrics.source_row_count == baseline.metrics.source_row_count
        and candidate.metrics.result_row_count == baseline.metrics.result_row_count
    )
    null_match = candidate.metrics.join_key_null_count == baseline.metrics.join_key_null_count
    checksum_match = candidate.metrics.aggregate_checksum == baseline.metrics.aggregate_checksum
    strict_match = candidate.metrics.strict_gate_pass_total == baseline.metrics.strict_gate_pass_total
    faster = candidate.metrics.runtime_ms < baseline.metrics.runtime_ms
    values = {
        "row_count_match_pandas": "1" if row_match else "0",
        "join_key_null_match_pandas": "1" if null_match else "0",
        "aggregate_checksum_match_pandas": "1" if checksum_match else "0",
        "strict_gate_pass_total_match_pandas": "1" if strict_match else "0",
        "faster_than_pandas": "1" if faster else "0",
    }
    return MetricComparison(comparison_pass="1" if all(value == "1" for value in values.values()) else "0", **values)


def pandas_strict_gate_aggregate_result(panel: Path, group_cols: list[str]) -> AggregateResult:
    metrics, rows = pandas_strict_gate_aggregate(panel, group_cols)
    return aggregate_result_from_metrics(metrics, rows)


def polars_strict_gate_aggregate_result(panel: Path, group_cols: list[str]) -> AggregateResult:
    metrics, rows = polars_strict_gate_aggregate(panel, group_cols)
    return aggregate_result_from_metrics(metrics, rows)


def duckdb_strict_gate_aggregate_result(panel: Path, group_cols: list[str]) -> AggregateResult:
    metrics, rows = duckdb_strict_gate_aggregate(panel, group_cols)
    return aggregate_result_from_metrics(metrics, rows)


def validate_sec_panel_schema_with_pandera(panel: Path, required_cols: list[str]) -> dict[str, object]:
    status = dependency_status("pandera")
    if status.dependency_status != "available":
        return {
            "schema_status": "dependency_missing",
            "dependency_status": status.dependency_status,
            "row_count": 0,
            "failure_cases": -1,
            "error": "",
            "required_columns": "|".join(required_cols),
        }

    import pandas as pd
    try:
        import pandera.pandas as pa
    except Exception:
        import pandera as pa
    from pandera import Check, Column, DataFrameSchema

    started = time.perf_counter()
    try:
        df = pd.read_csv(panel, dtype=str)
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
        return {
            "schema_status": "schema_checks_executed",
            "dependency_status": "available",
            "row_count": int(len(df)),
            "failure_cases": 0,
            "error": "",
            "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
            "required_columns": "|".join(required_cols),
        }
    except Exception as exc:
        return {
            "schema_status": "schema_execution_failed",
            "dependency_status": "available",
            "row_count": 0,
            "failure_cases": -1,
            "error": repr(exc)[:2000],
            "runtime_ms": round((time.perf_counter() - started) * 1000, 6),
            "required_columns": "|".join(required_cols),
        }


def validate_sec_panel_schema_with_pandera_venv(root: Path, venv_dir: Path, panel: Path, required_cols: list[str]) -> dict[str, object]:
    python_path = venv_python(venv_dir)
    if not python_path.exists():
        return {
            "schema_status": "blocked_venv_missing",
            "dependency_status": "dependency_missing",
            "row_count": 0,
            "failure_cases": -1,
            "error": f"missing venv python: {python_path}",
            "required_columns": "|".join(required_cols),
        }
    code = r"""
import json
import sys

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
    payload = {"schema_status": "schema_checks_executed", "dependency_status": "available", "row_count": int(len(df)), "failure_cases": 0, "error": ""}
except Exception as exc:
    payload = {"schema_status": "schema_execution_failed", "dependency_status": "available", "row_count": 0, "failure_cases": -1, "error": repr(exc)[:2000]}
print(json.dumps(payload, ensure_ascii=False))
"""
    result = _command_result([str(python_path), "-c", code, panel.as_posix()], cwd=root, timeout=300)
    try:
        payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
    except Exception:
        payload = {
            "schema_status": "schema_execution_failed",
            "dependency_status": "available",
            "row_count": 0,
            "failure_cases": -1,
            "error": "pandera_stdout_not_json",
        }
    payload["runtime_ms"] = result["runtime_ms"]
    payload["returncode"] = result["returncode"]
    payload["stderr"] = result["stderr"]
    payload["required_columns"] = "|".join(required_cols)
    return payload


def validate_sec_panel_schema_with_pandera_result(panel: Path, required_cols: list[str]) -> SchemaValidationResult:
    return schema_result_from_payload(validate_sec_panel_schema_with_pandera(panel, required_cols))


def validate_sec_panel_schema_with_pandera_venv_result(root: Path, venv_dir: Path, panel: Path, required_cols: list[str]) -> SchemaValidationResult:
    return schema_result_from_payload(validate_sec_panel_schema_with_pandera_venv(root, venv_dir, panel, required_cols))
