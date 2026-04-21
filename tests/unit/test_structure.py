from __future__ import annotations

import importlib
import inspect
import sys
import unittest
from pathlib import Path
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestRepositoryFoundationStructure(unittest.TestCase):
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
            "common.models",
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


if __name__ == "__main__":
    unittest.main()
