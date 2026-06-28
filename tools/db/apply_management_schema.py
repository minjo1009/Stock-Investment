from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from tools.db.news_l0_l1 import NEWS_PROVIDER_SPECS
from tools.db.source_acquisition.microstructure_checkpoint import CHECKPOINT_FIELDS
from tools.db.source_acquisition.scheduler_override import BASE_CONFIG_PATH, DEFAULT_OVERRIDE_PATH, load_effective_scheduler_config
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


DEFAULT_DB_PATH = Path("trading.db")


def connect(path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(path)


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists source_provider_specs (
            provider text primary key,
            provider_role text not null,
            authority_class text not null,
            trade_authority_flag integer not null,
            diagnostic_only integer not null,
            updated_at text default current_timestamp
        )
        """
    )
    conn.execute(
        """
        create table if not exists source_scheduler_registry (
            job_name text primary key,
            enabled integer not null,
            allow_network integer not null,
            interval_minutes integer not null,
            families_json text not null,
            symbols_json text not null,
            macro_series_json text not null,
            provider text not null,
            feed text,
            mode text,
            diagnostic_only integer not null,
            execution_permitted integer not null,
            broker_mutation_permitted integer not null,
            paper_promotion_permitted integer not null,
            real_capital_permitted integer not null,
            updated_at text default current_timestamp
        )
        """
    )
    conn.execute(
        """
        create table if not exists microstructure_backfill_checkpoint (
            checkpoint_id text primary key,
            provider text not null,
            feed text not null,
            source_type text not null,
            symbol text not null,
            session_date text not null,
            chunk_start_ts text not null,
            chunk_end_ts text not null,
            chunk_id text not null,
            status text not null,
            attempt_count integer not null,
            last_attempt_ts text,
            last_success_ts text,
            row_count integer not null,
            raw_path text,
            raw_sha256 text,
            error_category text,
            error_message_redacted text,
            created_at text,
            updated_at text
        )
        """
    )
    conn.execute(
        """
        create table if not exists source_acquisition_ledger (
            ledger_id integer primary key autoincrement,
            job_name text not null,
            family text not null,
            status text not null,
            diagnostic_only integer not null,
            raw_path text,
            raw_sha256 text,
            error_message_redacted text,
            created_at text default current_timestamp
        )
        """
    )
    ensure_l2_schema(conn)
    conn.commit()


def seed_provider_specs(conn: sqlite3.Connection) -> None:
    for provider, spec in NEWS_PROVIDER_SPECS.items():
        conn.execute(
            """
            insert into source_provider_specs(provider, provider_role, authority_class, trade_authority_flag, diagnostic_only)
            values (?, ?, ?, ?, 1)
            on conflict(provider) do update set
                provider_role=excluded.provider_role,
                authority_class=excluded.authority_class,
                trade_authority_flag=excluded.trade_authority_flag,
                diagnostic_only=1,
                updated_at=current_timestamp
            """,
            (
                provider,
                spec["provider_role"],
                spec["authority_class"],
                int(spec.get("trade_authority_flag", 0)),
            ),
        )
    conn.commit()


def seed_scheduler_registry(conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    for job in config.get("jobs", []):
        conn.execute(
            """
            insert into source_scheduler_registry(
                job_name, enabled, allow_network, interval_minutes, families_json, symbols_json, macro_series_json,
                provider, feed, mode, diagnostic_only, execution_permitted, broker_mutation_permitted,
                paper_promotion_permitted, real_capital_permitted
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 0, 0)
            on conflict(job_name) do update set
                enabled=excluded.enabled,
                allow_network=excluded.allow_network,
                interval_minutes=excluded.interval_minutes,
                families_json=excluded.families_json,
                symbols_json=excluded.symbols_json,
                macro_series_json=excluded.macro_series_json,
                provider=excluded.provider,
                feed=excluded.feed,
                mode=excluded.mode,
                diagnostic_only=1,
                execution_permitted=0,
                broker_mutation_permitted=0,
                paper_promotion_permitted=0,
                real_capital_permitted=0,
                updated_at=current_timestamp
            """,
            (
                job.get("name", ""),
                int(bool(job.get("enabled"))),
                int(bool(job.get("allow_network"))),
                int(job.get("interval_minutes", 0)),
                json.dumps(job.get("families", []), sort_keys=True),
                json.dumps(job.get("symbols", []), sort_keys=True),
                json.dumps(job.get("macro_series", []), sort_keys=True),
                str(job.get("provider", "")),
                str(job.get("feed", "")),
                str(job.get("mode", "")),
            ),
        )
    conn.commit()


def apply_operator_scheduler_override(conn: sqlite3.Connection, effective_config: dict[str, Any]) -> None:
    for job in effective_config.get("jobs", []):
        conn.execute(
            """
            update source_scheduler_registry
            set enabled=?,
                allow_network=?,
                interval_minutes=?,
                symbols_json=?,
                macro_series_json=?,
                diagnostic_only=1,
                execution_permitted=0,
                broker_mutation_permitted=0,
                paper_promotion_permitted=0,
                real_capital_permitted=0,
                updated_at=current_timestamp
            where job_name=?
            """,
            (
                int(bool(job.get("enabled"))),
                int(bool(job.get("allow_network"))),
                int(job.get("interval_minutes", 0)),
                json.dumps(job.get("symbols", []), sort_keys=True),
                json.dumps(job.get("macro_series", []), sort_keys=True),
                str(job.get("name", "")),
            ),
        )
    conn.commit()


def apply_management_schema(*, db_path: Path = DEFAULT_DB_PATH, base_path: Path = BASE_CONFIG_PATH, override_path: Path = DEFAULT_OVERRIDE_PATH) -> None:
    effective = load_effective_scheduler_config(base_path=base_path, override_path=override_path)
    conn = connect(db_path)
    try:
        apply_schema(conn)
        seed_provider_specs(conn)
        seed_scheduler_registry(conn, effective)
        apply_operator_scheduler_override(conn, effective)
    finally:
        conn.close()


def checkpoint_columns() -> list[str]:
    return list(CHECKPOINT_FIELDS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply L0 source acquisition management schema.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply_management_schema(db_path=args.db_path)
        print(f"[MANAGEMENT_SCHEMA_OK] db={args.db_path}")
    else:
        print("[MANAGEMENT_SCHEMA_DRY_RUN] pass --apply to create or reconcile tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
