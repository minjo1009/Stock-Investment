from __future__ import annotations

from news_ops_to_backtest_common import (
    ARTIFACT_DIR,
    NEWS_SOURCE_FAMILIES,
    REQUIRED_SOURCE_FAMILIES,
    connect_readonly,
    count_rows,
    ensure_dirs,
    fail_if_errors,
    safety_payload,
    table_exists,
    write_csv,
    write_json,
)


def main() -> None:
    ensure_dirs()
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    con = connect_readonly()
    try:
        required_tables = (
            "source_freshness",
            "source_receipts",
            "reference_hashes",
            "data_lineage_edges",
            "scheduler_run_ledger",
            "news_event_l0",
            "news_event_l1_evidence",
        )
        for table in required_tables:
            if not table_exists(con, table):
                errors.append(f"missing_table:{table}")
        if errors:
            raise AssertionError("; ".join(errors))

        for family in REQUIRED_SOURCE_FAMILIES:
            freshness = con.execute(
                """
                SELECT source_family, provider, freshness_status, strict_gate_allowed,
                       proxy_allowed, evidence_ref, max_source_ts, max_capture_ts,
                       max_available_to_brain_ts
                FROM source_freshness
                WHERE source_family=?
                """,
                (family,),
            ).fetchone()
            receipt_count = count_rows(con, "SELECT COUNT(*) FROM source_receipts WHERE source_family=?", (family,))
            ref_count = count_rows(con, "SELECT COUNT(*) FROM reference_hashes WHERE source_family=?", (family,))
            edge_count = count_rows(con, "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family=?", (family,))
            ledger_count = count_rows(
                con,
                "SELECT COUNT(*) FROM scheduler_run_ledger WHERE cadence=(SELECT job_name FROM scheduler_job_registry WHERE source_family=? LIMIT 1)",
                (family,),
            )
            target_tables = [
                row["target_table"]
                for row in con.execute(
                    "SELECT DISTINCT target_table FROM data_lineage_edges WHERE source_family=? ORDER BY target_table",
                    (family,),
                ).fetchall()
            ]
            row = {
                "source_family": family,
                "freshness_present": int(freshness is not None),
                "freshness_status": freshness["freshness_status"] if freshness else "",
                "receipt_count": receipt_count,
                "reference_hash_count": ref_count,
                "lineage_edge_count": edge_count,
                "scheduler_ledger_count": ledger_count,
                "target_tables": ",".join(target_tables),
                "strict_gate_allowed": int(freshness["strict_gate_allowed"]) if freshness else -1,
                "proxy_allowed": int(freshness["proxy_allowed"]) if freshness else -1,
                "evidence_ref": freshness["evidence_ref"] if freshness else "",
            }
            rows.append(row)
            if freshness is None:
                errors.append(f"missing_source_freshness:{family}")
                continue
            if int(freshness["strict_gate_allowed"]) != 0 or int(freshness["proxy_allowed"]) != 0:
                errors.append(f"authority_gate_open_without_scope:{family}")
            if not freshness["evidence_ref"]:
                errors.append(f"missing_evidence_ref:{family}")
            if receipt_count <= 0:
                errors.append(f"missing_receipts:{family}")
            if ref_count <= 0:
                errors.append(f"missing_reference_hashes:{family}")
            if edge_count <= 0:
                errors.append(f"missing_lineage_edges:{family}")
            if ledger_count <= 0:
                errors.append(f"missing_scheduler_ledger:{family}")
            if family in NEWS_SOURCE_FAMILIES:
                l0 = count_rows(con, "SELECT COUNT(*) FROM news_event_l0 WHERE source_family=?", (family,))
                l1 = count_rows(con, "SELECT COUNT(*) FROM news_event_l1_evidence WHERE source_family=?", (family,))
                row["news_event_l0_count"] = l0
                row["news_event_l1_count"] = l1
                if l0 <= 0:
                    errors.append(f"missing_news_event_l0_rows:{family}")
                if l1 <= 0:
                    errors.append(f"missing_news_event_l1_rows:{family}")

        bad_receipts = [
            dict(row)
            for row in con.execute(
                """
                SELECT source_family, receipt_id, source_ts, capture_ts,
                       available_to_brain_ts, raw_path, raw_sha256, source_time_basis
                FROM source_receipts
                WHERE receipt_id IN (
                    SELECT evidence_ref
                    FROM source_freshness
                    WHERE source_family IN ({})
                )
                  AND (capture_ts IS NULL OR capture_ts=''
                       OR available_to_brain_ts IS NULL OR available_to_brain_ts=''
                       OR raw_path IS NULL OR raw_path=''
                       OR raw_sha256 IS NULL OR raw_sha256=''
                       OR source_time_basis IS NULL OR source_time_basis='')
                ORDER BY source_family, receipt_id
                """.format(",".join("?" for _ in REQUIRED_SOURCE_FAMILIES)),
                REQUIRED_SOURCE_FAMILIES,
            ).fetchall()
        ]
        if bad_receipts:
            errors.append(f"bad_receipt_metadata_rows:{len(bad_receipts)}")
    finally:
        con.close()

    write_csv(ARTIFACT_DIR / "scope_c_l0_l1_storage_matrix.csv", rows)
    write_csv(ARTIFACT_DIR / "scope_c_bad_receipt_metadata.csv", bad_receipts)
    write_json(
        ARTIFACT_DIR / "scope_c_l0_l1_storage_validation.json",
        {"status": "PASS" if not errors else "FAIL", "errors": errors, **safety_payload()},
    )
    fail_if_errors(errors)
    print("[TASK3883_SCOPE_C_OK] l0_l1_storage_evidence=PASS receipts=PASS hashes=PASS lineage=PASS gates_closed=1")


if __name__ == "__main__":
    main()
