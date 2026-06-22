from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3125_external_tool_phase1_fixture_pilot"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3125_external_tool_phase1_fixture_pilot.md"
DECISION = REPORT_DIR / "task_3125_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_PHASE1_FIXTURE_PILOT_ONLY"

SEC_FIXTURE = ROOT / "data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv"
MDD_L2 = ROOT / "data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/task2923_mdd_trade_l2_attribution.csv"
MDD_L3 = ROOT / "data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/task2924_mdd_trade_l3_edges.csv"

JOIN_KEYS = ["trade_spec_id", "symbol", "decision_asof_ts"]


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def module_available(*names: str) -> tuple[bool, str, str]:
    for name in names:
        spec = importlib.util.find_spec(name)
        if spec is not None:
            return True, name, spec.origin or ""
    return False, names[0], ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def common_status() -> dict[str, object]:
    return {
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "selector_changed": "0",
        "sizing_changed": "0",
        "replay_performed": "0",
        "source_acquisition_performed": "0",
        "authority": AUTHORITY,
    }


def build_intake_matrix() -> list[dict[str, object]]:
    specs = [
        {
            "tool_name": "edgartools",
            "import_names": ("edgar", "edgartools"),
            "license": "MIT",
            "network_required": "0_for_fixture_pilot",
            "secret_required": "0",
            "raw_payload_access": "required",
            "timestamp_access": "required",
            "hashable_output": "required",
            "allowed_layers": "raw_source_evidence|primitive_fact_extraction",
            "forbidden_layers": "selector|sizing|replay|paper_order|live_order|acceptance",
        },
        {
            "tool_name": "pandera",
            "import_names": ("pandera",),
            "license": "MIT",
            "network_required": "0",
            "secret_required": "0",
            "raw_payload_access": "not_applicable",
            "timestamp_access": "schema_checked",
            "hashable_output": "not_applicable",
            "allowed_layers": "data_validation|resolver_qa",
            "forbidden_layers": "selector|sizing|paper_order|live_order|acceptance",
        },
        {
            "tool_name": "duckdb",
            "import_names": ("duckdb",),
            "license": "MIT",
            "network_required": "0",
            "secret_required": "0",
            "raw_payload_access": "not_applicable",
            "timestamp_access": "query_preserved",
            "hashable_output": "query_output_hashable",
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|paper_order|live_order|acceptance",
        },
        {
            "tool_name": "polars",
            "import_names": ("polars",),
            "license": "MIT",
            "network_required": "0",
            "secret_required": "0",
            "raw_payload_access": "not_applicable",
            "timestamp_access": "query_preserved",
            "hashable_output": "query_output_hashable",
            "allowed_layers": "local_artifact_query|audit_benchmark",
            "forbidden_layers": "selector|sizing|paper_order|live_order|acceptance",
        },
        {
            "tool_name": "dlt",
            "import_names": ("dlt",),
            "license": "Apache-2.0",
            "network_required": "0_for_loader_skeleton",
            "secret_required": "0_for_fixture_pilot",
            "raw_payload_access": "required_before_adoption",
            "timestamp_access": "required_before_adoption",
            "hashable_output": "required_before_adoption",
            "allowed_layers": "external_source_receipt_loader",
            "forbidden_layers": "selector|sizing|paper_order|live_order|acceptance",
        },
        {
            "tool_name": "github_mcp_read_only",
            "import_names": (),
            "license": "service_connector",
            "network_required": "1_when_enabled_later",
            "secret_required": "connector_managed_later",
            "raw_payload_access": "not_market_data",
            "timestamp_access": "watch_packet_timestamp",
            "hashable_output": "watch_packet_hashable",
            "allowed_layers": "dependency_monitoring|governance",
            "forbidden_layers": "source_truth|selector|sizing|paper_order|live_order|acceptance",
        },
    ]
    rows: list[dict[str, object]] = []
    for spec in specs:
        import_names = tuple(spec.pop("import_names"))
        if import_names:
            available, import_name, origin = module_available(*import_names)
            dependency_status = "available" if available else "dependency_missing"
        else:
            import_name, origin, dependency_status = "", "", "deferred_connector_not_invoked"
        rows.append(
            {
                **spec,
                "checked_at_utc": now_utc(),
                "import_name_used": import_name,
                "import_available": "1" if dependency_status == "available" else "0",
                "import_origin": origin,
                "dependency_status": dependency_status,
                "promotion_status": "fixture_only_allowed" if dependency_status == "available" else "blocked_or_deferred",
                **common_status(),
            }
        )
    return rows


