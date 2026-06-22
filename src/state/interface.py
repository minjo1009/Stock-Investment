"""State persistence contracts.

This module defines the W1 state boundary. Concrete SQLite persistence remains
in `state.store` and must not be treated as a contract-only module.
"""

from __future__ import annotations

from typing import Any, Protocol


class StateStorePort(Protocol):
    """Minimal persistence interface used by runtime and reconciliation code."""

    def initialize(self) -> None:
        """Prepare the backing store without placing trades or calling brokers."""
        ...

    def record_trade_run_start(
        self,
        *,
        symbol: str,
        side: str,
        requested_quantity: float,
        started_at: str,
        environment: str,
        result_status: str = "ORDER_SUBMITTED",
    ) -> str:
        """Record a trade run start and return the run identifier."""
        ...

    def record_trade_run_finish(self, run_id: str, result_status: str, finished_at: str) -> None:
        """Record a trade run terminal status."""
        ...

    def record_order(
        self,
        *,
        order_id: str,
        run_id: str,
        symbol: str,
        side: str,
        quantity: float,
        submitted_at: str,
        status: str,
        environment: str,
        intent_key: str | None = None,
        raw_status: str | None = None,
    ) -> None:
        """Record a submitted order snapshot."""
        ...

    def update_order_status(self, order_id: str, status: str, raw_status: str | None = None) -> None:
        """Record a local order status update."""
        ...

    def list_open_orders(self) -> list[dict[str, Any]]:
        """Return local orders that are still open."""
        ...


__all__ = ["StateStorePort"]
