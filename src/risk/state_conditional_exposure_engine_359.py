from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from common.models import RiskDecision, RiskInputContext, SymbolFeatureSnapshot, is_risk_evaluable


DEFAULT_STATE_MULTIPLIERS: dict[str, float] = {
    "risk_off": 0.0,
    "caution": 0.5,
    "neutral": 1.0,
    "risk_on": 1.25,
}


def resolve_state_multiplier(
    state: str | None,
    overrides: Mapping[str, float] | None = None,
) -> float:
    mapping = {**DEFAULT_STATE_MULTIPLIERS, **{str(k): float(v) for k, v in (overrides or {}).items()}}
    key = str(state or "neutral").strip().lower()
    return float(mapping.get(key, mapping["neutral"]))


def current_gross_exposure(context: RiskInputContext) -> float:
    if context.account is None or context.position is None:
        return 0.0
    balance = float(context.account.total_balance)
    if balance <= 0:
        return 0.0
    return abs(float(context.position.quantity) * float(context.position.avg_price)) / balance


def _signal_symbol_snapshot(context: RiskInputContext) -> SymbolFeatureSnapshot | None:
    return next((item for item in context.market_snapshot.symbols if item.symbol == context.signal.symbol), None)


@dataclass(frozen=True)
class StateConditionalExposureEngine:
    base_increment_exposure: float = 0.10
    max_total_exposure: float = 0.35
    min_reduce_factor: float = 0.25
    max_spread_bps: float = 35.0
    min_turnover: float = 1_000_000.0
    max_volatility_20d: float = 0.08
    state_feature_key: str = "exposure_state"
    state_multipliers: Mapping[str, float] | None = None

    def evaluate(self, context: RiskInputContext) -> RiskDecision | None:
        if not is_risk_evaluable(context):
            decision, flag = ("BLOCK", "STALE_DATA") if not context.market_snapshot.data_fresh else ("BLOCK", "MISSING_FEATURE")
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision=decision,
                reason="risk context is not evaluable",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=(flag,),
            )

        snapshot = _signal_symbol_snapshot(context)
        if snapshot is None:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="signal symbol snapshot is missing",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("MISSING_FEATURE",),
            )

        if snapshot.spread_bps is not None and float(snapshot.spread_bps) > self.max_spread_bps:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="spread is too wide for deterministic exposure sizing",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("SPREAD_TOO_WIDE",),
            )

        if snapshot.turnover is not None and float(snapshot.turnover) < self.min_turnover:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="turnover is too low for deterministic exposure sizing",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("LOW_LIQUIDITY",),
            )

        volatility = snapshot.features.get("volatility_20d")
        if volatility is not None and float(volatility) > self.max_volatility_20d:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="volatility hard limit exceeded",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("HIGH_VOLATILITY",),
            )

        if self.state_feature_key not in snapshot.features or snapshot.features[self.state_feature_key] is None:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="state feature is missing",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("MISSING_FEATURE",),
            )

        multiplier = resolve_state_multiplier(str(snapshot.features[self.state_feature_key]), self.state_multipliers)
        desired_increment = self.base_increment_exposure * multiplier
        if desired_increment <= 0:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="state disables incremental exposure",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
            )

        current_exposure = current_gross_exposure(context)
        remaining_capacity = self.max_total_exposure - current_exposure
        if remaining_capacity <= 0:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="max total exposure already reached",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("MAX_EXPOSURE_EXCEEDED",),
            )

        if desired_increment <= remaining_capacity:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="ALLOW",
                reason="state-conditioned exposure fits within capacity",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
            )

        reduce_factor = remaining_capacity / desired_increment
        if reduce_factor < self.min_reduce_factor:
            return RiskDecision(
                decision_id=f"{context.signal.event_id}:state-conditional-exposure",
                event_id=context.signal.event_id,
                decision="BLOCK",
                reason="remaining capacity is too small for minimum sized reduction",
                risk_snapshot_id=context.market_snapshot.snapshot_version,
                risk_flags=("MAX_EXPOSURE_EXCEEDED",),
            )

        return RiskDecision(
            decision_id=f"{context.signal.event_id}:state-conditional-exposure",
            event_id=context.signal.event_id,
            decision="REDUCE",
            reason="state-conditioned exposure must be reduced to fit capacity",
            risk_snapshot_id=context.market_snapshot.snapshot_version,
            risk_flags=("MAX_EXPOSURE_EXCEEDED",),
            reduce_factor=round(reduce_factor, 6),
        )
