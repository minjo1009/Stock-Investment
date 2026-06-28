from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping

from src.l2.runtime_context import ALLOWED_RUNTIME_CONTEXTS


REQUIRED_L2_PRIMITIVE_FACT_FIELDS = [
    "primitive_id",
    "primitive_batch_id",
    "source_receipt_id",
    "source_family",
    "provider",
    "symbol",
    "entity_id",
    "event_time",
    "source_ts",
    "capture_ts",
    "available_to_brain_ts",
    "asof_ts",
    "primitive_type",
    "primitive_subtype",
    "primitive_payload_json",
    "freshness_status",
    "source_time_certified",
    "closed_bar_only",
    "runtime_context",
    "input_hash",
    "output_hash",
    "lineage_edge_id",
    "missing_source_is_negative",
    "diagnostic_only",
    "trade_output_flag",
    "score_output_flag",
    "order_intent_flag",
]


@dataclass(frozen=True)
class L2PrimitiveFact:
    primitive_id: str
    primitive_batch_id: str
    source_receipt_id: str
    source_family: str
    provider: str
    symbol: str | None
    entity_id: str | None
    event_time: str
    source_ts: str
    capture_ts: str
    available_to_brain_ts: str
    asof_ts: str
    primitive_type: str
    primitive_subtype: str
    primitive_payload_json: str
    freshness_status: str
    source_time_certified: bool
    closed_bar_only: bool
    runtime_context: str
    input_hash: str
    output_hash: str
    lineage_edge_id: str
    missing_source_is_negative: bool = False
    diagnostic_only: bool = True
    trade_output_flag: int = 0
    score_output_flag: int = 0
    order_intent_flag: int = 0

    def __post_init__(self) -> None:
        if self.runtime_context not in ALLOWED_RUNTIME_CONTEXTS:
            raise ValueError(f"invalid runtime_context={self.runtime_context}")
        if self.missing_source_is_negative:
            raise ValueError("missing_source_is_negative must remain false")
        if not self.diagnostic_only:
            raise ValueError("L2 primitives are diagnostic-only in this task")
        for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(getattr(self, flag_name)) != 0:
                raise ValueError(f"{flag_name} must remain 0")
        for field_name in REQUIRED_L2_PRIMITIVE_FACT_FIELDS:
            value = getattr(self, field_name)
            if field_name in {"symbol", "entity_id"}:
                continue
            if value is None or str(value) == "":
                raise ValueError(f"{field_name} is required")

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "L2PrimitiveFact":
        values: dict[str, Any] = {}
        field_names = {field.name for field in fields(cls)}
        for name in field_names:
            value = row[name]
            if name in {"source_time_certified", "closed_bar_only", "missing_source_is_negative", "diagnostic_only"}:
                value = bool(int(value))
            values[name] = value
        return cls(**values)

    def to_db_row(self) -> dict[str, Any]:
        out = self.__dict__.copy()
        for name in ("source_time_certified", "closed_bar_only", "missing_source_is_negative", "diagnostic_only"):
            out[name] = 1 if bool(out[name]) else 0
        for name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            out[name] = int(out[name])
        return out


@dataclass(frozen=True)
class L2PrimitiveBatch:
    primitive_batch_id: str
    runtime_context: str
    builder_name: str
    builder_version: str
    asof_ts: str
    created_at: str
    source_family_set: str
    symbol_set: str
    row_count: int
    input_hash: str
    output_hash: str
    diagnostic_only: bool = True

    def __post_init__(self) -> None:
        if self.runtime_context not in ALLOWED_RUNTIME_CONTEXTS:
            raise ValueError(f"invalid runtime_context={self.runtime_context}")
        if not self.diagnostic_only:
            raise ValueError("L2 primitive batches are diagnostic-only in this task")
        if not self.primitive_batch_id:
            raise ValueError("primitive_batch_id is required")

    def to_db_row(self) -> dict[str, Any]:
        out = self.__dict__.copy()
        out["diagnostic_only"] = 1 if bool(self.diagnostic_only) else 0
        return out
