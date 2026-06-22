from __future__ import annotations

import csv
import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1408 = ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay"
RAW_DIR = ROOT / "data/raw/task_1428_1447_sec_companyfacts_full_candidate/companyfacts"
OUT_DIR = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition"
REPORT_DIR = ROOT / "docs/reports/task_1428_1447_full_ruler_source_time_acquisition"

AUTHORITY = "DIAGNOSTIC_FULL_RULER_SOURCE_TIME_ACQUISITION_ONLY"
SEC_USER_AGENT = "minjo quant research contact@example.com"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def candidate_cik_plan() -> list[dict[str, object]]:
    rows = read_csv(TASK1201 / "task1203_l5_trade_specs.csv")
    by_cik: dict[str, set[str]] = {}
    for row in rows:
        cik = row.get("cik", "").zfill(10)
        symbol = row.get("symbol", "")
        if not cik.strip("0"):
            continue
        by_cik.setdefault(cik, set()).add(symbol)
    plan: list[dict[str, object]] = []
    for idx, (cik, symbols) in enumerate(sorted(by_cik.items()), 1):
        symbol = sorted(symbols)[0]
        plan.append(
            {
                "task_id": "Task1429",
                "download_plan_id": f"CFPLAN1429-{idx:05d}",
                "cik": cik,
                "primary_symbol": symbol,
                "all_symbols": ";".join(sorted(symbols)),
                "sec_companyfacts_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                "raw_target_path": str(RAW_DIR / f"{symbol}_{cik}.json"),
                "source_family": "official_sec_companyfacts",
                "target_candidate_scope": "all_3100_l5_candidates_by_unique_cik",
                "authority": AUTHORITY,
            }
        )
    return plan


def download_one(url: str, target: Path) -> tuple[str, int, str]:
    if target.exists() and target.stat().st_size > 500:
        return "cached_existing", target.stat().st_size, ""
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return "downloaded", len(payload), ""
    except urllib.error.HTTPError as exc:
        return f"http_{exc.code}", 0, str(exc)
    except Exception as exc:  # noqa: BLE001 - ledger needs concrete failure text.
        return "download_error", 0, repr(exc)


def download_companyfacts(plan: list[dict[str, object]]) -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    for idx, row in enumerate(plan, 1):
        target = Path(str(row["raw_target_path"]))
        state, size, error = download_one(str(row["sec_companyfacts_url"]), target)
        ledger.append(
            {
                "task_id": "Task1430",
                "download_ledger_id": f"CFLEDGER1430-{idx:05d}",
                "cik": row["cik"],
                "primary_symbol": row["primary_symbol"],
                "sec_companyfacts_url": row["sec_companyfacts_url"],
                "raw_target_path": row["raw_target_path"],
                "download_state": state,
                "bytes": size,
                "error": error,
                "source_published_ts": "",
                "source_received_ts": "",
                "available_to_brain_ts_rule": "individual_facts_use_filed_date_at_or_before_decision",
                "authority": AUTHORITY,
            }
        )
        if state == "downloaded":
            time.sleep(0.12)
    return ledger


def source_time_schema() -> list[dict[str, object]]:
    rows = [
        ("source_published_ts", "original public release timestamp when available", "must be <= source_received_ts when both exist"),
        ("source_received_ts", "timestamp when local pipeline could have received source", "download timestamp is not used for historical availability"),
        ("available_to_brain_ts", "first timestamp allowed for L1-L4 or L5 receipt use", "must be <= decision_asof_ts for assignment"),
        ("decision_asof_ts", "candidate decision timestamp", "L1-L4 assignment boundary"),
        ("entry_ts", "trade entry timestamp", "post-entry source can only affect L5 hold/exit"),
        ("exit_ts", "trade exit timestamp", "post-entry receipt must be <= exit_ts"),
    ]
    return [
        {
            "task_id": "Task1428",
            "schema_id": f"SOURCETIME1428-{idx:03d}",
            "field_name": name,
            "definition": definition,
            "validation_rule": rule,
            "authority": AUTHORITY,
        }
        for idx, (name, definition, rule) in enumerate(rows, 1)
    ]


