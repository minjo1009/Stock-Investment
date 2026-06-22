from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "docs" / "reports" / "task_750_canonical_package_extraction_plan"
SRC_INVENTORY = (
    ROOT
    / "docs"
    / "reports"
    / "task_746_src_canonicalization"
    / "task746_src_canonicalization_inventory.csv"
)
TEST_INVENTORY = (
    ROOT
    / "docs"
    / "reports"
    / "task_747_test_validation_canonicalization"
    / "task747_test_validation_inventory.csv"
)


INIT_PATHS = {
    "src/__init__.py",
    "src/app/__init__.py",
    "src/backtest/__init__.py",
    "src/common/__init__.py",
    "src/execution/__init__.py",
    "src/integration/__init__.py",
    "src/market/__init__.py",
    "src/reporting/__init__.py",
    "src/risk/__init__.py",
    "src/state/__init__.py",
    "src/strategy/__init__.py",
}

CONTRACT_STATE_PATHS = {
    "src/common/models.py",
    "src/market/interface.py",
    "src/execution/interface.py",
    "src/reporting/interface.py",
    "src/risk/interface.py",
    "src/strategy/interface.py",
    "src/state/store.py",
}

BACKTEST_CORE_PATHS = {
    "src/backtest/models.py",
    "src/backtest/data_loader.py",
    "src/backtest/engine.py",
    "src/backtest/engine_full.py",
    "src/backtest/analysis.py",
}

APP_REPORT_PATHS = {
    "src/app/main.py",
    "src/app/pipeline.py",
    "src/app/report_recent_runs.py",
    "src/ui/app.py",
}

GUARDED_RUNTIME_PATHS = {
    "src/app/reconciliation.py",
    "src/app/run_trade_loop.py",
    "src/app/run_trade_once.py",
    "src/integration/kis_auth_manager.py",
    "src/integration/kis_client.py",
    "src/integration/slack_client.py",
}

