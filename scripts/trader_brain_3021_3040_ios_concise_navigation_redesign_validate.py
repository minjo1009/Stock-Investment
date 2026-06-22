from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3021_3040_ios_concise_navigation_redesign"
APP = ROOT / "apps/ios-trader-brain/src"
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
ARTIFACT_DIR = ROOT / "data/artifacts" / TASK_ID


def fail(message: str) -> None:
    raise SystemExit(f"[TASK3021_3040_VALIDATE_FAIL] {message}")


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"{label} missing token: {token}")


def reject(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text):
        fail(f"{label} forbidden pattern found: {pattern}")


def main() -> None:
    home = read(APP / "app/(tabs)/index.tsx")
    trades = read(APP / "app/(tabs)/trades.tsx")
    detail = read(APP / "app/trade/[id].tsx")
    risk = read(APP / "app/(tabs)/risk.tsx")
    settings = read(APP / "app/(tabs)/settings.tsx")
    types = read(APP / "types/cockpit.ts")
    report = read(REPORT_DIR / f"{TASK_ID}.md")
    decision = read(REPORT_DIR / "task_3040_decision.csv")
    closeout = read(ARTIFACT_DIR / "task3040_closeout.csv")
    packets = read(ARTIFACT_DIR / "subagent_packet_summary.csv")
    data_map = read(ARTIFACT_DIR / "page_data_contract_map.csv")

    app_sources = "\n".join([home, trades, detail, risk, settings])

    forbidden_patterns = [
        r"\bsubmitOrder\b",
        r"\bplaceOrder\b",
        r"\bsendLiveOrder\b",
        r"\bcreateOrder\b",
        r"\bexecuteOrder\b",
        r"realOrdersAllowed:\s*true",
        r"liveOrderButtonsAllowed:\s*true",
        r"method:\s*[\"'](?:POST|PUT|PATCH|DELETE)[\"']",
    ]
    for pattern in forbidden_patterns:
        reject(app_sources, pattern, "app")

    for token in ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if token not in report and token not in decision and token not in closeout:
            fail(f"standing status token missing from closeout/report: {token}")

    for token in ["todayCheck", "leadCandidate", "performanceAllowed", "router.push", "PriceChart"]:
        require(home, token, "home concise navigation")
    for token in ["AccountTrendChart", "MarketTape", "SymbolRow"]:
        if token in home:
            fail(f"home should not keep overloaded component import/use: {token}")

    for token in ["ScannerRow", "columnsOpen", "groupOptions", "sortOptions", "noTradeReasons", 'pathname: "/trade/[id]"']:
        require(trades, token, "trades scanner")

    for token in ["detailOptions", 'tab === "evidence"', 'tab === "risk"', 'tab === "sources"', "TimingAuditBlock", "PriceChart", "noLiveOrder"]:
        require(detail, token, "detail chart-first tabs")

    for token in ["activeBlockers", "topBlocker", "noTradeReasons", "liveOrdersCreated", "Strict as-of"]:
        require(risk, token, "risk compact governance")
    for token in ["policyFreezes", "splitOosPlan", "sameExperimentGate"]:
        if token in risk:
            fail(f"risk should not expose deep audit table by default: {token}")

    for token in ["requiredFiles", "noLiveOrderSafe", "realOrdersAllowed", "liveOrderButtonsAllowed", "sourceMode", "contractVersion", "generatedUtc"]:
        require(settings, token, "settings compact connection")

    for token in [
        "totalAssetsUsd",
        "cashUsd",
        "marketValueUsd",
        "totalReturnPct",
        "warningCodes",
        "strictAsofStatus",
        "performanceCompareAllowedNow",
        "sourceFreshnessState",
        "riskSeverity",
        "sourceIds",
    ]:
        if token not in app_sources and token not in types and token not in data_map:
            fail(f"data contract token missing: {token}")

    for token in ["readOnly: true", "paperOnly: true", "realOrdersAllowed: false", "liveOrderButtonsAllowed: false"]:
        require(types, token, "cockpit rules type")

    for token in ["worker", "explorer", "REPORTING_HEALTH", "GOVERNANCE_HEALTH"]:
        require(packets, token, "subagent packet summary")

    for token in ["ios_concise_navigation_redesign_completed_read_only", "replay_performed,0", "live_orders_created,0"]:
        require(closeout, token, "closeout")

    print("[TASK3021_3040_VALIDATE_OK]")


if __name__ == "__main__":
    main()
