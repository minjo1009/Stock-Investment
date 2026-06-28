from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path


OUT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_task742_packet_bridge_gap_audit.csv")
SEARCH_ROOTS = (Path("docs/reports"), Path("data/artifacts"))
TASK742_TOKENS = ("task742", "task_742", "742")
PACKET_KEYS = ("task742_packet_id", "packet_id", "meaning_id", "source_event_id", "source_receipt_id")
OUTCOME_KEYS = ("outcome_bridge_key", "lifecycle_id", "continuation_id", "simulated_lifecycle_id")
OUTCOME_VALUES = ("win_flag", "positive_return_flag", "return_from_entry", "net_return_from_entry", "forward_return_pct")


@dataclass(frozen=True)
class Task742PacketBridgeGapAuditRow:
    candidate_path: str
    artifact_type: str
    has_task742_name_flag: int
    has_packet_key_flag: int
    has_outcome_key_flag: int
    has_outcome_value_flag: int
    allowed_for_task742_calibration_flag: int
    inferred_matching_required_flag: int
    available_packet_columns: str
    available_outcome_columns: str
    rejection_reason: str


def main() -> None:
    rows = build_audit_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT_PATH, [asdict(row) for row in rows])
    allowed = sum(row.allowed_for_task742_calibration_flag for row in rows)
    print(f"[L3_TASK742_BRIDGE_GAP] candidates={len(rows)} allowed={allowed} out={OUT_PATH}")


def build_audit_rows() -> tuple[Task742PacketBridgeGapAuditRow, ...]:
    rows: list[Task742PacketBridgeGapAuditRow] = []
    for path in _candidate_paths():
        header = _csv_header(path) if path.suffix.lower() == ".csv" else ()
        packet_columns = [column for column in PACKET_KEYS if column in header]
        outcome_columns = [column for column in (*OUTCOME_KEYS, *OUTCOME_VALUES) if column in header]
        has_packet = bool(packet_columns)
        has_outcome_key = any(column in header for column in OUTCOME_KEYS)
        has_outcome_value = any(column in header for column in OUTCOME_VALUES)
        allowed = has_packet and has_outcome_key and has_outcome_value
        rows.append(
            Task742PacketBridgeGapAuditRow(
                candidate_path=path.as_posix(),
                artifact_type=path.suffix.lower().lstrip(".") or "file",
                has_task742_name_flag=1,
                has_packet_key_flag=int(has_packet),
                has_outcome_key_flag=int(has_outcome_key),
                has_outcome_value_flag=int(has_outcome_value),
                allowed_for_task742_calibration_flag=int(allowed),
                inferred_matching_required_flag=int(not allowed),
                available_packet_columns="|".join(packet_columns),
                available_outcome_columns="|".join(outcome_columns),
                rejection_reason="eligible_task742_packet_bridge" if allowed else _rejection_reason(has_packet, has_outcome_key, has_outcome_value),
            )
        )
    if rows:
        return tuple(rows)
    return (
        Task742PacketBridgeGapAuditRow(
            candidate_path="NO_LOCAL_TASK742_PACKET_ARTIFACT_FOUND",
            artifact_type="sentinel",
            has_task742_name_flag=0,
            has_packet_key_flag=0,
            has_outcome_key_flag=0,
            has_outcome_value_flag=0,
            allowed_for_task742_calibration_flag=0,
            inferred_matching_required_flag=1,
            available_packet_columns="",
            available_outcome_columns="",
            rejection_reason="missing_task742_packet_artifact",
        ),
    )


def _candidate_paths() -> tuple[Path, ...]:
    candidates: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path == OUT_PATH:
                continue
            if OUT_PATH.parent in path.parents:
                continue
            if "__pycache__" in path.parts:
                continue
            text = path.as_posix().lower()
            if any(token in text for token in TASK742_TOKENS):
                candidates.append(path)
    return tuple(sorted(candidates))


def _csv_header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return tuple(next(reader, ()))


def _rejection_reason(has_packet: bool, has_outcome_key: bool, has_outcome_value: bool) -> str:
    missing: list[str] = []
    if not has_packet:
        missing.append("packet_key")
    if not has_outcome_key:
        missing.append("outcome_key")
    if not has_outcome_value:
        missing.append("outcome_value")
    return "missing_" + "_and_".join(missing)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else [field.name for field in Task742PacketBridgeGapAuditRow.__dataclass_fields__.values()]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
