"""Execution loop foundation with minimal safety guards."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from app.run_trade_once import run as run_trade_once
from state.store import initialize_store, list_open_orders, list_positions


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_true(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _kill_switch_active() -> bool:
    return _is_true(os.environ.get("TRADING_KILL_SWITCH"))


def _interval_seconds() -> int:
    raw = os.environ.get("TRADING_LOOP_INTERVAL_SEC", "60")
    try:
        parsed = int(raw)
    except ValueError:
        parsed = 60
    return max(1, parsed)


def _default_lock_path() -> str:
    return os.environ.get("TRADING_LOOP_LOCK_PATH", ".trading.lock")


def _acquire_lock(lock_path: str) -> None:
    lock_file = Path(lock_path)
    if lock_file.exists():
        if _is_stale_lock(lock_file):
            lock_file.unlink(missing_ok=True)
        else:
            raise RuntimeError(f"Lock file exists: {lock_file}")
    try:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Lock file exists: {lock_file}") from exc
    try:
        payload = {
            "pid": os.getpid(),
            "created_at": _now_iso(),
        }
        os.write(fd, json.dumps(payload, ensure_ascii=True).encode("utf-8"))
    finally:
        os.close(fd)


def _release_lock(lock_path: str) -> None:
    lock_file = Path(lock_path)
    if lock_file.exists():
        lock_file.unlink()


def _is_stale_lock(lock_file: Path) -> bool:
    try:
        raw = lock_file.read_text(encoding="utf-8").strip()
        data = json.loads(raw)
        pid = int(data.get("pid"))
    except Exception:
        return False
    return not _pid_is_running(pid)


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        # Conservative fallback on unknown OS errors.
        return True


def _log_current_state(db_path: str) -> None:
    try:
        initialize_store(db_path)
        positions = list_positions(db_path)
        open_orders = list_open_orders(db_path)
    except Exception as exc:
        print(f"[INFO] state read failed: {exc}")
        return

    if not positions:
        print("[INFO] no current positions")
    else:
        first = positions[0]
        print(
            f"[INFO] current position exists: symbol={first['symbol']} qty={first['quantity']} avg_price={first['avg_price']}"
        )

    if not open_orders:
        print("[INFO] no open orders")
    else:
        first_open = open_orders[0]
        print(
            f"[INFO] open orders: count={len(open_orders)} first_order_id={first_open['order_id']} symbol={first_open['symbol']}"
        )


def run_loop(
    *,
    max_runs: int | None = None,
    lock_path: str | None = None,
    run_once_fn: Callable[[], None] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    if _kill_switch_active():
        print("[LOOP STOP] KILL SWITCH ACTIVE")
        return 0

    interval = _interval_seconds()
    db_path = os.environ.get("TRADING_DB_PATH", "trading.db")
    resolved_lock = lock_path or _default_lock_path()
    executor = run_once_fn or run_trade_once

    try:
        _acquire_lock(resolved_lock)
    except RuntimeError as exc:
        print(f"[LOOP BLOCKED] {exc}")
        return 1

    runs = 0
    try:
        while True:
            if max_runs is not None and runs >= max_runs:
                print(f"[LOOP STOP] reached max-runs={max_runs}")
                break

            if _kill_switch_active():
                print("[LOOP STOP] KILL SWITCH ACTIVE")
                break

            print(f"[RUN START] {_now_iso()} iteration={runs + 1}")
            _log_current_state(db_path)

            run_status = "OK"
            try:
                executor()
            except Exception as exc:
                run_status = f"ERROR: {exc}"
                print(f"[RUN ERROR] {exc}")
            finally:
                print(f"[RUN END] status={run_status}")

            runs += 1
            if max_runs is not None and runs >= max_runs:
                print(f"[LOOP STOP] reached max-runs={max_runs}")
                break

            print(f"[LOOP SLEEP] {interval} sec")
            sleep_fn(interval)
    finally:
        _release_lock(resolved_lock)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run paper-trade loop with minimal safety guards.")
    parser.add_argument("--max-runs", type=int, default=None, help="Stop after N runs (test/debug option).")
    args = parser.parse_args(argv)
    return run_loop(max_runs=args.max_runs)


if __name__ == "__main__":
    raise SystemExit(main())
