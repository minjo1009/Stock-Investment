from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "apps/ios-trader-brain/src/types/cockpit.ts",
    "apps/ios-trader-brain/src/lib/cockpit-data.ts",
    "apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts",
    "apps/ios-trader-brain/src/app/(tabs)/index.tsx",
    "apps/ios-trader-brain/src/app/(tabs)/trades.tsx",
    "apps/ios-trader-brain/src/app/trade/[id].tsx",
    "apps/ios-trader-brain/src/app/(tabs)/risk.tsx",
    "apps/ios-trader-brain/src/app/(tabs)/settings.tsx",
    "data/artifacts/task_3101_3120_db_navigation_ui_pass/db_navigation_ui_pass_report.png",
]

SCREENSHOTS = [
    "01_home.png",
    "02_trades.png",
    "03_detail.png",
    "04_risk.png",
    "05_settings.png",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required file: {rel}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required file: {rel}")

    types = read("apps/ios-trader-brain/src/types/cockpit.ts")
    for token in ["DataConnectorHealth", "RequiredDataFile", "RiskHealthMetric", "NavigationEdge", "dataHealth"]:
        if token not in types:
            errors.append(f"missing data contract type token: {token}")

    normalizer = read("apps/ios-trader-brain/src/lib/cockpit-data.ts")
    for token in ["normalizeDataHealth", "connector_health", "required_files", "risk_metrics", "navigationEdges"]:
        if token not in normalizer:
            errors.append(f"missing normalizer token: {token}")

    settings = read("apps/ios-trader-brain/src/app/(tabs)/settings.tsx")
    for token in ["Connector health", "Required files", "Page map", "dataHealth.connectors", "dataHealth.requiredFiles", "dataHealth.navigationEdges"]:
        if token not in settings:
            errors.append(f"settings missing visible contract token: {token}")

    risk = read("apps/ios-trader-brain/src/app/(tabs)/risk.tsx")
    for token in ["dataHealth.riskMetrics", "dataHealth.connectors", "symbolBlockers"]:
        if token not in risk:
            errors.append(f"risk missing contract token: {token}")

    home = read("apps/ios-trader-brain/src/app/(tabs)/index.tsx")
    for token in ["AccountTrendChart", "flowTitle", "trade.id / dataHealth.connectors"]:
        if token not in home:
            errors.append(f"home missing navigation token: {token}")

    detail = read("apps/ios-trader-brain/src/app/trade/[id].tsx")
    for token in ["selectedRange", "entryToNowPct", "latestVwapGapPct"]:
        if token not in detail:
            errors.append(f"detail missing selected range token: {token}")

    for forbidden in ["submitOrder", "placeOrder", "sendLiveOrder", "brokerMutation"]:
        for rel in REQUIRED_FILES[:8]:
            if forbidden in read(rel):
                errors.append(f"forbidden execution token {forbidden} in {rel}")

    screenshot_dir = ROOT / "data/artifacts/task_3101_3120_db_navigation_ui_pass/screenshots_live"
    for name in SCREENSHOTS:
        path = screenshot_dir / name
        if not path.exists() or path.stat().st_size <= 20_000:
            errors.append(f"missing or suspicious screenshot: {name}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3101-3120 DB-linked navigation UI pass is wired and bounded.")
    print("Validation authority: REPORTING_HEALTH only for UI contract checks.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

