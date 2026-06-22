from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    errors: list[str] = []

    cockpit = read("apps/ios-trader-brain/src/types/cockpit.ts")
    for token in [
        "MarketContext",
        "ThemeHeatRow",
        "SymbolCatalyst",
        "TradeReview",
        "marketContext",
        "themeHeat",
        "tradeReview",
    ]:
        if token not in cockpit:
            errors.append(f"cockpit contract missing token: {token}")

    normalizer = read("apps/ios-trader-brain/src/lib/cockpit-data.ts")
    for token in [
        "normalizeMarketContext",
        "normalizeThemeHeat",
        "normalizeSymbolCatalysts",
        "normalizeTradeReview",
        "SOURCE_NOT_ATTACHED",
    ]:
        if token not in normalizer:
            errors.append(f"normalizer missing token: {token}")

    tabs = read("apps/ios-trader-brain/src/app/(tabs)/_layout.tsx")
    for token in ["홈", "스캔", "분석", "시장", "위험"]:
        if token not in tabs:
            errors.append(f"tabs missing Korean label: {token}")

    for path, tokens in {
        "apps/ios-trader-brain/src/app/(tabs)/index.tsx": ["오늘의 계좌", "지금 봐야 할 3개", "marketContext"],
        "apps/ios-trader-brain/src/app/(tabs)/trades.tsx": ["테마 히트리스트", "themeHeat"],
        "apps/ios-trader-brain/src/app/(tabs)/analysis.tsx": ["판단 콘솔", "tradeReview", "symbolCatalysts"],
        "apps/ios-trader-brain/src/app/(tabs)/market.tsx": ["시장 상태", "themeHeat", "eventTimeline"],
        "apps/ios-trader-brain/src/app/(tabs)/risk.tsx": ["위험 보드", "Macro Risk Board", "LIVE ORDERS 0"],
    }.items():
        text = read(path)
        for token in tokens:
            if token not in text:
                errors.append(f"{path} missing token: {token}")

    for forbidden in ["submitOrder", "placeOrder", "sendLiveOrder", "realOrdersAllowed: true", "liveOrderButtonsAllowed: true"]:
        for path in [
            "apps/ios-trader-brain/src/app/(tabs)/index.tsx",
            "apps/ios-trader-brain/src/app/(tabs)/trades.tsx",
            "apps/ios-trader-brain/src/app/(tabs)/analysis.tsx",
            "apps/ios-trader-brain/src/app/(tabs)/market.tsx",
            "apps/ios-trader-brain/src/app/(tabs)/risk.tsx",
        ]:
            if forbidden in read(path):
                errors.append(f"forbidden live-order token in {path}: {forbidden}")

    for path in [
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/hybrid_investment_app_redesign_report.png",
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/01_home.png",
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/02_scanner.png",
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/03_analysis.png",
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/04_market.png",
        "data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/05_risk.png",
    ]:
        if not exists(path):
            errors.append(f"missing artifact: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3128-3140 hybrid investment app redesign is wired and bounded.")
    print("Validation authority: REPORTING_HEALTH only for UI/data-contract checks.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
