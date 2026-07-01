from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TASK-4138"
SLUG = "task_4138_l1_practical_hardening"
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "l1_source_time_precision_policy.yaml"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(ROOT)
    return p.as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def bool_text(value: object) -> str:
    return "1" if bool(value) else "0"


def load_policy() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def run_command(command: list[str]) -> dict[str, str]:
    started = utc_now()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    ended = utc_now()
    output = "\n".join(part for part in [proc.stdout, proc.stderr] if part)
    result_line = ""
    for line in output.splitlines():
        if line.startswith("RESULT:"):
            result_line = line.split(":", 1)[1].strip()
    status = "PASS" if proc.returncode == 0 else "FAIL"
    return {
        "task_id": TASK_ID,
        "validator": " ".join(command),
        "started_at": started,
        "ended_at": ended,
        "exit_code": str(proc.returncode),
        "status": status,
        "result_line": result_line or status,
        "evidence": output[-1200:].replace("\r", ""),
    }


def build_source_time_policy(policy: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in policy["source_family_policy"]:  # type: ignore[index]
        row = dict(item)
        row["task_id"] = TASK_ID
        row["strict_source_time_allowed"] = bool_text(row.get("strict_source_time_allowed"))
        row["feature_allowed_now"] = bool_text(row.get("feature_allowed_now"))
        row["is_imputed_time_possible"] = bool_text(row.get("is_imputed_time_possible"))
        rows.append(row)
    return rows


def build_wikimedia_policy(policy: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in policy["wikimedia_precision_policy"]:  # type: ignore[index]
        row = dict(item)
        row["task_id"] = TASK_ID
        row["source_family"] = "public_market_macro_news_feeds"
        row["source"] = "wikimedia_current_events"
        row["is_imputed_time"] = bool_text(row.get("is_imputed_time"))
        row["strict_source_time_allowed"] = bool_text(row.get("strict_source_time_allowed"))
        row["feature_allowed_now"] = bool_text(row.get("feature_allowed_now"))
        rows.append(row)
    return rows


def build_block_reason_matrix(policy_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    feature_gate = read_csv(ROOT / "data" / "artifacts" / "task_4136_l2_intake_feature_admission" / "l2_feature_admission_gate.csv")
    by_family = {row["source_family"]: row for row in feature_gate}
    rows: list[dict[str, object]] = []
    for item in policy_rows:
        source_family = str(item["source_family"])
        gate = by_family.get(source_family, {})
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": source_family,
                "l1_authority_status": item["authority_status"],
                "strict_source_time_allowed": item["strict_source_time_allowed"],
                "feature_allowed_now": item["feature_allowed_now"],
                "can_be_trading_feature_later": gate.get("can_be_trading_feature_later", "1"),
                "l1_block_reason": item["l1_block_reason"],
                "plain_korean_meaning": plain_korean_reason(source_family),
                "l2_current_state": gate.get("current_state", "L2_GATE_NOT_FOUND"),
                "required_next_validation": gate.get("required_next_validation", item["l2_next_gate"]),
                "why_not_now": gate.get("why_not_now", "L2 admission evidence is not complete."),
            }
        )
    return rows


def plain_korean_reason(source_family: str) -> str:
    reasons = {
        "market_bars_5m": "5분봉은 시간 자체는 믿을 수 있지만, 아직 L2 feature 테이블로 만들 검증은 끝나지 않았다.",
        "daily_bars": "일봉은 시간 자체는 믿을 수 있지만, 아직 L2 feature 테이블로 만들 검증은 끝나지 않았다.",
        "public_context_news_feeds": "뉴스/공식 문서는 후보가 될 수 있지만, 종목 연결과 중복 제거, 오래된 뉴스 처리, 효과 기간 검증이 먼저다.",
        "public_market_macro_news_feeds": "매크로 뉴스는 후보가 될 수 있지만, 실제 공개시각과 효과 기간이 불명확하면 매매 feature로 쓰면 안 된다.",
        "public_newswire_feeds": "뉴스와이어는 후보가 될 수 있지만, 티커 매핑 신뢰도와 이벤트 효과 검증 전에는 feature가 아니다.",
    }
    return reasons.get(source_family, "L1에서 증거와 차단 사유를 명확히 남긴 뒤 L2에서 입학 심사를 한다.")


def build_validation_ledger() -> list[dict[str, str]]:
    validators = [
        [sys.executable, "scripts/validate_l1_source_packet_bootstrap.py"],
        [sys.executable, "scripts/validate_l1_data_present_hardening.py"],
        [sys.executable, "scripts/validate_l2_intake_feature_admission.py"],
    ]
    return [run_command(command) for command in validators if (ROOT / command[1]).exists()]


def write_report(
    policy_rows: list[dict[str, object]],
    wikimedia_rows: list[dict[str, object]],
    block_rows: list[dict[str, object]],
    validation_rows: list[dict[str, str]],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for row in validation_rows if row["status"] == "PASS")
    report = f"""# TASK-4138 L1 Practical Hardening

## 결론

L1은 feature를 직접 만들지 않는다. 대신 아래 세 가지를 더 명확히 남기도록 보강했다.

| 보강 항목 | 이번 작업 결과 |
|---|---|
| 시간 정밀도 | source family별로 실제 시각, 날짜 보정, 정밀도 부족을 분리했다. |
| Wikimedia 정오 정책 | 연/월/일 중 일 단위만 정오 UTC로 둘 수 있지만, 이것은 실제 공개시각이 아니라 보정 시각이다. |
| 막힌 이유 | 각 소스가 왜 아직 trading feature가 아닌지 L1 block reason으로 남겼다. |
| 반복 검증 | 기존 L1/L2 경계 validator를 한 번에 다시 돌린 ledger를 남겼다. |

## 소스별 현재 판단

| Source | 지금 L1 판단 | 쉬운 설명 |
|---|---|---|
"""
    for row in block_rows:
        report += f"| `{row['source_family']}` | `{row['l1_authority_status']}` | {row['plain_korean_meaning']} |\n"
    report += f"""
## Wikimedia 규칙

| 정밀도 | 처리 | feature 가능 |
|---|---|---|
"""
    for row in wikimedia_rows:
        report += f"| `{row['precision']}` | {row['normalized_time_policy']} | `{row['feature_allowed_now']}` |\n"
    report += f"""
## 검증 결과

| 항목 | 값 |
|---|---|
| 실행 validator 수 | {len(validation_rows)} |
| 통과 validator 수 | {passed} |
| trading authority | 열지 않음 |
| paper/live/broker/order | 열지 않음 |

## 산출물

- `configs/l1_source_time_precision_policy.yaml`
- `data/artifacts/{SLUG}/l1_source_time_precision_policy.csv`
- `data/artifacts/{SLUG}/l1_wikimedia_noon_policy.csv`
- `data/artifacts/{SLUG}/l1_feature_block_reason_matrix.csv`
- `data/artifacts/{SLUG}/l1_repeated_validation_run_state.csv`

## 남은 일

L1 기준에서 더 할 일은 broad crawler나 feature 생성이 아니다. 다음은 L2에서 mapping, dedup, stale policy, effect window, leakage check를 붙여서 뉴스/매크로가 실제 매매 feature 후보가 될 수 있는지 입학 심사를 하는 것이다.
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4138 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4138 document registry entries", "modified"),
        ("configs/l1_source_time_precision_policy.yaml", "config", "L1 source-time precision and Wikimedia policy", "created"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "Active SSOT pointer for TASK-4138", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "Current task completion pointer for TASK-4138", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "Current status summary for TASK-4138", "modified"),
        ("docs/architecture/l0_source_acquisition_project_management_plan.md", "architecture_doc", "L1 hardening status update", "modified"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "Human-readable TASK-4138 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4138 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4138 validation results", "created"),
        (f"docs/reports/{SLUG}/l1_practical_hardening_summary.json", "summary", "Machine-readable TASK-4138 summary", "created"),
        ("scripts/run_l1_practical_hardening_4138.py", "script", "Build TASK-4138 L1 hardening artifacts", "created"),
        ("scripts/validate_l1_practical_hardening_4138.py", "validator", "Validate TASK-4138 L1 hardening artifacts", "created"),
        (f"data/artifacts/{SLUG}/l1_source_time_precision_policy.csv", "artifact", "Source-family time precision policy rows", "created"),
        (f"data/artifacts/{SLUG}/l1_wikimedia_noon_policy.csv", "artifact", "Wikimedia precision/noon policy rows", "created"),
        (f"data/artifacts/{SLUG}/l1_feature_block_reason_matrix.csv", "artifact", "Plain block reasons by source family", "created"),
        (f"data/artifacts/{SLUG}/l1_repeated_validation_run_state.csv", "artifact", "Repeated L1/L2 boundary validation run ledger", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [
            {
                "path": path,
                "type": artifact_type,
                "purpose": purpose,
                "created_or_modified": state,
                "task_id": TASK_ID,
            }
            for path, artifact_type, purpose, state in rows
        ],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def build_and_write() -> dict[str, object]:
    policy = load_policy()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    policy_rows = build_source_time_policy(policy)
    wikimedia_rows = build_wikimedia_policy(policy)
    block_rows = build_block_reason_matrix(policy_rows)
    validation_rows = build_validation_ledger()

    write_csv(
        ARTIFACT_DIR / "l1_source_time_precision_policy.csv",
        policy_rows,
        [
            "task_id",
            "source_family",
            "source_time_kind",
            "source_time_precision_allowed",
            "usable_after_policy",
            "authority_status",
            "strict_source_time_allowed",
            "feature_allowed_now",
            "is_imputed_time_possible",
            "l1_block_reason",
            "l2_next_gate",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "l1_wikimedia_noon_policy.csv",
        wikimedia_rows,
        [
            "task_id",
            "source_family",
            "source",
            "precision",
            "normalized_time_policy",
            "is_imputed_time",
            "strict_source_time_allowed",
            "feature_allowed_now",
            "status",
            "block_reason",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "l1_feature_block_reason_matrix.csv",
        block_rows,
        [
            "task_id",
            "source_family",
            "l1_authority_status",
            "strict_source_time_allowed",
            "feature_allowed_now",
            "can_be_trading_feature_later",
            "l1_block_reason",
            "plain_korean_meaning",
            "l2_current_state",
            "required_next_validation",
            "why_not_now",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "l1_repeated_validation_run_state.csv",
        validation_rows,
        ["task_id", "validator", "started_at", "ended_at", "exit_code", "status", "result_line", "evidence"],
    )
    write_report(policy_rows, wikimedia_rows, block_rows, validation_rows)
    write_manifest()

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "source_family_policy_rows": len(policy_rows),
        "wikimedia_policy_rows": len(wikimedia_rows),
        "block_reason_rows": len(block_rows),
        "validation_runs": len(validation_rows),
        "validation_failures": [row for row in validation_rows if row["status"] != "PASS"],
        "trading_authority_opened": False,
        "paper_live_broker_order_opened": False,
        "feature_allowed_now_rows": [row for row in policy_rows if row["feature_allowed_now"] != "0"],
    }
    (REPORT_DIR / "l1_practical_hardening_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
