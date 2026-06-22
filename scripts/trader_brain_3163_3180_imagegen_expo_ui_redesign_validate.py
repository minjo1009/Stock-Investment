from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    errors: list[str] = []

    checks = {
        "apps/ios-trader-brain/src/app/(tabs)/_layout.tsx": [
            "SymbolView",
            'title: "홈"',
            'title: "스캔"',
            'title: "분석"',
            'title: "시장"',
            'title: "위험"',
        ],
        "apps/ios-trader-brain/src/app/(tabs)/index.tsx": [
            "Trader Brain",
            "Total Assets",
            "Open Scanner",
            "Primary Blocker",
            "READ ONLY",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/trades.tsx": [
            "TACTICAL SCANNER",
            "Watchlist Console",
            "ThemeTape",
            "Search symbol / risk / source",
            "SELECTED CHART",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/analysis.tsx": [
            "Decision Console",
            "WHY NOW",
            "CATALYST",
            "INVALIDATION",
            "POLICY BLOCKER",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/market.tsx": [
            "Market Pulse",
            "Index Tape",
            "Macro Checks",
            "Theme Heat",
            "Event Timeline",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/risk.tsx": [
            "Risk Gate",
            "PRIMARY BLOCKER",
            "Limit Board",
            "Source Freshness",
            "Required Files",
        ],
    }

    for path, tokens in checks.items():
        text = read(path)
        for token in tokens:
            if token not in text:
                errors.append(f"{path} missing token: {token}")

    forbidden_tokens = [
        "submitOrder",
        "placeOrder",
        "sendLiveOrder",
        "realOrdersAllowed: true",
        "liveOrderButtonsAllowed: true",
    ]
    app_files = list(checks)
    for path in app_files:
        text = read(path)
        for token in forbidden_tokens:
            if token in text:
                errors.append(f"forbidden live-order token in {path}: {token}")

    artifact_paths = [
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/task3163_3180_ui_result_montage.png",
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/01_home.png",
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/02_scanner.png",
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/03_analysis.png",
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/04_market.png",
        "data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/05_risk.png",
    ]
    for path in artifact_paths:
        full = ROOT / path
        if not exists(path):
            errors.append(f"missing artifact: {path}")
        elif full.stat().st_size < 2500:
            errors.append(f"artifact too small: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3163-3180 ImageGen + Expo UI redesign is wired and bounded.")
    print("Validation authority: REPORTING_HEALTH only for UI/data-contract checks.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