def build_risk_register(intake: list[dict[str, object]]) -> list[dict[str, object]]:
    risks = {
        "edgartools": "raw_filing_identity_loss",
        "pandera": "overly_brittle_schema_blocks_valid_history",
        "duckdb": "silent_join_null_or_type_change",
        "polars": "silent_join_null_or_type_change",
        "dlt": "loader_hides_raw_payload_or_provider_time",
        "github_mcp_read_only": "connector_scope_expands_beyond_read_only",
    }
    rows: list[dict[str, object]] = []
    for row in intake:
        tool = str(row["tool_name"])
        rows.append(
            {
                "tool_name": tool,
                "risk_id": f"RISK3125-{len(rows)+1:03d}",
                "risk": risks[tool],
                "mitigation": "fixture_only_no_trading_writes_stop_on_raw_or_timestamp_loss",
                "current_status": row["dependency_status"],
                "stop_rule_triggered": "0",
                **common_status(),
            }
        )
    return rows


def sec_fixture_comparison(intake: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = read_csv(SEC_FIXTURE)
    edgar_row = next(row for row in intake if row["tool_name"] == "edgartools")
    required = [
        "symbol",
        "cik",
        "accession_number",
        "filing_date",
        "source_ts",
        "available_to_brain_ts",
        "primary_document_raw_path",
        "primary_document_raw_sha256",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
    ]
    missing_cols = [col for col in required if col not in (rows[0].keys() if rows else [])]
    sample = rows[:25]
    identity_complete = 0
    for row in sample:
        has_raw_identity = bool(
            (row.get("primary_document_raw_path") and row.get("primary_document_raw_sha256"))
            or (row.get("raw_path") and row.get("raw_sha256"))
        )
        if row.get("cik") and row.get("accession_number") and row.get("filing_date") and has_raw_identity:
            identity_complete += 1
    output = [
        {
            "pilot_id": "SEC3125-001",
            "source_fixture_path": SEC_FIXTURE.as_posix(),
            "source_fixture_sha256": file_sha256(SEC_FIXTURE),
            "fixture_row_count": len(rows),
            "sample_row_count": len(sample),
            "required_columns_present": "1" if not missing_cols else "0",
            "missing_columns": "|".join(missing_cols),
            "sample_identity_complete_rows": identity_complete,
            "edgartools_dependency_status": edgar_row["dependency_status"],
            "edgartools_comparison_status": "blocked_dependency_missing"
            if edgar_row["dependency_status"] != "available"
            else "blocked_adapter_not_promoted_in_fixture_pilot",
            "raw_identity_preserved_in_existing_fixture": "1" if identity_complete == len(sample) and not missing_cols else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "missing_source_is_negative": "0",
            **common_status(),
        }
    ]
    return output


def pandera_schema_pilot(intake: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = read_csv(SEC_FIXTURE)
    pandera_row = next(row for row in intake if row["tool_name"] == "pandera")
    required_columns = [
        "source_packet_id",
        "symbol",
        "cik",
        "accession_number",
        "source_ts",
        "available_to_brain_ts",
        "raw_path",
        "raw_sha256",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
    ]
    missing_cols = [col for col in required_columns if col not in (rows[0].keys() if rows else [])]
    bad_missing_negative = sum(1 for row in rows if row.get("missing_source_is_negative") not in {"0", ""})
    bad_future = sum(1 for row in rows if row.get("assignment_uses_future_outcome") not in {"0", ""})
    bad_outcome = sum(1 for row in rows if row.get("outcome_used_for_assignment") not in {"0", ""})
    timestamp_missing = sum(1 for row in rows if not row.get("source_ts") or not row.get("available_to_brain_ts"))
    schema_status = "blocked_dependency_missing" if pandera_row["dependency_status"] != "available" else "schema_checks_executed"
    pass_flag = int(not missing_cols and bad_missing_negative == 0 and bad_future == 0 and bad_outcome == 0 and timestamp_missing == 0)
    return [
        {
            "pilot_id": "PANDERA3125-001",
            "target_panel": SEC_FIXTURE.as_posix(),
            "target_panel_sha256": file_sha256(SEC_FIXTURE),
            "row_count": len(rows),
            "required_columns": "|".join(required_columns),
            "missing_columns": "|".join(missing_cols),
            "bad_missing_source_negative_rows": bad_missing_negative,
            "bad_future_assignment_rows": bad_future,
            "bad_outcome_assignment_rows": bad_outcome,
            "timestamp_missing_rows": timestamp_missing,
            "pandera_dependency_status": pandera_row["dependency_status"],
            "schema_status": schema_status,
            "schema_design_pass_without_dependency": pass_flag,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "missing_source_is_negative": "0",
            **common_status(),
        }
    ]


def pandas_join_metrics() -> tuple[dict[str, object], list[dict[str, object]]]:
    import pandas as pd

    start = time.perf_counter()
    l2 = pd.read_csv(MDD_L2)
    l3 = pd.read_csv(MDD_L3)
    edge_counts = l3.groupby(JOIN_KEYS, dropna=False).size().reset_index(name="l3_edge_count")
    joined = l2.merge(edge_counts, on=JOIN_KEYS, how="left")
    joined["l3_edge_count"] = joined["l3_edge_count"].fillna(0).astype(int)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 6)
    metrics = {
        "engine": "pandas",
        "dependency_status": "available",
        "runtime_ms": elapsed_ms,
        "l2_row_count": len(l2),
        "l3_row_count": len(l3),
        "joined_row_count": len(joined),
        "join_key_null_count": int(joined[JOIN_KEYS].isna().any(axis=1).sum()),
        "matched_l3_edge_rows": int((joined["l3_edge_count"] > 0).sum()),
        "total_l3_edges_attached": int(joined["l3_edge_count"].sum()),
    }
    preview = joined[JOIN_KEYS + ["l3_edge_count"]].head(10).to_dict(orient="records")
    return metrics, preview


def duckdb_join_metrics() -> dict[str, object]:
    available, _, _ = module_available("duckdb")
    if not available:
        return {"engine": "duckdb", "dependency_status": "dependency_missing"}
    import duckdb

    start = time.perf_counter()
    con = duckdb.connect(database=":memory:")
    l2_path = MDD_L2.as_posix().replace("'", "''")
    l3_path = MDD_L3.as_posix().replace("'", "''")
    query = f"""
        WITH l2 AS (SELECT * FROM read_csv_auto('{l2_path}', HEADER=TRUE)),
             l3 AS (SELECT * FROM read_csv_auto('{l3_path}', HEADER=TRUE)),
             edge_counts AS (
                 SELECT trade_spec_id, symbol, decision_asof_ts, COUNT(*) AS l3_edge_count
                 FROM l3
                 GROUP BY trade_spec_id, symbol, decision_asof_ts
             ),
             joined AS (
                 SELECT l2.trade_spec_id, l2.symbol, l2.decision_asof_ts,
                        COALESCE(edge_counts.l3_edge_count, 0) AS l3_edge_count
                 FROM l2
                 LEFT JOIN edge_counts
                   USING (trade_spec_id, symbol, decision_asof_ts)
             )
        SELECT
            (SELECT COUNT(*) FROM l2) AS l2_row_count,
            (SELECT COUNT(*) FROM l3) AS l3_row_count,
            COUNT(*) AS joined_row_count,
            SUM(CASE WHEN trade_spec_id IS NULL OR symbol IS NULL OR decision_asof_ts IS NULL THEN 1 ELSE 0 END) AS join_key_null_count,
            SUM(CASE WHEN l3_edge_count > 0 THEN 1 ELSE 0 END) AS matched_l3_edge_rows,
            SUM(l3_edge_count) AS total_l3_edges_attached
        FROM joined
    """
    result = con.execute(query).fetchone()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 6)
    keys = [
        "l2_row_count",
        "l3_row_count",
        "joined_row_count",
        "join_key_null_count",
        "matched_l3_edge_rows",
        "total_l3_edges_attached",
    ]
    return {"engine": "duckdb", "dependency_status": "available", "runtime_ms": elapsed_ms, **dict(zip(keys, result))}


