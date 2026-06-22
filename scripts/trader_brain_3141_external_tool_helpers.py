from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


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


def command_result(cmd: list[str], cwd: Path, timeout: int = 300) -> dict[str, object]:
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


def validate_sec_panel_with_pandera(root: Path, venv_dir: Path, panel: Path, required_cols: list[str]) -> dict[str, object]:
    python_path = venv_python(venv_dir)
    if not python_path.exists():
        return {
            "schema_status": "blocked_venv_missing",
            "row_count": 0,
            "failure_cases": -1,
            "error": f"missing venv python: {python_path}",
            "runtime_ms": 0,
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
    payload = {"schema_status": "schema_checks_executed", "row_count": int(len(df)), "failure_cases": 0, "error": ""}
except Exception as exc:
    payload = {"schema_status": "schema_execution_failed", "row_count": 0, "failure_cases": -1, "error": repr(exc)[:2000]}
print(json.dumps(payload, ensure_ascii=False))
"""
    result = command_result([str(python_path), "-c", code, panel.as_posix()], cwd=root, timeout=300)
    try:
        payload = json.loads(str(result["stdout"]).strip().splitlines()[-1])
    except Exception:
        payload = {"schema_status": "schema_execution_failed", "row_count": 0, "failure_cases": -1, "error": "pandera_stdout_not_json"}
    payload["runtime_ms"] = result["runtime_ms"]
    payload["returncode"] = result["returncode"]
    payload["stderr"] = result["stderr"]
    payload["required_columns"] = "|".join(required_cols)
    return payload


def pandas_agg(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
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


def polars_agg(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
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


def duckdb_agg(panel: Path, group_cols: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
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
