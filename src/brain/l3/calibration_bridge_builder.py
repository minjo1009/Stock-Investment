from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Mapping

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow, bridge_row_to_dict


BRIDGE_KEY_COLUMNS = ("meaning_id", "l2_primitive_id", "source_receipt_id", "primitive_id")
OUTCOME_KEY_COLUMNS = (
    "outcome_bridge_key",
    "lifecycle_id",
    "continuation_id",
    "simulated_lifecycle_id",
)
OUTCOME_VALUE_COLUMNS = (
    "win_flag",
    "positive_return_flag",
    "return_from_entry",
    "net_return_from_entry",
    "forward_return_pct",
)


@dataclass(frozen=True)
class L3BridgeEligibilityAuditRow:
    candidate_path: str
    has_l3_bridge_key_flag: int
    has_outcome_key_flag: int
    has_outcome_value_flag: int
    eligible_bridge_row_count: int
    inferred_matching_required_flag: int
    allowed_for_calibration_flag: int
    available_bridge_columns: str
    available_outcome_columns: str
    missing_bridge_columns: str
    rejection_reason: str


def bridge_rows_from_records(
    records: Iterable[Mapping[str, object]],
    *,
    outcome_source_table: str,
    bridge_source_artifact: str,
) -> tuple[L3OutcomeBridgeRow, ...]:
    rows: list[L3OutcomeBridgeRow] = []
    for idx, record in enumerate(records, start=1):
        meaning_id = _text(record.get("meaning_id"))
        l2_primitive_id = _text(record.get("l2_primitive_id")) or _text(record.get("primitive_id"))
        source_receipt_id = _text(record.get("source_receipt_id"))
        if not any((meaning_id, l2_primitive_id, source_receipt_id)):
            continue
        outcome_bridge_key = (
            _text(record.get("outcome_bridge_key"))
            or _text(record.get("lifecycle_id"))
            or _text(record.get("continuation_id"))
            or _text(record.get("simulated_lifecycle_id"))
        )
        if not outcome_bridge_key:
            continue
        method = _bridge_method(meaning_id, l2_primitive_id, source_receipt_id)
        bridge_id = _text(record.get("bridge_id")) or f"l3_bridge:{outcome_source_table}:{idx}:{outcome_bridge_key}"
        rows.append(
            L3OutcomeBridgeRow(
                bridge_id=bridge_id,
                meaning_id=meaning_id,
                l2_primitive_id=l2_primitive_id,
                source_receipt_id=source_receipt_id,
                outcome_source_table=outcome_source_table,
                outcome_bridge_key=outcome_bridge_key,
                lifecycle_id=_text(record.get("lifecycle_id")),
                continuation_id=_text(record.get("continuation_id")),
                bridge_method=method,
                bridge_source_artifact=bridge_source_artifact,
                inferred_matching_used_flag=_int_flag(record.get("inferred_matching_used_flag")),
            )
        )
    return tuple(rows)


def audit_csv_bridge_eligibility(path: str | Path) -> L3BridgeEligibilityAuditRow:
    csv_path = Path(path)
    header = read_csv_header(csv_path)
    header_set = set(header)
    bridge_columns = [column for column in BRIDGE_KEY_COLUMNS if column in header_set]
    outcome_columns = [column for column in (*OUTCOME_KEY_COLUMNS, *OUTCOME_VALUE_COLUMNS) if column in header_set]
    has_bridge = bool(bridge_columns)
    has_outcome_key = any(column in header_set for column in OUTCOME_KEY_COLUMNS)
    has_outcome_value = any(column in header_set for column in OUTCOME_VALUE_COLUMNS)
    eligible_count = 0
    if has_bridge and has_outcome_key:
        eligible_count = len(
            bridge_rows_from_records(
                read_csv_records(csv_path),
                outcome_source_table=csv_path.as_posix(),
                bridge_source_artifact=csv_path.as_posix(),
            )
        )
    allowed = bool(eligible_count and has_outcome_value)
    if allowed:
        reason = "eligible_explicit_bridge_rows_found"
    elif not has_bridge:
        reason = "missing_l3_bridge_key"
    elif not has_outcome_key:
        reason = "missing_outcome_key"
    elif not has_outcome_value:
        reason = "missing_outcome_value"
    else:
        reason = "no_row_level_explicit_bridge_values"
    return L3BridgeEligibilityAuditRow(
        candidate_path=csv_path.as_posix(),
        has_l3_bridge_key_flag=int(has_bridge),
        has_outcome_key_flag=int(has_outcome_key),
        has_outcome_value_flag=int(has_outcome_value),
        eligible_bridge_row_count=eligible_count,
        inferred_matching_required_flag=int(not allowed),
        allowed_for_calibration_flag=int(allowed),
        available_bridge_columns="|".join(bridge_columns),
        available_outcome_columns="|".join(outcome_columns),
        missing_bridge_columns="|".join(column for column in ("meaning_id", "l2_primitive_id", "source_receipt_id") if column not in header_set),
        rejection_reason=reason,
    )


def bridge_rows_to_dicts(rows: Iterable[L3OutcomeBridgeRow]) -> list[dict[str, object]]:
    return [bridge_row_to_dict(row) for row in rows]


def eligibility_rows_to_dicts(rows: Iterable[L3BridgeEligibilityAuditRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def read_csv_header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return tuple(next(reader, ()))


def read_csv_records(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _bridge_method(meaning_id: str, l2_primitive_id: str, source_receipt_id: str) -> L3OutcomeBridgeMethod:
    if meaning_id:
        return L3OutcomeBridgeMethod.DIRECT_MEANING_ID
    if l2_primitive_id:
        return L3OutcomeBridgeMethod.DIRECT_L2_PRIMITIVE_ID
    if source_receipt_id:
        return L3OutcomeBridgeMethod.DIRECT_SOURCE_RECEIPT_ID
    return L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _int_flag(value: object) -> int:
    return 1 if str(value).strip().lower() in {"1", "1.0", "true", "yes", "y"} else 0