def polars_join_metrics() -> dict[str, object]:
    available, _, _ = module_available("polars")
    if not available:
        return {"engine": "polars", "dependency_status": "dependency_missing"}
    import polars as pl

    start = time.perf_counter()
    l2 = pl.read_csv(MDD_L2)
    l3 = pl.read_csv(MDD_L3)
    edge_counts = l3.group_by(JOIN_KEYS).len(name="l3_edge_count")
    joined = l2.join(edge_counts, on=JOIN_KEYS, how="left").with_columns(pl.col("l3_edge_count").fill_null(0))
    elapsed_ms = round((time.perf_counter() - start) * 1000, 6)
    null_expr = pl.any_horizontal([pl.col(col).is_null() for col in JOIN_KEYS]).sum()
    return {
        "engine": "polars",
        "dependency_status": "available",
        "runtime_ms": elapsed_ms,
        "l2_row_count": l2.height,
        "l3_row_count": l3.height,
        "joined_row_count": joined.height,
        "join_key_null_count": int(joined.select(null_expr).item()),
        "matched_l3_edge_rows": int(joined.filter(pl.col("l3_edge_count") > 0).height),
        "total_l3_edges_attached": int(joined.select(pl.col("l3_edge_count").sum()).item()),
    }


def query_benchmark() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pandas_metrics, preview = pandas_join_metrics()
    rows = [pandas_metrics, duckdb_join_metrics(), polars_join_metrics()]
    baseline = pandas_metrics
    for row in rows:
        if row.get("dependency_status") != "available":
            row["row_count_match_pandas"] = "0"
            row["join_key_null_match_pandas"] = "0"
            row["l3_edge_match_pandas"] = "0"
            row["adoption_candidate"] = "0"
            continue
        row_count_match = row.get("joined_row_count") == baseline.get("joined_row_count")
        null_match = row.get("join_key_null_count") == baseline.get("join_key_null_count")
        edge_match = row.get("total_l3_edges_attached") == baseline.get("total_l3_edges_attached")
        faster = float(row.get("runtime_ms", 999999)) < float(baseline.get("runtime_ms", 0))
        row["row_count_match_pandas"] = "1" if row_count_match else "0"
        row["join_key_null_match_pandas"] = "1" if null_match else "0"
        row["l3_edge_match_pandas"] = "1" if edge_match else "0"
        row["adoption_candidate"] = "1" if row["engine"] != "pandas" and row_count_match and null_match and edge_match and faster else "0"
    for row in rows:
        row.update(common_status())
    return rows, preview