OWNER_REVIEW_ONLY_PATHS = {
    "src/app/run_trade_loop.py",
    "src/app/run_trade_once.py",
    "src/app/reconciliation.py",
    "src/integration/kis_auth_manager.py",
    "src/integration/kis_client.py",
    "src/integration/slack_client.py",
    "src/backtest/engine_full.py",
    "src/app/pipeline.py",
    "src/ui/app.py",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def classify_wave(path: str) -> tuple[str, str, str]:
    if path in INIT_PATHS:
        return (
            "W0",
            "package_skeleton",
            "namespace import and no side effect only; approval meaning forbidden",
        )
    if path in CONTRACT_STATE_PATHS:
        return (
            "W1",
            "contracts_state_interfaces",
            "interface contract, model compatibility, state boundary, no broker/live dependency",
        )
    if path in BACKTEST_CORE_PATHS:
        return (
            "W2",
            "backtest_core",
            "deterministic replay, as-of/timestamp discipline, no future leakage, W1 output compatibility",
        )
    if path in APP_REPORT_PATHS:
        return (
            "W3",
            "app_report_shell",
            "does not bypass canonical engine, evidence-only reporting, no acceptance/status overclaim",
        )
    if path in GUARDED_RUNTIME_PATHS:
        return (
            "W4",
            "guarded_runtime_integration",
            "EXECUTION_HEALTH only, external guard, no live/order side effect, broker-truth distinction",
        )
    return ("BLOCKED", "unmapped_candidate", "owner must classify before promotion")


def risk_level(path: str, wave: str) -> str:
    if wave == "W4":
        return "high_side_effect_external"
    if path in {"src/backtest/engine_full.py", "src/app/pipeline.py", "src/ui/app.py"}:
        return "medium_high_owner_review"
    if wave == "W2":
        return "medium_high_research_correctness"
    if wave == "W3":
        return "medium_overclaim_shell"
    if wave == "W1":
        return "medium_contract_drift"
    return "low_namespace_only"


def promotion_status(path: str) -> str:
    if path in OWNER_REVIEW_ONLY_PATHS:
        return "owner_review_only_even_if_import_passes"
    return "candidate_for_wave_promotion_after_gates"


def test_matches(candidate_path: str, test_row: dict[str, str]) -> bool:
    hint = test_row.get("canonical_target_hint", "")
    if hint == candidate_path:
        return True
    if hint.endswith(" canonical candidate before promotion"):
        return False
    if hint and candidate_path.startswith(hint.rstrip("/") + "/"):
        return True
    if hint == "src/backtest" and candidate_path.startswith("src/backtest/"):
        return True
    if hint == "src/app" and candidate_path.startswith("src/app/"):
        return True
    return False


def build_plan() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    src_rows = [
        row
        for row in read_csv(SRC_INVENTORY)
        if row.get("canonical_bucket") == "canonical_package_candidate"
    ]
    test_rows = read_csv(TEST_INVENTORY)
    promotion_test_rows = [
        row
        for row in test_rows
        if row.get("authority_tag")
        in {"PACKAGE_HEALTH", "DATA_HEALTH", "EXECUTION_HEALTH", "REPORTING_HEALTH", "GOVERNANCE_HEALTH"}
    ]

    candidate_to_tests: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in src_rows:
        candidate_path = candidate["path"]
        for test in promotion_test_rows:
            if test_matches(candidate_path, test):
                candidate_to_tests[candidate_path].append(test)

    plan_rows: list[dict[str, str]] = []
    for candidate in sorted(src_rows, key=lambda row: row["path"]):
        path = candidate["path"]
        wave_id, wave_name, gates = classify_wave(path)
        matched_tests = candidate_to_tests[path]
        authority_tags = sorted({test.get("authority_tag", "") for test in matched_tests if test.get("authority_tag")})
        plan_rows.append(
            {
                "path": path,
                "wave_id": wave_id,
                "wave_name": wave_name,
                "owner_team": candidate.get("owner_team", ""),
                "reviewer_team": "Research Governance"
                if candidate.get("owner_team") != "Research Governance"
                else "Relevant owner team",
                "promotion_status": promotion_status(path),
                "risk_level": risk_level(path, wave_id),
                "required_gate": gates,
                "mapped_validation_count": str(len(matched_tests)),
                "mapped_authority_tags": ";".join(authority_tags) if authority_tags else "none_mapped",
                "pass_does_not_mean": (
                    "strategy accepted; deployment ready; real capital allowed; "
                    "candidate approved beyond stated wave scope"
                ),
            }
        )

    wave_counts = Counter(row["wave_id"] for row in plan_rows)
    owner_review_count = sum(1 for row in plan_rows if row["promotion_status"].startswith("owner_review_only"))
    summary_rows = [
        {"field": "task_id", "value": "Task750"},
        {"field": "verdict", "value": "PRIMARY_PASS_PLAN_ONLY"},
        {"field": "scope", "value": "canonical package extraction plan"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
        {"field": "canonical_candidates_reviewed", "value": str(len(plan_rows))},
        {"field": "w0_package_skeleton", "value": str(wave_counts["W0"])},
        {"field": "w1_contracts_state_interfaces", "value": str(wave_counts["W1"])},
        {"field": "w2_backtest_core", "value": str(wave_counts["W2"])},
        {"field": "w3_app_report_shell", "value": str(wave_counts["W3"])},
        {"field": "w4_guarded_runtime_integration", "value": str(wave_counts["W4"])},
        {"field": "owner_review_only_candidates", "value": str(owner_review_count)},
        {"field": "gpt_review_captured", "value": "yes"},
        {"field": "src_files_moved_or_deleted", "value": "no"},
        {"field": "imports_changed", "value": "no"},
        {"field": "trading_logic_changed", "value": "no"},
        {"field": "next_safe_task", "value": "Task751 W0-W1 extraction validation only"},
    ]

    decision_rows = [
        {"field": "task_id", "value": "Task750"},
        {"field": "decision", "value": "create_plan_not_extract_code"},
        {"field": "gpt_correction_applied", "value": "W1 contracts/state/interfaces before W2 backtest core"},
        {"field": "promotion_allowed_now", "value": "no"},
        {"field": "next_allowed_work", "value": "W0-W1 validation and import graph audit only"},
        {"field": "new_alpha_allowed", "value": "no"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
    ]

    return plan_rows, summary_rows, decision_rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def write_report(plan_rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> None:
    wave_summary: list[dict[str, str]] = []
    by_wave = defaultdict(list)
    for row in plan_rows:
        by_wave[row["wave_id"]].append(row)
    for wave_id in ["W0", "W1", "W2", "W3", "W4", "BLOCKED"]:
        if wave_id not in by_wave:
            continue
        rows = by_wave[wave_id]
        wave_summary.append(
            {
                "wave_id": wave_id,
                "wave_name": rows[0]["wave_name"],
                "count": str(len(rows)),
                "owner_review_only": str(
                    sum(1 for row in rows if row["promotion_status"].startswith("owner_review_only"))
                ),
                "main_gate": rows[0]["required_gate"],
            }
        )

    report = f"""# Task750 Canonical Package Extraction Plan

## Decision Summary

Task750 creates an extraction plan only.

It does not move `src/` files, change imports, change trading logic, accept a strategy, or claim deployment readiness.

GPT review changed the order:

```text
contracts/state/interfaces first
backtest engines second
runtime/integration last
```

## Quant Expert Report

The 33 Task746 `canonical_package_candidate` files are still candidates.

The corrected extraction order is:

{markdown_table(wave_summary, ["wave_id", "wave_name", "count", "owner_review_only", "main_gate"])}

Key rule:

```text
Candidate != Approved
PASS != Acceptance
Import health != Trading validity
Runtime import != Broker truth
```

Owner-review-only even if import tests pass:

```text
src/app/run_trade_loop.py
src/app/run_trade_once.py
src/app/reconciliation.py
src/integration/kis_auth_manager.py
src/integration/kis_client.py
src/integration/slack_client.py
src/backtest/engine_full.py
src/app/pipeline.py
src/ui/app.py
```

## No-Background Decision-Maker Report

1. 먼저 껍데기와 계약부터 봅니다.
2. 그 다음 백테스트 엔진을 봅니다.
3. 실시간/외부연동/KIS/Slack은 맨 마지막입니다.
4. 테스트 통과는 정리 통과일 뿐입니다.
5. 전략 승인이나 실거래 가능 상태가 아닙니다.

## Artifact Manifest

Primary artifacts:

- `task750_canonical_package_plan.csv`
- `task750_summary.csv`
- `task_750_decision.csv`
- `gpt_review_notes.md`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (TASK_DIR / "task_750_canonical_package_extraction_plan.md").write_text(report, encoding="utf-8")


def write_gpt_notes() -> None:
    notes = """# Task750 GPT Review Notes

GPT was used as a review-only backend/platform architecture critic.

## Applied Review Points

1. Original W1/W2 order was corrected.
2. Contracts, interfaces, and state must precede backtest core extraction.
3. Runtime and external integrations must remain last.
4. `engine_full.py`, app pipeline, UI, broker/KIS/Slack, and runtime loop files remain owner-review-only even if imports pass.
5. EVIDENCE_ONLY tests must not be promotion evidence.

## Non-Authority

GPT review is not a source of truth.
GPT review does not accept strategy.
GPT review does not approve deployment.
"""
    (TASK_DIR / "gpt_review_notes.md").write_text(notes, encoding="utf-8")


def main() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    plan_rows, summary_rows, decision_rows = build_plan()
    plan_fields = [
        "path",
        "wave_id",
        "wave_name",
        "owner_team",
        "reviewer_team",
        "promotion_status",
        "risk_level",
        "required_gate",
        "mapped_validation_count",
        "mapped_authority_tags",
        "pass_does_not_mean",
    ]
    write_csv(TASK_DIR / "task750_canonical_package_plan.csv", plan_rows, plan_fields)
    write_csv(TASK_DIR / "task750_summary.csv", summary_rows, ["field", "value"])
    write_csv(TASK_DIR / "task_750_decision.csv", decision_rows, ["field", "value"])
    write_report(plan_rows, summary_rows)
    write_gpt_notes()
    print(f"[TASK750] wrote={TASK_DIR}")


if __name__ == "__main__":
    main()
