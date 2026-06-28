from __future__ import annotations

import csv
import sys
from pathlib import Path


ARTIFACT_DIR = Path("data/artifacts/task_l3_canonical_economic_meaning_rebuild")
REPORT_DIR = Path("docs/reports/task_l3_canonical_economic_meaning_rebuild")

MEANINGS_PATH = ARTIFACT_DIR / "l3_canonical_economic_meanings.csv"
EDGES_PATH = ARTIFACT_DIR / "l3_canonical_evidence_edges.csv"
GRAPHS_PATH = ARTIFACT_DIR / "l3_canonical_relation_graphs.csv"
CALIBRATION_OUTCOMES_PATH = ARTIFACT_DIR / "l3_canonical_calibration_outcomes.csv"
CALIBRATION_AUDIT_PATH = ARTIFACT_DIR / "l3_canonical_calibration_audit.csv"
UNRECOVERABLE_DECISION_PATH = REPORT_DIR / "task742_unrecoverable_artifact_decision.csv"
DECISION_PATH = REPORT_DIR / "l3_canonical_rebuild_decision.csv"


def validate() -> list[str]:
    errors: list[str] = []
    for path in (
        MEANINGS_PATH,
        EDGES_PATH,
        GRAPHS_PATH,
        CALIBRATION_OUTCOMES_PATH,
        CALIBRATION_AUDIT_PATH,
        UNRECOVERABLE_DECISION_PATH,
        DECISION_PATH,
    ):
        if not path.exists():
            errors.append(f"missing artifact: {path}")
    if errors:
        return errors

    meanings = _read_csv(MEANINGS_PATH)
    edges = _read_csv(EDGES_PATH)
    graphs = _read_csv(GRAPHS_PATH)
    outcomes = _read_csv(CALIBRATION_OUTCOMES_PATH)
    audit = _read_csv(CALIBRATION_AUDIT_PATH)
    decision = _decision_map(DECISION_PATH)
    unrecoverable = _decision_map(UNRECOVERABLE_DECISION_PATH)

    if not meanings:
        errors.append("canonical rebuild has no meanings")
    if len(meanings) != len(edges):
        errors.append("meaning and evidence edge counts must match")
    if not graphs:
        errors.append("canonical rebuild has no relation graphs")
    if not outcomes:
        errors.append("canonical rebuild has no calibration outcome rows")
    if not audit:
        errors.append("canonical rebuild has no calibration audit buckets")

    for row in meanings:
        candidate = row.get("meaning_id", "")
        if row.get("provider") != "canonical_source_event_rebuild":
            errors.append(f"unexpected meaning provider: {candidate}")
        if row.get("direction") != "NEUTRAL":
            errors.append(f"canonical source-event meanings must remain context-only NEUTRAL: {candidate}")
        if "NOT_TASK742_GOLDEN_REPLAY" not in row.get("reason_codes", ""):
            errors.append(f"meaning lacks NOT_TASK742_GOLDEN_REPLAY: {candidate}")
        _check_no_trade_flags(row, candidate, errors)

    for row in edges:
        candidate = row.get("evidence_edge_id", "")
        if row.get("direction") != "NEUTRAL":
            errors.append(f"canonical evidence edges must remain NEUTRAL: {candidate}")
        if row.get("edge_state") != "CONTEXT":
            errors.append(f"canonical evidence edges must remain CONTEXT: {candidate}")
        if "NOT_TASK742_GOLDEN_REPLAY" not in row.get("reason_codes", ""):
            errors.append(f"edge lacks NOT_TASK742_GOLDEN_REPLAY: {candidate}")

    for row in graphs:
        candidate = row.get("relation_graph_id", "")
        if row.get("graph_state") not in {"CONTEXT_ONLY", "MIXED_REVIEW", "INSUFFICIENT_EVIDENCE"}:
            errors.append(f"unexpected canonical graph state: {candidate} -> {row.get('graph_state')}")

    for row in outcomes:
        candidate = row.get("calibration_row_id", "")
        if _int(row.get("inferred_matching_used_flag")) != 0:
            errors.append(f"inferred matching used in canonical calibration row: {candidate}")
        if _int(row.get("label_used_in_assignment_flag")) != 0:
            errors.append(f"label used in assignment in canonical calibration row: {candidate}")
        if _int(row.get("outcome_used_in_assignment_flag")) != 0:
            errors.append(f"outcome used in assignment in canonical calibration row: {candidate}")
        if row.get("direction") != "NEUTRAL":
            errors.append(f"canonical calibration row must remain NEUTRAL: {candidate}")
        _check_no_trade_flags(row, candidate, errors)

    if decision.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy_acceptance must remain NOT_ACCEPTED")
    if decision.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment_readiness must remain DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    if decision.get("real_capital") != "FORBIDDEN":
        errors.append("real_capital must remain FORBIDDEN")
    if decision.get("buy_sell_signals") != "NOT_CREATED":
        errors.append("BUY/SELL signals must remain NOT_CREATED")
    if unrecoverable.get("task742_historical_packet_artifact") != "UNRECOVERABLE_ARTIFACT":
        errors.append("Task742 historical packet artifact must be marked UNRECOVERABLE_ARTIFACT")
    return errors


def _check_no_trade_flags(row: dict[str, str], candidate: str, errors: list[str]) -> None:
    for flag in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
        if _int(row.get(flag)) != 0:
            errors.append(f"{flag} must remain 0: {candidate}")


def _decision_map(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    return {row.get("field", ""): row.get("value", "") for row in rows}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_CANONICAL_REBUILD_ERROR] {error}")
        sys.exit(1)
    meanings = _read_csv(MEANINGS_PATH)
    graphs = _read_csv(GRAPHS_PATH)
    outcomes = _read_csv(CALIBRATION_OUTCOMES_PATH)
    print(
        "[L3_CANONICAL_REBUILD_OK] "
        f"meanings={len(meanings)} graphs={len(graphs)} calibration_rows={len(outcomes)}"
    )


if __name__ == "__main__":
    main()