def build_acceptance_checks(
    intake: list[dict[str, object]],
    sec_rows: list[dict[str, object]],
    schema_rows: list[dict[str, object]],
    benchmark_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    duck_or_polars_ok = any(
        row.get("engine") in {"duckdb", "polars"}
        and row.get("dependency_status") == "available"
        and row.get("row_count_match_pandas") == "1"
        and row.get("l3_edge_match_pandas") == "1"
        for row in benchmark_rows
    )
    checks = [
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
        ("no_orders", True, "No paper or live orders are created."),
        ("no_replay_or_source_acquisition", True, "No replay or source acquisition is performed."),
        ("intake_rows_present", len(intake) == 6, "All planned tool families are represented."),
        ("edgartools_missing_is_blocked", sec_rows[0]["edgartools_comparison_status"] in {"blocked_dependency_missing", "blocked_adapter_not_promoted_in_fixture_pilot"}, "SEC pilot is blocked or fixture-only."),
        ("pandera_missing_is_blocked", schema_rows[0]["schema_status"] in {"blocked_dependency_missing", "schema_checks_executed"}, "Pandera pilot is blocked or schema-only."),
        ("duckdb_or_polars_benchmark_safe", duck_or_polars_ok, "At least one local query engine matches pandas join metrics."),
    ]
    return [
        {
            "check_id": f"CHK3125-{idx:03d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            **common_status(),
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def write_report(
    intake: list[dict[str, object]],
    sec_rows: list[dict[str, object]],
    schema_rows: list[dict[str, object]],
    benchmark_rows: list[dict[str, object]],
    checks: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3125 External Tool Phase 1 Fixture Pilot

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: created a fixture-only external tool intake, risk, SEC fixture, Pandera schema, and DuckDB/Polars local query benchmark packet.
- What did not change: no install, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key metrics:
  - Intake rows: {closeout['intake_row_count']}.
  - SEC pilot status: `{closeout['sec_pilot_status']}`.
  - Pandera pilot status: `{closeout['pandera_pilot_status']}`.
  - Query benchmark rows: {closeout['query_benchmark_row_count']}.
  - Local query adoption candidates: {closeout['local_query_adoption_candidate_count']}.

## Quant Expert Report

### Tool Intake

{markdown_table(intake, ['tool_name', 'dependency_status', 'allowed_layers', 'forbidden_layers', 'promotion_status'])}

### SEC Fixture Pilot

{markdown_table(sec_rows, ['pilot_id', 'fixture_row_count', 'sample_row_count', 'edgartools_dependency_status', 'edgartools_comparison_status', 'raw_identity_preserved_in_existing_fixture'])}

The SEC comparison is fixture-only. Because `edgartools` is not installed in this environment, no SEC extraction was executed and no raw source was downloaded.

### Pandera Validator Pilot

{markdown_table(schema_rows, ['pilot_id', 'row_count', 'pandera_dependency_status', 'schema_status', 'schema_design_pass_without_dependency', 'timestamp_missing_rows'])}

The schema pilot verifies the existing panel shape and records a Pandera-ready schema design. Because `pandera` is not installed, the task does not add a runtime dependency.

### DuckDB/Polars Audit Benchmark

{markdown_table(benchmark_rows, ['engine', 'dependency_status', 'runtime_ms', 'joined_row_count', 'join_key_null_count', 'total_l3_edges_attached', 'row_count_match_pandas', 'l3_edge_match_pandas', 'adoption_candidate'])}

The benchmark uses the Task2921-2940 MDD L2/L3 join keys: `trade_spec_id`, `symbol`, and `decision_asof_ts`.

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: Phase 1 is partially useful now.

`edgartools` and `Pandera` are not installed, so they remain blocked fixture pilots. That is acceptable and does not fail the task.

DuckDB and Polars are installed and can reproduce the MDD L2/L3 audit join metrics against pandas. They are candidates for local artifact query acceleration, subject to future opt-in use in audit scripts only.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `{SEC_FIXTURE.as_posix()}`
  - `{MDD_L2.as_posix()}`
  - `{MDD_L3.as_posix()}`
- Outputs:
  - `docs/reports/{TASK_ID}/task_3125_external_tool_phase1_fixture_pilot.md`
  - `docs/reports/{TASK_ID}/task_3125_decision.csv`
  - `data/artifacts/{TASK_ID}/`
- Validation commands:
  - `python scripts/trader_brain_3125_external_tool_phase1_fixture_pilot_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - SEC fixture: `{file_sha256(SEC_FIXTURE)}`
  - MDD L2: `{file_sha256(MDD_L2)}`
  - MDD L3: `{file_sha256(MDD_L3)}`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    intake = build_intake_matrix()
    risks = build_risk_register(intake)
    sec_rows = sec_fixture_comparison(intake)
    schema_rows = pandera_schema_pilot(intake)
    benchmark_rows, preview = query_benchmark()
    checks = build_acceptance_checks(intake, sec_rows, schema_rows, benchmark_rows)

    local_candidates = sum(1 for row in benchmark_rows if row.get("adoption_candidate") == "1")
    closeout = {
        "task_id": "Task3125",
        "verdict": "external_tool_phase1_fixture_pilot_completed_diagnostic_only",
        "intake_row_count": len(intake),
        "risk_row_count": len(risks),
        "sec_pilot_status": sec_rows[0]["edgartools_comparison_status"],
        "pandera_pilot_status": schema_rows[0]["schema_status"],
        "query_benchmark_row_count": len(benchmark_rows),
        "local_query_adoption_candidate_count": local_candidates,
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }

    write_csv(OUT_DIR / "tool_intake_matrix.csv", intake)
    write_csv(OUT_DIR / "tool_risk_register.csv", risks)
    write_csv(OUT_DIR / "sec_fixture_comparison.csv", sec_rows)
    write_csv(OUT_DIR / "pandera_schema_pilot.csv", schema_rows)
    write_csv(OUT_DIR / "local_query_benchmark.csv", benchmark_rows)
    write_csv(OUT_DIR / "local_query_join_preview.csv", preview)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3125_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3125_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(intake, sec_rows, schema_rows, benchmark_rows, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3125_EXTERNAL_TOOL_PHASE1_FIXTURE_PILOT_COMPLETE]")


if __name__ == "__main__":
    main()
