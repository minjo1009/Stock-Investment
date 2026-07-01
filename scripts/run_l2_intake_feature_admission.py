from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.intake.contracts import INTAKE_ONLY_NOT_MATERIALIZED, build_intake_id, family_policy

TASK_ID = "TASK-4136"
SLUG = "task_4136_l2_intake_feature_admission"
DATA_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
CONTRACT_PATH = ROOT / "configs" / "l2_intake_feature_admission_contract.yaml"
HANDOFF_PATH = ROOT / "data" / "artifacts" / "task_4135_l1_final_hardening_l2_gpt_consult" / "l1_l2_handoff_contract.csv"
COVERAGE_PATH = ROOT / "data" / "artifacts" / "task_4135_l1_final_hardening_l2_gpt_consult" / "l1_coverage_audit.csv"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def contract_yaml(handoff_rows: list[dict[str, str]]) -> str:
    lines = [
        "version: 1",
        f"task_id: {TASK_ID}",
        "contract_name: l2_intake_feature_admission_contract",
        "trading_authority_opened: false",
        "broker_mutation_allowed: false",
        "paper_promotion_allowed: false",
        "missing_source_is_negative_allowed: false",
        "future_outcome_assignment_allowed: false",
        "legacy_l2_news_builder_allowed: false",
        "families:",
    ]
    for row in handoff_rows:
        family = row["source_family"]
        policy = family_policy(family)
        lines.extend(
            [
                f"  {family}:",
                f"    required_l1_classification: {row['l1_classification']}",
                f"    required_l2_allowed_action: {row['l2_allowed_action']}",
                f"    primitive_envelope_type: {policy['primitive_envelope_type']}",
                f"    feature_admission_state: {policy['feature_admission_state']}",
                f"    trading_feature_path: {policy['trading_feature_path']}",
                f"    mapping_gate: {policy['mapping_gate']}",
                "    feature_materialization_allowed_now: false",
            ]
        )
    return "\n".join(lines) + "\n"


def build_intake_manifest(handoff_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(handoff_rows, start=1):
        family = row["source_family"]
        policy = family_policy(family)
        source_packet_id = f"family_contract_{idx:03d}"
        rows.append(
            {
                "task_id": TASK_ID,
                "l2_intake_id": build_intake_id(TASK_ID, family, source_packet_id),
                "source_packet_id": source_packet_id,
                "source_family": family,
                "l1_classification": row["l1_classification"],
                "l2_allowed_action": row["l2_allowed_action"],
                "primitive_envelope_type": policy["primitive_envelope_type"],
                "l2_materialization_state": INTAKE_ONLY_NOT_MATERIALIZED,
                "feature_admission_state": policy["feature_admission_state"],
                "trading_feature_path": policy["trading_feature_path"],
                "feature_materialization_allowed_now": "0",
                "mapping_gate": policy["mapping_gate"],
                "legacy_l2_news_builder_allowed": "0",
                "trading_authority": "0",
                "paper_or_live_permission": "0",
                "notes": "intake contract row only; no L2 feature rows written",
            }
        )
    return rows


def build_feature_gate_rows(handoff_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    gate_text = {
        "daily_bars": "closed bar source-time, raw hash, symbol mapping, primitive schema",
        "market_bars_5m": "closed bar source-time, raw/db hash, symbol mapping, gap audit",
        "public_market_macro_news_feeds": "macro scope, source-time, no future outcome, effect window, stale policy",
        "public_context_news_feeds": "entity mapping, source-time, dedup, effect window, ambiguity review",
        "public_newswire_feeds": "high-confidence ticker mapping, source authority, dedup, effect window, ambiguity review",
    }
    rows = []
    for row in handoff_rows:
        family = row["source_family"]
        policy = family_policy(family)
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": family,
                "can_be_trading_feature_later": "1",
                "admitted_as_trading_feature_now": "0",
                "current_state": policy["feature_admission_state"],
                "required_next_validation": gate_text[family],
                "why_not_now": "L2 intake contract exists, but feature materialization/effect validation is not complete",
                "not_a_permanent_block": "1",
            }
        )
    return rows


