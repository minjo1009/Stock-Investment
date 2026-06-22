from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK401_ENTRY_CANDIDATES = Path(
    "docs/reports/task_401_forward_live_canonical_multifactor_decision_layer/multifactor_entry_candidate_log.csv"
)
DEFAULT_LABEL_SOURCE = Path(
    "docs/reports/task_399_intraday_universe_history_expansion/task_397_expanded/false_positive_lifecycle_panel.csv"
)
DEFAULT_OUT_DIR = Path("docs/reports/task_402r_decision_labelability_audit")
MIN_LABEL_COVERAGE_FOR_TASK401_VALIDATION = 0.80


@dataclass(frozen=True)
class DecisionLabelabilityAudit402RArtifacts:
    decision_labelability_audit: pd.DataFrame
    population_consistency_audit: pd.DataFrame
    unlabeled_candidate_audit: pd.DataFrame
    task_402r_decision: pd.DataFrame


def build_decision_labelability_audit_402r(
    *,
    task401_entry_candidates_path: Path = DEFAULT_TASK401_ENTRY_CANDIDATES,
    label_source_path: Path = DEFAULT_LABEL_SOURCE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> DecisionLabelabilityAudit402RArtifacts:
    decisions = pd.read_csv(task401_entry_candidates_path, encoding="utf-8-sig")
    labels = pd.read_csv(label_source_path, encoding="utf-8-sig")
    labels = labels.dropna(subset=["lifecycle_id"]).drop_duplicates(subset=["lifecycle_id"]).copy()
    labeled_ids = set(labels["lifecycle_id"].astype(str))
    audited = decisions.copy()
    audited["lifecycle_id"] = audited.get("lifecycle_id", "").fillna("").astype(str)
    audited["lifecycle_created_flag"] = audited["lifecycle_id"].str.len().gt(0).astype(int)
    audited["exact_label_match_flag"] = audited["lifecycle_id"].map(lambda value: int(bool(value) and value in labeled_ids))
    audited["label_status"] = "non_lifecycle_candidate"
    audited.loc[audited["lifecycle_created_flag"].eq(1), "label_status"] = "unlabeled_lifecycle"
    audited.loc[audited["exact_label_match_flag"].eq(1), "label_status"] = "labelable_exact_lifecycle"

    labelability = summarize_labelability(audited)
    population = build_population_consistency_audit(audited, labels)
    unlabeled = build_unlabeled_candidate_audit(audited)
    decision = build_task_402r_decision(labelability, population)
    artifacts = DecisionLabelabilityAudit402RArtifacts(labelability, population, unlabeled, decision)
    write_task_402r_artifacts(artifacts, out_dir)
    return artifacts


def summarize_labelability(audited: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for bucket, group in audited.groupby("bucket", dropna=False):
        lifecycle_count = int(group["lifecycle_created_flag"].sum())
        exact_count = int(group["exact_label_match_flag"].sum())
        rows.append(
            {
                "bucket": bucket,
                "candidate_count": int(len(group)),
                "lifecycle_created_count": lifecycle_count,
                "non_lifecycle_candidate_count": int((group["lifecycle_created_flag"] == 0).sum()),
                "exact_label_count": exact_count,
                "unlabeled_lifecycle_count": lifecycle_count - exact_count,
                "label_coverage_rate": exact_count / lifecycle_count if lifecycle_count else 0.0,
                "unlabeled_treated_as_negative_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("bucket")


def build_population_consistency_audit(audited: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    lifecycle_created = audited[audited["lifecycle_created_flag"].eq(1)]
    exact_overlap = int(audited["exact_label_match_flag"].sum())
    lifecycle_count = int(lifecycle_created["lifecycle_id"].nunique())
    label_count = int(labels["lifecycle_id"].nunique())
    coverage = exact_overlap / lifecycle_count if lifecycle_count else 0.0
    return pd.DataFrame(
        [
            {
                "task401_entry_candidate_count": int(len(audited)),
                "task401_lifecycle_created_count": lifecycle_count,
                "label_source_lifecycle_count": label_count,
                "exact_lifecycle_id_overlap_count": exact_overlap,
                "task401_exact_label_coverage_rate": coverage,
                "task401_label_coverage_sufficient": "YES" if coverage >= MIN_LABEL_COVERAGE_FOR_TASK401_VALIDATION else "NO",
                "population_mismatch_status": "NO_EXACT_OVERLAP" if exact_overlap == 0 else "PARTIAL_EXACT_OVERLAP",
                "join_key_used": "lifecycle_id_exact_only",
                "symbol_date_price_time_fallback_used_flag": 0,
                "unlabeled_treated_as_negative_flag": 0,
            }
        ]
    )


def build_unlabeled_candidate_audit(audited: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "decision_id",
        "candidate_id",
        "lifecycle_id",
        "bucket",
        "symbol",
        "theme_id",
        "decision_ts_utc",
        "label_status",
        "unlabeled_treated_as_negative_flag",
    ]
    out = audited[audited["label_status"].ne("labelable_exact_lifecycle")].copy()
    out["unlabeled_treated_as_negative_flag"] = 0
    for col in cols:
        if col not in out.columns:
            out[col] = ""
    return out[cols].copy()


def build_task_402r_decision(labelability: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    pop = population.iloc[0].to_dict() if not population.empty else {}
    return pd.DataFrame(
        [
            {
                "task_402r_verdict": "COMPLETE_PASS",
                "evaluation_status": "DECISION_LABELABILITY_AUDIT_COMPLETE",
                "task401_label_coverage_sufficient": pop.get("task401_label_coverage_sufficient", "NO"),
                "task401_exact_label_coverage_rate": pop.get("task401_exact_label_coverage_rate", 0.0),
                "exact_lifecycle_id_overlap_count": pop.get("exact_lifecycle_id_overlap_count", 0),
                "population_mismatch_status": pop.get("population_mismatch_status", ""),
                "unlabeled_treated_as_negative_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "strategy_acceptance_status": "NOT_DEPLOYMENT_READY",
                "next_priority": "task403_multi_archetype_portfolio_discovery_on_exact_labeled_population",
            }
        ]
    )


def write_task_402r_artifacts(artifacts: DecisionLabelabilityAudit402RArtifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.decision_labelability_audit.to_csv(out_dir / "decision_labelability_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.population_consistency_audit.to_csv(out_dir / "population_consistency_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.unlabeled_candidate_audit.to_csv(out_dir / "unlabeled_candidate_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_402r_decision.to_csv(out_dir / "task_402r_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 402R - Decision Labelability Audit",
        "",
        "## Required Answers",
        "- Did we use inferred lifecycle matching? `NO`",
        "- Are unlabeled rows treated as negative? `NO`",
        "",
        "## Decision",
        _csv_block(artifacts.task_402r_decision),
        "",
        "## Population Consistency",
        _csv_block(artifacts.population_consistency_audit),
        "",
        "## Labelability By Bucket",
        _csv_block(artifacts.decision_labelability_audit),
    ]
    (out_dir / "task_402r_decision_labelability_audit.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 402R decision labelability audit.")
    parser.add_argument("--task401-entry-candidates", type=Path, default=DEFAULT_TASK401_ENTRY_CANDIDATES)
    parser.add_argument("--label-source", type=Path, default=DEFAULT_LABEL_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_decision_labelability_audit_402r(
        task401_entry_candidates_path=args.task401_entry_candidates,
        label_source_path=args.label_source,
        out_dir=args.out_dir,
    )
    row = artifacts.task_402r_decision.iloc[0]
    print(
        "[TASK402R] "
        f"coverage={row['task401_exact_label_coverage_rate']} "
        f"sufficient={row['task401_label_coverage_sufficient']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
