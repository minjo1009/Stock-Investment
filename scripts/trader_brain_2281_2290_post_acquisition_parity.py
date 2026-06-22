from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2281_2290_post_acquisition_parity"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2281_2290_post_acquisition_parity.md"
DECISION = REPORT_DIR / "task_2281_2290_decision.csv"

TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
AUTHORITY = "POST_ACQUISITION_PLUS8000_PARITY_GATE_ONLY"
PARITY_THRESHOLD = 0.95


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return row.get("candidate_source_id", ""), row.get("trade_spec_id", ""), row.get("symbol", ""), row.get("decision_asof_ts", "")


def record(row: dict[str, str]) -> dict[str, object]:
    try:
        return json.loads(row.get("record_json", "") or "{}")
    except json.JSONDecodeError:
        return {}


def build_index(rows: list[dict[str, str]]) -> dict[str, dict[str, list[dict[str, object]]]]:
    index: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        symbol = row.get("symbol", "")
        endpoint = row.get("endpoint_name", "")
        if symbol and endpoint:
            packed = dict(row)
            packed.update({k: str(v) for k, v in record(row).items()})
            index[symbol][endpoint].append(packed)
    return index


def has_asof(rows: list[dict[str, object]], decision_ts: str, keys: list[str]) -> int:
    decision = parse_dt(decision_ts)
    if decision is None:
        return 0
    for row in rows:
        ts = None
        for k in keys:
            ts = parse_dt(row.get(k))
            if ts:
                break
        if ts and ts <= decision:
            return 1
    return 0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pool = read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv")
    features = read_csv(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv")
    normalized = read_csv(TASK2251 / "task2253_normalized_sources.csv")
    existing_path = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay/task2123_api_normalized_sources.csv"
    if existing_path.exists():
        normalized = read_csv(existing_path) + normalized
    feature_by_key = {key(row): row for row in features}
    index = build_index(normalized)
    panel: list[dict[str, object]] = []
    for idx, row in enumerate(pool, start=1):
        symbol = row["symbol"]
        endpoints = index.get(symbol, {})
        feature = feature_by_key.get(key(row), {})
        endpoint_flags = {
            "stock_filings": int(bool(endpoints.get("stock_filings"))),
            "stock_recommendation": int(bool(endpoints.get("stock_recommendation") or endpoints.get("grades_historical"))),
            "earnings_history": int(bool(endpoints.get("earnings_history") or endpoints.get("earnings"))),
            "financial_statement": int(bool(endpoints.get("income_statement") or endpoints.get("balance_sheet") or endpoints.get("cash_flow") or endpoints.get("companyfacts"))),
        }
        asof_flags = {
            "stock_filings": has_asof(endpoints.get("stock_filings", []), row["decision_asof_ts"], ["acceptedDate", "filedDate", "source_ts"]),
            "stock_recommendation": has_asof(endpoints.get("stock_recommendation", []) + endpoints.get("grades_historical", []), row["decision_asof_ts"], ["date", "period", "source_ts"]),
            "earnings_history": has_asof(endpoints.get("earnings_history", []) + endpoints.get("earnings", []), row["decision_asof_ts"], ["date", "reportedDate", "source_ts"]),
            "financial_statement": has_asof(endpoints.get("income_statement", []) + endpoints.get("balance_sheet", []) + endpoints.get("cash_flow", []) + endpoints.get("companyfacts", []), row["decision_asof_ts"], ["acceptedDate", "filingDate", "date", "filed", "end", "source_ts"]),
        }
        source_parity = int(all(endpoint_flags.values()))
        asof_parity = int(all(asof_flags.values()))
        feature_parity = int(bool(feature))
        replay_gate = int(feature_parity and asof_flags["stock_filings"] and asof_flags["earnings_history"] and asof_flags["financial_statement"])
        panel.append(
            {
                "task_id": "Task2283",
                "parity_row_id": f"POSTPARITY2283-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                **{f"symbol_endpoint_{name}": value for name, value in endpoint_flags.items()},
                **{f"asof_endpoint_{name}": value for name, value in asof_flags.items()},
                "source_family_parity_pass": source_parity,
                "asof_source_family_parity_pass": asof_parity,
                "feature_schema_parity_pass": feature_parity,
                "replay_gate_candidate_pass": replay_gate,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    summary: list[dict[str, object]] = []
    metrics = [
        "symbol_endpoint_stock_filings",
        "symbol_endpoint_stock_recommendation",
        "symbol_endpoint_earnings_history",
        "symbol_endpoint_financial_statement",
        "asof_endpoint_stock_filings",
        "asof_endpoint_stock_recommendation",
        "asof_endpoint_earnings_history",
        "asof_endpoint_financial_statement",
        "source_family_parity_pass",
        "asof_source_family_parity_pass",
        "feature_schema_parity_pass",
        "replay_gate_candidate_pass",
    ]
    for idx, metric in enumerate(metrics, start=1):
        covered = sum(int(row[metric]) for row in panel)
        summary.append(
            {
                "task_id": "Task2284",
                "coverage_row_id": f"POSTCOVER2284-{idx:03d}",
                "coverage_metric": metric,
                "candidate_rows": len(panel),
                "covered_rows": covered,
                "missing_rows": len(panel) - covered,
                "coverage_ratio": round(covered / len(panel), 6),
                "parity_threshold": PARITY_THRESHOLD,
                "parity_gate_pass": "1" if covered / len(panel) >= PARITY_THRESHOLD else "0",
                "authority": AUTHORITY,
            }
        )
    gate_row = next(row for row in summary if row["coverage_metric"] == "replay_gate_candidate_pass")
    parity_gate_pass = gate_row["parity_gate_pass"] == "1"
    closeout = [
        {
            "task_id": "Task2290",
            "verdict": "post_acquisition_parity_pass_replay_still_requires_user_confirmation" if parity_gate_pass else "post_acquisition_parity_insufficient_replay_blocked",
            "candidate_rows": len(panel),
            "replay_gate_candidate_rows": gate_row["covered_rows"],
            "replay_gate_candidate_ratio": gate_row["coverage_ratio"],
            "parity_gate_pass": "1" if parity_gate_pass else "0",
            "replay_allowed": "0",
            "replay_requires_user_confirmation": "1",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]
    write_csv(OUT_DIR / "task2283_post_acquisition_parity_panel.csv", panel)
    write_csv(OUT_DIR / "task2284_post_acquisition_parity_summary.csv", summary)
    write_csv(OUT_DIR / "task2290_closeout.csv", closeout)
    write_json(OUT_DIR / "task2290_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    lines = "\n".join(f"- `{row['coverage_metric']}`: {row['covered_rows']}/{row['candidate_rows']} ({row['coverage_ratio']}), pass {row['parity_gate_pass']}." for row in summary)
    REPORT.write_text(
        f"""# Task2281-2290 Post-Acquisition Parity

## Decision Summary

- Verdict: `{closeout[0]['verdict']}`.
- Replay gate rows: {closeout[0]['replay_gate_candidate_rows']}/{closeout[0]['candidate_rows']}.
- Replay allowed: `{closeout[0]['replay_allowed']}`.
- User confirmation required: `{closeout[0]['replay_requires_user_confirmation']}`.

## Quant Expert Report

{lines}

## No-Background Decision-Maker Report

Conclusion first: this is still a parity gate, not a backtest. It tells whether the new acquisition is enough to ask for replay authorization.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2281_2290_post_acquisition_parity/`.
- Validator: `python scripts/trader_brain_2281_2290_post_acquisition_parity_validate.py`.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK2281_2290_POST_ACQUISITION_PARITY_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
