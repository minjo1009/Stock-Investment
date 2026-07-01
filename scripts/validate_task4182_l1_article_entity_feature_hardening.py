from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4182"
SLUG = "task_4182_l1_article_entity_feature_hardening"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    lines = ["TASK-4182 L1 ARTICLE ENTITY FEATURE HARDENING VALIDATION"]
    lines.extend(f"PASS {item}" for item in passes)
    lines.extend(f"WARN {item}" for item in warnings)
    lines.extend(f"FAIL {item}" for item in failures)
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)

    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4182 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_task4182_l1_article_entity_feature_hardening import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "task_4182_l1_hardening_summary.json",
        ARTIFACT_DIR / "task_4182_feature_backfill_resolution.csv",
        ARTIFACT_DIR / "task_4182_source_recall_review_queue.csv",
        ARTIFACT_DIR / "task_4182_l1_article_source_family_rollup.csv",
        ARTIFACT_DIR / "task_4182_l1_article_source_key_rollup.csv",
        REPORT_DIR / "task_result_contract.yaml",
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    resolution = read_csv(ARTIFACT_DIR / "task_4182_feature_backfill_resolution.csv")
    recall = read_csv(ARTIFACT_DIR / "task_4182_source_recall_review_queue.csv")
    family = read_csv(ARTIFACT_DIR / "task_4182_l1_article_source_family_rollup.csv")
    source = read_csv(ARTIFACT_DIR / "task_4182_l1_article_source_key_rollup.csv")
    summary_disk = read_json(ARTIFACT_DIR / "task_4182_l1_hardening_summary.json")
    if summary_disk.get("task_id") != TASK_ID:
        failures.append("summary task_id mismatch")

    if summary["after_l1_article_packets"] <= summary["baseline_l1_article_packets"]:
        failures.append("L1 article packets did not increase")
    else:
        passes.append(f"L1 article packets increased: {summary['baseline_l1_article_packets']} -> {summary['after_l1_article_packets']}")

    if summary["after_l1_article_ready_packets"] <= summary["baseline_l1_article_ready_packets"]:
        failures.append("READY L1 article packets did not increase")
    else:
        passes.append(f"READY article packets increased: {summary['baseline_l1_article_ready_packets']} -> {summary['after_l1_article_ready_packets']}")

    families = {row.get("source_family") for row in family}
    expected_families = {"public_context_news_feeds", "public_market_macro_news_feeds", "public_newswire_feeds"}
    missing_families = sorted(expected_families - families)
    if missing_families:
        failures.append(f"article packet rollup missing source families: {missing_families}")
    else:
        passes.append("article packet coverage includes context, macro, and newswire families")
    if len(source) < 5:
        failures.append(f"article packet source-key coverage too narrow: {len(source)}")
    else:
        passes.append(f"article source-key coverage: {len(source)}")

    if summary["after_l2_diagnostic_feature_rows"] <= summary["baseline_l2_diagnostic_feature_rows"]:
        failures.append("diagnostic feature rows did not increase")
    else:
        passes.append(f"diagnostic feature rows increased: {summary['baseline_l2_diagnostic_feature_rows']} -> {summary['after_l2_diagnostic_feature_rows']}")

    if not resolution:
        failures.append("feature backfill resolution ledger is empty")
    elif summary["feature_backfill_required_unresolved"] != 0:
        failures.append(f"unresolved feature materialization gaps remain: {summary['feature_backfill_required_unresolved']}")
    else:
        passes.append(f"feature materialization gaps represented in wide ledger: {len(resolution)}")
    if any(row.get("exact_l1_l2_pair_in_wide_ledger") != "1" for row in resolution):
        failures.append("feature resolution ledger contains non-exact L1/L2 references")

    if summary["source_recall_review_required_before"] != len(recall):
        failures.append(
            f"source recall review queue mismatch: before={summary['source_recall_review_required_before']} queue={len(recall)}"
        )
    elif not recall:
        failures.append("source recall review queue is empty")
    else:
        passes.append(f"source recall review queue explicit: {len(recall)}")

    if summary["forced_ticker_mapping_count"] != 0:
        failures.append("forced ticker mapping was used")
    else:
        passes.append("forced ticker mapping count is zero")
    if summary["llm_entity_inference_count"] != 0:
        failures.append("LLM entity inference was used")
    else:
        passes.append("LLM entity inference count is zero")
    if summary["negative_evidence_allowed_count"] != 0:
        failures.append("negative evidence was allowed")
    else:
        passes.append("negative evidence count is zero")
    if summary["unsafe_authority_row_count"] != 0:
        failures.append("unsafe authority rows found")
    else:
        passes.append("trading/action authority rows remain zero")

    if summary.get("upstream_l0_worker_blocker_count", 0) > 0:
        warnings.append(f"upstream L0 worker blockers remain explicit: {summary.get('upstream_l0_worker_blockers')}")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
