from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "ios-trader-brain" / "src"
REPORT_DIR = ROOT / "docs" / "reports" / "task_2821_2830_ios_chart_scanner_controls"
REPORT = REPORT_DIR / "task_2821_2830_ios_chart_scanner_controls.md"
DECISION = REPORT_DIR / "task_2830_decision.csv"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require_terms(name: str, text: str, terms: list[str]) -> None:
    for term in terms:
        if term not in text:
            fail(f"{name} missing required term: {term}")


def main() -> None:
    files = {
        "chart": read(APP / "components" / "price-chart.tsx"),
        "detail": read(APP / "app" / "trade" / "[id].tsx"),
        "trades": read(APP / "app" / "(tabs)" / "trades.tsx"),
        "symbol_row": read(APP / "components" / "symbol-row.tsx"),
        "account_chart": read(APP / "components" / "account-trend-chart.tsx"),
        "types": read(APP / "types" / "cockpit.ts"),
        "data": read(APP / "lib" / "cockpit-data.ts"),
        "fixture": read(APP / "fixtures" / "cockpit-fixture.ts"),
        "report": read(REPORT),
        "decision": read(DECISION),
    }

    require_terms(
        "chart",
        files["chart"],
        [
            "onResponderMove",
            "showMarkers",
            "showVwap",
            "showVolume",
            "expanded",
            "intervalMs",
            "ChartInterval",
            "windowAndAggregateBars",
            "axisLabel",
            "axisIndices",
            "xAxisLabelY",
            "intervalLabel(range, interval)",
            "rowsWithVwap",
            "vwapValues.length >= 2",
            "O {selected.open",
            'VWAP {selected.vwap == null ? "-"',
            'VOL {selected.volume == null ? "-"',
        ],
    )
    require_terms(
        "detail",
        files["detail"],
        [
            "TogglePill",
            "showMarkers",
            "showVwap",
            "showVolume",
            "expanded",
            "PriceChart",
            "intervalOptions",
            "TimingMetric",
            "nearestBar",
            "timingAudit",
            "notVwapOnly",
            "entryVsVwap",
            "exitVsVwap",
            "barTimeDiff",
            "NEAREST_BAR_TOO_FAR",
            "uiAggregated",
            "timeDiffLabel",
        ],
    )
    require_terms(
        "trades",
        files["trades"],
        [
            "ScannerViewMode",
            "visibleColumns",
            "groupForTrade",
            "rejectedRows",
            "noTradeReasons",
            "ColumnToggle",
            "RejectedCard",
        ],
    )
    require_terms(
        "symbol_row",
        files["symbol_row"],
        [
            "ScannerColumn",
            "ScannerViewMode",
            "UNKNOWN_SOURCE_FRESHNESS",
            "scannerChangePct",
            "scannerVolume",
            "sourceFreshnessState",
        ],
    )
    require_terms(
        "account_chart",
        files["account_chart"],
        ["axisLabel", "axisIndices", "axisLabelY", "ko.invested", "ko.assets"],
    )
    require_terms(
        "types",
        files["types"],
        [
            "scannerRangeKey",
            "scannerIntervalLabel",
            "scannerChangeUsd",
            "scannerChangePct",
            "scannerVolume",
            "sourceFreshnessState",
            "scannerRiskState",
        ],
    )
    require_terms(
        "data",
        files["data"],
        [
            "scanner_change_pct",
            "source_freshness_state",
            "normalizeMarkers",
            "realOrdersAllowed: false",
            "liveOrderButtonsAllowed: false",
        ],
    )
    require_terms("fixture", files["fixture"], ["AI 인프라 winner", "sourceFreshnessState", "scannerRiskState", "매수", "매도"])
    require_terms("report", files["report"], ["PRIMARY_PASS", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"])
    require_terms("decision", files["decision"], ["ios_chart_scanner_controls_primary_pass"])

    combined = "\n".join(files.values())
    bad_patterns = ["蹂", "紐", "援ш", "李", "덉", "쒖", "곌", "뱀", "願", "醫", "洹", "?꾪", "?덉", "?ㅼ", "쨌"]
    for pattern in bad_patterns:
        if pattern in combined:
            fail(f"broken mojibake pattern detected: {pattern}")

    for forbidden in [
        "selected.vwap ?? selected.close",
        "row.vwap ?? row.close",
        "realOrdersAllowed: true",
        "liveOrderButtonsAllowed: true",
        "submitOrder",
        "placeOrder",
        "sendLiveOrder",
    ]:
        if forbidden in combined:
            fail(f"forbidden frontend pattern detected: {forbidden}")

    print("PASS: Task2821-2830 iOS chart scanner controls are valid")


if __name__ == "__main__":
    main()
