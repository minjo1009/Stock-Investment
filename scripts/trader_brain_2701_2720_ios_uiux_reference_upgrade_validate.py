from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/ios-trader-brain"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _read(relative_path: str) -> str:
    return (APP / relative_path).read_text(encoding="utf-8")


def main() -> None:
    package = json.loads((APP / "package.json").read_text(encoding="utf-8"))
    deps = package.get("dependencies", {})
    _assert(deps.get("expo", "").startswith("~54."), "Expo SDK must remain 54 for Expo Go compatibility")
    _assert(deps.get("expo-router", "").startswith("~6."), "Expo Router SDK54 route stack expected")
    _assert("react-native-svg" in deps, "chart rendering dependency missing")

    segmented = _read("src/components/segmented-control.tsx")
    symbol_row = _read("src/components/symbol-row.tsx")
    mini_sparkline = _read("src/components/mini-sparkline.tsx")
    benchmark_panel = _read("src/components/benchmark-panel.tsx")
    price_chart = _read("src/components/price-chart.tsx")
    account_strip = _read("src/components/account-strip.tsx")
    tab_benchmarks = _read("src/lib/tab-benchmarks.ts")
    root_layout = _read("src/app/_layout.tsx")
    home = _read("src/app/(tabs)/index.tsx")
    trades = _read("src/app/(tabs)/trades.tsx")
    risk = _read("src/app/(tabs)/risk.tsx")
    detail = _read("src/app/trade/[id].tsx")
    settings = _read("src/app/(tabs)/settings.tsx")
    loader = _read("src/lib/cockpit-data.ts")
    fixture = _read("src/fixtures/cockpit-fixture.ts")
    korean_labels = _read("src/lib/korean-labels.ts")
    tab_layout = _read("src/app/(tabs)/_layout.tsx")

    _assert("Pressable" in segmented and "selected" in segmented, "segmented control not implemented")
    _assert("SymbolRow" in symbol_row and "unrealizedPnlPct" in symbol_row, "dense symbol row not implemented")
    _assert("MiniSparkline" in symbol_row and "Polyline" in mini_sparkline, "watchlist mini sparkline not implemented")
    _assert("volume" in price_chart and "VWAP" in price_chart and "range" in price_chart, "chart lacks range/VWAP/volume UI")
    _assert("mode?: \"line\" | \"candles\"" in price_chart and "candle" in price_chart.lower(), "candlestick chart mode missing")
    _assert("내 포트폴리오" in home and "보유 종목" in home and "내 계좌" in account_strip, "Toss-style portfolio/account surface missing")
    _assert("관심/보유 종목" in trades and "종목 / 판단" in trades and "variant=\"dark\"" in trades, "TradingView-style dark watchlist surface missing")
    _assert("sortOptions" in trades and "손익" in trades and "가나다" in trades, "watchlist sorting controls missing")
    _assert("noTradeReasons" in risk and "거절한 후보" in risk, "risk/no-trade explanation surface missing")
    _assert("근거" in detail and "출처" in detail and "위험" in detail and "PriceChart" in detail, "chart-first trade detail tabs missing")
    _assert('headerShown: false' in root_layout, "trade detail native header should be hidden for chart-first surface")
    _assert("SDK 54" in settings, "SDK54 compatibility note missing")
    _assert("tabBenchmarks" in settings and "BenchmarkPanel" in settings, "settings tab benchmark map not rendered")
    _assert("내 포트폴리오" in home and "관심/보유 종목" in trades and "실거래는 막혀 있어요" in risk, "Korean paraphrased main tabs missing")
    _assert("홈" in tab_layout and "종목" in tab_layout and "위험" in tab_layout and "설정" in tab_layout, "Korean native tab labels missing")
    _assert("매수 근거 유지" in korean_labels and "진단 전용" in korean_labels, "Korean state label mapping missing")
    for tab_name in ["홈", "종목", "종목 상세", "위험", "설정"]:
        _assert(tab_name in tab_benchmarks, f"tab benchmark missing: {tab_name}")
    _assert("아직 더 가까워져야 할 부분" in benchmark_panel, "benchmark panel must expose remaining gaps")

    _assert("cockpitFixture" in loader and "cockpit-fixture.json" not in loader, "typed cockpit fixture not wired")
    _assert("realOrdersAllowed: false" in loader, "real order guard missing")
    _assert("liveOrderButtonsAllowed: false" in loader, "live order button guard missing")
    _assert("AVGO" in fixture and "CIEN" in fixture, "fixture should expose non-empty paper positions")
    _assert("AI 인프라" in fixture and "당시 확인 가능했던 정보" in fixture, "fixture explanation should be Korean-paraphrased")
    _assert("SURVIVAL_DILUTION_BLOCK" in fixture, "fixture should expose rejected/no-trade reasons")

    print("[TASK2701_2720_IOS_UIUX_REFERENCE_UPGRADE_VALIDATE_OK]")


if __name__ == "__main__":
    main()
