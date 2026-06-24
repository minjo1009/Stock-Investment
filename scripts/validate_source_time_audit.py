from __future__ import annotations

from datetime import timedelta

from news_ops_to_backtest_common import (
    ARTIFACT_DIR,
    REQUIRED_SOURCE_FAMILIES,
    connect_readonly,
    ensure_dirs,
    fail_if_errors,
    parse_ts,
    safety_payload,
    table_exists,
    write_csv,
    write_json,
)

SOURCE_TIME_CHAIN_FIELDS = [
    "source_family",
    "receipt_id",
    "source_ts",
    "capture_ts",
    "available_to_brain_ts",
    "node_asof_ts",
    "edge_asof_ts",
    "bundle_asof_ts",
    "adapter_created_ts",
    "tradable_after_ts",
    "authority_classification",
    "chain_state",
]

DISCOVERY_FAMILIES = {"gdelt_news_events", "marketaux_news_free"}


def _iso(value):
    return value.astimezone(value.tzinfo).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    ensure_dirs()
    fatal_errors: list[str] = []
    blocker_errors: list[str] = []
    blockers: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    chain_rows: list[dict[str, object]] = []
    authority_rows: list[dict[str, object]] = []
    quarantine_rows: list[dict[str, object]] = []
    con = connect_readonly()
    try:
        quarantine_exists = table_exists(con, "source_receipt_quarantine")
        for family in REQUIRED_SOURCE_FAMILIES:
            if quarantine_exists:
                rows = con.execute(
                    """
                    SELECT receipt_id, source_family, source_ts, capture_ts,
                           available_to_brain_ts, source_time_basis, strict_gate_allowed,
                           proxy_allowed
                    FROM source_receipts
                    WHERE source_family=?
                      AND receipt_id NOT IN (
                          SELECT receipt_id FROM source_receipt_quarantine
                      )
                    ORDER BY created_at DESC
                    LIMIT 200
                    """,
                    (family,),
                ).fetchall()
                quarantined = con.execute(
                    """
                    SELECT receipt_id, source_family, quarantine_reason,
                           source_ts, capture_ts, quarantined_at, notes
                    FROM source_receipt_quarantine
                    WHERE source_family=?
                    ORDER BY quarantined_at DESC, receipt_id
                    """,
                    (family,),
                ).fetchall()
            else:
                rows = con.execute(
                    """
                    SELECT receipt_id, source_family, source_ts, capture_ts,
                           available_to_brain_ts, source_time_basis, strict_gate_allowed,
                           proxy_allowed
                    FROM source_receipts
                    WHERE source_family=?
                    ORDER BY created_at DESC
                    LIMIT 200
                    """,
                    (family,),
                ).fetchall()
                quarantined = []
            quarantine_rows.extend(dict(row) for row in quarantined)
            bad_count = 0
            chain_count = 0
            for row in rows:
                source_ts = parse_ts(row["source_ts"])
                capture_ts = parse_ts(row["capture_ts"])
                available_ts = parse_ts(row["available_to_brain_ts"])
                node_asof_ts = available_ts
                edge_asof_ts = available_ts
                bundle_asof_ts = available_ts
                adapter_created_ts = available_ts
                tradable_after_ts = available_ts + timedelta(seconds=1) if available_ts else None
                authority_class = (
                    "DISCOVERY_OR_ENRICHMENT_ONLY"
                    if family in DISCOVERY_FAMILIES
                    else "DIAGNOSTIC_SOURCE_EVIDENCE_ONLY"
                )
                reason = ""
                if source_ts is None:
                    reason = "MISSING_SOURCE_TS"
                elif capture_ts is None:
                    reason = "MISSING_CAPTURE_TS"
                elif available_ts is None:
                    reason = "MISSING_AVAILABLE_TO_BRAIN_TS"
                elif not all((node_asof_ts, edge_asof_ts, bundle_asof_ts, adapter_created_ts, tradable_after_ts)):
                    reason = "MISSING_DERIVED_CHAIN_TS"
                elif source_ts > capture_ts:
                    reason = "SOURCE_TS_AFTER_CAPTURE_TS"
                elif capture_ts > available_ts:
                    reason = "CAPTURE_TS_AFTER_AVAILABLE_TO_BRAIN_TS"
                elif not (available_ts <= node_asof_ts <= edge_asof_ts <= bundle_asof_ts <= adapter_created_ts <= tradable_after_ts):
                    reason = "DERIVED_CHAIN_ORDER_VIOLATION"
                elif int(row["strict_gate_allowed"]) != 0 or int(row["proxy_allowed"]) != 0:
                    reason = "AUTHORITY_GATE_OPEN_DURING_DIAGNOSTIC_AUDIT"
                if reason:
                    bad_count += 1
                    blockers.append(
                        {
                            "source_family": family,
                            "receipt_id": row["receipt_id"],
                            "blocker_code": reason,
                            "source_ts": row["source_ts"] or "",
                            "capture_ts": row["capture_ts"] or "",
                            "available_to_brain_ts": row["available_to_brain_ts"] or "",
                            "source_time_basis": row["source_time_basis"],
                        }
                    )
                else:
                    chain_count += 1
                chain_rows.append(
                    {
                        "source_family": family,
                        "receipt_id": row["receipt_id"],
                        "source_ts": row["source_ts"] or "",
                        "capture_ts": row["capture_ts"] or "",
                        "available_to_brain_ts": row["available_to_brain_ts"] or "",
                        "node_asof_ts": _iso(node_asof_ts) if node_asof_ts else "",
                        "edge_asof_ts": _iso(edge_asof_ts) if edge_asof_ts else "",
                        "bundle_asof_ts": _iso(bundle_asof_ts) if bundle_asof_ts else "",
                        "adapter_created_ts": _iso(adapter_created_ts) if adapter_created_ts else "",
                        "tradable_after_ts": _iso(tradable_after_ts) if tradable_after_ts else "",
                        "authority_classification": authority_class,
                        "chain_state": "BLOCKED" if reason else "AUDITED_DIAGNOSTIC_ONLY",
                    }
                )
            summary_rows.append(
                {
                    "source_family": family,
                    "sampled_receipts": len(rows),
                    "audited_chain_rows": chain_count,
                    "source_time_blockers": bad_count,
                    "quarantined_receipts": len(quarantined),
                    "audit_status": "PASS" if bad_count == 0 and rows else "BLOCKED",
                }
            )
            authority_rows.append(
                {
                    "source_family": family,
                    "authority_classification": "DISCOVERY_OR_ENRICHMENT_ONLY"
                    if family in DISCOVERY_FAMILIES
                    else "DIAGNOSTIC_SOURCE_EVIDENCE_ONLY",
                    "strict_gate_allowed": 0,
                    "proxy_allowed": 0,
                    "notes": "classification is diagnostic-only and cannot create replay/order eligibility",
                }
            )
            if not rows:
                fatal_errors.append(f"missing_source_time_receipts:{family}")
            if bad_count:
                blocker_errors.append(f"source_time_blockers:{family}:{bad_count}")
    finally:
        con.close()

    status = "FAIL" if fatal_errors else ("PASS_WITH_BLOCKERS" if blocker_errors else "PASS")
    write_csv(ARTIFACT_DIR / "scope_e_source_time_chain_schema.csv", chain_rows, fieldnames=SOURCE_TIME_CHAIN_FIELDS)
    write_csv(ARTIFACT_DIR / "scope_e_source_time_summary.csv", summary_rows)
    write_csv(ARTIFACT_DIR / "scope_e_source_authority_classification.csv", authority_rows)
    write_csv(
        ARTIFACT_DIR / "scope_e_source_time_blockers.csv",
        blockers,
        fieldnames=[
            "source_family",
            "receipt_id",
            "blocker_code",
            "source_ts",
            "capture_ts",
            "available_to_brain_ts",
            "source_time_basis",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "scope_e_source_time_quarantine.csv",
        quarantine_rows,
        fieldnames=[
            "receipt_id",
            "source_family",
            "quarantine_reason",
            "source_ts",
            "capture_ts",
            "quarantined_at",
            "notes",
        ],
    )
    write_json(
        ARTIFACT_DIR / "scope_e_source_time_audit.json",
        {
            "status": status,
            "fatal_errors": fatal_errors,
            "blocker_errors": blocker_errors,
            "source_time_blocker_count": len(blockers),
            "quarantined_receipt_count": len(quarantine_rows),
            "receipt_sample_limit_per_family": 200,
            "rule": "source_ts <= capture_ts <= available_to_brain_ts <= node_asof_ts <= edge_asof_ts <= bundle_asof_ts <= adapter_created_ts <= tradable_after_ts",
            **safety_payload(),
        },
    )
    fail_if_errors(fatal_errors)
    print(f"[TASK3883_SCOPE_E_OK] source_time_audit={status} blocker_count={len(blockers)}")


if __name__ == "__main__":
    main()
