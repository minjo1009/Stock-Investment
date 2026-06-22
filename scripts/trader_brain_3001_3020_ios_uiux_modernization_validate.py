from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3001_3020_ios_uiux_modernization"
APP = ROOT / "apps/ios-trader-brain/src"
ARTIFACT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def fail(message: str) -> None:
    raise SystemExit(f"[TASK3001_3020_VALIDATE_FAIL] {message}")


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        fail(f"missing {path}")
    frame = pd.read_csv(path, dtype=str).fillna("")
    if frame.empty:
        fail(f"empty {path}")
    return frame


def app_sources() -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in APP.rglob("*.ts*"))


def main() -> None:
    sources = app_sources()
    ui = read(APP / "components/ui.tsx")
    home = read(APP / "app/(tabs)/index.tsx")
    trades = read(APP / "app/(tabs)/trades.tsx")
    symbol_row = read(APP / "components/symbol-row.tsx")
    price_chart = read(APP / "components/price-chart.tsx")
    settings = read(APP / "app/(tabs)/settings.tsx")
    tab_benchmarks = read(APP / "lib/tab-benchmarks.ts")
    report = read(REPORT_DIR / f"{TASK_ID}.md")

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
        if re.search(pattern, sources):
            fail(f"forbidden order/trading mutation pattern found: {pattern}")

    for token in ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN", "readOnly: true", "paperOnly: true"]:
        if token not in sources and token not in report:
            fail(f"status/read-only token missing: {token}")

    for token in ["오늘의 계좌", "거래 스캐너", "위험", "앱 설정", "매수", "매도", "읽기 전용"]:
        if token not in sources:
            fail(f"Korean UI token missing: {token}")

    if "\ufffd" in sources:
        fail("replacement character found in app source")
    if re.search(r">\?{2,}<", sources):
        fail("visible question-mark mojibake found")

    for token in ["onResponderMove", "axisLabel", "xAxisLabelY", "showMarkers", "showVwap", "showVolume", "intervalMs", "windowAndAggregateBars", "containerWidth"]:
        if token not in price_chart:
            fail(f"chart safety token missing: {token}")

    for path in [
        APP / "app/(tabs)/index.tsx",
        APP / "app/(tabs)/trades.tsx",
        APP / "app/(tabs)/risk.tsx",
        APP / "app/(tabs)/settings.tsx",
        APP / "app/trade/[id].tsx",
    ]:
        text = read(path)
        if "ScrollView" not in text or 'contentInsetAdjustmentBehavior="automatic"' not in text:
            fail(f"safe ScrollView missing in {path}")
        if "paddingBottom" not in text:
            fail(f"paddingBottom missing in {path}")

    for token in ["AppHeader", "MetricTile", "InsightCard", "elevated", "glass"]:
        if token not in ui:
            fail(f"modern UI primitive/token missing: {token}")

    for token in ["AccountStrip", "오늘의 판단 상태", "주도 후보", "Strict as-of"]:
        if token not in home:
            fail(f"home modernization missing: {token}")

    for token in ["changeSort", "volumeSort", "sourceSort", "sourceFreshnessRank"]:
        if token not in trades:
            fail(f"trades scanner improvement missing: {token}")

    for token in ["riskRailColor", "freshness", "railColor"]:
        if token not in symbol_row:
            fail(f"symbol row risk/source rail missing: {token}")

    for token in ["UI/UX 맵", "런타임 카탈로그", "안전 경계"]:
        if token not in settings:
            fail(f"settings UX map missing: {token}")

    for token in ["Toss", "TradingView", "Apple HIG", "종목 상세"]:
        if token not in tab_benchmarks:
            fail(f"benchmark copy missing: {token}")

    closeout = read_csv(ARTIFACT_DIR / "task3020_closeout.csv").iloc[0].to_dict()
    if closeout.get("replay_performed") != "0":
        fail("replay_performed must stay 0")
    if closeout.get("paper_order_intents_created") != "0" or closeout.get("live_orders_created") != "0":
        fail("paper/live orders must stay 0")
    if closeout.get("strategy_acceptance") != "NOT_ACCEPTED":
        fail("strategy status changed")
    if closeout.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        fail("deployment status changed")
    if closeout.get("real_capital") != "FORBIDDEN":
        fail("real capital status changed")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_rows = registry[registry["task_id"].isin([f"Task{idx}" for idx in range(3001, 3021)])]
    if len(task_rows) != 20:
        fail(f"expected 20 task registry rows, found {len(task_rows)}")

    opstate = read(ROOT / "docs/operating_system/project_operating_state.md")
    if "Task3001-Task3020 modernized" not in opstate:
        fail("operating state missing Task3001-3020")

    print("[TASK3001_3020_VALIDATE_OK]")


if __name__ == "__main__":
    main()
