"""Operator-owned dry-run runtime scheduler supervisor.

This module runs diagnostic heartbeats only. It does not submit orders, call a
broker, run replay, install an OS scheduler, or change acceptance status.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

try:
    from src.app.diagnostic_scheduler import DiagnosticSchedulerResult, run_diagnostic_scheduler_once
    from src.brain.diagnostic_orchestration import DiagnosticHeartbeatCadence
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from app.diagnostic_scheduler import DiagnosticSchedulerResult, run_diagnostic_scheduler_once
    from brain.diagnostic_orchestration import DiagnosticHeartbeatCadence


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(UTC)


def _bucket_ts(now: str, interval_minutes: int) -> str:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    dt = _parse_utc(now)
    floored_minute = (dt.minute // interval_minutes) * interval_minutes
    bucket = dt.replace(minute=floored_minute, second=0, microsecond=0)
    return bucket.isoformat().replace("+00:00", "Z")


def _is_due(now: str, interval_minutes: int) -> bool:
    dt = _parse_utc(now)
    minute_of_day = dt.hour * 60 + dt.minute
    return dt.second == 0 and minute_of_day % interval_minutes == 0


def _items(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    raise ValueError("expected string or list of strings")


@dataclass(frozen=True)
class CadenceConfig:
    cadence: str
    interval_minutes: int
    enabled: bool = True
    source_receipt_ids: tuple[str, ...] = ()
    runtime_decision_ids: tuple[str, ...] = ("runtime-review-state",)
    changed_candidate_ids: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = ("python scripts/task_registry_validate.py",)

    @classmethod
    def from_dict(cls, payload: dict) -> "CadenceConfig":
        cadence = str(payload.get("cadence") or "").strip()
        DiagnosticHeartbeatCadence(cadence)
        interval = int(payload.get("interval_minutes") or 0)
        if interval <= 0:
            raise ValueError("interval_minutes must be positive")
        return cls(
            cadence=cadence,
            interval_minutes=interval,
            enabled=bool(payload.get("enabled", True)),
            source_receipt_ids=_items(payload.get("source_receipt_ids")),
            runtime_decision_ids=_items(payload.get("runtime_decision_ids")) or ("runtime-review-state",),
            changed_candidate_ids=_items(payload.get("changed_candidate_ids")),
            validation_refs=_items(payload.get("validation_refs")) or ("python scripts/task_registry_validate.py",),
        )


@dataclass(frozen=True)
class RuntimeSchedulerConfig:
    owner_id: str
    db_path: str
    kis_environment: str
    lease_ttl_seconds: int
    cadences: tuple[CadenceConfig, ...]

    @classmethod
    def from_dict(cls, payload: dict) -> "RuntimeSchedulerConfig":
        owner_id = str(payload.get("owner_id") or "").strip()
        if not owner_id:
            raise ValueError("owner_id is required")
        db_path = str(payload.get("db_path") or "trading.db").strip()
        kis_environment = str(payload.get("kis_environment") or "paper").strip().lower() or "paper"
        lease_ttl_seconds = int(payload.get("lease_ttl_seconds") or 300)
        cadences = tuple(CadenceConfig.from_dict(item) for item in payload.get("cadences", ()))
        if not cadences:
            raise ValueError("at least one cadence is required")
        if kis_environment != "paper":
            raise ValueError("runtime diagnostic scheduler config must use paper KIS environment")
        return cls(
            owner_id=owner_id,
            db_path=db_path,
            kis_environment=kis_environment,
            lease_ttl_seconds=lease_ttl_seconds,
            cadences=cadences,
        )


@dataclass(frozen=True)
class RuntimeSchedulerSupervisorResult:
    now: str
    owner_id: str
    dry_run_only: bool
    executed: tuple[dict, ...]
    skipped: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "now": self.now,
            "owner_id": self.owner_id,
            "dry_run_only": self.dry_run_only,
            "executed": list(self.executed),
            "skipped": list(self.skipped),
        }


def load_runtime_scheduler_config(path: str | Path) -> RuntimeSchedulerConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("scheduler config must be a JSON object")
    return RuntimeSchedulerConfig.from_dict(payload)


def run_runtime_scheduler_supervisor_once(
    *,
    config: RuntimeSchedulerConfig,
    now: str | None = None,
    force_due: bool = False,
) -> RuntimeSchedulerSupervisorResult:
    now = now or _utc_now()
    executed: list[dict] = []
    skipped: list[dict] = []
    for cadence in config.cadences:
        if not cadence.enabled:
            skipped.append({"cadence": cadence.cadence, "reason": "CADENCE_DISABLED"})
            continue
        if not force_due and not _is_due(now, cadence.interval_minutes):
            skipped.append({"cadence": cadence.cadence, "reason": "NOT_DUE"})
            continue
        bucket = _bucket_ts(now, cadence.interval_minutes)
        try:
            result: DiagnosticSchedulerResult = run_diagnostic_scheduler_once(
                db_path=config.db_path,
                cadence=cadence.cadence,
                heartbeat_bucket_ts=bucket,
                owner_id=config.owner_id,
                now=now,
                source_receipt_ids=cadence.source_receipt_ids,
                runtime_decision_ids=cadence.runtime_decision_ids,
                changed_candidate_ids=cadence.changed_candidate_ids,
                validation_refs=cadence.validation_refs,
                lease_ttl_seconds=config.lease_ttl_seconds,
                kis_environment=config.kis_environment,
            )
            executed.append(result.to_dict())
        except Exception as exc:
            skipped.append({"cadence": cadence.cadence, "reason": "CADENCE_FAILED", "detail": str(exc)})
    return RuntimeSchedulerSupervisorResult(
        now=now,
        owner_id=config.owner_id,
        dry_run_only=True,
        executed=tuple(executed),
        skipped=tuple(skipped),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one dry-run runtime scheduler supervisor cycle.")
    parser.add_argument("--config", default="configs/runtime_diagnostic_scheduler.json")
    parser.add_argument("--now", default=None)
    parser.add_argument("--force-due", action="store_true")
    args = parser.parse_args()
    config = load_runtime_scheduler_config(args.config)
    result = run_runtime_scheduler_supervisor_once(config=config, now=args.now, force_due=args.force_due)
    print(json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
