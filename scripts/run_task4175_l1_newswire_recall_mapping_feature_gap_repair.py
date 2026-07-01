from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4175"
INPUT = Path("data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l3_gap_triage.csv")
OUT_DIR = Path("data/artifacts/task_4175_l1_newswire_recall_mapping_feature_gap_repair")


ALLOWED_DECISIONS = {
    "ACCEPT_MAPPED",
    "NEEDS_ALIAS",
    "AMBIGUOUS_BLOCKER",
    "NON_ISSUER",
    "INSUFFICIENT_CONTEXT",
    "FEATURE_BACKFILL_REQUIRED",
}


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def decision_for(row: dict[str, str]) -> tuple[str, str]:
    subreason = row.get("gap_subreason", "")
    l1_mapping = row.get("l1_mapping_status", "")
    l2_status = row.get("l2_admission_status", "")
    recall = as_int(row.get("l1_newswire_recall_review_rows")) + as_int(row.get("l2_newswire_recall_review_count"))
    entity_review = as_int(row.get("l1_entity_candidate_review_rows")) + as_int(row.get("l2_entity_candidate_review_count"))
    blocked_unmapped = as_int(row.get("l1_blocked_unmapped_rows"))
    mapped = as_int(row.get("l1_mapped_rows"))

    if subreason == "NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING":
        return "FEATURE_BACKFILL_REQUIRED", "L1/L2 mapping exists but article/entity feature materialization is missing"
    if recall and entity_review:
        return "AMBIGUOUS_BLOCKER", "Recall and entity review both remain; do not force ticker/entity mapping"
    if recall:
        return "NEEDS_ALIAS", "Recall candidate needs deterministic alias/source parser extension"
    if blocked_unmapped and mapped == 0:
        return "INSUFFICIENT_CONTEXT", "Blocked unmapped rows have no mapped row evidence in the packet"
    if blocked_unmapped:
        return "NEEDS_ALIAS", "Unmapped rows exist beside mapped rows; add deterministic alias/parser only when evidence is explicit"
    if l1_mapping == "NEWSWIRE_MAPPED_BY_L0_COLLECTOR" and "REVIEW_READY" in l2_status:
        return "FEATURE_BACKFILL_REQUIRED", "Mapped review-ready packet needs feature builder/backfill"
    return "NON_ISSUER", "No deterministic issuer/ticker feature action from this aggregate row"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(INPUT)
    decisions: list[dict[str, Any]] = []
    freq: dict[tuple[str, str, str, str], dict[str, Any]] = defaultdict(lambda: {"row_count": 0, "l1_blocked_unmapped_rows": 0, "recall_review_rows": 0, "feature_gap_rows": 0})
    for row in rows:
        decision, reason = decision_for(row)
        key = (row.get("gap_subreason", ""), row.get("source", ""), row.get("entity", ""), row.get("event_month", ""))
        freq[key]["row_count"] += 1
        freq[key]["l1_blocked_unmapped_rows"] += as_int(row.get("l1_blocked_unmapped_rows"))
        freq[key]["recall_review_rows"] += as_int(row.get("l1_newswire_recall_review_rows")) + as_int(row.get("l2_newswire_recall_review_count"))
        freq[key]["feature_gap_rows"] += 1 if row.get("gap_subreason") == "NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING" else 0
        decisions.append(
            {
                "task_id": TASK_ID,
                "l3_gap_id": row.get("l3_gap_id", ""),
                "gap_subreason": row.get("gap_subreason", ""),
                "source": row.get("source", ""),
                "entity": row.get("entity", ""),
                "ticker": row.get("ticker", ""),
                "event_month": row.get("event_month", ""),
                "l1_reference": row.get("l1_reference", ""),
                "l2_reference": row.get("l2_reference", ""),
                "decision_state": decision,
                "decision_reason": reason,
                "mapping_authority": "DETERMINISTIC_ONLY_NO_LLM_NO_FORCED_TICKER",
                "negative_evidence_allowed": 0,
                "diagnostic_only": 1,
            }
        )

    freq_rows = [
        {
            "task_id": TASK_ID,
            "gap_subreason": key[0],
            "source": key[1],
            "entity": key[2],
            "event_month": key[3],
            **value,
        }
        for key, value in sorted(freq.items(), key=lambda item: (-item[1]["row_count"], item[0]))
    ]
    write_csv(
        OUT_DIR / "task_4175_l1_mapping_decision_ledger.csv",
        decisions,
        [
            "task_id",
            "l3_gap_id",
            "gap_subreason",
            "source",
            "entity",
            "ticker",
            "event_month",
            "l1_reference",
            "l2_reference",
            "decision_state",
            "decision_reason",
            "mapping_authority",
            "negative_evidence_allowed",
            "diagnostic_only",
        ],
    )
    write_csv(
        OUT_DIR / "task_4175_l1_candidate_frequency.csv",
        freq_rows,
        ["task_id", "gap_subreason", "source", "entity", "event_month", "row_count", "l1_blocked_unmapped_rows", "recall_review_rows", "feature_gap_rows"],
    )
    counts = Counter(row["decision_state"] for row in decisions)
    summary = {
        "task_id": TASK_ID,
        "generated_at": now_z(),
        "input_path": str(INPUT),
        "decision_rows": len(decisions),
        "pending_before": len(decisions),
        "pending_after": sum(1 for row in decisions if row["decision_state"] not in ALLOWED_DECISIONS),
        "reclassified_count": len(decisions),
        "decision_state_counts": dict(counts),
        "negative_evidence_allowed": 0,
        "diagnostic_only": 1,
    }
    write_json(OUT_DIR / "task_4175_l1_mapping_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
