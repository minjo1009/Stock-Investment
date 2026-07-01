from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.data.env_loader import load_repo_env


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_env_file(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def load_runtime_env(env_file: Path | None = None) -> None:
    load_repo_env()
    if env_file is not None:
        load_env_file(env_file)


def table_exists(db_path: Path, table: str) -> bool:
    if not db_path.exists():
        return False
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def read_table(db_path: Path, table: str, *, order_by: str = "rowid", limit: int | None = None) -> pd.DataFrame:
    if not table_exists(db_path, table):
        return pd.DataFrame()
    con = sqlite3.connect(db_path)
    try:
        query = f"SELECT * FROM {table} ORDER BY {order_by} DESC"
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return pd.read_sql_query(query, con)
    finally:
        con.close()


def latest_batch(frame: pd.DataFrame, column: str = "created_at") -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return frame.iloc[0:0].copy()
    latest = frame[column].astype(str).max()
    return frame.loc[frame[column].astype(str).eq(latest)].copy()


def latest_indicator_snapshot(db_path: Path) -> pd.DataFrame:
    frame = read_table(db_path, "indicator_snapshots", order_by="created_at", limit=1000)
    return latest_batch(frame, "created_at")


def latest_runtime_decision(db_path: Path) -> dict[str, Any] | None:
    frame = read_table(db_path, "runtime_strategy_decisions", order_by="created_at", limit=1)
    if frame.empty:
        return None
    return frame.iloc[0].where(pd.notnull(frame.iloc[0]), None).to_dict()


def ensure_report_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(report_dir: Path, name: str, frame: pd.DataFrame) -> None:
    ensure_report_dir(report_dir)
    frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")


def write_json(report_dir: Path, name: str, payload: dict[str, Any]) -> None:
    ensure_report_dir(report_dir)
    (report_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def write_task_report(
    report_dir: Path,
    filename: str,
    *,
    title: str,
    decision_summary: list[str],
    quant_lines: list[str],
    decision_maker_lines: list[str],
) -> None:
    ensure_report_dir(report_dir)
    write_standard_report(
        report_dir / filename,
        title=title,
        decision_summary=decision_summary,
        quant_expert_lines=quant_lines,
        decision_maker_lines=decision_maker_lines,
    )
    write_manifest(report_dir, report_dir / "artifact_manifest.csv")


def append_registry_rows(rows: list[dict[str, str]]) -> None:
    registry = Path("tasks/task_registry.csv")
    if not registry.exists():
        return
    frame = pd.read_csv(registry)
    existing = set(frame["task_id"].astype(str)) if "task_id" in frame.columns else set()
    new_rows = [row for row in rows if row.get("task_id") not in existing]
    if not new_rows:
        return
    combined = pd.concat([frame, pd.DataFrame(new_rows)], ignore_index=True)
    combined.to_csv(registry, index=False, encoding="utf-8")
