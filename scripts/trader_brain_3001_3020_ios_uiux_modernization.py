from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3001_3020_ios_uiux_modernization"
ARTIFACT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REGISTRY = ROOT / "tasks/task_registry.csv"
OPSTATE = ROOT / "docs/operating_system/project_operating_state.md"
LLM_WIKI = ROOT / "docs/llm_wiki/frontend_ios_cockpit.md"
OBSIDIAN = ROOT / "docs/obsidian/mocs/Mobile Cockpit Map.md"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("") if path.exists() else pd.DataFrame()


def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).to_csv(ARTIFACT_DIR / name, index=False, encoding="utf-8-sig")


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ARTIFACT_DIR / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8")
    if marker in current:
        return
    path.write_text(current.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_registry() -> None:
    frame = read_csv(REGISTRY)
    frame = frame[~frame["task_id"].isin([f"Task{idx}" for idx in range(3001, 3021)])]
    rows = []
    for idx in range(3001, 3021):
        rows.append(
            {
                "task_id": f"Task{idx}",
                "title": f"iOS UIUX Modernization Step {idx}",
                "owner_team": "Frontend iOS / Product Design / Read-only Cockpit",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "ios-uiux-modernization-no-trading-logic-change",
                "parent_task": "Task3000" if idx == 3001 else f"Task{idx - 1}",
                "key_report": f"docs/reports/{TASK_ID}/{TASK_ID}.md",
                "key_decision": f"docs/reports/{TASK_ID}/task_3020_decision.csv",
                "key_artifacts": f"data/artifacts/{TASK_ID}",
                "validation_command": "python scripts/trader_brain_3001_3020_ios_uiux_modernization_validate.py",
                "notes": "Apple-modern + Toss-readable + TradingView-scannable iOS UIUX modernization; read-only and no replay/order changes.",
            }
        )
    pd.concat([frame, pd.DataFrame(rows)], ignore_index=True).to_csv(REGISTRY, index=False, encoding="utf-8-sig")


def write_report() -> None:
    decision = {
        "task_id": "Task3020",
        "verdict": "ios_uiux_map_and_modernization_completed_read_only",
        "uiux_map_created": "1",
        "apple_modern_design_applied": "1",
        "tradingview_scanner_chart_improved": "1",
        "toss_readability_repaired": "1",
        "replay_performed": "0",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    pd.DataFrame([decision]).to_csv(REPORT_DIR / "task_3020_decision.csv", index=False, encoding="utf-8-sig")
    report = """# Task3001-3020 iOS UIUX Modernization

## Decision Summary

- Verdict: `ios_uiux_map_and_modernization_completed_read_only`.
- UI/UX map created: `1`.
- Apple-modern design applied: `1`.
- TradingView scanner/chart improved: `1`.
- Toss readability repaired: `1`.
- Replay performed: `0`.
- Paper order intents created: `0`.
- Live orders created: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task only changes the read-only iOS cockpit presentation layer. It does not change selector, sizing, exit, replay, source acquisition, paper order generation, broker integration, or live trading status.

Design references used for the UI/UX map:

- Apple Human Interface Guidelines: clarity, hierarchy, layout, typography, materials, accessibility.
- Apple chart guidance: charts should support decision-making and avoid decorative complexity.
- TradingView mobile/chart documentation: mobile chart readout, touch tracking, watchlist/scanner behavior, quote-driven legend.
- Toss/Toss Securities public positioning: easy and intuitive investing interface with low cognitive load.

Implementation summary:

- Shared UI tokens and primitives were modernized for Apple-like spacing, elevation, and readable metric tiles.
- Home was rebuilt as a Toss-like account cockpit: total assets, invested cash, PnL, source mode, judgment state, and lead candidate.
- Trades scanner gained additional sort axes: change, volume, source freshness, risk, symbol, PnL.
- Symbol rows gained a risk/source rail and denser watchlist hierarchy.
- PriceChart now measures container width instead of relying on a fixed width.
- Settings benchmark copy was repaired into readable Korean and now documents the UI/UX map inside the app.

## No-Background Decision-Maker Report

Conclusion first: the app now feels more like a modern iOS trading cockpit.

It is still read-only. No replay, no paper order, no live order, no strategy approval changed.

## Artifact Manifest

- Artifacts: `data/artifacts/task_3001_3020_ios_uiux_modernization/`.
- Validator: `python scripts/trader_brain_3001_3020_ios_uiux_modernization_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    (REPORT_DIR / f"{TASK_ID}.md").write_text(report, encoding="utf-8")


def write_manifest() -> None:
    rows = []
    for path in sorted(ARTIFACT_DIR.iterdir()):
        if path.name.startswith("artifact_manifest") or not path.is_file():
            continue
        rows.append(
            {
                "task_id": "Task3001-3020",
                "file_name": path.name,
                "path": path.as_posix(),
                "artifact_class": "ios_uiux_modernization",
                "schema_version": "task3001_3020_v1",
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "created_utc": datetime.now(tz=UTC).isoformat(),
            }
        )
    write_csv("artifact_manifest.csv", rows)
    write_json("artifact_manifest.json", {"manifest": rows})


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        "task3001_uiux_map.csv",
        [
            {"tab": "home", "north_star": "Toss-like account clarity", "p0": "total assets/invested cash/PnL/source state/lead candidate", "must_not": "no order buttons"},
            {"tab": "trades", "north_star": "TradingView-like scanner density", "p0": "sort by PnL/change/volume/source/risk/symbol", "must_not": "no order intent"},
            {"tab": "detail", "north_star": "TradingView-like chart-first reasoning", "p0": "responsive chart/OHLC/VWAP/volume/markers/time axis", "must_not": "no broker action"},
            {"tab": "risk", "north_star": "institutional audit clarity", "p0": "freeze/compare/replay blocker visible", "must_not": "no replay claim"},
            {"tab": "settings", "north_star": "Apple-like system status", "p0": "catalog/source/version/read-only boundary/UIUX map", "must_not": "no deployment claim"},
        ],
    )
    write_csv(
        "task3002_reference_context.csv",
        [
            {"source": "Apple HIG", "url": "https://developer.apple.com/design/human-interface-guidelines", "use": "clarity hierarchy layout typography accessibility"},
            {"source": "Apple charting data", "url": "https://developer.apple.com/design/human-interface-guidelines/charting-data", "use": "decision-oriented chart display"},
            {"source": "TradingView mobile specifics", "url": "https://www.tradingview.com/charting-library-docs/latest/mobile_specifics/", "use": "touch tracking crosshair mobile chart behavior"},
            {"source": "TradingView watchlist", "url": "https://www.tradingview.com/charting-library-docs/latest/trading_terminal/Watch-List/", "use": "watchlist/scanner quote behavior"},
            {"source": "Toss", "url": "https://toss.im/en", "use": "easy intuitive investing interface"},
        ],
    )
    write_csv(
        "task3003_three_loop_audit.csv",
        [
            {"loop": "1", "auditor": "Apple/Toss design", "finding": "home/settings readability and benchmark copy needed repair", "action": "implemented"},
            {"loop": "1", "auditor": "TradingView chart/scanner", "finding": "fixed chart width and weak scanner sort axes", "action": "implemented"},
            {"loop": "1", "auditor": "QA/safety", "finding": "new validator must guard no-live-order and chart features", "action": "implemented"},
            {"loop": "2", "auditor": "implementation review", "finding": "tsc/lint gate run after first pass", "action": "implemented"},
            {"loop": "3", "auditor": "final governance", "finding": "registry/report/opstate/wiki updated", "action": "implemented"},
        ],
    )
    closeout = {
        "task_id": "Task3020",
        "verdict": "ios_uiux_map_and_modernization_completed_read_only",
        "uiux_map_created": "1",
        "apple_modern_design_applied": "1",
        "tradingview_scanner_chart_improved": "1",
        "toss_readability_repaired": "1",
        "replay_performed": "0",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_csv("task3020_closeout.csv", [closeout])
    write_json("task3020_closeout.json", closeout)
    write_report()
    update_registry()
    append_once(
        OPSTATE,
        "Task3001-Task3020 modernized",
        "147. Task3001-Task3020 modernized the read-only iOS cockpit UI/UX with an Apple-modern design map, Toss-style account readability, TradingView-style scanner/chart improvements, responsive PriceChart width, repaired benchmark copy, and a no-live-order governance validator; no replay, selector tuning, paper order, or live order was performed. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.",
    )
    append_once(
        LLM_WIKI,
        "Task3001-3020: iOS UIUX modernization",
        "## Task3001-3020: iOS UIUX modernization\n\n- Apple-modern shared UI primitives added.\n- Home now reads like a Toss-style account cockpit.\n- Trades scanner adds change/volume/source/risk sorting and denser risk-source rows.\n- PriceChart uses responsive container width.\n- Settings now contains a readable UI/UX map.\n- No replay, paper order, live order, or strategy acceptance change.",
    )
    append_once(
        OBSIDIAN,
        "Task3001-3020](../../reports/task_3001_3020_ios_uiux_modernization",
        "- [Task3001-3020](../../reports/task_3001_3020_ios_uiux_modernization/task_3001_3020_ios_uiux_modernization.md): Apple-modern/Toss-readable/TradingView-scannable iOS UIUX modernization.",
    )
    write_manifest()
    print("[TASK3001_3020_IOS_UIUX_MODERNIZATION_OK]")


if __name__ == "__main__":
    main()
