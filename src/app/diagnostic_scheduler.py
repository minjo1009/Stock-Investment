"""Dry-run diagnostic scheduler for the L0-L6 operating loop.

This module coordinates diagnostic heartbeats only. It does not call KIS,
submit orders, run replay, mutate broker state, or change acceptance status.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime

try:
    from src.brain.diagnostic_orchestration import (
        DiagnosticHeartbeatCadence,
        L0L6DiagnosticRuntimeState,
        build_diagnostic_orchestration_decision,
    )
    from src.state.store import (
        acquire_scheduler_lease,
        get_latest_diagnostic_state_hash,
        initialize_store,
        list_runtime_operating_metrics,
        record_diagnostic_runtime_heartbeat,
        release_scheduler_lease,
        validate_scheduler_lease_token,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from brain.diagnostic_orchestration import (
        DiagnosticHeartbeatCadence,
        L0L6DiagnosticRuntimeState,
        build_diagnostic_orchestration_decision,
    )
    from state.store import (
        acquire_scheduler_lease,
        get_latest_diagnostic_state_hash,
        initialize_store,
        list_runtime_operating_metrics,
        record_diagnostic_runtime_heartbeat,
        release_scheduler_lease,
        validate_scheduler_lease_token,
    )


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _items(value: str | tuple[str, ...] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(item.strip() for item in str(value).split(",") if item.strip())


@dataclass(frozen=True)
class DiagnosticSchedulerResult:
    cadence: str
    status: str
    should_execute: bool
    state_hash: str
    idempotency_key: str
    heartbeat_inserted: bool
    lease_acquired: bool
    lease_key: str
    lease_token: str
    reason_codes: tuple[str, ...]
    metrics: dict

    def to_dict(self) -> dict:
        return {
            "cadence": self.cadence,
            "status": self.status,
            "should_execute": self.should_execute,
            "state_hash": self.state_hash,
            "idempotency_key": self.idempotency_key,
            "heartbeat_inserted": self.heartbeat_inserted,
            "lease_acquired": self.lease_acquired,
            "lease_key": self.lease_key,
            "lease_token": self.lease_token,
            "reason_codes": list(self.reason_codes),
            "metrics": self.metrics,
        }


def run_diagnostic_scheduler_once(
    *,
    db_path: str,
    cadence: str,
    heartbeat_bucket_ts: str,
    owner_id: str = "diagnostic-scheduler",
    now: str | None = None,
    market_session_id: str = "diagnostic-session",
    market_data_asof_ts: str | None = None,
    account_state_ref: str = "paper-account:diagnostic-only",
    source_receipt_ids: tuple[str, ...] = (),
    primitive_batch_ids: tuple[str, ...] = (),
    meaning_ids: tuple[str, ...] = (),
    thesis_ids: tuple[str, ...] = (),
    policy_action_ids: tuple[str, ...] = (),
    runtime_decision_ids: tuple[str, ...] = ("runtime-review-state",),
    order_state_refs: tuple[str, ...] = ("orders:none",),
    changed_candidate_ids: tuple[str, ...] = (),
    validation_refs: tuple[str, ...] = ("python scripts/task_registry_validate.py",),
    lease_ttl_seconds: int = 300,
    kis_environment: str | None = None,
) -> DiagnosticSchedulerResult:
    initialize_store(db_path)
    now = now or utc_now()
    cadence_enum = DiagnosticHeartbeatCadence(cadence)
    state = L0L6DiagnosticRuntimeState(
        cadence=cadence_enum,
        heartbeat_bucket_ts=heartbeat_bucket_ts,
        market_session_id=market_session_id,
        market_data_asof_ts=market_data_asof_ts or heartbeat_bucket_ts,
        account_state_ref=account_state_ref,
        source_receipt_ids=source_receipt_ids,
        primitive_batch_ids=primitive_batch_ids,
        meaning_ids=meaning_ids,
        thesis_ids=thesis_ids,
        policy_action_ids=policy_action_ids,
        runtime_decision_ids=runtime_decision_ids,
        order_state_refs=order_state_refs,
        changed_candidate_ids=changed_candidate_ids,
        validation_refs=validation_refs,
    )
    previous_hash = get_latest_diagnostic_state_hash(
        db_path,
        cadence=cadence_enum.value,
        heartbeat_bucket_ts=heartbeat_bucket_ts,
    )
    decision = build_diagnostic_orchestration_decision(state, previous_state_hash=previous_hash)
    lease_key = f"{cadence_enum.value}:{heartbeat_bucket_ts}"
    environment = str(kis_environment or os.environ.get("KIS_ENVIRONMENT", "paper")).strip().lower() or "paper"
    if environment != "paper":
        heartbeat_inserted = record_diagnostic_runtime_heartbeat(
            db_path,
            idempotency_key=decision.idempotency_key,
            cadence=decision.cadence.value,
            heartbeat_bucket_ts=heartbeat_bucket_ts,
            state_hash=decision.state_hash,
            status="BLOCKED_NON_PAPER_ENV",
            should_execute=False,
            reason_codes=tuple(decision.reason_codes + ("KIS_ENVIRONMENT_NOT_PAPER",)),
            allowed_operations=decision.allowed_operations,
            forbidden_operations=decision.forbidden_operations,
            created_at=now,
        )
        return DiagnosticSchedulerResult(
            cadence=cadence_enum.value,
            status="BLOCKED_NON_PAPER_ENV",
            should_execute=False,
            state_hash=decision.state_hash,
            idempotency_key=decision.idempotency_key,
            heartbeat_inserted=heartbeat_inserted,
            lease_acquired=False,
            lease_key=lease_key,
            lease_token="",
            reason_codes=tuple(decision.reason_codes + ("KIS_ENVIRONMENT_NOT_PAPER",)),
            metrics=list_runtime_operating_metrics(db_path, now_iso=now),
        )

    if not decision.should_execute:
        heartbeat_inserted = record_diagnostic_runtime_heartbeat(
            db_path,
            idempotency_key=decision.idempotency_key,
            cadence=decision.cadence.value,
            heartbeat_bucket_ts=heartbeat_bucket_ts,
            state_hash=decision.state_hash,
            status=decision.status.value,
            should_execute=False,
            reason_codes=decision.reason_codes,
            allowed_operations=decision.allowed_operations,
            forbidden_operations=decision.forbidden_operations,
            created_at=now,
        )
        return DiagnosticSchedulerResult(
            cadence=cadence_enum.value,
            status=decision.status.value,
            should_execute=False,
            state_hash=decision.state_hash,
            idempotency_key=decision.idempotency_key,
            heartbeat_inserted=heartbeat_inserted,
            lease_acquired=False,
            lease_key=lease_key,
            lease_token="",
            reason_codes=decision.reason_codes,
            metrics=list_runtime_operating_metrics(db_path, now_iso=now),
        )

    lease = acquire_scheduler_lease(
        db_path,
        lease_key=lease_key,
        cadence=cadence_enum.value,
        bucket_ts=heartbeat_bucket_ts,
        owner_id=owner_id,
        state_hash=decision.state_hash,
        now=now,
        ttl_seconds=lease_ttl_seconds,
    )
    if not lease["acquired"]:
        heartbeat_inserted = record_diagnostic_runtime_heartbeat(
            db_path,
            idempotency_key=decision.idempotency_key,
            cadence=decision.cadence.value,
            heartbeat_bucket_ts=heartbeat_bucket_ts,
            state_hash=decision.state_hash,
            status="LEASE_HELD_SKIPPED",
            should_execute=False,
            reason_codes=tuple(decision.reason_codes + ("LEASE_HELD_BY_ACTIVE_OWNER",)),
            allowed_operations=decision.allowed_operations,
            forbidden_operations=decision.forbidden_operations,
            created_at=now,
        )
        return DiagnosticSchedulerResult(
            cadence=cadence_enum.value,
            status="LEASE_HELD_SKIPPED",
            should_execute=False,
            state_hash=decision.state_hash,
            idempotency_key=decision.idempotency_key,
            heartbeat_inserted=heartbeat_inserted,
            lease_acquired=False,
            lease_key=lease_key,
            lease_token=str(lease["lease_token"]),
            reason_codes=tuple(decision.reason_codes + ("LEASE_HELD_BY_ACTIVE_OWNER",)),
            metrics=list_runtime_operating_metrics(db_path, now_iso=now),
        )

    lease_token = str(lease["lease_token"])
    if not validate_scheduler_lease_token(db_path, lease_key=lease_key, lease_token=lease_token, now=now):
        raise RuntimeError("scheduler lease token is not active")
    heartbeat_inserted = record_diagnostic_runtime_heartbeat(
        db_path,
        idempotency_key=decision.idempotency_key,
        cadence=decision.cadence.value,
        heartbeat_bucket_ts=heartbeat_bucket_ts,
        state_hash=decision.state_hash,
        status=decision.status.value,
        should_execute=decision.should_execute,
        reason_codes=tuple(decision.reason_codes + ("LEASE_TOKEN_VALIDATED",)),
        allowed_operations=decision.allowed_operations,
        forbidden_operations=decision.forbidden_operations,
        created_at=now,
    )
    release_scheduler_lease(db_path, lease_key=lease_key, lease_token=lease_token, released_at=now)
    return DiagnosticSchedulerResult(
        cadence=cadence_enum.value,
        status=decision.status.value,
        should_execute=decision.should_execute,
        state_hash=decision.state_hash,
        idempotency_key=decision.idempotency_key,
        heartbeat_inserted=heartbeat_inserted,
        lease_acquired=True,
        lease_key=lease_key,
        lease_token=lease_token,
        reason_codes=tuple(decision.reason_codes + ("LEASE_TOKEN_VALIDATED",)),
        metrics=list_runtime_operating_metrics(db_path, now_iso=now),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one dry-run diagnostic scheduler tick.")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--cadence", required=True, choices=[item.value for item in DiagnosticHeartbeatCadence])
    parser.add_argument("--bucket-ts", required=True)
    parser.add_argument("--owner-id", default="diagnostic-scheduler")
    parser.add_argument("--now", default=None)
    parser.add_argument("--market-session-id", default="diagnostic-session")
    parser.add_argument("--market-data-asof-ts", default=None)
    parser.add_argument("--account-state-ref", default="paper-account:diagnostic-only")
    parser.add_argument("--source-receipt-ids", default="")
    parser.add_argument("--runtime-decision-ids", default="runtime-review-state")
    parser.add_argument("--changed-candidate-ids", default="")
    args = parser.parse_args()
    result = run_diagnostic_scheduler_once(
        db_path=args.db_path,
        cadence=args.cadence,
        heartbeat_bucket_ts=args.bucket_ts,
        owner_id=args.owner_id,
        now=args.now,
        market_session_id=args.market_session_id,
        market_data_asof_ts=args.market_data_asof_ts,
        account_state_ref=args.account_state_ref,
        source_receipt_ids=_items(args.source_receipt_ids),
        runtime_decision_ids=_items(args.runtime_decision_ids),
        changed_candidate_ids=_items(args.changed_candidate_ids),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
