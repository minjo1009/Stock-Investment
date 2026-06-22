from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RankingConfig:
    w_momentum: float = 0.5
    w_volume: float = 0.35
    w_volatility_penalty: float = 0.15


def rank_universe(snapshot: pd.DataFrame, *, config: RankingConfig | None = None) -> pd.DataFrame:
    cfg = config or RankingConfig()
    if snapshot.empty:
        return snapshot.copy()

    ranked = snapshot.copy()
    ranked["momentum_rank"] = ranked["momentum"].rank(pct=True, method="average")
    ranked["volume_rank"] = ranked["avg_dollar_volume"].rank(pct=True, method="average")
    ranked["volatility_rank"] = ranked["volatility"].rank(pct=True, method="average")
    ranked["volatility_penalty"] = ranked["volatility_rank"]
    ranked["score"] = (
        cfg.w_momentum * ranked["momentum_rank"]
        + cfg.w_volume * ranked["volume_rank"]
        - cfg.w_volatility_penalty * ranked["volatility_penalty"]
    )
    return ranked.sort_values(["score", "momentum", "avg_dollar_volume"], ascending=[False, False, False]).reset_index(drop=True)
