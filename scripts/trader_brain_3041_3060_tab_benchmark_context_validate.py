from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/reports/task_3041_3060_tab_benchmark_context/task_3041_3060_tab_benchmark_context.md",
    "docs/reports/task_3041_3060_tab_benchmark_context/task_3060_decision.csv",
    "data/artifacts/task_3041_3060_tab_benchmark_context/tab_benchmark_image_report.png",
    "data/artifacts/task_3041_3060_tab_benchmark_context/tab_benchmark_comparison.csv",
    "data/artifacts/task_3041_3060_tab_benchmark_context/benchmark_source_manifest.csv",
    "data/artifacts/task_3041_3060_tab_benchmark_context/subagent_packet_summary.csv",
    "data/artifacts/task_3041_3060_tab_benchmark_context/artifact_manifest.md",
]

REQUIRED_SCREENSHOTS = [
    "apple_stocks_detail_support.png",
    "apple_stocks_appstore.png",
    "ibkr_risk_measures.png",
    "toss_appstore.png",
    "toss_security.png",
    "tradingview_watchlists.png",
]

FORBIDDEN_CLAIMS = [
    "Strategy: ACCEPTED",
    "Deployment: READY",
    "Real Capital: ALLOWED",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required file: {rel}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required file: {rel}")

    screenshot_dir = ROOT / "data/artifacts/task_3041_3060_tab_benchmark_context/screenshots_benchmark"
    for name in REQUIRED_SCREENSHOTS:
        path = screenshot_dir / name
        if not path.exists():
            errors.append(f"missing benchmark screenshot: {name}")
        elif path.stat().st_size <= 1024:
            errors.append(f"suspiciously small benchmark screenshot: {name}")

    report_text = (ROOT / REQUIRED_FILES[0]).read_text(encoding="utf-8")
    manifest_text = (ROOT / REQUIRED_FILES[-1]).read_text(encoding="utf-8")
    combined = report_text + "\n" + manifest_text

    for required in [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "REPORTING_HEALTH",
        "replay performed 0",
        "live orders created 0",
    ]:
        if required not in combined:
            errors.append(f"missing required status text: {required}")

    for forbidden in FORBIDDEN_CLAIMS:
        if forbidden in combined:
            errors.append(f"forbidden claim present: {forbidden}")

    matrix = (ROOT / REQUIRED_FILES[3]).read_text(encoding="utf-8")
    for tab in ["Home", "Trades", "Detail", "Risk", "Settings"]:
        if tab not in matrix:
            errors.append(f"missing tab in comparison matrix: {tab}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: Task3041-3060 tab benchmark context artifacts are present and bounded.")
    print("Validation authority: REPORTING_HEALTH only.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
