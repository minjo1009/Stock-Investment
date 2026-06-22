from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "ios-trader-brain" / "src"
REPORT = ROOT / "docs" / "reports" / "task_2811_2820_ios_tradingview_frontend_gap_repair" / "task_2811_2820_ios_tradingview_frontend_gap_repair.md"
DECISION = ROOT / "docs" / "reports" / "task_2811_2820_ios_tradingview_frontend_gap_repair" / "task_2820_decision.csv"


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
        "account_chart": read(APP / "components" / "account-trend-chart.tsx"),
        "account_strip": read(APP / "components" / "account-strip.tsx"),
        "home": read(APP / "app" / "(tabs)" / "index.tsx"),
        "detail": read(APP / "app" / "trade" / "[id].tsx"),
        "types": read(APP / "types" / "cockpit.ts"),
        "data": read(APP / "lib" / "cockpit-data.ts"),
        "fixture": read(APP / "fixtures" / "cockpit-fixture.ts"),
        "report": read(REPORT),
        "decision": read(DECISION),
    }

    require_terms("chart", files["chart"], ["24 * 60 * 60 * 1000", "31 * 24 * 60 * 60 * 1000", "markerColor", "hasLifecycleShade"])
    require_terms("account_chart", files["account_chart"], ["투입현금 / 총자산 추이", "investedCashUsd", "totalAssetsUsd"])
    require_terms("account_strip", files["account_strip"], ["총 투입현금", "총 자산", "보유평가", "총수익률"])
    require_terms("home", files["home"], ["AccountTrendChart", "totalInvestedCashUsd", "marketValueUsd"])
    require_terms("detail", files["detail"], ["timelineMarkers", "AI 인프라 winner란", "왜 이 종목인가", "왜 이 시점에 진입했나"])
    require_terms("types", files["types"], ["winnerDefinition", "winnerWhy", "entryTimingReason", "AccountHistoryPoint"])
    require_terms("data", files["data"], ["normalizeAccountHistory", "winner_definition_ko", "total_invested_cash_usd"])
    require_terms("fixture", files["fixture"], ["winnerDefinition", "winnerWhy", "entryTimingReason", "accountHistory"])
    require_terms("report", files["report"], ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"])
    require_terms("decision", files["decision"], ["ios_tradingview_frontend_gap_repair_primary_pass"])

    combined = "\n".join(files.values())
    for pattern in [r"蹂", r"紐", r"援ш", r"李", r"Decision reason", r"Hold/reduce", r"diagnostic benchmark only"]:
      if re.search(pattern, combined):
          fail(f"broken or stale copy pattern detected: {pattern}")
    for forbidden in ["realOrdersAllowed: true", "liveOrderButtonsAllowed: true"]:
        if forbidden in combined:
            fail(f"forbidden live-order capability detected: {forbidden}")

    print("PASS: Task2811-2820 iOS TradingView frontend gap repair is valid")


if __name__ == "__main__":
    main()
