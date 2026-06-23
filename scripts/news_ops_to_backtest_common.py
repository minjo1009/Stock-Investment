from __future__ import annotations

import csv
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "trading.db"
TASK_ID = "task_3883_news_ops_scope_a_g_implementation"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID

REQUIRED_SOURCE_FAMILIES = (
    "market_ticks_intraday",
    "market_bars_5m",
    "macro_rates",
    "sec_events",
    "official_public_releases",
    "gdelt_news_events",
    "marketaux_news_free",
)

NEWS_SOURCE_FAMILIES = (
    "official_public_releases",
    "gdelt_news_events",
    "marketaux_news_free",
)

DISCOVERY_NEWS_SOURCE_FAMILIES = (
    "gdelt_news_events",
    "marketaux_news_free",
)

PERMISSION_COLUMNS = (
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
)


def ensure_dirs() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if rows:
            fieldnames = []
            for row in rows:
                for key in row:
                    if key not in fieldnames:
                        fieldnames.append(key)
        else:
            fieldnames = ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def connect_readonly() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone() is not None


def count_rows(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    return int(con.execute(sql, params).fetchone()[0])


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def fail_if_errors(errors: list[str]) -> None:
    if errors:
        raise AssertionError("; ".join(errors[:20]))


def safety_payload() -> dict[str, str]:
    return {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "broker_mutation": "FORBIDDEN",
        "live_order": "FORBIDDEN",
        "paper_promotion": "FORBIDDEN",
    }
