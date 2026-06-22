from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    errors: list[str] = []

    checks = {
        "apps/ios-trader-brain/src/app/(tabs)/trades.tsx": [
            "TACTICAL SCANNER",
            "Watchlist Console",
            "ThemeTape",
            "trade.id",
            "LIVE ORDER LOCKED",
            "panelWidth",
        ],
        "apps/ios-trader-brain/src/app/trade/[id].tsx": [
            "execution chart",
            "ENTRY VWAP",
            "LAST VWAP",
            "NO LIVE ORDERS",
            "panelWidth",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/index.tsx": [
            "Total assets",
            "Top 3 now",
            "Primary blocker",
            "NO LIVE ORDERS",
        ],
        "apps/ios-trader-brain/src/app/(tabs)/analysis.tsx": [
            "Decision Console",
            "WHY NOW",
            "INVALIDATION",
            "POLICY BLOCKER",
            "panelWidth",
        ],
        "apps/ios-trader-brain/src/components/price-chart.tsx": [
            "chartHeight = expanded ? 382 : 270",
            "selected.open",
            "VWAP",
            "VOL",
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
    app_files = [
        "apps/ios-trader-brain/src/app/(tabs)/index.tsx",
        "apps/ios-trader-brain/src/app/(tabs)/trades.tsx",
        "apps/ios-trader-brain/src/app/(tabs)/analysis.tsx",
        "apps/ios-trader-brain/src/app/trade/[id].tsx",
        "apps/ios-trader-brain/src/components/price-chart.tsx",
    ]
    for path in app_files:
        text = read(path)
        for token in forbidden_tokens:
            if token in text:
                errors.append(f"forbidden live-order token in {path}: {token}")

    artifact_paths = [
        "data/artifacts/task_3147_3160_tactical_console_redesign/tactical_console_redesign_report.png",
        "data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/01_home.png",
        "data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/02_scanner.png",
        "data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/03_detail.png",
        "data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/04_analysis.png",
        "data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/05_risk.png",
    ]
    for path in artifact_paths:
        if not exists(path):
            errors.append(f"missing artifact: {path}")
        elif (ROOT / path).stat().st_size < 2500:
            errors.append(f"artifact too small: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3147-3160 tactical console redesign is wired and bounded.")
    print("Validation authority: REPORTING_HEALTH only for UI/data-contract checks.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
