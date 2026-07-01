from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4199"
OUT = ROOT / "data/artifacts/task_4199_l0_scheduler_deletion_and_l0_l5_integration_audit/layer_watermarks"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False, "sha256": None, "mtime_utc": None}
    return {
        "path": rel(path),
        "exists": True,
        "sha256": sha256_file(path),
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
    }


def count_csv(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def count_jsonl(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig") as fh:
        return sum(1 for line in fh if line.strip())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_state_hash(values: dict[str, Any]) -> str:
    payload = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build() -> dict[str, Any]:
    generated_at = now_iso()
    l0_status_path = ROOT / "data/artifacts/l0_operating_status/current_l0_status.json"
    l0 = read_json(l0_status_path)
    pn = l0.get("public_newswire") or {}
    by_source = pn.get("by_source") or {}
    l0_partial = bool((pn.get("pending_units") or 0) or (pn.get("partial_units") or 0) or l0.get("blockers"))
    l0_watermark_values = {
        "overall_verdict": l0.get("overall_verdict"),
        "progress_pct": pn.get("progress_pct"),
        "completed_units": pn.get("completed_units"),
        "pending_units": pn.get("pending_units"),
        "partial_units": pn.get("partial_units"),
        "failed_units": pn.get("failed_units"),
        "total_units": pn.get("total_units"),
        "by_source": by_source,
    }
    l0_watermark = {
        "schema_version": "layer_watermark.v1",
        "task_id": TASK_ID,
        "layer": "L0",
        "produced_at": generated_at,
        "status": "PARTIAL_RUNNING" if l0_partial else "COMPLETE",
        "source_family": "public_newswire_backfill",
        "watermark_hash": source_state_hash(l0_watermark_values),
        "source_state": l0_watermark_values,
        "artifact": file_meta(l0_status_path),
        "authority": {
            "diagnostic_only": True,
            "complete_source_coverage_claim": not l0_partial,
            "negative_evidence_allowed": 0,
            "trading_authority": 0,
        },
    }

    layer_specs = [
        {
            "layer": "L1",
            "artifact": ROOT / "data/artifacts/task_4186_l1_completion_gpt_review_and_audit/task_4186_l1_completion_audit_summary.json",
            "counts": lambda: read_json(ROOT / "data/artifacts/task_4186_l1_completion_gpt_review_and_audit/task_4186_l1_completion_audit_summary.json"),
            "upstream": ["L0"],
        },
        {
            "layer": "L2",
            "artifact": ROOT / "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l0_l2_hardening_summary.json",
            "counts": lambda: read_json(ROOT / "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l0_l2_hardening_summary.json"),
            "upstream": ["L1", "L0"],
        },
        {
            "layer": "L3",
            "artifact": ROOT / "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graph_v2_manifest.json",
            "counts": lambda: read_json(ROOT / "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graph_v2_manifest.json").get("output_counts") or {},
            "upstream": ["L2", "L1", "L0"],
        },
        {
            "layer": "L4",
            "artifact": ROOT / "data/diagnostics/l4/l4_run_manifest.json",
            "counts": lambda: {
                "l4_thesis_bundles": count_jsonl(ROOT / "data/diagnostics/l4/l4_thesis_bundles.jsonl"),
                "l4_thesis_evidence_links": count_csv(ROOT / "data/diagnostics/l4/l4_thesis_evidence_links.csv"),
                "l4_thesis_blockers": count_csv(ROOT / "data/diagnostics/l4/l4_thesis_blockers.csv"),
            },
            "upstream": ["L3", "L2", "L1", "L0"],
        },
    ]

    watermarks = [l0_watermark]
    for spec in layer_specs:
        meta = file_meta(spec["artifact"])
        exists = bool(meta["exists"])
        status = "BLOCKED_BY_L0_INCOMPLETE" if l0_partial else "REFRESHED_TO_LATEST_L0_WATERMARK"
        if not exists:
            status = "STALE_VS_L0_WATERMARK"
        counts = spec["counts"]()
        watermarks.append({
            "schema_version": "layer_watermark.v1",
            "task_id": TASK_ID,
            "layer": spec["layer"],
            "produced_at": generated_at,
            "status": status,
            "consumed_upstream_layers": spec["upstream"],
            "consumed_l0_watermark_hash": l0_watermark["watermark_hash"],
            "upstream_l0_status": l0_watermark["status"],
            "artifact": meta,
            "counts": counts,
            "authority": {
                "diagnostic_only": True,
                "complete_source_coverage_claim": False if l0_partial else True,
                "negative_evidence_allowed": 0,
                "trading_authority": 0,
            },
        })

    chain = {
        "schema_version": "layer_refresh_chain.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "verdict": "REFRESH_CHAIN_EXISTS_WITH_L0_PARTIAL_BLOCKER" if l0_partial else "REFRESH_CHAIN_EXISTS_L0_COMPLETE",
        "l0_watermark_hash": l0_watermark["watermark_hash"],
        "layers": watermarks,
        "safety": {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "broker_mutation": 0,
            "live_order": 0,
            "paper_promotion": 0,
            "missing_or_stale_data": "UNKNOWN/BLOCKER",
        },
    }

    for row in watermarks:
        write_json(OUT / f"{row['layer'].lower()}_refresh_watermark.json", row)
    write_json(OUT / "layer_refresh_chain.json", chain)
    write_markdown(chain)
    return chain


def write_markdown(chain: dict[str, Any]) -> None:
    lines = [
        "# TASK-4199 Layer Refresh Chain",
        "",
        f"- Verdict: {chain['verdict']}",
        f"- Generated at: {chain['generated_at']}",
        f"- L0 watermark: `{chain['l0_watermark_hash']}`",
        "",
        "| layer | status | artifact | complete coverage claim | trading authority |",
        "|---|---|---|---:|---:|",
    ]
    for row in chain["layers"]:
        lines.append(
            f"| {row['layer']} | {row['status']} | {row['artifact']['path']} | "
            f"{int(bool(row['authority']['complete_source_coverage_claim']))} | {row['authority']['trading_authority']} |"
        )
    lines.extend([
        "",
        "Missing, stale, or incomplete data remains UNKNOWN/BLOCKER and is never negative evidence.",
        "This chain is a freshness/lineage proof, not strategy acceptance or deployment readiness.",
    ])
    (OUT / "layer_refresh_chain.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    chain = build()
    print(json.dumps({
        "task_id": TASK_ID,
        "verdict": chain["verdict"],
        "output": str(OUT / "layer_refresh_chain.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
