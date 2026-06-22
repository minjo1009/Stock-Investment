#!/usr/bin/env python
"""Validate the read-only L6/L7 runtime catalog adapter.

This validator calls build_paper_ops_runtime_catalog(root) for an in-memory
payload only. It does not call write_paper_ops_runtime_catalog, run replay,
submit orders, or mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.build_trader_terminal_catalog import build_paper_ops_runtime_catalog
from brain.runtime_catalog import (
    PAPER_OPS_RUNTIME_CONTRACT_VERSION,
    build_frontend_read_model_from_paper_ops_catalog,
)


ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3164_runtime_catalog_adapter_validation"


def main() -> int:
    payload = build_paper_ops_runtime_catalog(ROOT)
    if not isinstance(payload, dict):
        print("[TASK3164_ERROR] catalog payload is not a dict")
        return 1

    read_model = build_frontend_read_model_from_paper_ops_catalog(
        payload,
        read_model_id="task3164-paper-ops-read-model",
        runtime_decision_id="task3164-runtime-catalog-validation",
        provenance_path="frontend/trader-terminal/public/catalog/paper_ops_runtime_catalog.json",
    )

    rules = payload.get("rules", {}) if isinstance(payload.get("rules"), dict) else {}
    data_quality = payload.get("data_quality", {}) if isinstance(payload.get("data_quality"), dict) else {}
    shadow_rows = payload.get("shadow_decision_journal", [])
    shadow_rows_shape_ok = isinstance(shadow_rows, list) and all(isinstance(row, dict) for row in shadow_rows)
    shadow_rows_count = len(shadow_rows) if isinstance(shadow_rows, list) else -1

    checks = [
        {
            "check_name": "catalog_contract_version",
            "pass": int(payload.get("contract_version") == PAPER_OPS_RUNTIME_CONTRACT_VERSION),
            "detail": str(payload.get("contract_version")),
        },
        {
            "check_name": "ui_reads_catalog_only",
            "pass": int(rules.get("ui_reads_catalog_only") is True),
            "detail": str(rules.get("ui_reads_catalog_only")),
        },
        {
            "check_name": "deployment_claim_blocked",
            "pass": int(rules.get("deployment_claim_allowed") is False),
            "detail": str(rules.get("deployment_claim_allowed")),
        },
        {
            "check_name": "missing_source_approximation_blocked",
            "pass": int(rules.get("missing_source_approximation_allowed") is False),
            "detail": str(rules.get("missing_source_approximation_allowed")),
        },
        {
            "check_name": "read_model_read_only",
            "pass": int(read_model.read_only is True),
            "detail": str(read_model.read_only),
        },
        {
            "check_name": "read_model_has_provenance",
            "pass": int(bool(read_model.provenance_paths)),
            "detail": "|".join(read_model.provenance_paths),
        },
        {
            "check_name": "data_quality_status_mapped",
            "pass": int(read_model.display_status == str(data_quality.get("data_quality_status") or "UNKNOWN")),
            "detail": read_model.display_status,
        },
        {
            "check_name": "shadow_journal_shape_reviewable",
            "pass": int(shadow_rows_shape_ok),
            "detail": f"type={type(shadow_rows).__name__};rows={shadow_rows_count}",
        },
    ]

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with (ARTIFACT_DIR / "runtime_catalog_adapter_validation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_name", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3164_ERROR] {row['check_name']}: {row['detail']}")
        return 1

    print(
        "[TASK3164_OK] "
        f"checks={len(checks)} "
        f"shadow_journal_rows={shadow_rows_count} "
        f"read_model_status={read_model.display_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
