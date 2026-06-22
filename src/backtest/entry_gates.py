from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EntryGateConfig:
    use_ker_gate: bool = False
    use_volume_gate: bool = False
    use_daily_bias_gate: bool = False
    ker_window: int = 20
    ker_trend_threshold: float = 0.50
    ker_mean_rev_threshold: float = 0.30
    ker_allow_mixed: bool = False
    volume_window: int = 100
    volume_percentile_threshold: float = 0.60
    daily_fast_window: int = 20
    daily_slow_window: int = 50

    @classmethod
    def disabled(cls) -> "EntryGateConfig":
        return cls()

    @property
    def is_enabled(self) -> bool:
        return self.use_ker_gate or self.use_volume_gate or self.use_daily_bias_gate


@dataclass(frozen=True)
class EntryGateDecision:
    passed: bool
    failed_reasons: tuple[str, ...]
    ker_value: float | None = None
    ker_regime: str | None = None
    volume_percentile: float | None = None
    daily_bias: str | None = None


def prepare_entry_gate_frame(frame: pd.DataFrame, config: EntryGateConfig) -> pd.DataFrame:
    out = frame.copy()
    close = out["close"]
    volume = out["volume"]

    ker_window = max(int(config.ker_window), 1)
    change_abs = close.diff().abs()
    rolling_change_sum = change_abs.rolling(ker_window, min_periods=ker_window).sum()
    out["ker"] = (close - close.shift(ker_window)).abs() / rolling_change_sum.replace(0.0, np.nan)
    out["ker"] = out["ker"].clip(lower=0.0, upper=1.0)

    vol_window = max(int(config.volume_window), 1)

    def _last_percentile(values: np.ndarray) -> float:
        if values.size == 0:
            return np.nan
        current = values[-1]
        return float(np.count_nonzero(values <= current) / values.size)

    out["volume_percentile"] = volume.rolling(vol_window, min_periods=vol_window).apply(
        _last_percentile,
        raw=True,
    )

    fast_window = max(int(config.daily_fast_window), 1)
    slow_window = max(int(config.daily_slow_window), 1)
    out["daily_sma20"] = close.rolling(fast_window, min_periods=fast_window).mean()
    out["daily_sma50"] = close.rolling(slow_window, min_periods=slow_window).mean()
    return out


def evaluate_entry_gate(frame: pd.DataFrame, idx: int, config: EntryGateConfig) -> EntryGateDecision:
    if not config.is_enabled:
        return EntryGateDecision(passed=True, failed_reasons=())

    failed: list[str] = []
    ker_value: float | None = None
    ker_regime: str | None = None
    volume_percentile: float | None = None
    daily_bias: str | None = None

    if config.use_ker_gate:
        ker = _frame_value(frame, idx, "ker")
        ker_value = ker
        if ker is None:
            failed.append("KER_NA")
            ker_regime = "UNKNOWN"
        else:
            if ker > config.ker_trend_threshold:
                ker_regime = "TREND"
            elif ker < config.ker_mean_rev_threshold:
                ker_regime = "MEAN_REV"
            else:
                ker_regime = "MIXED"
            if ker_regime == "MEAN_REV":
                failed.append("KER_MEAN_REV")
            elif ker_regime == "MIXED" and not config.ker_allow_mixed:
                failed.append("KER_MIXED_BLOCKED")

    if config.use_volume_gate:
        pct = _frame_value(frame, idx, "volume_percentile")
        volume_percentile = pct
        if pct is None:
            failed.append("VOLUME_PERCENTILE_NA")
        elif pct < config.volume_percentile_threshold:
            failed.append("VOLUME_PERCENTILE_LOW")

    if config.use_daily_bias_gate:
        close = _frame_value(frame, idx, "close")
        sma20 = _frame_value(frame, idx, "daily_sma20")
        sma50 = _frame_value(frame, idx, "daily_sma50")
        if close is None or sma20 is None or sma50 is None:
            daily_bias = "UNKNOWN"
            failed.append("DAILY_BIAS_NA")
        else:
            if close > sma50 and sma20 > sma50:
                daily_bias = "STRONG_BULLISH"
            elif close > sma50:
                daily_bias = "BULLISH"
            else:
                daily_bias = "BEARISH"
            if daily_bias not in {"BULLISH", "STRONG_BULLISH"}:
                failed.append("DAILY_BIAS_BEARISH")

    return EntryGateDecision(
        passed=len(failed) == 0,
        failed_reasons=tuple(sorted(set(failed))),
        ker_value=ker_value,
        ker_regime=ker_regime,
        volume_percentile=volume_percentile,
        daily_bias=daily_bias,
    )


def _frame_value(frame: pd.DataFrame, idx: int, column: str) -> float | None:
    if column not in frame.columns or not (0 <= idx < len(frame)):
        return None
    value = frame.iloc[idx][column]
    if pd.isna(value):
        return None
    return float(value)
