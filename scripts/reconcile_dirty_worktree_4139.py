from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TASK-4139"
SLUG = "task_4139_dirty_worktree_artifact_reconciliation"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(ROOT)
    return p.as_posix()


def git_status_rows() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    parts = [part.decode("utf-8", errors="replace") for part in proc.stdout.split(b"\0") if part]
    rows: list[dict[str, str]] = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        status = entry[:2]
        path = entry[3:].replace("\\", "/")
        if status.startswith("R") or status.startswith("C"):
            i += 1
            if i < len(parts):
                path = parts[i].replace("\\", "/")
        rows.append({"status": status, "path": path})
        i += 1
    return rows


def classify(status: str, path: str) -> tuple[str, str, str, str]:
    deleted = "D" in status
    untracked = status == "??"
    modified = "M" in status
    if path.startswith("docs/reports/task_4139_") or path.startswith("data/artifacts/task_4139_"):
        return ("TASK_4139_OUTPUT", "KEEP_AND_REGISTER", "P0", "이번 task 산출물이다.")
    if path in {
        "ops/task_registry.yaml",
        "ops/doc_registry.yaml",
        "configs/l1_source_time_precision_policy.yaml",
        "scripts/run_l1_practical_hardening_4138.py",
        "scripts/validate_l1_practical_hardening_4138.py",
    } or path.startswith("docs/reports/task_4138_"):
        return ("RECENT_L1_TASK_OUTPUT", "KEEP_AND_REGISTER_OR_COMMIT_TOGETHER", "P0", "최근 L1 작업 산출물이다.")
    if path.startswith("ops/") or path.startswith("docs/active/"):
        return ("GOVERNANCE_OR_ACTIVE_DOC", "KEEP_AND_RECONCILE_REGISTRY", "P0", "프로젝트 관리/현재 상태 문서다.")
    if deleted and path.endswith(".dvc"):
        return ("DVC_POINTER_DELETED", "RESTORE_OR_CONFIRM_DVC_RETIREMENT", "P0", "DVC pointer 삭제는 원본 복구 가능성에 직접 영향이 있다.")
    if deleted and (path.startswith("src/brain/") or path.startswith("src/l2/") or "/l2_" in path or "/l3_" in path):
        return ("L2_L3_CODE_OR_REPORT_DELETED", "OWNER_REVIEW_BEFORE_DELETE_OR_RESTORE", "P0", "L2/L3 코드나 보고서 삭제 표시다. 자동 삭제 확정 금지.")
    if deleted and (path.startswith("docs/reports/A") or path.startswith("docs/reports/task_l")):
        return ("HISTORICAL_REPORT_DELETED", "CONFIRM_ARCHIVE_OR_RESTORE", "P1", "과거 보고서 삭제 표시다. archive 정책 확인이 필요하다.")
    if path.startswith("configs/source_registry/") or path.startswith("configs/db_source_acquisition") or path.startswith("configs/local_templates/"):
        return ("L0_SOURCE_CONFIG_CHANGED", "KEEP_AND_RECONCILE_WITH_L0_REPORTS", "P0", "L0 소스/스케줄러 설정 변경이다.")
    if path.startswith("scripts/run_l0") or path.startswith("scripts/start_l0") or path.startswith("scripts/validate_l0") or path.startswith("tools/db/source_acquisition/"):
        return ("L0_SOURCE_CODE_CHANGED", "KEEP_AND_RECONCILE_WITH_L0_REPORTS", "P0", "L0 수집 코드 변경이다.")
    if path.startswith("data/artifacts/"):
        return ("DATA_ARTIFACT_CHANGED", "KEEP_AS_ARTIFACT_OR_DVC_IGNORE_DECISION", "P1", "데이터 산출물 변경이다. Git/DVC/ignore 정책 판단이 필요하다.")
    if path.startswith("docs/reports/task_41") or path.startswith("docs/architecture/") or path.startswith("docs/operating_system/"):
        return ("CURRENT_DOC_OR_TASK_REPORT", "KEEP_AND_RECONCILE_REGISTRY", "P1", "최근 작업 문서 또는 운영 문서다.")
    if path.startswith("src/app/") or path.startswith("src/integration/") or path.startswith("src/strategy/") or path.startswith("src/risk/"):
        return ("RUNTIME_OR_TRADING_ADJACENT_CHANGED", "OWNER_REVIEW_BEFORE_COMMIT", "P0", "런타임/브로커/전략 인접 변경이다. 자동 정리 금지.")
    if path.startswith("frontend/"):
        return ("FRONTEND_OR_CATALOG_CHANGED", "KEEP_OR_REGISTER_IF_ACTIVE", "P2", "프론트엔드 또는 read-model 카탈로그 변경이다.")
    if path.startswith("tests/"):
        return ("TEST_FILE_CHANGED", "PAIR_WITH_RELATED_CODE_OR_RESTORE", "P1", "테스트 변경/삭제다. 관련 코드와 함께 판단해야 한다.")
    if untracked:
        return ("UNTRACKED_FILE", "CLASSIFY_REGISTER_OR_IGNORE", "P2", "Git에 새로 잡힌 파일이다.")
    if deleted:
        return ("DELETED_UNCLASSIFIED", "OWNER_REVIEW_BEFORE_DELETE_OR_RESTORE", "P1", "삭제 표시지만 분류 규칙에 걸리지 않았다.")
    if modified:
        return ("MODIFIED_UNCLASSIFIED", "OWNER_REVIEW_BEFORE_COMMIT", "P2", "수정 표시지만 분류 규칙에 걸리지 않았다.")
    return ("OTHER_GIT_STATE", "OWNER_REVIEW", "P2", "기타 Git 상태다.")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def build() -> dict[str, object]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows = git_status_rows()
    rows: list[dict[str, object]] = []
    for item in raw_rows:
        bucket, action, priority, reason = classify(item["status"], item["path"])
        rows.append(
            {
                "task_id": TASK_ID,
                "git_status": item["status"],
                "path": item["path"],
                "bucket": bucket,
                "recommended_action": action,
                "priority": priority,
                "reason": reason,
            }
        )
    write_csv(
        ARTIFACT_DIR / "dirty_worktree_inventory.csv",
        rows,
        ["task_id", "git_status", "path", "bucket", "recommended_action", "priority", "reason"],
    )

    bucket_counts = Counter(str(row["bucket"]) for row in rows)
    action_counts = Counter(str(row["recommended_action"]) for row in rows)
    priority_counts = Counter(str(row["priority"]) for row in rows)
    summary_rows = [
        {"metric_type": "bucket", "name": name, "count": count}
        for name, count in sorted(bucket_counts.items())
    ] + [
        {"metric_type": "recommended_action", "name": name, "count": count}
        for name, count in sorted(action_counts.items())
    ] + [
        {"metric_type": "priority", "name": name, "count": count}
        for name, count in sorted(priority_counts.items())
    ]
    write_csv(ARTIFACT_DIR / "dirty_worktree_summary.csv", summary_rows, ["metric_type", "name", "count"])

    p0_rows = [row for row in rows if row["priority"] == "P0"]
    write_csv(
        ARTIFACT_DIR / "dirty_worktree_p0_review_queue.csv",
        p0_rows,
        ["task_id", "git_status", "path", "bucket", "recommended_action", "priority", "reason"],
    )

    report = "# TASK-4139 Dirty Worktree / Artifact Reconciliation\n\n"
    report += "## 결론\n\n"
    report += "현재 dirty file은 단순 임시파일 묶음이 아니다. 최근 L0/L1 작업 산출물, 과거 삭제 표시, DVC pointer 삭제, L2/L3 코드 삭제 표시, 런타임 인접 변경이 섞여 있다. 그래서 자동 삭제나 자동 restore를 하지 않고 분류표와 P0 review queue를 만들었다.\n\n"
    report += "## 요약\n\n"
    report += "| 항목 | 개수 |\n|---|---:|\n"
    report += f"| 전체 dirty row | {len(rows)} |\n"
    report += f"| P0 review row | {len(p0_rows)} |\n"
    report += f"| 삭제 표시 row | {sum(1 for row in rows if 'D' in str(row['git_status']))} |\n"
    report += f"| untracked row | {sum(1 for row in rows if row['git_status'] == '??')} |\n\n"
    report += "## 가장 중요한 처리 원칙\n\n"
    report += "| 원칙 | 의미 |\n|---|---|\n"
    report += "| 삭제 자동 확정 금지 | `D` 표시 파일은 사용자/owner 확인 전 삭제 확정하지 않는다. |\n"
    report += "| DVC pointer 우선 확인 | `.dvc` 삭제는 데이터 복구성에 영향을 주므로 restore/retire 결정을 따로 해야 한다. |\n"
    report += "| 최근 L0/L1 산출물 보존 | TASK-4116 이후 source acquisition 산출물은 registry/manifest와 맞춰 보존한다. |\n"
    report += "| 런타임 인접 변경 주의 | `src/app`, `src/integration`, `src/strategy`, `src/risk` 변경은 별도 owner review 전 커밋/삭제하지 않는다. |\n\n"
    report += "## 다음 액션\n\n"
    report += "1. `dirty_worktree_p0_review_queue.csv`부터 owner 판단을 받는다.\n"
    report += "2. DVC pointer 삭제는 restore할지, 명시적으로 retire할지 결정한다.\n"
    report += "3. 최근 TASK-4116~TASK-4140 산출물은 manifest/doc registry 기준으로 묶어 보존한다.\n"
    report += "4. 삭제 확정은 별도 cleanup task에서만 진행한다.\n"
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")

    manifest_rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4139 registry entry", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4139 doc registry entries", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4139 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4139 project status note", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4139 active report pointer", "modified"),
        ("scripts/reconcile_dirty_worktree_4139.py", "script", "Build dirty worktree reconciliation artifacts", "created"),
        ("scripts/validate_dirty_worktree_reconciliation_4139.py", "validator", "Validate dirty worktree reconciliation artifacts", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4139 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4139 manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4139 validation results", "created"),
        (f"docs/reports/{SLUG}/dirty_reconciliation_summary.json", "summary", "Machine-readable dirty reconciliation summary", "created"),
        (f"data/artifacts/{SLUG}/dirty_worktree_inventory.csv", "artifact", "Full dirty file classification inventory", "created"),
        (f"data/artifacts/{SLUG}/dirty_worktree_summary.csv", "artifact", "Dirty file summary counts", "created"),
        (f"data/artifacts/{SLUG}/dirty_worktree_p0_review_queue.csv", "artifact", "P0 dirty file review queue", "created"),
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
            for path, artifact_type, purpose, state in manifest_rows
        ],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "total_dirty_rows": len(rows),
        "p0_review_rows": len(p0_rows),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "files_deleted_or_restored_by_this_task": 0,
        "automatic_cleanup_performed": False,
    }
    (REPORT_DIR / "dirty_reconciliation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
