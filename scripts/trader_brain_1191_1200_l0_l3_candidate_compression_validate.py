from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1191_1200_l0_l3_candidate_compression"
REPORT = ROOT / "docs/reports/task_1191_1200_l0_l3_candidate_compression"

REQUIRED_FILES = [
    "task1191_l0_security_filter.csv",
    "task1192_industry_theme_map.csv",
    "task1193_l1_source_packets.csv",
    "task1194_l2_meaning_panel.csv",
    "task1195_macro_policy_bridge.csv",
    "task1196_l3_relation_edges.csv",
    "task1197_compressed_candidates.csv",
    "task1198_negative_fixtures.csv",
    "task1199_candidate_quality_diagnostic.csv",
    "task1200_replay_preregistration_gate.csv",
    "task1200_l0_l3_candidate_compression_closeout.csv",
    "task1200_l0_l3_candidate_compression_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1191_1200_l0_l3_candidate_compression.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1191_1200_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    l0 = rows("task1191_l0_security_filter.csv")
    industry = rows("task1192_industry_theme_map.csv")
    packets = rows("task1193_l1_source_packets.csv")
    meaning = rows("task1194_l2_meaning_panel.csv")
    macro = rows("task1195_macro_policy_bridge.csv")
    edges = rows("task1196_l3_relation_edges.csv")
    candidates = rows("task1197_compressed_candidates.csv")
    negatives = rows("task1198_negative_fixtures.csv")
    quality = rows("task1199_candidate_quality_diagnostic.csv")
    prereg = rows("task1200_replay_preregistration_gate.csv")
    closeout = rows("task1200_l0_l3_candidate_compression_closeout.csv")
    closeout_json = json.loads((ART / "task1200_l0_l3_candidate_compression_closeout.json").read_text(encoding="utf-8"))

    if len(l0) != 29397:
        errors.append("L0 filter must cover 29397 feature rows")
    l0_pass = sum(1 for row in l0 if row["l0_tradable_pass"] == "1")
    if l0_pass <= 1000 or l0_pass >= len(l0):
        errors.append("L0 filter pass count must be nontrivial")
    if any(row["assignment_uses_future_outcome"] != "0" for row in l0[:1000]):
        errors.append("L0 assignment must not use future outcome")

    for name, table in [
        ("industry map", industry),
        ("source packets", packets),
        ("meaning", meaning),
        ("macro bridge", macro),
    ]:
        if len(table) != len(l0):
            errors.append(f"{name} must match L0 row count")
        if any(row["assignment_uses_future_outcome"] != "0" for row in table[:1000] if "assignment_uses_future_outcome" in row):
            errors.append(f"{name} assignment must not use future outcome")

    if len(edges) != len(l0) * 4:
        errors.append("L3 relation edges must create four edges per L0 row")
    if not {"company_to_industry", "company_to_theme", "theme_to_policy_driver", "company_to_risk_invalidator"}.issubset(
        {row["edge_type"] for row in edges[:5000]}
    ):
        errors.append("L3 edge types missing expected primitives")

    if len(candidates) <= 0:
        errors.append("compressed candidates must exist")
    if any(row["assignment_uses_future_outcome"] != "0" for row in candidates):
        errors.append("candidate compression must not use future outcome")
    if any("forward_return" not in row["forbidden_assignment_inputs"] for row in candidates[:100]):
        errors.append("candidate rows must declare forbidden future inputs")
    bucket_counts = {bucket: sum(1 for row in candidates if row["candidate_bucket"] == bucket) for bucket in ["top50", "top100", "top150"]}
    if min(bucket_counts.values()) <= 0:
        errors.append("candidate compression must contain top50 top100 and top150 buckets")

    if len(negatives) < 10:
        errors.append("negative fixtures must include at least 10 rows")
    if any(row["appears_in_compressed_candidates"] != "0" for row in negatives):
        errors.append("negative fixtures must not appear in compressed candidates")

    if len(quality) <= 0:
        errors.append("quality diagnostics must exist")
    if any(row["outcome_used_for_assignment"] != "0" for row in quality):
        errors.append("quality diagnostics must not feed assignment")
    if any(row["selection_promoted"] != "0" for row in quality):
        errors.append("quality diagnostics must not promote selection")

    if len(prereg) != 1:
        errors.append("preregistration gate must have one row")
    else:
        row = prereg[0]
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("preregistration must not execute replay or promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("preregistration changed strategy acceptance")
        if float(row["top50_avg_hit_rate_eval_only"]) <= 0:
            errors.append("preregistration must record top50 hit rate")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("closeout must not execute replay or promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")
        if int(row["compressed_candidate_rows"]) != len(candidates):
            errors.append("closeout candidate count mismatch")

    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json strategy acceptance changed")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1191_1200_L0_L3_CANDIDATE_COMPRESSION_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1191_1200_L0_L3_CANDIDATE_COMPRESSION_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
