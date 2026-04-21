from __future__ import annotations

import importlib
import inspect
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from typing import get_type_hints
from urllib import error
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestRepositoryFoundationStructure(unittest.TestCase):
    @staticmethod
    def _build_market_snapshot(*, data_fresh: bool = True, features: dict[str, float | None] | None = None):
        from common.models import MarketDataSnapshot, MarketSessionState, SymbolFeatureSnapshot

        symbol_features = {
            "turnover_rank": 10.0,
            "volatility_20d": 0.2,
            "gap_pct": -0.3,
            "momentum_20d": 1.5,
        }
        if features is not None:
            symbol_features = features

        return MarketDataSnapshot(
            market="KR",
            env="paper",
            timestamp="2026-01-01T00:00:00Z",
            session=MarketSessionState(
                market="KR",
                session_state="OPEN",
                timestamp="2026-01-01T00:00:00Z",
                is_trading_day=True,
            ),
            symbols=(
                SymbolFeatureSnapshot(
                    market="KR",
                    symbol="005930",
                    timestamp="2026-01-01T00:00:00Z",
                    last_price=100.0,
                    volume=1000.0,
                    turnover=100000.0,
                    spread_bps=2.0,
                    feature_version="foundation-v1",
                    features=symbol_features,
                ),
            ),
            universe_size=1,
            data_fresh=data_fresh,
            snapshot_version="foundation-v1",
        )

    @staticmethod
    def _build_signal():
        from common.models import SignalEvent

        return SignalEvent(
            event_id="sig-1",
            timestamp="2026-01-01T00:00:00Z",
            market="KR",
            symbol="005930",
            strategy_id="s1",
            action="ENTER",
            side="BUY",
            reason="test",
            score=None,
        )

    def test_required_directories_exist(self) -> None:
        required_dirs = [
            "src/market",
            "src/strategy",
            "src/risk",
            "src/execution",
            "src/reporting",
            "src/common",
            "src/app",
            "tests/unit",
            "tests/integration",
            "tests/replay",
        ]
        for rel in required_dirs:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_dir())

    def test_required_files_exist(self) -> None:
        required_files = [
            "src/app/main.py",
            "src/app/pipeline.py",
            "src/common/models.py",
            "src/market/interface.py",
            "src/strategy/interface.py",
            "src/risk/interface.py",
            "src/execution/interface.py",
            "src/reporting/interface.py",
        ]
        for rel in required_files:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file())

    def test_imports_work(self) -> None:
        modules = [
            "app.main",
            "app.pipeline",
            "app.run_trade_once",
            "common.models",
            "integration.kis_auth_manager",
            "integration.kis_client",
            "integration.slack_client",
            "market.interface",
            "strategy.interface",
            "risk.interface",
            "execution.interface",
            "reporting.interface",
        ]
        for name in modules:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_market_snapshot_models_exist(self) -> None:
        from common.models import MarketDataSnapshot, MarketSessionState, SymbolFeatureSnapshot

        self.assertTrue(inspect.isclass(MarketSessionState))
        self.assertTrue(inspect.isclass(SymbolFeatureSnapshot))
        self.assertTrue(inspect.isclass(MarketDataSnapshot))

    def test_market_interface_returns_market_data_snapshot(self) -> None:
        from common.models import MarketDataSnapshot
        from market.interface import MarketDataPort

        hints = get_type_hints(MarketDataPort.load_market_snapshot)
        self.assertIn("return", hints)
        self.assertIs(hints["return"], MarketDataSnapshot)

    def test_strategy_interface_accepts_market_data_snapshot(self) -> None:
        from common.models import MarketDataSnapshot
        from strategy.interface import StrategyPort

        hints = get_type_hints(StrategyPort.generate_signal)
        self.assertIn("feature_snapshot", hints)
        self.assertIs(hints["feature_snapshot"], MarketDataSnapshot)

    def test_risk_input_context_exists(self) -> None:
        from common.models import RISK_INPUT_CONTEXT_VERSION, RiskInputContext

        self.assertTrue(inspect.isclass(RiskInputContext))
        self.assertEqual(RISK_INPUT_CONTEXT_VERSION, "foundation-v1")

    def test_risk_interface_accepts_risk_input_context(self) -> None:
        from common.models import RiskInputContext
        from risk.interface import RiskPort

        hints = get_type_hints(RiskPort.evaluate)
        self.assertIn("context", hints)
        self.assertIs(hints["context"], RiskInputContext)

    def test_required_strategy_feature_keys_exist(self) -> None:
        from common.models import REQUIRED_STRATEGY_FEATURE_KEYS, StrategyFeatureKey

        expected = {"turnover_rank", "volatility_20d", "gap_pct", "momentum_20d"}
        self.assertEqual(set(REQUIRED_STRATEGY_FEATURE_KEYS), expected)
        self.assertEqual(len(REQUIRED_STRATEGY_FEATURE_KEYS), 4)
        # 타입 심볼이 import 가능해야 한다.
        self.assertIsNotNone(StrategyFeatureKey)

    def test_dummy_market_snapshot_contains_required_features(self) -> None:
        from app.main import DummyMarketPort
        from common.models import REQUIRED_STRATEGY_FEATURE_KEYS

        snapshot = DummyMarketPort().load_market_snapshot("KR", "paper")
        self.assertGreaterEqual(len(snapshot.symbols), 1)
        first = snapshot.symbols[0]
        for key in REQUIRED_STRATEGY_FEATURE_KEYS:
            with self.subTest(feature_key=key):
                self.assertIn(key, first.features)

    def test_dummy_risk_port_signature_uses_risk_input_context(self) -> None:
        from app.main import DummyRiskPort
        from common.models import RiskInputContext

        hints = get_type_hints(DummyRiskPort.evaluate)
        self.assertIn("context", hints)
        self.assertIs(hints["context"], RiskInputContext)

    def test_is_risk_evaluable_allows_none_account_in_paper_foundation(self) -> None:
        from common.models import RiskInputContext, is_risk_evaluable

        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=self._build_market_snapshot(),
            account=None,
            position=None,
        )
        self.assertTrue(is_risk_evaluable(context))

    def test_is_risk_evaluable_allows_none_position_as_flat(self) -> None:
        from common.models import RiskInputContext, is_risk_evaluable

        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=self._build_market_snapshot(),
            account=None,
            position=None,
        )
        self.assertTrue(is_risk_evaluable(context))

    def test_is_risk_evaluable_blocks_stale_snapshot(self) -> None:
        from common.models import RiskInputContext, is_risk_evaluable

        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=self._build_market_snapshot(data_fresh=False),
            account=None,
            position=None,
        )
        self.assertFalse(is_risk_evaluable(context))

    def test_missing_required_feature_key_means_not_evaluable(self) -> None:
        from common.models import RiskInputContext, has_required_strategy_features, is_risk_evaluable

        features = {
            "turnover_rank": 10.0,
            "volatility_20d": 0.2,
            "gap_pct": -0.3,
            # "momentum_20d" missing
        }
        snapshot = self._build_market_snapshot(features=features)
        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=snapshot,
            account=None,
            position=None,
        )

        self.assertFalse(has_required_strategy_features(snapshot.symbols[0]))
        self.assertFalse(is_risk_evaluable(context))

    def test_none_required_feature_value_means_not_evaluable(self) -> None:
        from common.models import RiskInputContext, is_risk_evaluable

        features = {
            "turnover_rank": 10.0,
            "volatility_20d": 0.2,
            "gap_pct": -0.3,
            "momentum_20d": None,
        }
        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=self._build_market_snapshot(features=features),
            account=None,
            position=None,
        )
        self.assertFalse(is_risk_evaluable(context))

    def test_risk_decision_has_semantics_fields(self) -> None:
        from common.models import RiskDecision

        decision = RiskDecision(
            decision_id="d1",
            event_id="e1",
            decision="ALLOW",
            reason="ok",
            risk_snapshot_id="r1",
            risk_flags=(),
            reduce_factor=None,
        )
        self.assertEqual(decision.decision, "ALLOW")
        self.assertEqual(decision.reason, "ok")
        self.assertEqual(decision.risk_flags, ())
        self.assertIsNone(decision.reduce_factor)

    def test_risk_decision_legacy_fields_removed(self) -> None:
        from dataclasses import fields

        from common.models import RiskDecision

        names = {f.name for f in fields(RiskDecision)}
        self.assertNotIn("status", names)
        self.assertNotIn("block_reason", names)
        self.assertNotIn("approved_size", names)

    def test_risk_decision_decision_values_are_canonical(self) -> None:
        from common.models import RiskDecision

        for value in ("ALLOW", "BLOCK", "REDUCE"):
            with self.subTest(decision=value):
                decision = RiskDecision(
                    decision_id=f"d-{value}",
                    event_id="e1",
                    decision=value,  # type: ignore[arg-type]
                    reason="dummy",
                    risk_snapshot_id="r1",
                    risk_flags=(),
                    reduce_factor=0.5 if value == "REDUCE" else None,
                )
                self.assertIn(decision.decision, ("ALLOW", "BLOCK", "REDUCE"))

    def test_risk_decision_block_requires_no_reduce_factor(self) -> None:
        from common.models import RiskDecision

        blocked = RiskDecision(
            decision_id="d-block",
            event_id="e1",
            decision="BLOCK",
            reason="risk limit",
            risk_snapshot_id="r1",
            risk_flags=("MAX_EXPOSURE_EXCEEDED",),
            reduce_factor=None,
        )
        self.assertIsNone(blocked.reduce_factor)
        with self.assertRaises(ValueError):
            RiskDecision(
                decision_id="d-block-invalid",
                event_id="e1",
                decision="BLOCK",
                reason="invalid",
                risk_snapshot_id="r1",
                reduce_factor=0.5,
            )

    def test_risk_flag_taxonomy_symbols_exist(self) -> None:
        from common.models import RISK_FLAG_VALUES, RiskFlag

        expected = {
            "MAX_POSITION_EXCEEDED",
            "MAX_EXPOSURE_EXCEEDED",
            "MAX_DAILY_LOSS_REACHED",
            "SPREAD_TOO_WIDE",
            "LOW_LIQUIDITY",
            "HIGH_VOLATILITY",
            "STALE_DATA",
            "MISSING_FEATURE",
        }
        self.assertEqual(set(RISK_FLAG_VALUES), expected)
        self.assertIsNotNone(RiskFlag)

    def test_invalid_risk_flag_is_rejected(self) -> None:
        from common.models import RiskDecision

        with self.assertRaises(ValueError):
            RiskDecision(
                decision_id="d-invalid-flag",
                event_id="e1",
                decision="ALLOW",
                reason="invalid flag",
                risk_snapshot_id="r1",
                risk_flags=("UNKNOWN_FLAG",),  # type: ignore[arg-type]
                reduce_factor=None,
            )

    def test_execution_status_symbols_exist(self) -> None:
        from common.models import EXECUTION_STATUS_VALUES, ExecutionStatus

        expected = {
            "NEW",
            "SUBMITTED",
            "PARTIAL_FILLED",
            "FILLED",
            "CANCELLED",
            "REJECTED",
        }
        self.assertEqual(set(EXECUTION_STATUS_VALUES), expected)
        self.assertIsNotNone(ExecutionStatus)

    def test_execution_valid_transition_paths(self) -> None:
        from common.models import is_valid_transition

        self.assertTrue(is_valid_transition("NEW", "SUBMITTED"))
        self.assertTrue(is_valid_transition("SUBMITTED", "FILLED"))
        self.assertTrue(is_valid_transition("SUBMITTED", "PARTIAL_FILLED"))
        self.assertTrue(is_valid_transition("PARTIAL_FILLED", "FILLED"))

    def test_execution_invalid_transition_is_rejected(self) -> None:
        from common.models import is_valid_transition

        self.assertFalse(is_valid_transition("NEW", "FILLED"))
        self.assertFalse(is_valid_transition("FILLED", "SUBMITTED"))

    def test_transition_order_status_updates_timestamp(self) -> None:
        from common.models import BrokerOrder, transition_order_status

        order = BrokerOrder(
            order_id="o1",
            intent_id="i1",
            symbol="005930",
            side="BUY",
            quantity=1.0,
            filled_quantity=0.0,
            status="NEW",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        moved = transition_order_status(order, "SUBMITTED", updated_at="2026-01-01T00:00:01Z")
        self.assertEqual(moved.status, "SUBMITTED")
        self.assertEqual(moved.updated_at, "2026-01-01T00:00:01Z")
        self.assertEqual(order.status, "NEW")

    def test_transition_order_status_blocks_invalid_path(self) -> None:
        from common.models import BrokerOrder, transition_order_status

        order = BrokerOrder(
            order_id="o2",
            intent_id="i2",
            symbol="005930",
            side="BUY",
            quantity=1.0,
            filled_quantity=0.0,
            status="NEW",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        with self.assertRaises(ValueError):
            transition_order_status(order, "FILLED", updated_at="2026-01-01T00:00:02Z")

    def test_apply_fill_event_partial_sets_partial_filled(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o3",
            intent_id="i3",
            symbol="005930",
            side="BUY",
            quantity=10.0,
            filled_quantity=0.0,
            status="SUBMITTED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f1",
            order_id="o3",
            symbol="005930",
            side="BUY",
            fill_quantity=4.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:03Z",
            is_final=False,
        )
        updated = apply_fill_event(order, fill)
        self.assertEqual(updated.status, "PARTIAL_FILLED")
        self.assertEqual(updated.filled_quantity, 4.0)

    def test_apply_fill_event_full_sets_filled(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o4",
            intent_id="i4",
            symbol="005930",
            side="BUY",
            quantity=5.0,
            filled_quantity=0.0,
            status="SUBMITTED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f2",
            order_id="o4",
            symbol="005930",
            side="BUY",
            fill_quantity=5.0,
            fill_price=101.0,
            timestamp="2026-01-01T00:00:04Z",
            is_final=True,
        )
        updated = apply_fill_event(order, fill)
        self.assertEqual(updated.status, "FILLED")
        self.assertEqual(updated.filled_quantity, 5.0)

    def test_apply_fill_event_overfill_rejected(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o5",
            intent_id="i5",
            symbol="005930",
            side="BUY",
            quantity=5.0,
            filled_quantity=4.0,
            status="PARTIAL_FILLED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f3",
            order_id="o5",
            symbol="005930",
            side="BUY",
            fill_quantity=2.0,
            fill_price=102.0,
            timestamp="2026-01-01T00:00:05Z",
            is_final=True,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_apply_fill_event_wrong_order_id_rejected(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o6",
            intent_id="i6",
            symbol="005930",
            side="BUY",
            quantity=3.0,
            filled_quantity=0.0,
            status="SUBMITTED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f4",
            order_id="other",
            symbol="005930",
            side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:06Z",
            is_final=False,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_apply_fill_event_cumulative_updates(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o7",
            intent_id="i7",
            symbol="005930",
            side="BUY",
            quantity=8.0,
            filled_quantity=2.0,
            status="SUBMITTED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f5",
            order_id="o7",
            symbol="005930",
            side="BUY",
            fill_quantity=3.0,
            fill_price=99.0,
            timestamp="2026-01-01T00:00:07Z",
            is_final=False,
        )
        updated = apply_fill_event(order, fill)
        self.assertEqual(updated.filled_quantity, 5.0)
        self.assertEqual(updated.status, "PARTIAL_FILLED")

    def test_apply_fill_event_accepts_partial_filled_status(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o8",
            intent_id="i8",
            symbol="005930",
            side="BUY",
            quantity=8.0,
            filled_quantity=5.0,
            status="PARTIAL_FILLED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f6",
            order_id="o8",
            symbol="005930",
            side="BUY",
            fill_quantity=3.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:08Z",
            is_final=True,
        )
        updated = apply_fill_event(order, fill)
        self.assertEqual(updated.status, "FILLED")
        self.assertEqual(updated.filled_quantity, 8.0)

    def test_apply_fill_event_rejects_new_status(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o9",
            intent_id="i9",
            symbol="005930",
            side="BUY",
            quantity=2.0,
            filled_quantity=0.0,
            status="NEW",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f7",
            order_id="o9",
            symbol="005930",
            side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:09Z",
            is_final=False,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_apply_fill_event_rejects_cancelled_status(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o10",
            intent_id="i10",
            symbol="005930",
            side="BUY",
            quantity=2.0,
            filled_quantity=0.0,
            status="CANCELLED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f8",
            order_id="o10",
            symbol="005930",
            side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:10Z",
            is_final=False,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_apply_fill_event_rejects_rejected_status(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o11",
            intent_id="i11",
            symbol="005930",
            side="BUY",
            quantity=2.0,
            filled_quantity=0.0,
            status="REJECTED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f9",
            order_id="o11",
            symbol="005930",
            side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:11Z",
            is_final=False,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_apply_fill_event_rejects_filled_status(self) -> None:
        from common.models import BrokerOrder, FillEvent, apply_fill_event

        order = BrokerOrder(
            order_id="o12",
            intent_id="i12",
            symbol="005930",
            side="BUY",
            quantity=2.0,
            filled_quantity=2.0,
            status="FILLED",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        fill = FillEvent(
            fill_id="f10",
            order_id="o12",
            symbol="005930",
            side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:12Z",
            is_final=False,
        )
        with self.assertRaises(ValueError):
            apply_fill_event(order, fill)

    def test_dummy_risk_port_returns_risk_decision_contract(self) -> None:
        from app.main import DummyRiskPort
        from common.models import RiskDecision, RiskInputContext

        context = RiskInputContext(
            signal=self._build_signal(),
            market_snapshot=self._build_market_snapshot(),
            account=None,
            position=None,
        )
        result = DummyRiskPort().evaluate(context)
        self.assertIsInstance(result, RiskDecision)
        self.assertEqual(result.decision, "ALLOW")
        self.assertIsNone(result.reduce_factor)

    def test_order_intent_has_handoff_fields(self) -> None:
        from common.models import OrderIntent

        intent = OrderIntent(
            symbol="005930",
            side="BUY",
            quantity=1.0,
            price_type="MARKET",
            reduce_factor=None,
            source_decision_id="d1",
        )
        self.assertEqual(intent.symbol, "005930")
        self.assertEqual(intent.side, "BUY")
        self.assertEqual(intent.quantity, 1.0)
        self.assertEqual(intent.price_type, "MARKET")
        self.assertIsNone(intent.reduce_factor)
        self.assertEqual(intent.source_decision_id, "d1")

    def test_quantity_instruction_import_and_validation(self) -> None:
        from common.models import QUANTITY_INSTRUCTION_VERSION, QuantityInstruction

        instruction = QuantityInstruction(
            symbol="005930",
            side="BUY",
            final_quantity=1.0,
            instruction_version=QUANTITY_INSTRUCTION_VERSION,
            source="sizing-engine",
        )
        self.assertEqual(instruction.final_quantity, 1.0)
        self.assertEqual(instruction.instruction_version, "foundation-v1")

        with self.assertRaises(ValueError):
            QuantityInstruction(symbol="005930", side="BUY", final_quantity=0.0)

    def test_order_intent_reduce_factor_range_validation(self) -> None:
        from common.models import OrderIntent

        with self.assertRaises(ValueError):
            OrderIntent(
                symbol="005930",
                side="BUY",
                quantity=1.0,
                price_type="MARKET",
                reduce_factor=1.2,
                source_decision_id="d1",
            )
        with self.assertRaises(ValueError):
            OrderIntent(
                symbol="005930",
                side="BUY",
                quantity=1.0,
                price_type="MARKET",
                reduce_factor=0.0,
                source_decision_id="d1",
            )

    def test_order_intent_quantity_must_be_positive_if_provided(self) -> None:
        from common.models import OrderIntent

        with self.assertRaises(ValueError):
            OrderIntent(
                symbol="005930",
                side="BUY",
                quantity=0,
                price_type="MARKET",
                reduce_factor=None,
                source_decision_id="d1",
            )

    def test_handoff_block_returns_none_even_with_quantity(self) -> None:
        from common.models import QuantityInstruction, RiskDecision, build_order_intent_from_handoff

        decision = RiskDecision(
            decision_id="d-block",
            event_id="e1",
            decision="BLOCK",
            reason="risk",
            risk_snapshot_id="r1",
            reduce_factor=None,
        )
        instruction = QuantityInstruction(symbol="005930", side="BUY", final_quantity=1.0)
        self.assertIsNone(build_order_intent_from_handoff(self._build_signal(), decision, instruction))

    def test_handoff_returns_none_without_quantity_instruction(self) -> None:
        from common.models import RiskDecision, build_order_intent_from_handoff

        allow = RiskDecision(
            decision_id="d-allow",
            event_id="e1",
            decision="ALLOW",
            reason="ok",
            risk_snapshot_id="r1",
            reduce_factor=None,
        )
        self.assertIsNone(build_order_intent_from_handoff(self._build_signal(), allow, None))

    def test_handoff_allow_and_reduce_with_quantity_instruction(self) -> None:
        from common.models import QuantityInstruction, RiskDecision, build_order_intent_from_handoff

        allow = RiskDecision(
            decision_id="d-allow",
            event_id="e1",
            decision="ALLOW",
            reason="ok",
            risk_snapshot_id="r1",
            reduce_factor=None,
        )
        allow_instruction = QuantityInstruction(symbol="005930", side="BUY", final_quantity=1.0)
        allow_intent = build_order_intent_from_handoff(self._build_signal(), allow, allow_instruction)
        self.assertIsNotNone(allow_intent)
        assert allow_intent is not None
        self.assertIsNone(allow_intent.reduce_factor)
        self.assertEqual(allow_intent.quantity, 1.0)
        self.assertEqual(allow_intent.source_decision_id, allow.decision_id)

        reduce = RiskDecision(
            decision_id="d-reduce",
            event_id="e1",
            decision="REDUCE",
            reason="limit",
            risk_snapshot_id="r1",
            reduce_factor=0.5,
        )
        reduce_instruction = QuantityInstruction(symbol="005930", side="BUY", final_quantity=2.0)
        reduce_intent = build_order_intent_from_handoff(self._build_signal(), reduce, reduce_instruction)
        self.assertIsNotNone(reduce_intent)
        assert reduce_intent is not None
        self.assertEqual(reduce_intent.reduce_factor, 0.5)
        self.assertEqual(reduce_intent.quantity, 2.0)
        self.assertEqual(reduce_intent.source_decision_id, reduce.decision_id)

    def test_reduce_factor_and_final_quantity_are_independent_fields(self) -> None:
        from common.models import QuantityInstruction, RiskDecision, build_order_intent_from_handoff

        reduce = RiskDecision(
            decision_id="d-reduce",
            event_id="e1",
            decision="REDUCE",
            reason="limit",
            risk_snapshot_id="r1",
            reduce_factor=0.5,
        )
        instruction = QuantityInstruction(symbol="005930", side="BUY", final_quantity=2.0)
        intent = build_order_intent_from_handoff(self._build_signal(), reduce, instruction)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.reduce_factor, 0.5)
        self.assertEqual(intent.quantity, 2.0)

    @staticmethod
    def _build_order_for_reconciliation(*, status: str, order_id: str = "late-o1"):
        from common.models import BrokerOrder

        return BrokerOrder(
            order_id=order_id,
            intent_id="intent-late",
            symbol="005930",
            side="BUY",
            quantity=10.0,
            filled_quantity=10.0 if status == "FILLED" else 0.0,
            status=status,  # type: ignore[arg-type]
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    @staticmethod
    def _build_fill_for_reconciliation(*, order_id: str = "late-o1", symbol: str = "005930", side: str = "BUY"):
        from common.models import FillEvent

        return FillEvent(
            fill_id="late-f1",
            order_id=order_id,
            symbol=symbol,
            side=side,  # type: ignore[arg-type]
            fill_quantity=1.0,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:20Z",
            is_final=False,
        )

    def test_reconcile_late_fill_cancelled_returns_review_required(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="CANCELLED")
        fill = self._build_fill_for_reconciliation()
        result = reconcile_late_fill(order, fill)
        self.assertTrue(result.accepted_for_review)
        self.assertEqual(result.reconciliation_status, "REVIEW_REQUIRED")
        self.assertEqual(result.original_order_status, "CANCELLED")

    def test_reconcile_late_fill_filled_returns_review_required(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="FILLED")
        fill = self._build_fill_for_reconciliation()
        result = reconcile_late_fill(order, fill)
        self.assertTrue(result.accepted_for_review)
        self.assertEqual(result.reconciliation_status, "REVIEW_REQUIRED")
        self.assertEqual(result.original_order_status, "FILLED")

    def test_reconcile_late_fill_rejects_new_status(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="NEW")
        fill = self._build_fill_for_reconciliation()
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_rejected_status(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="REJECTED")
        fill = self._build_fill_for_reconciliation()
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_submitted_status(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="SUBMITTED")
        fill = self._build_fill_for_reconciliation()
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_partial_filled_status(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="PARTIAL_FILLED")
        fill = self._build_fill_for_reconciliation()
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_order_id_mismatch(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="CANCELLED", order_id="late-o2")
        fill = self._build_fill_for_reconciliation(order_id="late-o3")
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_symbol_mismatch(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="CANCELLED")
        fill = self._build_fill_for_reconciliation(symbol="AAPL")
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_reconcile_late_fill_rejects_side_mismatch(self) -> None:
        from common.models import reconcile_late_fill

        order = self._build_order_for_reconciliation(status="CANCELLED")
        fill = self._build_fill_for_reconciliation(side="SELL")
        with self.assertRaises(ValueError):
            reconcile_late_fill(order, fill)

    def test_auth_manager_reuses_valid_cached_token(self) -> None:
        from integration.kis_auth_manager import KISAuthManager

        with tempfile.TemporaryDirectory() as td:
            cache_path = Path(td) / "token.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "access_token": "cached-token",
                        "issued_at": "2026-01-01T00:00:00+00:00",
                        "expires_at": "2099-01-01T00:00:00+00:00",
                        "environment": "paper",
                    }
                ),
                encoding="utf-8",
            )
            manager = KISAuthManager(
                app_key="k",
                app_secret="s",
                environment="paper",
                base_url="https://openapivts.koreainvestment.com:29443",
                cache_path=str(cache_path),
            )
            manager._issue_new_access_token = Mock(side_effect=AssertionError("must not re-issue"))  # type: ignore[attr-defined]
            token = manager.get_valid_access_token()
            self.assertEqual(token, "cached-token")

    def test_auth_manager_issues_when_cache_missing(self) -> None:
        from integration.kis_auth_manager import KISAuthManager, TokenState

        with tempfile.TemporaryDirectory() as td:
            cache_path = Path(td) / "token.json"
            manager = KISAuthManager(
                app_key="k",
                app_secret="s",
                environment="paper",
                base_url="https://openapivts.koreainvestment.com:29443",
                cache_path=str(cache_path),
            )
            manager._issue_new_access_token = Mock(  # type: ignore[attr-defined]
                return_value=TokenState(
                    access_token="new-token",
                    issued_at=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
                    expires_at=datetime.fromisoformat("2099-01-01T00:00:00+00:00"),
                    environment="paper",
                )
            )
            token = manager.get_valid_access_token()
            self.assertEqual(token, "new-token")
            self.assertTrue(cache_path.exists())

    def test_auth_manager_reissues_when_cached_token_expired(self) -> None:
        from integration.kis_auth_manager import KISAuthManager, TokenState

        with tempfile.TemporaryDirectory() as td:
            cache_path = Path(td) / "token.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "access_token": "expired-token",
                        "issued_at": "2020-01-01T00:00:00+00:00",
                        "expires_at": "2020-01-01T00:01:00+00:00",
                        "environment": "paper",
                    }
                ),
                encoding="utf-8",
            )
            manager = KISAuthManager(
                app_key="k",
                app_secret="s",
                environment="paper",
                base_url="https://openapivts.koreainvestment.com:29443",
                cache_path=str(cache_path),
            )
            manager._issue_new_access_token = Mock(  # type: ignore[attr-defined]
                return_value=TokenState(
                    access_token="refreshed-token",
                    issued_at=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
                    expires_at=datetime.fromisoformat("2099-01-01T00:00:00+00:00"),
                    environment="paper",
                )
            )
            token = manager.get_valid_access_token()
            self.assertEqual(token, "refreshed-token")

    def test_kis_client_uses_auth_manager_for_authorization_header(self) -> None:
        from integration.kis_client import KISClient

        class FakeAuthManager:
            def __init__(self) -> None:
                self.called = False

            def get_valid_access_token(self) -> str:
                self.called = True
                return "token-from-manager"

            def describe_token_state(self) -> dict[str, str | bool]:
                return {"cache_exists": True, "token_present": True, "environment_match": True, "expired": False}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self) -> bytes:
                return b"{}"

        fake_manager = FakeAuthManager()
        client = KISClient(
            app_key="k",
            app_secret="s",
            account_number="50182316",
            product_code="01",
            environment="paper",
            exchange_code="NASD",
            auth_manager=fake_manager,  # type: ignore[arg-type]
        )

        def _fake_urlopen(req, timeout=15):
            self.assertEqual(req.headers.get("Authorization"), "Bearer token-from-manager")
            return FakeResponse()

        with patch("integration.kis_client.request.urlopen", side_effect=_fake_urlopen):
            client._request("GET", "/dummy", auth_required=True)
        self.assertTrue(fake_manager.called)

    def test_auth_error_message_does_not_expose_token_value(self) -> None:
        from integration.kis_auth_manager import KISAuthManager

        manager = KISAuthManager(
            app_key="k",
            app_secret="s",
            environment="paper",
            base_url="https://openapivts.koreainvestment.com:29443",
            cache_path=str(Path(tempfile.gettempdir()) / "kis_token_test.json"),
        )
        sensitive_token = "super-secret-token-value"
        body = json.dumps({"error_code": "EGW00133", "error_description": "rate limited", "access_token": sensitive_token})
        http_error = error.HTTPError(
            url="https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=io.BytesIO(body.encode("utf-8")),
        )

        with patch("integration.kis_auth_manager.request.urlopen", side_effect=http_error):
            with self.assertRaises(RuntimeError) as ctx:
                manager.force_refresh_access_token()
        self.assertNotIn(sensitive_token, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