def build_source_time_panel() -> list[dict[str, object]]:
    rows = read_csv(OUT_DIR / "task1410_companyfacts_denominator_panel.csv")
    panel: list[dict[str, object]] = []
    for idx, row in enumerate(rows, 1):
        dates = [
            row.get("ttm_revenue_filed_date", ""),
            row.get("cash_filed_date", ""),
            row.get("operating_cash_flow_filed_date", ""),
            row.get("shares_filed_date", ""),
            row.get("public_float_filed_date", ""),
        ]
        available = max([d for d in dates if d], default="")
        panel.append(
            {
                "task_id": "Task1431",
                "source_time_row_id": f"SOURCETIME1431-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "decision_asof_ts": row["decision_asof_ts"],
                "source_family": "sec_companyfacts",
                "source_published_ts": "",
                "source_received_ts": available,
                "available_to_brain_ts": available,
                "source_time_state": "asof_fact_filed_before_decision" if available else "source_gap",
                "assignment_time_pass": "1" if available and available <= row["decision_asof_ts"][:10] else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return panel


def compare_coverage() -> list[dict[str, object]]:
    old_denom = read_csv(TASK1408 / "task1410_companyfacts_denominator_panel.csv")
    new_denom = read_csv(OUT_DIR / "task1410_companyfacts_denominator_panel.csv")
    old_mat = read_csv(TASK1408 / "task1413_materiality_ruler_panel.csv")
    new_mat = read_csv(OUT_DIR / "task1413_materiality_ruler_panel.csv")
    metrics = read_csv(OUT_DIR / "task1426_replay_metrics.csv")
    old_metric = {row["policy_variant_id"]: row for row in read_csv(TASK1408 / "task1426_replay_metrics.csv")}
    new_metric = {row["policy_variant_id"]: row for row in metrics}
    rows = [
        {
            "task_id": "Task1432",
            "coverage_area": "verified_denominator_rows",
            "before_task1408": sum(1 for row in old_denom if row["denominator_source_gap"] == "0"),
            "after_task1447": sum(1 for row in new_denom if row["denominator_source_gap"] == "0"),
            "delta": sum(1 for row in new_denom if row["denominator_source_gap"] == "0") - sum(1 for row in old_denom if row["denominator_source_gap"] == "0"),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1432",
            "coverage_area": "materiality_source_gap_rows",
            "before_task1408": sum(1 for row in old_mat if row["materiality_ruler_state"] == "materiality_source_gap"),
            "after_task1447": sum(1 for row in new_mat if row["materiality_ruler_state"] == "materiality_source_gap"),
            "delta": sum(1 for row in new_mat if row["materiality_ruler_state"] == "materiality_source_gap") - sum(1 for row in old_mat if row["materiality_ruler_state"] == "materiality_source_gap"),
            "authority": AUTHORITY,
        },
    ]
    for policy in ["ruler_top3_v1", "ruler_top5_v1", "ruler_top10_v1"]:
        rows.append(
            {
                "task_id": "Task1446",
                "coverage_area": f"{policy}_final_equity",
                "before_task1408": old_metric[policy]["final_equity"],
                "after_task1447": new_metric[policy]["final_equity"],
                "delta": round(float(new_metric[policy]["final_equity"]) - float(old_metric[policy]["final_equity"]), 4),
                "authority": AUTHORITY,
            }
        )
        rows.append(
            {
                "task_id": "Task1446",
                "coverage_area": f"{policy}_cagr",
                "before_task1408": old_metric[policy]["cagr"],
                "after_task1447": new_metric[policy]["cagr"],
                "delta": round(float(new_metric[policy]["cagr"]) - float(old_metric[policy]["cagr"]), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def copy_key_outputs() -> None:
    mapping = {
        "task1410_companyfacts_denominator_panel.csv": "task1432_full_companyfacts_denominator_panel.csv",
        "task1411_market_cap_proxy_panel.csv": "task1433_full_market_cap_proxy_panel.csv",
        "task1413_materiality_ruler_panel.csv": "task1434_full_materiality_ruler_panel.csv",
        "task1417_expectation_ruler_panel.csv": "task1435_expectation_ruler_time_checked_panel.csv",
        "task1419_absorption_ruler_panel.csv": "task1436_absorption_ruler_time_checked_panel.csv",
        "task1421_source_receipt_exit_panel.csv": "task1437_source_receipt_exit_time_checked_panel.csv",
        "task1422_price_path_risk_exit_panel.csv": "task1438_price_path_exit_time_checked_panel.csv",
        "task1424_integrated_ruler_panel.csv": "task1444_integrated_ruler_panel_v2.csv",
        "task1425_payoff_ranker_v3.csv": "task1445_payoff_ranker_v4.csv",
        "task1426_policy_specs.csv": "task1446_policy_specs.csv",
        "task1426_replay_trades.csv": "task1446_replay_trades.csv",
        "task1426_replay_equity.csv": "task1446_replay_equity.csv",
        "task1426_replay_metrics.csv": "task1446_replay_metrics.csv",
    }
    for src, dst in mapping.items():
        shutil.copyfile(OUT_DIR / src, OUT_DIR / dst)


def write_report(closeout: dict[str, object], coverage: list[dict[str, object]]) -> None:
    metrics = read_csv(OUT_DIR / "task1446_replay_metrics.csv")
    best = max(metrics, key=lambda row: float(row["final_equity"]))
    denom_row = next(row for row in coverage if row["coverage_area"] == "verified_denominator_rows")
    gap_row = next(row for row in coverage if row["coverage_area"] == "materiality_source_gap_rows")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task1428-1447 Full Ruler Source-Time Acquisition

## Decision Summary

- Verdict: `full_ruler_source_time_acquisition_diagnostic_not_accepted`.
- SEC companyfacts unique CIK plan: {closeout['planned_unique_cik_count']}.
- SEC companyfacts successful/cached files: {closeout['companyfacts_available_count']}.
- Verified denominator rows: {denom_row['before_task1408']} -> {denom_row['after_task1447']}.
- Materiality source-gap rows: {gap_row['before_task1408']} -> {gap_row['after_task1447']}.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.

## Quant Expert Report

- Data source: official SEC companyfacts API plus prior Task1201/1318/1408 artifacts.
- Time rule: each fact can only enter assignment if its `filed` date is at or before `decision_asof_ts`.
- No inferred lifecycle matching, no symbol/date proximity fallback, and no missing data treated as negative evidence.
- Same top3/top5/top10 replay structure was reused to test whether broader ruler coverage changes the result.
- Analyst PIT remains unavailable; non-SEC historical source receipts remain partial.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: item["policy_variant_id"]):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['trade_count']} | {row['source_receipt_exit_count']} | {row['price_path_exit_count']} | "
            f"{row['beats_benchmark']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += """
## No-Background Decision-Maker Report

필수 정보 전수 확보를 한 단계 진행했다.

핵심은 더 깊은 정보를 새로 실험한 게 아니다.

기존 ruler 구조에 필요한 SEC denominator 정보를 후보 CIK 전수 기준으로 붙였다.

그래도 전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1428_source_time_schema.csv`
- `task1429_candidate_cik_download_plan.csv`
- `task1430_sec_companyfacts_download_ledger.csv`
- `task1431_source_time_panel.csv`
- `task1432_coverage_comparison.csv`
- `task1446_replay_metrics.csv`
- `task1447_acceptance_gate.csv`
- `task1447_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1428_1447_full_ruler_source_time_acquisition_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1428_1447_full_ruler_source_time_acquisition.md").write_text(report, encoding="utf-8")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    schema = source_time_schema()
    plan = candidate_cik_plan()
    ledger = download_companyfacts(plan)
    write_csv(OUT_DIR / "task1428_source_time_schema.csv", schema)
    write_csv(OUT_DIR / "task1429_candidate_cik_download_plan.csv", plan)
    write_csv(OUT_DIR / "task1430_sec_companyfacts_download_ledger.csv", ledger)

    replay.COMPANYFACTS_DIR = RAW_DIR
    replay.OUT_DIR = OUT_DIR
    replay.REPORT_DIR = REPORT_DIR
    replay.AUTHORITY = AUTHORITY
    replay.main()

    source_time_panel = build_source_time_panel()
    write_csv(OUT_DIR / "task1431_source_time_panel.csv", source_time_panel)
    copy_key_outputs()
    coverage = compare_coverage()
    write_csv(OUT_DIR / "task1432_coverage_comparison.csv", coverage)
    metrics = read_csv(OUT_DIR / "task1446_replay_metrics.csv")
    best = max(metrics, key=lambda row: float(row["final_equity"]))
    available_count = sum(1 for row in ledger if row["download_state"] in {"downloaded", "cached_existing"})
    closeout = {
        "task_id": "Task1447",
        "verdict": "full_ruler_source_time_acquisition_diagnostic_not_accepted",
        "planned_unique_cik_count": len(plan),
        "companyfacts_available_count": available_count,
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "fill analyst PIT and non-SEC source receipt gaps before another acceptance claim",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1447_acceptance_gate.csv", [closeout])
    write_csv(OUT_DIR / "task1447_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1447_closeout.json", closeout)
    write_report(closeout, coverage)
    write_csv(REPORT_DIR / "task_1428_1447_decision.csv", [closeout])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
