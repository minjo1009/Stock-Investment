from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import StrEnum


class L3OutcomeBridgeMethod(StrEnum):
    DIRECT_MEANING_ID = "DIRECT_MEANING_ID"
    DIRECT_L2_PRIMITIVE_ID = "DIRECT_L2_PRIMITIVE_ID"
    DIRECT_SOURCE_RECEIPT_ID = "DIRECT_SOURCE_RECEIPT_ID"
    MANIFEST_BACKED_EXACT_KEY = "MANIFEST_BACKED_EXACT_KEY"


@dataclass(frozen=True)
class L3OutcomeBridgeRow:
    bridge_id: str
    meaning_id: str
    l2_primitive_id: str
    source_receipt_id: str
    outcome_source_table: str
    outcome_bridge_key: str
    lifecycle_id: str
    continuation_id: str
    bridge_method: L3OutcomeBridgeMethod
    bridge_source_artifact: str
    inferred_matching_used_flag: int
    diagnostic_only: bool = True
    trade_output_flag: int = 0
    score_output_flag: int = 0
    order_intent_flag: int = 0

    def __post_init__(self) -> None:
        for name in ("bridge_id", "outcome_source_table", "outcome_bridge_key", "bridge_source_artifact"):
            if not str(getattr(self, name, "")).strip():
                raise ValueError(f"{name} is required")
        if not any((self.meaning_id, self.l2_primitive_id, self.source_receipt_id)):
            raise ValueError("bridge row requires meaning_id, l2_primitive_id, or source_receipt_id")
        if int(self.inferred_matching_used_flag) != 0:
            raise ValueError("outcome bridges must not use inferred matching")
        if not self.diagnostic_only:
            raise ValueError("outcome bridges are diagnostic-only")
        for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(getattr(self, flag_name)) != 0:
                raise ValueError(f"{flag_name} must remain 0")


def bridge_row_to_dict(row: L3OutcomeBridgeRow) -> dict[str, object]:
    values = asdict(row)
    values["bridge_method"] = row.bridge_method.value
    return values
