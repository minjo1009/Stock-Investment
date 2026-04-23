"""Report recent run/order/fill summaries from the local sqlite state store."""

from __future__ import annotations

import argparse
import os

from state.store import initialize_store, list_positions, list_recent_reconciliation_runs, list_recent_run_order_fill_rows


def _format_row(row: dict, *, show_intent_key: bool = False) -> str:
    fill_exists = row["fill_id"] is not None
    fill_price = "-" if row["fill_price"] is None else str(row["fill_price"])
    fill_qty = "-" if row["fill_quantity"] is None else str(row["fill_quantity"])
    fill_source = "-" if row["fill_source"] is None else row["fill_source"]
    fallback_used = "YES" if row["fallback_used"] else "NO"
    base = (
        f"- run_id={row['run_id']} | started={row['started_at']} | finished={row['finished_at'] or '-'} "
        f"| run_status={row['run_status']} | order_id={row['order_id'] or '-'} | order_status={row['order_status'] or '-'} "
        f"| fill={('YES' if fill_exists else 'NO')} | fill_qty={fill_qty} | fill_price={fill_price} "
        f"| fill_source={fill_source} | fallback_used={fallback_used}"
    )
    if show_intent_key:
        return f"{base} | intent_key={row['intent_key'] or '-'}"
    return base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show recent trade runs from sqlite state store.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of recent runs to display (default: 10)")
    parser.add_argument("--positions", action="store_true", help="Show current position snapshots")
    parser.add_argument("--show-intent-key", action="store_true", help="Include order intent_key in run report output")
    parser.add_argument("--show-reconciliation", action="store_true", help="Show recent reconciliation runs")
    parser.add_argument("--recon-summary", action="store_true", help="Show compact reconciliation summary for latest runs")
    args = parser.parse_args(argv)

    db_path = os.environ.get("TRADING_DB_PATH", "trading.db")
    initialize_store(db_path)
    if args.positions:
        positions = list_positions(db_path)
        print(f"[Positions] db={db_path}")
        if not positions:
            print("No positions")
            return 0
        print("symbol | qty | avg_price | updated_at")
        for pos in positions:
            print(f"{pos['symbol']} | {pos['quantity']} | {pos['avg_price']} | {pos['updated_at']}")
        return 0
    if args.show_reconciliation:
        rows = list_recent_reconciliation_runs(db_path, limit=args.limit)
        print(f"[Reconciliation Runs] db={db_path} limit={args.limit}")
        if not rows:
            print("No reconciliation runs")
            return 0
        for row in rows:
            print(
                f"- reconciliation_id={row['reconciliation_id']} | run_id={row['run_id']} | "
                f"status={row['status']} | severity={row['max_severity']} | block_new_orders={row['block_new_orders']} | "
                f"event_count={row['event_count']} | summary={row['summary_text']}"
            )
        return 0
    if args.recon_summary:
        rows = list_recent_reconciliation_runs(db_path, limit=5)
        print("[Recon Summary] last 5 runs")
        if not rows:
            print("No reconciliation runs")
            return 0
        print("status | severity | block | events")
        for row in rows:
            print(f"{row['status']} | {row['max_severity']} | {row['block_new_orders']} | {row['event_count']}")
        return 0

    rows = list_recent_run_order_fill_rows(db_path, limit=args.limit)

    print(f"[Recent Runs] db={db_path} limit={args.limit}")
    if not rows:
        print("No runs found")
        return 0

    for row in rows:
        print(_format_row(row, show_intent_key=args.show_intent_key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
