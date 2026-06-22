from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "ios-trader-brain" / "src"
REPORT = ROOT / "docs" / "reports" / "task_2801_2810_ios_trade_lifecycle_chart_markers" / "task_2801_2810_ios_trade_lifecycle_chart_markers.md"
DECISION = ROOT / "docs" / "reports" / "task_2801_2810_ios_trade_lifecycle_chart_markers" / "task_2810_decision.csv"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    files = {
        "types": APP / "types" / "cockpit.ts",
        "data": APP / "lib" / "cockpit-data.ts",
        "hook": APP / "lib" / "use-cockpit.ts",
        "chart": APP / "components" / "price-chart.tsx",
        "detail": APP / "app" / "trade" / "[id].tsx",
        "row": APP / "components" / "symbol-row.tsx",
        "fixture": APP / "fixtures" / "cockpit-fixture.ts",
        "report": REPORT,
        "decision": DECISION,
    }
    text = {name: require(path) for name, path in files.items()}

    required = {
        "types": ["TradeMarker", "exitAt", "sellReason", "chart", "markers"],
        "data": ["normalizeMarkers", "exit_at", "actual_exit_date", "chart.markers"],
        "hook": ["AUTO_REFRESH_MS", "setInterval", "EXPO_PUBLIC_TRADER_BRAIN_CATALOG_BASE_URL"],
        "chart": ["매수", "매도", "현재", "markerColor", "hasLifecycleShade"],
        "detail": ["매수~매도 리뷰 차트", "보유종목 실시간 차트", "매매 흐름", "왜 매도했나"],
        "row": ["종료 리뷰", "매매 지점 표시"],
        "fixture": ["PAPER_CLOSED", "sellReason", "tradeReviewSummary", "kind: \"sell\""],
        "report": ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"],
        "decision": ["ios_trade_lifecycle_chart_markers_primary_pass"],
    }
    for name, terms in required.items():
        for term in terms:
            if term not in text[name]:
                fail(f"{name} missing required term: {term}")

    forbidden_terms = ["realOrdersAllowed: true", "liveOrderButtonsAllowed: true"]
    combined = "\n".join(text.values())
    for term in forbidden_terms:
        if term in combined:
            fail(f"forbidden live-order capability detected: {term}")

    print("PASS: Task2801-2810 iOS trade lifecycle chart markers are valid")


if __name__ == "__main__":
    main()
