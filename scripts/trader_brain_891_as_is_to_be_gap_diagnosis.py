from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_891_as_is_to_be_gap_diagnosis"
TASK880_SUMMARY = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay/controlled_replay_summary.csv"
TASK881_SUMMARY = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_brain_backtest_prep_summary.json"
TASK881_GATE = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/replay_harness_data_gate_status.csv"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"

KEYWORDS = (
    "source",
    "evidence",
    "filing",
    "news",
    "transcript",
    "macro",
    "candidate",
    "bundle",
    "graph",
    "relation",
    "primitive",
    "meaning",
    "event",
    "packet",
)

TIMESTAMP_COLUMNS = {"published_ts", "published_at", "received_ts", "available_to_brain_ts", "event_timestamp", "created_at", "asof_ts", "decision_asof_ts", "bundle_asof_ts", "edge_asof_ts", "timestamp", "session_date"}
SOURCE_COLUMNS = {"source_hash", "source_url", "source_url_or_file", "source_file", "source_family", "source_id", "evidence_id", "source_event_id", "source_text", "source_linked_event_count_sum"}
LINEAGE_COLUMNS = {"candidate_bundle_id", "graph_snapshot_id", "source_graph_id", "edge_id", "node_id", "relation_type", "primitive_fact_state", "economic_meaning_state"}
FORBIDDEN_HINT_COLUMNS = {"future_return", "realized_return", "pnl", "net_pnl", "label_return", "position_size", "rank", "score"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_header_and_sample(path: Path, sample_limit: int = 200) -> tuple[list[str], int, str]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            sample_count = 0
            for sample_count, _row in enumerate(reader, start=1):
                if sample_count >= sample_limit:
                    break
            return headers, sample_count, ""
    except Exception as exc:  # noqa: BLE001
        return [], 0, f"{type(exc).__name__}: {exc}"


def candidate_csv_paths() -> list[Path]:
    paths: list[Path] = []
    for root in [ROOT / "docs", ROOT / "data"]:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            rel = path.relative_to(ROOT).as_posix().lower()
            if any(keyword in rel for keyword in KEYWORDS):
                paths.append(path)
    return sorted(paths)


def classify_source_candidate(headers: list[str], rel: str) -> tuple[str, str]:
    header_set = {h.strip() for h in headers}
    if "task_881_890_historical_brain_backtest_prep/historical_source_time_panel_status.csv" in rel:
        return "source_time_status_gap_report", "prep status report, not raw historical evidence"
    has_symbol = "symbol" in header_set
    has_timestamp = bool(header_set & TIMESTAMP_COLUMNS)
    has_source = bool(header_set & SOURCE_COLUMNS)
    has_lineage = bool(header_set & LINEAGE_COLUMNS)
    has_required_source_time = {"published_ts", "received_ts", "available_to_brain_ts"}.issubset(header_set)
    forbidden = sorted(header_set & FORBIDDEN_HINT_COLUMNS)
    if has_required_source_time and has_source:
        return "source_time_candidate", "has required source-time columns"
    if "source_event_dataset" in rel and has_symbol and has_timestamp:
        return "derived_event_context_candidate", "has symbol and event timestamp but not full source-time proof"
    if has_lineage and has_source:
        return "lineage_support_candidate", "has source or evidence lineage but incomplete source-time fields"
    if has_source or "evidence" in rel or "source" in rel:
        return "source_inventory_candidate", "source-related but incomplete source-time fields"
    if forbidden:
        return "evaluation_or_outcome_artifact", f"contains outcome-like columns: {';'.join(forbidden[:5])}"
    return "supporting_context_candidate", "keyword match only"


def build_source_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in candidate_csv_paths():
        rel = path.relative_to(ROOT).as_posix()
        headers, sample_rows, error = read_header_and_sample(path)
        classification, reason = classify_source_candidate(headers, rel.lower())
        header_set = set(headers)
        rows.append(
            {
                "relative_path": rel,
                "artifact_size_bytes": path.stat().st_size,
                "sample_rows_checked": sample_rows,
                "column_count": len(headers),
                "has_symbol": int("symbol" in header_set),
                "has_theme": int("theme" in header_set),
                "has_published_ts": int("published_ts" in header_set or "published_at" in header_set),
                "has_received_ts": int("received_ts" in header_set),
                "has_available_to_brain_ts": int("available_to_brain_ts" in header_set),
                "has_source_hash": int("source_hash" in header_set or "source_file_sha256" in header_set),
                "has_source_id": int(bool(header_set & {"source_id", "evidence_id", "source_event_id"})),
                "has_lineage_id": int(bool(header_set & LINEAGE_COLUMNS)),
                "has_forbidden_outcome_hint": int(bool(header_set & FORBIDDEN_HINT_COLUMNS)),
                "classification": classification,
                "classification_reason": reason,
                "source_time_bridge_state": "bridge_ready" if classification == "source_time_candidate" else "needs_normalization_or_rejected",
                "read_error": error,
                "sha256": sha256_file(path) if not error and path.stat().st_size < 50_000_000 else "",
            }
        )
    return rows


def summarize_inventory(inventory: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: dict[str, int] = {}
    for row in inventory:
        key = str(row["classification"])
        summary[key] = summary.get(key, 0) + 1
    return [{"classification": key, "file_count": count} for key, count in sorted(summary.items())]


def build_gap_matrix(inventory: list[dict[str, object]]) -> list[dict[str, object]]:
    task881 = json.loads(TASK881_SUMMARY.read_text(encoding="utf-8"))
    gate_rows = read_csv_rows(TASK881_GATE)
    gate_status = {row["gate"]: row["status"] for row in gate_rows}
    bridge_ready_count = sum(1 for row in inventory if row["source_time_bridge_state"] == "bridge_ready")
    derived_context_count = sum(1 for row in inventory if row["classification"] == "derived_event_context_candidate")
    return [
        {
            "area": "universe",
            "as_is": "70-symbol fixed research universe exists",
            "to_be": "PIT tradable universe or explicit diagnostic-only authority",
            "status": "partial",
            "gap": "current universe is fixed_research_universe_diagnostic_only, not PIT top500",
            "next_action": "keep diagnostic-only wording or attach as-of membership evidence",
        },
        {
            "area": "market_data",
            "as_is": f"daily={gate_status.get('daily_market_data')} intraday={gate_status.get('intraday_15m_market_data')} corporate_actions={gate_status.get('corporate_actions')}",
            "to_be": "certified replay data for all 70 symbols plus QQQ through 2026-03-31",
            "status": "ready_for_diagnostic_replay_data_gate",
            "gap": "market data is not the active blocker",
            "next_action": "preserve manifests and do not redownload blindly",
        },
        {
            "area": "historical_source_time_panel",
            "as_is": f"bridge_ready_files={bridge_ready_count}; derived_context_files={derived_context_count}",
            "to_be": "row-level published_ts received_ts available_to_brain_ts source_hash for evidence used by the brain",
            "status": "not_ready",
            "gap": "repo has source/evidence-like artifacts but not enough compliant source-time rows",
            "next_action": "normalize eligible repo-native source artifacts into Task883 schema; collect missing filings/news/transcripts separately",
        },
        {
            "area": "brain_state",
            "as_is": f"{task881['brain_state_rows']} preview rows blocked_before_candidate_generation",
            "to_be": "L1/L2/L3 states populated from compliant source-time evidence",
            "status": "blocked",
            "gap": "source-time panel missing",
            "next_action": "do not infer meanings from price or future outcomes",
        },
        {
            "area": "relationship_graph",
            "as_is": f"{task881['graph_snapshot_rows']} preview rows blocked_missing_source_time_panel",
            "to_be": "rolling graph snapshots with node_asof and edge_asof <= decision_asof",
            "status": "blocked",
            "gap": "no historical edges from compliant evidence",
            "next_action": "build graph only after Task883/884 pass",
        },
        {
            "area": "candidate_decision_trade_spec",
            "as_is": "candidate bundles blocked; trader decisions skip; trade specs blocked",
            "to_be": "candidate bundle -> trader decision -> trade spec generated only from as-of graph state",
            "status": "blocked",
            "gap": "no replayable brain decisions yet",
            "next_action": "keep first real replay no_go until source-time and brain states pass",
        },
        {
            "area": "leakage_guard",
            "as_is": f"negative fixtures rejected={task881['negative_fixture_rejected_count']}/{task881['negative_fixture_count']}",
            "to_be": "row-level temporal and no-inference checks for every production artifact",
            "status": "implemented_initial_guard",
            "gap": "guard exists for prep artifacts but not full production source panel yet",
            "next_action": "extend the same checks to normalized Task883 rows",
        },
    ]


def build_to_be_requirements() -> list[dict[str, object]]:
    return [
        {"priority": 1, "requirement": "Task883 compliant source-time panel", "done_when": "every used evidence row has source id, source family, published_ts, received_ts, available_to_brain_ts, source_hash, and source_gap_flag"},
        {"priority": 2, "requirement": "repo-native source bridge", "done_when": "eligible existing artifacts are normalized or explicitly rejected with reason"},
        {"priority": 3, "requirement": "external historical source acquisition plan", "done_when": "missing filings, news, transcripts, and macro sources have provider, raw path, hash, and coverage target"},
        {"priority": 4, "requirement": "L1-L3 brain-state builder", "done_when": "source-time rows produce primitive facts, economic meanings, and relation states without future data"},
        {"priority": 5, "requirement": "rolling graph/candidate/decision trace", "done_when": "each trade spec links to decision, bundle, graph, brain state, and evidence ids"},
        {"priority": 6, "requirement": "replay go/no-go upgrade", "done_when": "Task890 changes from no_go only after source-time, leakage, split/OOS, cost/slippage, and artifact audit pass"},
    ]


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_source_inventory()
    inventory_summary = summarize_inventory(inventory)
    gap_matrix = build_gap_matrix(inventory)
    to_be = build_to_be_requirements()
    write_csv(
        out_dir / "repo_source_evidence_inventory.csv",
        inventory,
        [
            "relative_path",
            "artifact_size_bytes",
            "sample_rows_checked",
            "column_count",
            "has_symbol",
            "has_theme",
            "has_published_ts",
            "has_received_ts",
            "has_available_to_brain_ts",
            "has_source_hash",
            "has_source_id",
            "has_lineage_id",
            "has_forbidden_outcome_hint",
            "classification",
            "classification_reason",
            "source_time_bridge_state",
            "read_error",
            "sha256",
        ],
    )
    write_csv(out_dir / "repo_source_evidence_inventory_summary.csv", inventory_summary, ["classification", "file_count"])
    write_csv(out_dir / "as_is_to_be_gap_matrix.csv", gap_matrix, ["area", "as_is", "to_be", "status", "gap", "next_action"])
    write_csv(out_dir / "to_be_requirement_backlog.csv", to_be, ["priority", "requirement", "done_when"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task891",
        "inventory_file_count": len(inventory),
        "bridge_ready_file_count": sum(1 for row in inventory if row["source_time_bridge_state"] == "bridge_ready"),
        "derived_context_file_count": sum(1 for row in inventory if row["classification"] == "derived_event_context_candidate"),
        "active_blocker": "historical_source_time_panel_not_ready",
        "first_real_historical_brain_replay": "no_go",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_891_gap_diagnosis_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_891_GAP_DIAGNOSIS_OK] "
        f"inventory_files={summary['inventory_file_count']} bridge_ready={summary['bridge_ready_file_count']} "
        f"blocker={summary['active_blocker']} replay={summary['first_real_historical_brain_replay']}"
    )


if __name__ == "__main__":
    main()
