from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    checks = {
        "apps/trader-brain-web/package.json": [
            '"next": "16.2.9"',
            '"lightweight-charts": "5.2.0"',
            '"@tanstack/react-table": "8.21.3"',
            '"@assistant-ui/react": "0.14.23"',
        ],
        "apps/trader-brain-web/src/app/page.tsx": [
            "Institutional Tactical Console",
            "Tremor-style KPI patterns",
            "Tactical Console",
            "Portfolio / Risk",
            "Execution / Orders",
            "AI Research Chat",
            "No replay, no selector tuning, no paper/live order mutation.",
        ],
        "apps/trader-brain-web/src/components/TradingChart.tsx": [
            "lightweight-charts",
            "CandlestickSeries",
            "LineSeries",
            "HistogramSeries",
        ],
        "apps/trader-brain-web/src/components/CandidateTable.tsx": [
            "@tanstack/react-table",
            "useReactTable",
        ],
        "apps/trader-brain-web/src/lib/cockpit-data.ts": [
            "paper_ops_runtime_catalog.json",
            "paper_trade_detail_view.json",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
            "NOT_ACCEPTED",
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
    for path in checks:
        text = read(path)
        for token in forbidden_tokens:
            if token in text:
                errors.append(f"forbidden live-order token in {path}: {token}")

    artifact_paths = [
        "data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/05_desktop_cockpit_final.png",
        "data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/04_mobile_cockpit_responsive.png",
    ]
    for path in artifact_paths:
        full = ROOT / path
        if not full.exists():
            errors.append(f"missing artifact: {path}")
        elif full.stat().st_size < 20_000:
            errors.append(f"artifact too small: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3191-3210 Next cockpit redesign is wired and bounded.")
    print("Validation authority: REPORTING_HEALTH only for read-only frontend checks.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
