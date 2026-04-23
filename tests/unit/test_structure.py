from __future__ import annotations

import importlib
import inspect
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
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
            "src/app/run_trade_loop.py",
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
            "app.reconciliation",
            "app.report_recent_runs",
            "app.run_trade_loop",
            "app.run_trade_once",
            "common.models",
            "integration.kis_auth_manager",
            "integration.kis_client",
            "integration.slack_client",
            "state.store",
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

    def test_state_store_initialize_creates_required_tables(self) -> None:
        from state.store import initialize_store

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            con = sqlite3.connect(db_path)
            try:
                names = {
                    row[0]
                    for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                }
            finally:
                con.close()
            self.assertTrue(
                {
                    "trade_runs",
                    "orders",
                    "fills",
                    "positions",
                    "position_events",
                    "reconciliation_runs",
                    "reconciliation_events",
                }.issubset(names)
            )

    def test_state_store_trade_run_start_and_finish(self) -> None:
        from state.store import initialize_store, record_trade_run_finish, record_trade_run_start

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    "CREATE TABLE IF NOT EXISTS control_state (control_key TEXT PRIMARY KEY, run_mode TEXT NOT NULL, kill_switch_active INTEGER NOT NULL, kill_switch_reason TEXT)"
                )
                con.execute(
                    "INSERT OR REPLACE INTO control_state(control_key, run_mode, kill_switch_active, kill_switch_reason) VALUES ('default', 'LIVE_ENABLED', 0, NULL)"
                )
                con.commit()
            finally:
                con.close()
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_trade_run_finish(db_path, run_id, "FILLED", "2026-01-01T00:00:10Z")
            con = sqlite3.connect(db_path)
            try:
                row = con.execute(
                    "SELECT result_status, finished_at FROM trade_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
            finally:
                con.close()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], "FILLED")
            self.assertEqual(row[1], "2026-01-01T00:00:10Z")

    def test_state_store_order_insert_and_update(self) -> None:
        from state.store import (
            get_order,
            initialize_store,
            record_order,
            record_trade_run_start,
            update_order_status,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            update_order_status(db_path, "ord-1", "FILLED", raw_status="FILLED")
            row = get_order(db_path, "ord-1")
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["status"], "FILLED")
            self.assertEqual(row["raw_status"], "FILLED")

    def test_state_store_fill_insert_and_source_validation(self) -> None:
        from state.store import (
            get_fills_for_order,
            initialize_store,
            record_fill,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-2",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            record_fill(
                db_path,
                fill_id="ord-2:2026-01-01T00:00:03Z:ORDER_STATUS",
                order_id="ord-2",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=None,
                filled_at="2026-01-01T00:00:03Z",
                source="ORDER_STATUS",
            )
            fills = get_fills_for_order(db_path, "ord-2")
            self.assertEqual(len(fills), 1)
            self.assertEqual(fills[0]["source"], "ORDER_STATUS")

            with self.assertRaises(ValueError):
                record_fill(
                    db_path,
                    fill_id="ord-2:2026-01-01T00:00:04Z:BAD_SOURCE",
                    order_id="ord-2",
                    run_id=run_id,
                    symbol="AAPL",
                    side="BUY",
                    filled_quantity=1.0,
                    fill_price=None,
                    filled_at="2026-01-01T00:00:04Z",
                    source="BAD_SOURCE",
                )

    def test_state_store_fill_dedupe_ignores_duplicate_insert(self) -> None:
        from state.store import (
            FILL_DUPLICATE_IGNORED,
            FILL_INSERTED,
            get_fills_for_order,
            initialize_store,
            record_fill,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-dd1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            first = record_fill(
                db_path,
                fill_id="fill-1",
                order_id="ord-dd1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=190.0,
                filled_at="2026-01-01T00:00:03Z",
                source="ORDER_STATUS",
            )
            duplicate = record_fill(
                db_path,
                fill_id="fill-2-different-id-but-same-body",
                order_id="ord-dd1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=190.0,
                filled_at="2026-01-01T00:00:04Z",
                source="ORDER_STATUS",
            )
            fills = get_fills_for_order(db_path, "ord-dd1")
            self.assertEqual(first, FILL_INSERTED)
            self.assertEqual(duplicate, FILL_DUPLICATE_IGNORED)
            self.assertEqual(len(fills), 1)

    def test_state_store_fill_dedupe_applies_to_fallback_source(self) -> None:
        from state.store import (
            FILL_DUPLICATE_IGNORED,
            FILL_INSERTED,
            get_fills_for_order,
            initialize_store,
            record_fill,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-dd2",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            first = record_fill(
                db_path,
                fill_id="fill-fb-1",
                order_id="ord-dd2",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=None,
                filled_at="2026-01-01T00:00:03Z",
                source="POSITION_DELTA_FALLBACK",
            )
            duplicate = record_fill(
                db_path,
                fill_id="fill-fb-2",
                order_id="ord-dd2",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=None,
                filled_at="2026-01-01T00:00:04Z",
                source="POSITION_DELTA_FALLBACK",
            )
            fills = get_fills_for_order(db_path, "ord-dd2")
            self.assertEqual(first, FILL_INSERTED)
            self.assertEqual(duplicate, FILL_DUPLICATE_IGNORED)
            self.assertEqual(len(fills), 1)
            self.assertEqual(fills[0]["source"], "POSITION_DELTA_FALLBACK")

    def test_order_intent_key_is_deterministic(self) -> None:
        from state.store import build_order_intent_key

        key1 = build_order_intent_key(
            symbol="AAPL",
            side="BUY",
            intended_price=150.0,
            quantity=1.0,
            strategy_id="default",
        )
        key2 = build_order_intent_key(
            symbol="AAPL",
            side="BUY",
            intended_price=150.0,
            quantity=1.0,
            strategy_id="default",
        )
        self.assertEqual(key1, key2)

    def test_different_price_produces_different_intent_and_allows_submit_path(self) -> None:
        from state.store import (
            build_order_intent_key,
            has_blocking_order_intent,
            initialize_store,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            key_150 = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=150.0,
                quantity=1.0,
                strategy_id="default",
            )
            key_151 = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=151.0,
                quantity=1.0,
                strategy_id="default",
            )
            self.assertNotEqual(key_150, key_151)
            record_order(
                db_path,
                order_id="ord-intent-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                intent_key=key_150,
                submitted_at="2026-01-01T00:00:01Z",
                status="SUBMITTED",
                environment="paper",
            )
            self.assertTrue(has_blocking_order_intent(db_path, intent_key=key_150))
            self.assertFalse(has_blocking_order_intent(db_path, intent_key=key_151))

    def test_filled_status_does_not_block_same_intent(self) -> None:
        from state.store import (
            build_order_intent_key,
            has_blocking_order_intent,
            initialize_store,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            key = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=150.0,
                quantity=1.0,
                strategy_id="default",
            )
            record_order(
                db_path,
                order_id="ord-filled-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                intent_key=key,
                submitted_at="2026-01-01T00:00:01Z",
                status="FILLED",
                environment="paper",
            )
            self.assertFalse(has_blocking_order_intent(db_path, intent_key=key))

    def test_recent_intent_window_blocking(self) -> None:
        from state.store import (
            build_order_intent_key,
            has_recent_order_intent,
            initialize_store,
            record_order,
            record_trade_run_start,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            key = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=150.0,
                quantity=1.0,
                strategy_id="default",
            )
            record_order(
                db_path,
                order_id="ord-recent-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                intent_key=key,
                submitted_at="2026-01-01T00:00:30Z",
                status="FILLED",
                environment="paper",
            )
            self.assertTrue(
                has_recent_order_intent(
                    db_path,
                    intent_key=key,
                    within_seconds=60,
                    now_iso="2026-01-01T00:01:00Z",
                )
            )
            self.assertFalse(
                has_recent_order_intent(
                    db_path,
                    intent_key=key,
                    within_seconds=10,
                    now_iso="2026-01-01T00:01:00Z",
                )
            )

    def test_reconciliation_clean_does_not_block(self) -> None:
        from app.reconciliation import reconcile_local_and_broker

        outcome = reconcile_local_and_broker(
            local_open_orders=[
                {"order_id": "o1", "symbol": "AAPL", "status": "SUBMITTED"},
            ],
            local_filled_order_ids=set(),
            broker_orders=[
                {
                    "order_id": "o1",
                    "symbol": "AAPL",
                    "mapped_status": "SUBMITTED",
                    "filled_qty": 0.0,
                    "order_qty": 1.0,
                }
            ],
        )
        self.assertEqual(outcome.status, "CLEAN")
        self.assertEqual(outcome.severity, "INFO")
        self.assertFalse(outcome.block_new_orders)
        self.assertEqual(len(outcome.events), 0)

    def test_reconciliation_missing_local_blocks(self) -> None:
        from app.reconciliation import reconcile_local_and_broker

        outcome = reconcile_local_and_broker(
            local_open_orders=[],
            local_filled_order_ids=set(),
            broker_orders=[
                {
                    "order_id": "bo1",
                    "symbol": "AAPL",
                    "mapped_status": "SUBMITTED",
                    "filled_qty": 0.0,
                    "order_qty": 1.0,
                }
            ],
        )
        self.assertEqual(outcome.status, "MISMATCH")
        self.assertEqual(outcome.severity, "CRITICAL")
        self.assertTrue(outcome.block_new_orders)
        self.assertTrue(any(e["event_type"] == "MISSING_LOCAL" for e in outcome.events))

    def test_reconciliation_missing_broker_blocks(self) -> None:
        from app.reconciliation import reconcile_local_and_broker

        outcome = reconcile_local_and_broker(
            local_open_orders=[{"order_id": "lo1", "symbol": "AAPL", "status": "SUBMITTED"}],
            local_filled_order_ids=set(),
            broker_orders=[],
        )
        self.assertEqual(outcome.status, "MISMATCH")
        self.assertEqual(outcome.severity, "CRITICAL")
        self.assertTrue(outcome.block_new_orders)
        self.assertTrue(any(e["event_type"] == "MISSING_BROKER" for e in outcome.events))

    def test_reconciliation_unknown_status_is_warn_not_block(self) -> None:
        from app.reconciliation import reconcile_local_and_broker

        outcome = reconcile_local_and_broker(
            local_open_orders=[{"order_id": "o1", "symbol": "AAPL", "status": "SUBMITTED"}],
            local_filled_order_ids=set(),
            broker_orders=[
                {
                    "order_id": "o1",
                    "symbol": "AAPL",
                    "mapped_status": "UNKNOWN",
                    "filled_qty": 0.0,
                    "order_qty": 1.0,
                }
            ],
        )
        self.assertEqual(outcome.status, "MISMATCH")
        self.assertEqual(outcome.severity, "WARN")
        self.assertFalse(outcome.block_new_orders)
        self.assertTrue(any(e["severity"] == "WARN" for e in outcome.events))

    def test_reconciliation_critical_only_blocks(self) -> None:
        from app.reconciliation import reconcile_local_and_broker

        warn_outcome = reconcile_local_and_broker(
            local_open_orders=[{"order_id": "o1", "symbol": "AAPL", "status": "SUBMITTED"}],
            local_filled_order_ids=set(),
            broker_orders=[
                {
                    "order_id": "o1",
                    "symbol": "AAPL",
                    "mapped_status": "UNKNOWN",
                    "filled_qty": 0.0,
                    "order_qty": 1.0,
                }
            ],
        )
        self.assertFalse(warn_outcome.block_new_orders)

        critical_outcome = reconcile_local_and_broker(
            local_open_orders=[{"order_id": "o2", "symbol": "AAPL", "status": "SUBMITTED"}],
            local_filled_order_ids=set(),
            broker_orders=[
                {
                    "order_id": "o2",
                    "symbol": "AAPL",
                    "mapped_status": "REJECTED",
                    "filled_qty": 0.0,
                    "order_qty": 1.0,
                }
            ],
        )
        self.assertTrue(critical_outcome.block_new_orders)
        self.assertEqual(critical_outcome.severity, "CRITICAL")

    def test_broker_status_mapping_table(self) -> None:
        from app.reconciliation import map_broker_status

        self.assertEqual(map_broker_status("FILLED"), "FILLED")
        self.assertEqual(map_broker_status("PARTIALLY_FILLED"), "SUBMITTED")
        self.assertEqual(map_broker_status("OPEN"), "SUBMITTED")
        self.assertEqual(map_broker_status("CANCELLED"), "CANCELLED")
        self.assertEqual(map_broker_status("REJECTED"), "REJECTED")

    def test_broker_status_mapping_unknown_fallback(self) -> None:
        from app.reconciliation import map_broker_status

        self.assertEqual(map_broker_status("SOMETHING_NEW"), "UNKNOWN")
        self.assertEqual(map_broker_status(""), "UNKNOWN")

    def test_reconciliation_persistence_records_run_and_events(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import initialize_store, list_reconciliation_events, list_recent_reconciliation_runs, record_trade_run_start

        class FakeKIS:
            def fetch_broker_order_statuses(self, *, symbol: str | None = None):
                return [
                    {
                        "order_id": "bo1",
                        "symbol": "AAPL",
                        "mapped_status": "SUBMITTED",
                        "filled_qty": 0.0,
                        "order_qty": 1.0,
                    }
                ]

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            outcome = run_trade_once._run_reconciliation_check(  # type: ignore[attr-defined]
                db_path=db_path,
                run_id=run_id,
                symbol="AAPL",
                kis=FakeKIS(),  # type: ignore[arg-type]
            )
            self.assertEqual(outcome.status, "MISMATCH")
            rows = list_recent_reconciliation_runs(db_path, limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "MISMATCH")
            self.assertEqual(rows[0]["max_severity"], "CRITICAL")
            recon_id = rows[0]["reconciliation_id"]
            events = list_reconciliation_events(db_path, recon_id)
            self.assertGreaterEqual(len(events), 1)
            self.assertEqual(events[0]["event_type"], "MISSING_LOCAL")

    def test_reconciliation_broker_fetch_failure_blocks(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import initialize_store, list_recent_reconciliation_runs, record_trade_run_start

        class FailingKIS:
            def fetch_broker_order_statuses(self, *, symbol: str | None = None):
                raise RuntimeError("broker down")

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            outcome = run_trade_once._run_reconciliation_check(  # type: ignore[attr-defined]
                db_path=db_path,
                run_id=run_id,
                symbol="AAPL",
                kis=FailingKIS(),  # type: ignore[arg-type]
            )
            self.assertEqual(outcome.status, "ERROR")
            self.assertEqual(outcome.severity, "CRITICAL")
            self.assertTrue(outcome.block_new_orders)
            rows = list_recent_reconciliation_runs(db_path, limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "ERROR")
            self.assertEqual(rows[0]["block_new_orders"], 1)
            self.assertEqual(rows[0]["max_severity"], "CRITICAL")

    def test_run_trade_once_blocks_duplicate_intent_before_submit(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import build_order_intent_key, initialize_store, record_order, record_trade_run_start

        class FakeKIS:
            environment = "paper"

            def __init__(self) -> None:
                self.submit_called = False

            def describe_auth_state(self) -> dict[str, bool]:
                return {"token_present": True, "expired": False}

            def get_position_quantity(self, symbol: str) -> int:
                return 0

            def get_current_price(self, symbol: str) -> float:
                return 182.3

            def fetch_broker_order_statuses(self, *, symbol: str | None = None):
                return [
                    {
                        "order_id": "ord-dup-1",
                        "symbol": "AAPL",
                        "mapped_status": "SUBMITTED",
                        "filled_qty": 0.0,
                        "order_qty": 1.0,
                    }
                ]

            def submit_order(self, symbol: str, side: str, quantity: int, limit_price: float) -> str:
                self.submit_called = True
                return "ord-should-not-happen"

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    "CREATE TABLE IF NOT EXISTS control_state (control_key TEXT PRIMARY KEY, run_mode TEXT NOT NULL, kill_switch_active INTEGER NOT NULL, kill_switch_reason TEXT)"
                )
                con.execute(
                    "INSERT OR REPLACE INTO control_state(control_key, run_mode, kill_switch_active, kill_switch_reason) VALUES ('default', 'LIVE_ENABLED', 0, NULL)"
                )
                con.commit()
            finally:
                con.close()
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            key = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=182.3,
                quantity=1.0,
                strategy_id="default",
            )
            record_order(
                db_path,
                order_id="ord-dup-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                intent_key=key,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )

            fake_kis = FakeKIS()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "KIS_ENVIRONMENT": "paper",
                    "TRADING_INTENT_RECENT_SEC": "0",
                },
                clear=False,
            ):
                with patch("app.run_trade_once.KISClient.from_env", return_value=fake_kis):
                    with patch("app.run_trade_once.slack_client.send_message"):
                        run_trade_once.run()

            self.assertFalse(fake_kis.submit_called)
            con = sqlite3.connect(db_path)
            try:
                latest = con.execute(
                    "SELECT result_status FROM trade_runs ORDER BY started_at DESC LIMIT 1"
                ).fetchone()
            finally:
                con.close()
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest[0], "SKIPPED_DUPLICATE")

    def test_run_trade_once_recon_block_skips_submit(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import initialize_store

        class FakeKIS:
            environment = "paper"

            def __init__(self) -> None:
                self.submit_called = False

            def describe_auth_state(self) -> dict[str, bool]:
                return {"token_present": True, "expired": False}

            def fetch_broker_order_statuses(self, *, symbol: str | None = None):
                return [
                    {
                        "order_id": "bo-recon-1",
                        "symbol": "AAPL",
                        "mapped_status": "SUBMITTED",
                        "filled_qty": 0.0,
                        "order_qty": 1.0,
                    }
                ]

            def submit_order(self, symbol: str, side: str, quantity: int, limit_price: float):
                self.submit_called = True
                return "ord-should-not-submit"

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    "CREATE TABLE IF NOT EXISTS control_state (control_key TEXT PRIMARY KEY, run_mode TEXT NOT NULL, kill_switch_active INTEGER NOT NULL, kill_switch_reason TEXT)"
                )
                con.execute(
                    "INSERT OR REPLACE INTO control_state(control_key, run_mode, kill_switch_active, kill_switch_reason) VALUES ('default', 'LIVE_ENABLED', 0, NULL)"
                )
                con.commit()
            finally:
                con.close()

            fake_kis = FakeKIS()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "KIS_ENVIRONMENT": "paper",
                },
                clear=False,
            ):
                with patch("app.run_trade_once.KISClient.from_env", return_value=fake_kis):
                    with patch("app.run_trade_once.slack_client.send_message"):
                        run_trade_once.run()

            self.assertFalse(fake_kis.submit_called)
            con = sqlite3.connect(db_path)
            try:
                latest = con.execute(
                    "SELECT result_status FROM trade_runs ORDER BY started_at DESC LIMIT 1"
                ).fetchone()
            finally:
                con.close()
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest[0], "SKIPPED_RECON_BLOCK")

    def test_recon_alert_triggers_on_critical(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import initialize_store

        class FakeKIS:
            environment = "paper"

            def describe_auth_state(self) -> dict[str, bool]:
                return {"token_present": True, "expired": False}

            def fetch_broker_order_statuses(self, *, symbol: str | None = None):
                return [
                    {
                        "order_id": "bo-alert-1",
                        "symbol": "AAPL",
                        "mapped_status": "SUBMITTED",
                        "filled_qty": 0.0,
                        "order_qty": 1.0,
                    }
                ]

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    "CREATE TABLE IF NOT EXISTS control_state (control_key TEXT PRIMARY KEY, run_mode TEXT NOT NULL, kill_switch_active INTEGER NOT NULL, kill_switch_reason TEXT)"
                )
                con.execute(
                    "INSERT OR REPLACE INTO control_state(control_key, run_mode, kill_switch_active, kill_switch_reason) VALUES ('default', 'LIVE_ENABLED', 0, NULL)"
                )
                con.commit()
            finally:
                con.close()
            with patch.dict(
                os.environ,
                {"TRADING_DB_PATH": db_path, "KIS_ENVIRONMENT": "paper", "TRADING_RECON_ALERT": "true"},
                clear=False,
            ):
                with patch("app.run_trade_once.KISClient.from_env", return_value=FakeKIS()):
                    with patch("app.run_trade_once.slack_client.send_message") as slack_mock:
                        run_trade_once.run()
            self.assertTrue(slack_mock.called)
            called_texts = [str(call.args[0]) for call in slack_mock.call_args_list if call.args]
            self.assertTrue(any("[RECON ALERT]" in text for text in called_texts))

    def test_position_first_fill_creates_snapshot(self) -> None:
        from state.store import apply_fill_to_position

        new_qty, new_avg = apply_fill_to_position(
            old_quantity=0.0,
            old_avg_price=0.0,
            fill_side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
        )
        self.assertEqual(new_qty, 1.0)
        self.assertEqual(new_avg, 100.0)

    def test_position_two_buys_updates_weighted_avg_price(self) -> None:
        from state.store import apply_fill_to_position

        qty1, avg1 = apply_fill_to_position(
            old_quantity=0.0,
            old_avg_price=0.0,
            fill_side="BUY",
            fill_quantity=1.0,
            fill_price=100.0,
        )
        qty2, avg2 = apply_fill_to_position(
            old_quantity=qty1,
            old_avg_price=avg1,
            fill_side="BUY",
            fill_quantity=1.0,
            fill_price=200.0,
        )
        self.assertEqual(qty2, 2.0)
        self.assertAlmostEqual(avg2, 150.0)

    def test_position_event_record_inserted(self) -> None:
        from state.store import (
            POSITION_EVENT_INSERTED,
            initialize_store,
            record_position_event,
        )

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            result = record_position_event(
                db_path,
                run_id="run-1",
                order_id="ord-1",
                fill_id="fill-1",
                symbol="AAPL",
                side="LONG",
                fill_qty=1.0,
                fill_price=100.0,
                position_qty_after=1.0,
                avg_price_after=100.0,
                created_at="2026-01-01T00:00:03Z",
            )
            self.assertEqual(result, POSITION_EVENT_INSERTED)
            con = sqlite3.connect(db_path)
            try:
                row = con.execute(
                    "SELECT fill_id, position_qty_after, avg_price_after FROM position_events WHERE fill_id = ?",
                    ("fill-1",),
                ).fetchone()
            finally:
                con.close()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], "fill-1")
            self.assertEqual(row[1], 1.0)
            self.assertEqual(row[2], 100.0)

    def test_positions_overwrite_latest_snapshot(self) -> None:
        from state.store import get_position, initialize_store, upsert_position

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            upsert_position(
                db_path,
                symbol="AAPL",
                side="LONG",
                quantity=1.0,
                avg_price=100.0,
                updated_at="2026-01-01T00:00:01Z",
            )
            upsert_position(
                db_path,
                symbol="AAPL",
                side="LONG",
                quantity=2.0,
                avg_price=150.0,
                updated_at="2026-01-01T00:00:02Z",
            )
            pos = get_position(db_path, "AAPL")
            self.assertIsNotNone(pos)
            assert pos is not None
            self.assertEqual(pos["quantity"], 2.0)
            self.assertEqual(pos["avg_price"], 150.0)
            self.assertEqual(pos["updated_at"], "2026-01-01T00:00:02Z")

    def test_report_recent_runs_cli_outputs_rows(self) -> None:
        from app.report_recent_runs import main
        from state.store import initialize_store, record_fill, record_order, record_trade_run_start

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-cli-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="FILLED",
                environment="paper",
            )
            record_fill(
                db_path,
                fill_id="fill-cli-1",
                order_id="ord-cli-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                filled_quantity=1.0,
                fill_price=None,
                filled_at="2026-01-01T00:00:03Z",
                source="POSITION_DELTA_FALLBACK",
            )
            out = io.StringIO()
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with redirect_stdout(out):
                    code = main(["--limit", "5"])
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("run_id=", text)
            self.assertIn("order_id=ord-cli-1", text)
            self.assertIn("fill=YES", text)
            self.assertIn("fill_source=POSITION_DELTA_FALLBACK", text)
            self.assertIn("fallback_used=YES", text)

    def test_report_recent_runs_cli_show_intent_key(self) -> None:
        from app.report_recent_runs import main
        from state.store import build_order_intent_key, initialize_store, record_order, record_trade_run_start

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            intent_key = build_order_intent_key(
                symbol="AAPL",
                side="BUY",
                intended_price=100.0,
                quantity=1.0,
                strategy_id="default",
            )
            record_order(
                db_path,
                order_id="ord-cli-intent-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                intent_key=intent_key,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            out = io.StringIO()
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with redirect_stdout(out):
                    code = main(["--limit", "5", "--show-intent-key"])
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn(f"intent_key={intent_key}", text)

    def test_report_recent_runs_cli_show_reconciliation(self) -> None:
        from app.report_recent_runs import main
        from state.store import initialize_store, record_reconciliation_run

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            record_reconciliation_run(
                db_path,
                run_id="run-1",
                started_at="2026-01-01T00:00:00Z",
                finished_at="2026-01-01T00:00:01Z",
                status="MISMATCH",
                max_severity="CRITICAL",
                block_new_orders=True,
                summary_text="1 mismatch event(s) detected",
                raw_snapshot_json='{"broker_orders":[]}',
            )
            out = io.StringIO()
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with redirect_stdout(out):
                    code = main(["--limit", "5", "--show-reconciliation"])
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("[Reconciliation Runs]", text)
            self.assertIn("status=MISMATCH", text)
            self.assertIn("block_new_orders=1", text)

    def test_report_recent_runs_cli_no_data(self) -> None:
        from app.report_recent_runs import main
        from state.store import initialize_store

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            out = io.StringIO()
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with redirect_stdout(out):
                    code = main(["--limit", "3"])
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("No runs found", text)

    def test_report_recent_runs_cli_positions(self) -> None:
        from app.report_recent_runs import main
        from state.store import initialize_store, upsert_position

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            upsert_position(
                db_path,
                symbol="AAPL",
                side="LONG",
                quantity=3.0,
                avg_price=123.45,
                updated_at="2026-01-01T00:00:20Z",
            )
            out = io.StringIO()
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with redirect_stdout(out):
                    code = main(["--positions"])
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("symbol | qty | avg_price | updated_at", text)
            self.assertIn("AAPL | 3.0 | 123.45 | 2026-01-01T00:00:20Z", text)

    def test_run_trade_once_has_store_initialize_and_env_db_path(self) -> None:
        import app.run_trade_once as run_trade_once

        source = inspect.getsource(run_trade_once)
        self.assertIn("TRADING_DB_PATH", source)
        self.assertIn("initialize_store(db_path)", source)

    def test_report_recent_runs_uses_trading_db_path_env(self) -> None:
        import app.report_recent_runs as report_recent_runs

        source = inspect.getsource(report_recent_runs)
        self.assertIn("TRADING_DB_PATH", source)

    def test_run_trade_loop_max_runs_one_calls_once(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = str(Path(td) / ".trading.lock")
            run_once = Mock()
            sleep_fn = Mock()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "TRADING_KILL_SWITCH": "false",
                    "TRADING_LOOP_INTERVAL_SEC": "5",
                },
                clear=False,
            ):
                code = run_loop(max_runs=1, lock_path=lock_path, run_once_fn=run_once, sleep_fn=sleep_fn)
            self.assertEqual(code, 0)
            run_once.assert_called_once()
            sleep_fn.assert_not_called()
            self.assertFalse(Path(lock_path).exists())

    def test_run_trade_loop_kill_switch_stops_before_run(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = str(Path(td) / ".trading.lock")
            run_once = Mock()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "TRADING_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                code = run_loop(max_runs=1, lock_path=lock_path, run_once_fn=run_once)
            self.assertEqual(code, 0)
            run_once.assert_not_called()
            self.assertFalse(Path(lock_path).exists())

    def test_run_trade_loop_lock_file_blocks_execution(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = Path(td) / ".trading.lock"
            lock_path.write_text("99999", encoding="utf-8")
            run_once = Mock()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "TRADING_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                code = run_loop(max_runs=1, lock_path=str(lock_path), run_once_fn=run_once)
            self.assertEqual(code, 1)
            run_once.assert_not_called()
            self.assertTrue(lock_path.exists())

    def test_run_trade_loop_stale_lock_dead_pid_allows_start(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = Path(td) / ".trading.lock"
            lock_path.write_text('{"pid": 424242, "created_at": "2026-01-01T00:00:00Z"}', encoding="utf-8")
            run_once = Mock()
            with patch("app.run_trade_loop._pid_is_running", return_value=False):
                with patch.dict(
                    os.environ,
                    {"TRADING_DB_PATH": db_path, "TRADING_KILL_SWITCH": "false"},
                    clear=False,
                ):
                    code = run_loop(max_runs=1, lock_path=str(lock_path), run_once_fn=run_once)
            self.assertEqual(code, 0)
            run_once.assert_called_once()

    def test_run_trade_loop_stale_lock_live_pid_blocks_start(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = Path(td) / ".trading.lock"
            lock_path.write_text('{"pid": 123, "created_at": "2026-01-01T00:00:00Z"}', encoding="utf-8")
            run_once = Mock()
            with patch("app.run_trade_loop._pid_is_running", return_value=True):
                with patch.dict(
                    os.environ,
                    {"TRADING_DB_PATH": db_path, "TRADING_KILL_SWITCH": "false"},
                    clear=False,
                ):
                    code = run_loop(max_runs=1, lock_path=str(lock_path), run_once_fn=run_once)
            self.assertEqual(code, 1)
            run_once.assert_not_called()

    def test_run_trade_loop_interval_applies_between_runs(self) -> None:
        from app.run_trade_loop import run_loop

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = str(Path(td) / ".trading.lock")
            run_once = Mock()
            sleep_fn = Mock()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "TRADING_KILL_SWITCH": "false",
                    "TRADING_LOOP_INTERVAL_SEC": "2",
                },
                clear=False,
            ):
                code = run_loop(max_runs=2, lock_path=lock_path, run_once_fn=run_once, sleep_fn=sleep_fn)
            self.assertEqual(code, 0)
            self.assertEqual(run_once.call_count, 2)
            sleep_fn.assert_called_once_with(2)

    def test_run_trade_loop_logs_positions_and_open_orders(self) -> None:
        from app.run_trade_loop import run_loop
        from state.store import initialize_store, record_order, record_trade_run_start, upsert_position

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            lock_path = str(Path(td) / ".trading.lock")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            upsert_position(
                db_path,
                symbol="AAPL",
                side="LONG",
                quantity=1.0,
                avg_price=100.0,
                updated_at="2026-01-01T00:00:01Z",
            )
            record_order(
                db_path,
                order_id="ord-open-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:02Z",
                status="SUBMITTED",
                environment="paper",
            )
            run_once = Mock()
            out = io.StringIO()
            with patch.dict(
                os.environ,
                {
                    "TRADING_DB_PATH": db_path,
                    "TRADING_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                with redirect_stdout(out):
                    code = run_loop(max_runs=1, lock_path=lock_path, run_once_fn=run_once)
            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("[INFO] current position exists:", text)
            self.assertIn("[INFO] open orders: count=1", text)

    def test_backtest_daily_loader_loads_and_sorts_csv(self) -> None:
        import pandas as pd
        from backtest.data_loader import load_daily_bars

        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td) / "data" / "raw" / "us_daily"
            base_dir.mkdir(parents=True, exist_ok=True)
            csv_path = base_dir / "AAPL.csv"

            raw = pd.DataFrame(
                [
                    {"timestamp": "2026-01-03", "open": 102, "high": 103, "low": 101, "close": 102.5, "volume": 1100, "symbol": "AAPL"},
                    {"timestamp": "2026-01-01", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000, "symbol": "AAPL"},
                    {"timestamp": "2026-01-02", "open": 101, "high": 102, "low": 100, "close": 101.5, "volume": 1050, "symbol": "AAPL"},
                ]
            )
            raw.to_csv(csv_path, index=False)

            loaded = load_daily_bars("AAPL", base_dir=base_dir)
            self.assertEqual(list(loaded["symbol"].unique()), ["AAPL"])
            self.assertEqual(
                list(loaded["timestamp"].dt.strftime("%Y-%m-%d")),
                ["2026-01-01", "2026-01-02", "2026-01-03"],
            )
            for col in ("timestamp", "open", "high", "low", "close", "volume", "symbol"):
                self.assertIn(col, loaded.columns)

    def test_backtest_daily_loader_missing_required_columns_raises(self) -> None:
        import pandas as pd
        from backtest.data_loader import load_daily_bars

        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td) / "data" / "raw" / "us_daily"
            base_dir.mkdir(parents=True, exist_ok=True)
            csv_path = base_dir / "MSFT.csv"
            bad = pd.DataFrame(
                [
                    {"timestamp": "2026-01-01", "open": 1, "high": 2, "low": 1, "volume": 1000, "symbol": "MSFT"}
                ]
            )  # close column missing
            bad.to_csv(csv_path, index=False)

            with self.assertRaises(ValueError):
                load_daily_bars("MSFT", base_dir=base_dir)

    def test_backtest_universe_loader_returns_symbol_map(self) -> None:
        import pandas as pd
        from backtest.data_loader import load_universe_daily_bars

        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td) / "data" / "raw" / "us_daily"
            base_dir.mkdir(parents=True, exist_ok=True)

            for symbol in ("AAPL", "NVDA"):
                pd.DataFrame(
                    [
                        {
                            "timestamp": "2026-01-01",
                            "open": 100.0,
                            "high": 101.0,
                            "low": 99.0,
                            "close": 100.5,
                            "volume": 1000000,
                            "symbol": symbol,
                        }
                    ]
                ).to_csv(base_dir / f"{symbol}.csv", index=False)

            result = load_universe_daily_bars(["AAPL", "NVDA"], base_dir=base_dir)
            self.assertEqual(set(result.keys()), {"AAPL", "NVDA"})
            self.assertEqual(len(result["AAPL"]), 1)
            self.assertEqual(result["NVDA"].iloc[0]["symbol"], "NVDA")


if __name__ == "__main__":
    unittest.main()
