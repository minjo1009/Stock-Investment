from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SCHEDULER_CONFIG = ROOT / "configs/db_source_acquisition_scheduler.json"
ROADMAP = ROOT / "docs/architecture/l0_source_acquisition_project_management_plan.md"
OPERATOR_POLICY = ROOT / "docs/architecture/l0_source_acquisition_operator_override_policy.md"
NEWS_POLICY = ROOT / "docs/architecture/l0_news_enablement_policy.md"
MICROSTRUCTURE_POLICY = ROOT / "docs/architecture/l0_microstructure_collection_policy.md"
ACTIVE_SSOT = ROOT / "docs/active/ACTIVE_SSOT_INDEX.md"
CURRENT_TASKS = ROOT / "docs/active/CURRENT_TASKS.md"
PROJECT_STATUS = ROOT / "docs/active/PROJECT_STATUS.md"
WORKSTREAM_MAP = ROOT / "docs/active/WORKSTREAM_MAP.md"

REQUIRED_STAGE_NAMES = [
    "official_core_api_smoke_stabilization",
    "realtime_source_budget_optimization",
    "realtime_scheduler_setup_and_execution",
    "historical_backfill_optimization",
    "background_historical_backfill_from_2016",
    "l1_quality_coverage_audit_and_l2_handoff",
]

FORBIDDEN_TRUE_FIELDS = [
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
    "live_order_enabled",
    "replay_permission_granted",
    "buy_sell_signal_generation_permitted",
]

CLOUD_MATERIALIZATION_CHECKS = [
    ROOT / "tools/db/source_acquisition/public_newswire_collector.py",
    ROOT / "tools/db/source_acquisition/public_market_macro_news_collector.py",
    ROOT / "configs/source_registry/l0_public_news_capability_sources.json",
]

CONFLICT_SUFFIX_FILES = [
    ROOT / "scripts/start_l0_public_market_macro_news_backfill-DESKTOP-2R00TB4.ps1",
    ROOT / "scripts/start_l0_public_market_macro_news_collector-DESKTOP-2R00TB4.ps1",
    ROOT / "src/data/alpaca_historical_microstructure_export-DESKTOP-2R00TB4.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def require_contains(errors: list[str], path: Path, needles: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")
        return
    text = read_text(path)
    for needle in needles:
        if needle not in text:
            errors.append(f"{path.relative_to(ROOT)} missing required text: {needle}")


def validate_scheduler(errors: list[str]) -> None:
    config = read_json(SCHEDULER_CONFIG)
    if config.get("posture") != "conservative_default":
        errors.append("scheduler posture must remain conservative_default")
    permissions = config.get("permissions", {})
    for field in FORBIDDEN_TRUE_FIELDS:
        if int(bool(permissions.get(field, 0))) != 0:
            errors.append(f"scheduler permissions.{field} must remain closed")
    for job in config.get("jobs", []):
        if bool(job.get("enabled")):
            errors.append(f"base scheduler job must remain disabled: {job.get('name')}")
        if bool(job.get("allow_network")):
            errors.append(f"base scheduler job allow_network must remain false: {job.get('name')}")
        for field in FORBIDDEN_TRUE_FIELDS[:4]:
            if int(bool(job.get(field, 0))) != 0:
                errors.append(f"{job.get('name')}.{field} must remain closed")
    plan = config.get("management_plan", {})
    if plan.get("active_task") != "TASK-4117":
        errors.append("scheduler management_plan.active_task must be TASK-4117")
    stages = plan.get("stages", [])
    names = [str(stage.get("name", "")) for stage in stages if isinstance(stage, dict)]
    if names != REQUIRED_STAGE_NAMES:
        errors.append("scheduler management_plan stages do not match required 1-6 roadmap")
    next_count = sum(1 for stage in stages if str(stage.get("status", "")).upper() == "NEXT")
    stage6 = next((stage for stage in stages if stage.get("stage") == 6), {})
    stage6_closed = stage6.get("status") in {"COMPLETE_AUDIT_L2_HANDOFF_BLOCKED", "COMPLETE_PARTIAL_L2_CONTEXT_HANDOFF_READY"}
    if stage6_closed:
        if next_count != 0:
            errors.append("scheduler management_plan must have no NEXT stage after Stage 6 closeout")
    elif next_count != 1:
        errors.append("scheduler management_plan must have exactly one NEXT stage before Stage 6 closeout")
    modes = plan.get("implementation_modes", {})
    if modes.get("codex_gpt_role") != "planning_review_recovery_only_not_runtime_collection":
        errors.append("Codex/GPT role must remain planning/review/recovery only")
    if "public_headline_browser_watch" not in modes.get("chrome_smoke_only", []):
        errors.append("Chrome crawler must be classified as smoke-only")


def validate_docs(errors: list[str]) -> None:
    require_contains(
        errors,
        ROADMAP,
        [
            "Six-Stage Roadmap",
            "Source Implementation Modes",
            "Mapping Status",
            "Codex/GPT is not a runtime collection engine or source of truth.",
            "Strategy: NOT_ACCEPTED",
        ],
    )
    for path in [OPERATOR_POLICY, NEWS_POLICY, MICROSTRUCTURE_POLICY]:
        require_contains(errors, path, ["l0_source_acquisition_project_management_plan.md"])
    require_contains(errors, ACTIVE_SSOT, ["task_4116_l0_l1_source_acquisition_stash_recovery", "task_4117_l0_source_acquisition_project_management_integration"])
    require_contains(errors, CURRENT_TASKS, ["TASK-4117", "TASK-4118"])
    require_contains(errors, PROJECT_STATUS, ["L0/L1 Source Acquisition Status", "PARTIAL_CONTEXT_ONLY_HANDOFF_READY"])
    require_contains(errors, WORKSTREAM_MAP, ["l0_source_acquisition_project_management_plan.md"])


def validate_conflict_files(errors: list[str]) -> None:
    for path in CONFLICT_SUFFIX_FILES:
        if path.exists():
            errors.append(f"conflict suffix file must not remain active: {path.relative_to(ROOT)}")


def materialization_warnings() -> list[str]:
    warnings: list[str] = []
    for path in CLOUD_MATERIALIZATION_CHECKS:
        try:
            path.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            warnings.append(f"optional restored file missing locally: {path.relative_to(ROOT)}")
        except OSError as exc:
            warnings.append(f"optional restored file not materialized locally: {path.relative_to(ROOT)} {type(exc).__name__}")
    return warnings


def main() -> int:
    errors: list[str] = []
    validate_scheduler(errors)
    validate_docs(errors)
    validate_conflict_files(errors)
    for warning in materialization_warnings():
        print(f"[L0_SOURCE_ACQUISITION_PM_WARNING] {warning}")
    if errors:
        for error in errors:
            print(f"[L0_SOURCE_ACQUISITION_PM_ERROR] {error}")
        return 1
    print("[L0_SOURCE_ACQUISITION_PM_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
