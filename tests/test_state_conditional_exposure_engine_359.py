from __future__ import annotations

import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from common.models import (
    AccountSnapshot,
    MarketDataSnapshot,
    MarketSessionState,
    PositionSnapshot,
    RiskInputContext,
    SignalEvent,
    SymbolFeatureSnapshot,
)

MODULE_PATH = SRC / "risk" / "state_conditional_exposure_engine_359.py"
SPEC = spec_from_file_location("state_conditional_exposure_engine_359", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load module from {MODULE_PATH}")
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
StateConditionalExposureEngine = MODULE.StateConditionalExposureEngine
resolve_state_multiplier = MODULE.resolve_state_multiplier


class TestStateConditionalExposureEngine359(unittest.TestCase):
    def _signal(self) -> SignalEvent:
        return SignalEvent(
            event_id="evt-359",
            timestamp="2026-05-09T13:30:00Z",
            market="US",
            symbol="NVDA",
            strategy_id="state-conditional-exposure-359",
            action="ENTER",
            side="BUY",
            reason="breakout",
            score=0.9,
        )

    def _symbol_snapshot(self, **overrides: object) -> SymbolFeatureSnapshot:
        features = {
            "turnover_rank": 10,
            "volatility_20d": 0.04,
            "gap_pct": 0.01,
            "momentum_20d": 0.12,
            "exposure_state": "neutral",
        }
        features.update(overrides.pop("features", {}))
        return SymbolFeatureSnapshot(
            market="US",
            symbol="NVDA",
            timestamp="2026-05-09T13:30:00Z",
            last_price=float(overrides.pop("last_price", 100.0)),
            volume=float(overrides.pop("volume", 1_000_000.0)),
            turnover=float(overrides.pop("turnover", 5_000_000.0)),
            spread_bps=float(overrides.pop("spread_bps", 10.0)),
            feature_version="foundation-v1",
            features=features,
        )

    def _context(
        self,
        *,
        env: str = "paper",
        account: AccountSnapshot | None = None,
        position: PositionSnapshot | None = None,
        data_fresh: bool = True,
        snapshot: SymbolFeatureSnapshot | None = None,
    ) -> RiskInputContext:
        session = MarketSessionState(
            market="US",
            session_state="OPEN",
            timestamp="2026-05-09T13:30:00Z",
            is_trading_day=True,
        )
        market_snapshot = MarketDataSnapshot(
            market="US",
            env=env,
            timestamp="2026-05-09T13:30:00Z",
            session=session,
            symbols=(snapshot or self._symbol_snapshot(),),
            universe_size=1,
            data_fresh=data_fresh,
            snapshot_version="snap-359",
        )
        return RiskInputContext(
            signal=self._signal(),
            market_snapshot=market_snapshot,
            account=account,
            position=position,
        )

    def test_resolve_state_multiplier_uses_configured_override(self) -> None:
        self.assertEqual(resolve_state_multiplier("risk_on", {"risk_on": 1.4}), 1.4)

    def test_resolve_state_multiplier_falls_back_to_neutral_for_unknown_state(self) -> None:
        self.assertEqual(resolve_state_multiplier("unknown-state"), 1.0)

    def test_evaluate_allows_paper_flat_context_under_cap(self) -> None:
        engine = StateConditionalExposureEngine()
        decision = engine.evaluate(self._context(account=None, position=None))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "ALLOW")
        self.assertIsNone(decision.reduce_factor)

    def test_evaluate_reduces_when_risk_on_increment_exceeds_remaining_capacity(self) -> None:
        engine = StateConditionalExposureEngine(base_increment_exposure=0.10, max_total_exposure=0.35)
        snapshot = self._symbol_snapshot(features={"exposure_state": "risk_on"})
        account = AccountSnapshot(env="paper", total_balance=1000.0, available_balance=800.0, timestamp="2026-05-09T13:30:00Z")
        position = PositionSnapshot(symbol="NVDA", quantity=3.0, avg_price=100.0, unrealized_pnl=0.0, realized_pnl=0.0)
        decision = engine.evaluate(self._context(account=account, position=position, snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "REDUCE")
        self.assertAlmostEqual(float(decision.reduce_factor or 0.0), 0.4, places=6)
        self.assertIn("MAX_EXPOSURE_EXCEEDED", decision.risk_flags)

    def test_evaluate_blocks_when_remaining_capacity_is_below_min_reduce_factor(self) -> None:
        engine = StateConditionalExposureEngine(base_increment_exposure=0.10, max_total_exposure=0.35, min_reduce_factor=0.25)
        snapshot = self._symbol_snapshot(features={"exposure_state": "risk_on"})
        account = AccountSnapshot(env="paper", total_balance=1000.0, available_balance=700.0, timestamp="2026-05-09T13:30:00Z")
        position = PositionSnapshot(symbol="NVDA", quantity=3.3, avg_price=100.0, unrealized_pnl=0.0, realized_pnl=0.0)
        decision = engine.evaluate(self._context(account=account, position=position, snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertIn("MAX_EXPOSURE_EXCEEDED", decision.risk_flags)

    def test_evaluate_blocks_stale_snapshot_before_state_logic(self) -> None:
        engine = StateConditionalExposureEngine()
        decision = engine.evaluate(self._context(data_fresh=False))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertEqual(decision.risk_flags, ("STALE_DATA",))

    def test_evaluate_blocks_missing_state_feature(self) -> None:
        engine = StateConditionalExposureEngine()
        snapshot = self._symbol_snapshot(features={"exposure_state": None})
        decision = engine.evaluate(self._context(snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertEqual(decision.risk_flags, ("MISSING_FEATURE",))

    def test_evaluate_blocks_when_spread_is_too_wide(self) -> None:
        engine = StateConditionalExposureEngine(max_spread_bps=35.0)
        snapshot = self._symbol_snapshot(spread_bps=60.0)
        decision = engine.evaluate(self._context(snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertEqual(decision.risk_flags, ("SPREAD_TOO_WIDE",))

    def test_evaluate_blocks_when_turnover_is_too_low(self) -> None:
        engine = StateConditionalExposureEngine(min_turnover=1_000_000.0)
        snapshot = self._symbol_snapshot(turnover=250_000.0)
        decision = engine.evaluate(self._context(snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertEqual(decision.risk_flags, ("LOW_LIQUIDITY",))

    def test_evaluate_blocks_when_volatility_hard_limit_is_exceeded(self) -> None:
        engine = StateConditionalExposureEngine(max_volatility_20d=0.08)
        snapshot = self._symbol_snapshot(features={"volatility_20d": 0.12})
        decision = engine.evaluate(self._context(snapshot=snapshot))
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertEqual(decision.risk_flags, ("HIGH_VOLATILITY",))


if __name__ == "__main__":
    unittest.main()