def build_mapping_gate_rows(handoff_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    mapping_rows = []
    for row in handoff_rows:
        family = row["source_family"]
        policy = family_policy(family)
        if family in {"daily_bars", "market_bars_5m"}:
            confidence = "symbol must be exact"
        elif family == "public_market_macro_news_feeds":
            confidence = "macro scope must be explicit; ticker mapping required only for symbol-specific feature"
        elif family == "public_context_news_feeds":
            confidence = "entity or ticker mapping must be explicit and ambiguity-reviewed"
        else:
            confidence = "ticker mapping must be high-confidence, deduped, and effect-window reviewed"
        mapping_rows.append(
            {
                "task_id": TASK_ID,
                "source_family": family,
                "mapping_gate": policy["mapping_gate"],
                "minimum_mapping_evidence": confidence,
                "ambiguous_mapping_action": "BLOCK_OR_MANUAL_REVIEW",
                "missing_mapping_action": "BLOCK_FEATURE_ADMISSION",
                "allowed_for_context_without_ticker": "1" if family == "public_market_macro_news_feeds" else "0",
            }
        )
    return mapping_rows


def build_legacy_quarantine_rows() -> list[dict[str, str]]:
    return [
        {
            "task_id": TASK_ID,
            "legacy_path": "src/l2/builders/news_event_primitives.py",
            "status": "QUARANTINED_STUB",
            "replacement_path": "src/l2/intake/contracts.py + configs/l2_intake_feature_admission_contract.yaml",
            "direct_l0_to_l2_allowed": "0",
            "notes": "legacy builder can be imported but raises before use; new L2 work must enter through intake contract",
        },
        {
            "task_id": TASK_ID,
            "legacy_path": "scripts/ingest_l0_news_to_l2.py",
            "status": "FAIL_CLOSED_BY_DEFAULT",
            "replacement_path": "scripts/run_l2_intake_feature_admission.py",
            "direct_l0_to_l2_allowed": "0",
            "notes": "legacy CLI remains blocked unless explicit diagnostic override is passed",
        },
    ]


def build_l1_validation_plan() -> list[dict[str, str]]:
    return [
        {
            "task_id": TASK_ID,
            "hook_name": "l1_bootstrap_gate_validation",
            "cadence": "after_each_l0_batch_or_hourly",
            "command": "python scripts/validate_l1_source_packet_bootstrap.py",
            "blocks_l2_on_fail": "1",
        },
        {
            "task_id": TASK_ID,
            "hook_name": "l1_data_present_hardening_validation",
            "cadence": "after_each_l0_batch_or_hourly",
            "command": "python scripts/validate_l1_data_present_hardening.py",
            "blocks_l2_on_fail": "1",
        },
        {
            "task_id": TASK_ID,
            "hook_name": "l1_final_handoff_validation",
            "cadence": "after_each_l0_batch_or_hourly",
            "command": "python scripts/validate_l1_final_hardening_l2_consult_prep.py",
            "blocks_l2_on_fail": "1",
        },
    ]


def run_l1_validation_once(plan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in plan_rows:
        started = utc_now()
        proc = subprocess.run(row["command"].split(), cwd=ROOT, text=True, capture_output=True, timeout=180)
        rows.append(
            {
                "task_id": TASK_ID,
                "hook_name": row["hook_name"],
                "command": row["command"],
                "started_at": started,
                "finished_at": utc_now(),
                "exit_code": str(proc.returncode),
                "result": "PASS" if proc.returncode == 0 else "FAIL",
                "stdout_tail": proc.stdout[-500:].replace("\n", " | "),
                "stderr_tail": proc.stderr[-500:].replace("\n", " | "),
            }
        )
    return rows


def artifact_rows() -> list[dict[str, str]]:
    entries = [
        ("configs/l2_intake_feature_admission_contract.yaml", "contract", "L2 intake and feature-admission contract.", "created"),
        ("src/l2/builders/news_event_primitives.py", "source", "Quarantines legacy L2 news builder.", "modified"),
        ("src/l2/intake/__init__.py", "source", "New L2 intake package boundary.", "created"),
        ("src/l2/intake/contracts.py", "source", "L2 intake policy helpers.", "created"),
        ("scripts/run_l2_intake_feature_admission.py", "script", "Builds TASK-4136 L2 intake artifacts.", "created"),
        ("scripts/validate_l2_intake_feature_admission.py", "validator", "Validates TASK-4136 L2 intake artifacts.", "created"),
        (f"docs/reports/{SLUG}/report.md", "report", "TASK-4136 Korean report.", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "manifest", "TASK-4136 artifact manifest.", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation", "TASK-4136 validation results.", "created"),
        (f"docs/reports/{SLUG}/l2_intake_feature_admission_summary.json", "summary", "Machine-readable TASK-4136 summary.", "created"),
        (f"data/artifacts/{SLUG}/l2_intake_manifest.csv", "artifact", "L2 intake manifest.", "created"),
        (f"data/artifacts/{SLUG}/l2_feature_admission_gate.csv", "artifact", "Feature admission gate rows.", "created"),
        (f"data/artifacts/{SLUG}/ticker_news_mapping_gate.csv", "artifact", "Ticker/news/macro mapping gate.", "created"),
        (f"data/artifacts/{SLUG}/legacy_l2_news_quarantine.csv", "artifact", "Legacy L2 news quarantine evidence.", "created"),
        (f"data/artifacts/{SLUG}/l1_continuous_validation_plan.csv", "artifact", "Continuous L1 validation hook plan.", "created"),
        (f"data/artifacts/{SLUG}/l1_continuous_validation_ledger.csv", "artifact", "One-shot L1 validation evidence.", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator result.", "created"),
    ]
    return [
        {"path": path, "type": typ, "purpose": purpose, "created_or_modified": status, "task_id": TASK_ID}
        for path, typ, purpose, status in entries
    ]


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    handoff_rows = read_csv(HANDOFF_PATH)
    coverage_rows = read_csv(COVERAGE_PATH)
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(contract_yaml(handoff_rows), encoding="utf-8", newline="\n")
    intake_rows = build_intake_manifest(handoff_rows)
    feature_rows = build_feature_gate_rows(handoff_rows)
    mapping_rows = build_mapping_gate_rows(handoff_rows)
    legacy_rows = build_legacy_quarantine_rows()
    l1_plan_rows = build_l1_validation_plan()
    l1_ledger_rows = run_l1_validation_once(l1_plan_rows)

    write_csv(DATA_DIR / "l2_intake_manifest.csv", intake_rows, list(intake_rows[0]))
    write_csv(DATA_DIR / "l2_feature_admission_gate.csv", feature_rows, list(feature_rows[0]))
    write_csv(DATA_DIR / "ticker_news_mapping_gate.csv", mapping_rows, list(mapping_rows[0]))
    write_csv(DATA_DIR / "legacy_l2_news_quarantine.csv", legacy_rows, list(legacy_rows[0]))
    write_csv(DATA_DIR / "l1_continuous_validation_plan.csv", l1_plan_rows, list(l1_plan_rows[0]))
    write_csv(DATA_DIR / "l1_continuous_validation_ledger.csv", l1_ledger_rows, list(l1_ledger_rows[0]))
    write_csv(REPORT_DIR / "artifact_manifest.csv", artifact_rows(), ["path", "type", "purpose", "created_or_modified", "task_id"])

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "l2_intake_rows": len(intake_rows),
        "feature_candidate_rows": len(feature_rows),
        "news_macro_feature_path_rows": sum(1 for r in feature_rows if r["source_family"].startswith("public_")),
        "feature_admitted_now": sum(1 for r in feature_rows if r["admitted_as_trading_feature_now"] == "1"),
        "legacy_l2_news_quarantined": True,
        "l1_validation_hooks": len(l1_plan_rows),
        "l1_validation_pass_count": sum(1 for r in l1_ledger_rows if r["result"] == "PASS"),
        "l1_coverage_rows": len(coverage_rows),
        "trading_authority_opened": False,
        "l2_materialization_written": False,
    }
    (REPORT_DIR / "l2_intake_feature_admission_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )
    report = f"""# TASK-4136 L2 입구와 feature 입학 규칙

## 결론

뉴스/매크로는 매매 feature로 쓸 수 있게 개발해야 한다. 다만 지금 바로 feature로 넣는 것이 아니라, L2에서 입학시험을 통과한 것만 feature 후보가 되게 한다.

## 이번에 만든 것

| 항목 | 결과 |
|---|---|
| L2 입구 계약 | `configs/l2_intake_feature_admission_contract.yaml` 생성 |
| L2 intake manifest | {len(intake_rows)}개 source family 등록 |
| 뉴스/매크로 feature 경로 | 영구 차단이 아니라 검증 후 승격 가능으로 명시 |
| 티커/뉴스 매핑 | 모호하면 차단 또는 수동 검토로 분리 |
| 기존 L2 뉴스 코드 | 실행 불가한 quarantine stub으로 분리 |
| L1 계속 검증 | {len(l1_plan_rows)}개 검증 명령과 1회 실행 ledger 생성 |

## 쉽게 말하면

- 일봉/5분봉은 시장 관측값으로 먼저 L2 입구를 통과할 수 있다.
- 뉴스/매크로는 나중에 매매 feature가 될 수 있다.
- 하지만 뉴스/매크로가 매매 feature가 되려면 시간, 출처, 티커/대상 매핑, 중복 제거, 효과 구간 검증을 먼저 통과해야 한다.
- 기존 L2 뉴스 코드는 낡은 우회로라서 새 L2 경로와 분리했다.
- L1 검증은 한 번 하고 끝이 아니라, L0 수집 이후나 주기적으로 다시 돌 수 있게 명령 목록과 실행 증거를 남겼다.

## 아직 일부러 안 한 것

- 실제 L2 feature row 생성
- 매매 신호 생성
- 점수화
- L3 연결
- broker/order/paper/live 권한 변경
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
