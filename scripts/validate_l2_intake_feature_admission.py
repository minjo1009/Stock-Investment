from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4136"
SLUG = "task_4136_l2_intake_feature_admission"
DATA_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("L2 INTAKE FEATURE ADMISSION VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    (DATA_DIR / "validator_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    markdown = f"# TASK-4136 Validation Results\n\nResult: `{result}`\n\n"
    for label, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        markdown += f"## {label}\n\n"
        markdown += "\n".join(f"- {item}" for item in items) if items else "- none"
        markdown += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(markdown, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    run = subprocess.run(
        [sys.executable, "scripts/run_l2_intake_feature_admission.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
    )
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    if run.returncode != 0:
        failures.append(f"runner failed: {run.stderr[-500:]}")
        return emit(passes, warnings, failures)

    required = [
        ROOT / "configs" / "l2_intake_feature_admission_contract.yaml",
        ROOT / "src" / "l2" / "builders" / "news_event_primitives.py",
        ROOT / "src" / "l2" / "intake" / "contracts.py",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l2_intake_feature_admission_summary.json",
        DATA_DIR / "l2_intake_manifest.csv",
        DATA_DIR / "l2_feature_admission_gate.csv",
        DATA_DIR / "ticker_news_mapping_gate.csv",
        DATA_DIR / "legacy_l2_news_quarantine.csv",
        DATA_DIR / "l1_continuous_validation_plan.csv",
        DATA_DIR / "l1_continuous_validation_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    if failures:
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    intake_rows = read_csv(DATA_DIR / "l2_intake_manifest.csv")
    feature_rows = read_csv(DATA_DIR / "l2_feature_admission_gate.csv")
    mapping_rows = read_csv(DATA_DIR / "ticker_news_mapping_gate.csv")
    legacy_rows = read_csv(DATA_DIR / "legacy_l2_news_quarantine.csv")
    l1_ledger_rows = read_csv(DATA_DIR / "l1_continuous_validation_ledger.csv")
    contract = (ROOT / "configs" / "l2_intake_feature_admission_contract.yaml").read_text(encoding="utf-8")
    legacy_builder = (ROOT / "src" / "l2" / "builders" / "news_event_primitives.py").read_text(encoding="utf-8")

    if len(intake_rows) != 5:
        failures.append("L2 intake manifest must contain the five current L1 source families")
    else:
        passes.append("l2_intake_manifest_has_five_families")
    if any(row.get("feature_materialization_allowed_now") != "0" for row in intake_rows):
        failures.append("TASK-4136 must not materialize trading features yet")
    else:
        passes.append("feature_materialization_stays_closed")
    public_feature_rows = [row for row in feature_rows if row.get("source_family", "").startswith("public_")]
    if len(public_feature_rows) != 3 or any(row.get("can_be_trading_feature_later") != "1" for row in public_feature_rows):
        failures.append("news/macro families must have an explicit future trading-feature path")
    else:
        passes.append("news_macro_have_future_feature_path")
    if any(row.get("admitted_as_trading_feature_now") != "0" for row in feature_rows):
        failures.append("feature rows cannot be admitted before mapping/effect validation")
    else:
        passes.append("feature_admission_not_premature")
    if not any(row.get("source_family") == "public_newswire_feeds" and "HIGH_CONFIDENCE" in row.get("mapping_gate", "") for row in mapping_rows):
        failures.append("public_newswire_feeds must require high-confidence ticker/news mapping")
    else:
        passes.append("ticker_news_mapping_gate_hardened")
    if "LEGACY_L2_NEWS_BUILDER_QUARANTINED" not in legacy_builder or "raise RuntimeError" not in legacy_builder:
        failures.append("legacy L2 news builder is not quarantined")
    elif not legacy_rows or any(row.get("direct_l0_to_l2_allowed") != "0" for row in legacy_rows):
        failures.append("legacy L2 news quarantine ledger is unsafe")
    else:
        passes.append("legacy_l2_news_code_separated")
    if "legacy_l2_news_builder_allowed: false" not in contract:
        failures.append("L2 contract does not forbid legacy news builder")
    else:
        passes.append("contract_forbids_legacy_l2_news_builder")
    if not l1_ledger_rows or any(row.get("result") != "PASS" for row in l1_ledger_rows):
        failures.append("continuous L1 validation smoke did not pass")
    else:
        passes.append(f"l1_continuous_validation_smoke_passed: {len(l1_ledger_rows)}")
    if "trading_authority_opened" in (REPORT_DIR / "l2_intake_feature_admission_summary.json").read_text(encoding="utf-8"):
        passes.append("summary_records_trading_authority_boundary")
    else:
        failures.append("summary missing trading authority boundary")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
