from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/artifacts/task_3061_3080_actual_mobile_app_benchmark"

REQUIRED = [
    "docs/reports/task_3061_3080_actual_mobile_app_benchmark/task_3061_3080_actual_mobile_app_benchmark.md",
    "docs/reports/task_3061_3080_actual_mobile_app_benchmark/task_3080_decision.csv",
    "data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_mobile_app_ui_benchmark_report.png",
    "data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_appstore_contact_sheet.png",
    "data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_mobile_appstore_screenshot_manifest.csv",
    "data/artifacts/task_3061_3080_actual_mobile_app_benchmark/curated_mobile_app_reference_matrix.csv",
    "data/artifacts/task_3061_3080_actual_mobile_app_benchmark/artifact_manifest.md",
]

CURATED = [
    "tradingview_chart_card.jpg",
    "tradingview_watchlist_card.jpg",
    "tradingview_detail_card.jpg",
]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required artifact: {rel}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required artifact: {rel}")

    raw = BASE / "raw_appstore_screenshots"
    raw_count = len(list(raw.glob("*.jpg"))) if raw.exists() else 0
    if raw_count < 40:
        errors.append(f"too few actual App Store screenshots: {raw_count}")

    curated = BASE / "curated_references"
    for name in CURATED:
        path = curated / name
        if not path.exists() or path.stat().st_size <= 1024:
            errors.append(f"missing curated TradingView phone card: {name}")

    report = (ROOT / REQUIRED[0]).read_text(encoding="utf-8")
    manifest = (ROOT / REQUIRED[-1]).read_text(encoding="utf-8")
    combined = report + "\n" + manifest
    for required in [
        "Supersedes",
        "actual mobile app screenshots",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "app code changes 0",
        "live orders 0",
        "REPORTING_HEALTH",
    ]:
        if required not in combined:
            errors.append(f"missing required text: {required}")

    matrix = (BASE / "curated_mobile_app_reference_matrix.csv").read_text(encoding="utf-8")
    for tab in ["Home", "Trades", "Detail", "Risk", "Settings"]:
        if tab not in matrix:
            errors.append(f"missing tab from matrix: {tab}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3061-3080 corrected actual mobile app benchmark artifacts are present.")
    print(f"Actual App Store screenshots: {raw_count}")
    print("Validation authority: REPORTING_HEALTH only.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
