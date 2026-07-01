from __future__ import annotations

import json
from pathlib import Path


CRITICAL_BACKFILL_LANES = (
    "public_newswire_backfill",
    "public_market_macro_news_backfill",
)


def load_coverage_gaps(path: str | Path) -> list[dict[str, object]]:
    status = json.loads(Path(path).read_text(encoding="utf-8"))
    gaps: list[dict[str, object]] = []
    for lane in CRITICAL_BACKFILL_LANES:
        row = status.get(lane, {})
        progress = _float(row.get("progress_pct"))
        running = str(row.get("status", "")).upper() == "RUNNING"
        complete = progress >= 99.999
        if not complete:
            gaps.append(
                {
                    "gap_id": f"coverage_gap:{lane}",
                    "lane": lane,
                    "source_family": str(row.get("provider") or lane),
                    "progress_pct": progress,
                    "status": row.get("status", "UNKNOWN"),
                    "running": int(running),
                    "severity": "NONCRITICAL_GAP_RUNNING" if running else "CRITICAL_BLOCKER_NOT_RUNNING",
                    "gap_type": "INCOMPLETE_BACKFILL",
                    "negative_evidence_allowed": 0,
                    "diagnostic_only": 1,
                    "reason_codes": "L0_BACKFILL_INCOMPLETE;MISSING_IS_UNKNOWN_NOT_NEGATIVE",
                }
            )
    return gaps


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

