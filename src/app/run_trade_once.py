"""Run one end-to-end paper trade with KIS + Slack."""

from __future__ import annotations

import os
import sqlite3
import time

from integration.kis_client import KISClient
from integration import slack_client


def _order_decision_message(*, symbol: str, side: str, reason: str, price: float, quantity: int, env: str) -> str:
    return (
        "[ORDER DECISION]\n\n"
        f"symbol: {symbol}\n"
        f"side: {side}\n"
        f"reason: {reason}\n"
        f"price: {price}\n"
        f"quantity: {quantity}\n"
        f"env: {env}"
    )


def _fill_message(*, symbol: str, side: str, quantity: int, status: str, order_id: str) -> str:
    return (
        "[FILL CONFIRMED]\n\n"
        f"symbol: {symbol}\n"
        f"side: {side}\n"
        f"quantity: {quantity}\n"
        f"status: {status}\n"
        f"order_id: {order_id}"
    )


def _assert_trading_allowed(db_path: str) -> None:
    if not os.path.exists(db_path):
        return
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        row = cur.execute(
            "SELECT run_mode, kill_switch_active, kill_switch_reason FROM control_state WHERE control_key='default'"
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return
    run_mode, kill_switch_active, kill_switch_reason = row
    if int(kill_switch_active) == 1:
        raise RuntimeError(f"Trading blocked by kill switch: {kill_switch_reason or 'no reason'}")
    if str(run_mode).strip().upper() != "LIVE_ENABLED":
        raise RuntimeError(f"Trading blocked by control_state run_mode={run_mode}")


def run() -> None:
    symbol = "AAPL"
    quantity = 1
    signal = "BUY"
    reason = "dummy_signal_true"
    db_path = os.environ.get("TRADING_DB_PATH", "trading.db")

    _assert_trading_allowed(db_path)

    kis = KISClient.from_env()
    auth_state = kis.describe_auth_state()
    if auth_state.get("token_present") and not auth_state.get("expired"):
        print("[auth] cached token reused")
    else:
        print("[auth] token issue path (cache missing/expired)")
    before_qty = 0
    try:
        before_qty = kis.get_position_quantity(symbol)
    except Exception:
        before_qty = 0

    price = kis.get_current_price(symbol)

    slack_client.send_message(
        _order_decision_message(
            symbol=symbol,
            side=signal,
            reason=reason,
            price=price,
            quantity=quantity,
            env=kis.environment,
        )
    )

    order_id = kis.submit_order(symbol=symbol, side=signal, quantity=quantity, limit_price=price)

    final_status = "PENDING"
    for _ in range(10):
        final_status = kis.get_order_status(order_id)
        if final_status == "FILLED":
            break
        try:
            current_qty = kis.get_position_quantity(symbol)
            if current_qty >= before_qty + quantity:
                final_status = "FILLED"
                break
        except Exception:
            pass
        time.sleep(1)

    if final_status == "FILLED":
        slack_client.send_message(
            _fill_message(symbol=symbol, side=signal, quantity=quantity, status=final_status, order_id=order_id)
        )
        return

    timeout_text = (
        "[FILL CONFIRMED]\n\n"
        f"symbol: {symbol}\n"
        f"side: {signal}\n"
        f"quantity: {quantity}\n"
        "status: TIMEOUT\n"
        f"order_id: {order_id}"
    )
    slack_client.send_message(timeout_text)
    raise RuntimeError(f"Order fill polling timeout for order_id={order_id}")


if __name__ == "__main__":
    run()
