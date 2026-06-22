from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AllocationConfig:
    max_positions: int = 3
    max_exposure_per_symbol: float = 0.40


def allocate_equal_weight(symbols: list[str], *, config: AllocationConfig | None = None) -> list[dict[str, float | str]]:
    cfg = config or AllocationConfig()
    if not symbols or cfg.max_positions <= 0:
        return []

    selected = list(dict.fromkeys(symbols))[: cfg.max_positions]
    if not selected:
        return []

    raw_weight = 1.0 / float(len(selected))
    capped_weight = min(raw_weight, cfg.max_exposure_per_symbol)
    allocations = [{"symbol": symbol, "allocation_pct": float(capped_weight)} for symbol in selected]

    total = sum(float(item["allocation_pct"]) for item in allocations)
    if total < 1.0 and allocations:
        residual = 1.0 - total
        allocations[0]["allocation_pct"] = float(allocations[0]["allocation_pct"]) + residual
    return allocations
