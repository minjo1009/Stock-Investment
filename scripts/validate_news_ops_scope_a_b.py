from __future__ import annotations

import json

from news_ops_to_backtest_common import (
    ARTIFACT_DIR,
    DB,
    PERMISSION_COLUMNS,
    REQUIRED_SOURCE_FAMILIES,
    connect_readonly,
    ensure_dirs,
    fail_if_errors,
    safety_payload,
    write_csv,
    write_json,
)

from tools.db.apply_management_schema import CADENCE_SPECS
from tools.db.news_l0_l1 import PROVIDER_SPECS
from tools.db.run_registered_loop_once import ADAPTER_SOURCE_FAMILIES
from tools.db.run_source_acquisition_once import FAMILY_TO_JOB


ROOT_CONFIG = "configs/db_source_acquisition_scheduler.json"


EXPECTED_CONFIG_JOBS = {
    "intraday_market_sources_5m": {"interval_minutes": 5, "enabled": True, "allow_network": True},
    "heavy_sources_60m": {"interval_minutes": 60, "enabled": True, "allow_network": True},
    "official_news_sources_15m": {"interval_minutes": 30, "enabled": False, "allow_network": False},
    "gdelt_news_discovery_15m": {"interval_minutes": 15, "enabled": False, "allow_network": False},
    "marketaux_news_free_30m": {"interval_minutes": 60, "enabled": False, "allow_network": False},
    "registered_db_loop_5m": {"interval_minutes": 5, "enabled": True, "allow_network": False},
}


def _load_config() -> dict:
    from news_ops_to_backtest_common import ROOT

    path = ROOT / ROOT_CONFIG
    if not path.exists():
        raise AssertionError(f"missing scheduler config: {ROOT_CONFIG}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ensure_dirs()
    errors: list[str] = []
    config = _load_config()
    jobs = {str(job.get("name")): job for job in config.get("jobs", [])}
    config_rows: list[dict[str, object]] = []

    for name, expected in EXPECTED_CONFIG_JOBS.items():
        job = jobs.get(name)
        if not job:
            errors.append(f"missing_config_job:{name}")
            continue
        row = {"job_name": name, **expected}
        for key, value in expected.items():
            if job.get(key) != value:
                errors.append(f"config_drift:{name}:{key}:{job.get(key)}!={value}")
        row["families"] = ",".join(job.get("families", []))
        config_rows.append(row)

    config_families = {family for job in jobs.values() for family in job.get("families", [])}
    for family in REQUIRED_SOURCE_FAMILIES:
        if family not in config_families:
            errors.append(f"family_missing_from_scheduler_config:{family}")

    cadence_by_family = {spec["source_family"]: spec for spec in CADENCE_SPECS}
    static_rows: list[dict[str, object]] = []
    for family in REQUIRED_SOURCE_FAMILIES:
        spec = cadence_by_family.get(family)
        static_rows.append(
            {
                "source_family": family,
                "cadence_spec": int(bool(spec)),
                "family_to_job": int(family in FAMILY_TO_JOB),
                "registered_adapter": int(family in ADAPTER_SOURCE_FAMILIES),
                "provider_spec": int(family in PROVIDER_SPECS or family not in {"official_public_releases", "gdelt_news_events", "marketaux_news_free"}),
            }
        )
        if not spec:
            errors.append(f"family_missing_from_cadence_specs:{family}")
        if family not in FAMILY_TO_JOB:
            errors.append(f"family_missing_from_source_runner_map:{family}")
        if family not in ADAPTER_SOURCE_FAMILIES:
            errors.append(f"family_missing_from_registered_loop_adapter_map:{family}")

    con = connect_readonly()
    db_rows: list[dict[str, object]] = []
    try:
        for family in REQUIRED_SOURCE_FAMILIES:
            row = con.execute(
                """
                SELECT job_name, source_family, enabled, cadence_seconds, max_lag_seconds,
                       diagnostic_only, execution_permitted, broker_mutation_permitted,
                       paper_promotion_permitted, real_capital_permitted
                FROM scheduler_job_registry
                WHERE source_family=?
                """,
                (family,),
            ).fetchone()
            policy = con.execute(
                """
                SELECT source_family, target_cadence_seconds, max_lag_seconds,
                       missing_semantics, stale_semantics
                FROM source_freshness_policy
                WHERE source_family=?
                """,
                (family,),
            ).fetchone()
            spec = cadence_by_family.get(family)
            if row is None:
                errors.append(f"db_scheduler_registry_missing:{family}")
                continue
            db_record = dict(row)
            db_record["policy_present"] = int(policy is not None)
            db_rows.append(db_record)
            if policy is None:
                errors.append(f"db_freshness_policy_missing:{family}")
            if int(row["diagnostic_only"]) != 1:
                errors.append(f"db_job_not_diagnostic_only:{family}")
            for column in PERMISSION_COLUMNS:
                if int(row[column]) != 0:
                    errors.append(f"db_permission_not_zero:{family}:{column}")
            if spec:
                for key in ("cadence_seconds", "max_lag_seconds"):
                    if int(row[key]) != int(spec[key]):
                        errors.append(f"db_cadence_drift:{family}:{key}:{row[key]}!={spec[key]}")
                if policy is not None and int(policy["target_cadence_seconds"]) != int(spec["cadence_seconds"]):
                    errors.append(f"db_policy_cadence_drift:{family}")
                if policy is not None and policy["missing_semantics"] != "UNKNOWN_BLOCKER":
                    errors.append(f"db_policy_missing_semantics_drift:{family}")
                if policy is not None and policy["stale_semantics"] != "UNKNOWN_BLOCKER":
                    errors.append(f"db_policy_stale_semantics_drift:{family}")
    finally:
        con.close()

    write_csv(ARTIFACT_DIR / "scope_a_b_config_jobs.csv", config_rows)
    write_csv(ARTIFACT_DIR / "scope_a_b_static_registration.csv", static_rows)
    write_csv(ARTIFACT_DIR / "scope_a_b_db_registry.csv", db_rows)
    result = {
        "database": str(DB),
        "required_families": list(REQUIRED_SOURCE_FAMILIES),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
        **safety_payload(),
    }
    write_json(ARTIFACT_DIR / "scope_a_b_scheduler_reconciliation.json", result)
    fail_if_errors(errors)
    print("[TASK3883_SCOPE_A_B_OK] scheduler_registry_reconciliation=PASS cadence_policy=PASS permissions_closed=1")


if __name__ == "__main__":
    main()
