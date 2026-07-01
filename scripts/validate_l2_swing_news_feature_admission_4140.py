from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4140"
SLUG = "task_4140_swing_news_macro_newswire_feature_admission"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4140 SWING NEWS FEATURE ADMISSION VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "validator_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    md = "# TASK-4140 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l2_swing_news_feature_admission_4140 import build

    build()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        ARTIFACT_DIR / "swing_feature_admission_policy.csv",
        ARTIFACT_DIR / "swing_time_activation_policy.csv",
        ARTIFACT_DIR / "swing_effect_window_policy.csv",
        ARTIFACT_DIR / "swing_mapping_scope_policy.csv",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "swing_news_feature_admission_summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    family_rows = read_csv(ARTIFACT_DIR / "swing_feature_admission_policy.csv")
    expected_families = {"public_context_news_feeds", "public_market_macro_news_feeds", "public_newswire_feeds"}
    families = {row["source_family"] for row in family_rows}
    if families != expected_families:
        failures.append(f"unexpected source families: {sorted(families)}")
    else:
        passes.append("news_macro_newswire_families_present")
    for row in family_rows:
        if row["swing_feature_candidate_now"] != "1":
            failures.append(f"swing feature candidate not enabled: {row['source_family']}")
        if row["blocked_by_intraday_timestamp"] != "0":
            failures.append(f"source family still blocked by intraday timestamp: {row['source_family']}")
        if row["minute_second_timestamp_required"] != "0":
            failures.append(f"minute/second timestamp still required: {row['source_family']}")
        if row["daily_publication_date_can_be_sufficient"] != "1":
            failures.append(f"daily publication date not allowed: {row['source_family']}")
        if row["feature_materialization_allowed_now"] != "0":
            failures.append(f"feature materialization gate unexpectedly open: {row['source_family']}")
    if not failures:
        passes.append("swing_feature_candidates_enabled_without_intraday_timestamp_block")

    effect_rows = read_csv(ARTIFACT_DIR / "swing_effect_window_policy.csv")
    windows = {row["effect_window"] for row in effect_rows}
    if not {"1D", "5D", "20D", "60D"}.issubset(windows):
        failures.append(f"effect windows missing: {sorted({'1D', '5D', '20D', '60D'} - windows)}")
    else:
        passes.append("effect_windows_include_1d_5d_20d_60d")
    if not any(row["effect_window"] == "20D" and row["is_primary"] == "1" for row in effect_rows):
        failures.append("20D must be the primary swing effect window")
    else:
        passes.append("primary_effect_window_20d")

    mapping_rows = read_csv(ARTIFACT_DIR / "swing_mapping_scope_policy.csv")
    allowed_scopes = {row["mapping_scope"] for row in mapping_rows if row["swing_feature_allowed"] == "1"}
    if not {"TICKER", "ENTITY", "SECTOR", "MACRO"}.issubset(allowed_scopes):
        failures.append("ticker/entity/sector/macro scopes must be allowed for swing candidates")
    else:
        passes.append("ticker_entity_sector_macro_mapping_scopes_allowed")
    unknown = [row for row in mapping_rows if row["mapping_scope"] == "UNKNOWN"]
    if not unknown or unknown[0]["swing_feature_allowed"] != "0":
        failures.append("UNKNOWN mapping scope must block feature admission")
    else:
        passes.append("unknown_mapping_blocks_feature_admission")

    summary = json.loads((REPORT_DIR / "swing_news_feature_admission_summary.json").read_text(encoding="utf-8"))
    if summary.get("paper_live_broker_order_opened") or summary.get("trading_authority_opened"):
        failures.append("trading/paper/live/broker/order gate unexpectedly opened")
    else:
        passes.append("trading_paper_live_broker_order_gates_closed")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
