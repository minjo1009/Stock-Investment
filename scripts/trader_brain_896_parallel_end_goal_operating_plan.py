from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_896_parallel_end_goal_operating_plan"
TASK894_SUMMARY = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed/task_894_current_state_to_be_l1_seed_summary.json"
TASK895_SUMMARY = ROOT / "data/artifacts/task_895_l1_source_attachment/task_895_l1_source_attachment_summary.json"
TASK894_COVERAGE = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed/source_time_symbol_coverage_matrix.csv"
TASK895_QUEUE = ROOT / "data/artifacts/task_895_l1_source_attachment/raw_source_attachment_acquisition_queue.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def build_scorecard(task894: dict[str, object], task895: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "stage": "0_universe_market_data",
            "end_goal_requirement": "70-symbol 10-theme universe, QQQ benchmark, historical market data gate",
            "current_state": "diagnostic universe and market data path exist",
            "gap": "not PIT production universe; market data is not the active brain blocker",
            "next_move": "keep as diagnostic backbone while brain/data lanes progress",
            "status": "usable_diagnostic_backbone",
        },
        {
            "stage": "1_l1_source_evidence",
            "end_goal_requirement": "source-time evidence with raw trace, timestamps, hashes, and coverage",
            "current_state": f"{task894['recovered_l1_seed_rows']} L1 seed rows; {task894['universe_symbols_with_l1_seed']} of {task894['universe_symbols']} universe symbols have seed; {task895['complete_local_lineage_attachments']} local lineage attachments complete",
            "gap": f"{task895['raw_external_documents_missing']} raw external documents missing; {task894['universe_symbols_missing_l1_seed']} symbols lack seed",
            "next_move": "run raw source attachment for 8 seed symbols and source-time seed acquisition for 62 missing symbols",
            "status": "partial_but_structured",
        },
        {
            "stage": "2_l2_primitive_fact",
            "end_goal_requirement": "convert L1 evidence into source-local primitive facts without economic promotion",
            "current_state": "not implemented for Task895 L1 seed panel",
            "gap": "no controlled L2 builder consuming attached L1 rows",
            "next_move": "implement thin L2 builder on 139 attached L1 rows with no outcome/trade fields",
            "status": "next_vertical_slice_step",
        },
        {
            "stage": "3_l3_relationship_graph",
            "end_goal_requirement": "rolling as-of relation edges showing reinforcement, contradiction, blockers, and context",
            "current_state": "contracts and fixtures exist; historical rolling graph not populated",
            "gap": "no as-of graph from the recovered L1/L2 path",
            "next_move": "build minimal relation edges only after L2 facts exist",
            "status": "blocked_by_l2",
        },
        {
            "stage": "4_l4_candidate_thesis",
            "end_goal_requirement": "candidate thesis bundles traceable to evidence, facts, meanings, and relations",
            "current_state": "candidate contracts exist; no historical candidate bundles from current L1/L2/L3 path",
            "gap": "no traceable thesis candidates",
            "next_move": "generate review-only candidates for seed symbols after L3 edges",
            "status": "blocked_by_l3",
        },
        {
            "stage": "5_l5_trader_decision",
            "end_goal_requirement": "skip/watch/reduce/activate decisions with explicit uncertainty and no direct source-to-trade jump",
            "current_state": "policy contracts exist; no historical decisions from current brain path",
            "gap": "no L5 decisions",
            "next_move": "generate dry decisions only after candidate bundles pass provenance checks",
            "status": "blocked_by_l4",
        },
        {
            "stage": "6_backtest_paper_live_gate",
            "end_goal_requirement": "split/OOS/cost/leakage/artifact-audited backtest before paper/live gate",
            "current_state": "diagnostic plumbing replays exist; no brain-driven backtest",
            "gap": "no trade specs from brain decisions; strategy remains NOT_ACCEPTED",
            "next_move": "run only after L5 creates controlled trade-spec inputs",
            "status": "no_go",
        },
    ]


def build_parallel_plan() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task897",
            "lane": "vertical_slice",
            "title": "L2 Primitive Fact Builder for Attached L1 Seeds",
            "input": "Task895 enriched L1 panel",
            "output": "primitive_fact_seed_panel",
            "success_criteria": "139 rows mapped to deterministic source-local facts with source span, as_of timestamp, uncertainty, reproducible rule id, and no economic meaning, score, rank, side, entry, exit, position_size, pnl",
            "blocked_by": "none",
            "why_now": "moves the brain forward without waiting for full 70-symbol corpus",
        },
        {
            "task_id": "Task898",
            "lane": "vertical_slice",
            "title": "L2 Meaning Gate and Uncertainty Tags",
            "input": "Task897 primitive facts",
            "output": "economic_meaning_seed_panel",
            "success_criteria": "facts receive bounded meaning/uncertainty tags; raw external gaps propagate; no trade instruction",
            "blocked_by": "Task897;Task903",
            "why_now": "creates the first trader-brain interpretation layer",
        },
        {
            "task_id": "Task899",
            "lane": "vertical_slice",
            "title": "Minimal As-Of Relation Snapshot",
            "input": "Task898 meaning panel",
            "output": "rolling_relation_seed_snapshot",
            "success_criteria": "edges only use available_to_brain_ts <= decision_asof_ts; contradiction/source-gap edges preserved",
            "blocked_by": "Task898",
            "why_now": "starts the information relationship network, which is the core brain goal",
        },
        {
            "task_id": "Task900",
            "lane": "vertical_slice",
            "title": "Review-Only Candidate Thesis Packets",
            "input": "Task899 relation snapshots",
            "output": "candidate_thesis_seed_packets",
            "success_criteria": "candidate packets trace to evidence/fact/meaning/edge ids; no adapter trade fields",
            "blocked_by": "Task899",
            "why_now": "connects relationship graph to thesis generation without execution leap",
        },
        {
            "task_id": "Task901",
            "lane": "vertical_slice",
            "title": "Dry Trader Decision and Backtest Gate Check",
            "input": "Task900 candidate packets",
            "output": "dry_decision_gate_report",
            "success_criteria": "skip/watch/review-only states emitted; trade-spec generation remains blocked unless adapter fields are explicit and approved",
            "blocked_by": "Task900",
            "why_now": "shows exactly what is missing before a real brain-driven replay",
        },
        {
            "task_id": "Task902",
            "lane": "data_corpus",
            "title": "Raw Source Schema and Provider Map",
            "input": "Task895 raw source acquisition queue",
            "output": "source_family_provider_contract",
            "success_criteria": "for each theme, source families, minimum fields, raw path, hash, and timestamp rules are fixed",
            "blocked_by": "none",
            "why_now": "prevents random data downloads",
        },
        {
            "task_id": "Task903",
            "lane": "data_corpus",
            "title": "Small Corpus Reality Check for 8 Seed Symbols",
            "input": "Task902 contract and Task895 8 existing-seed symbols",
            "output": "raw_source_attachment_panel_and_primitive_recheck_for_seed_symbols",
            "success_criteria": "raw_source_uri/hash attached where available; missing raw sources remain explicit; Task897 primitives are rechecked against raw-source availability before Task898",
            "blocked_by": "Task902",
            "why_now": "upgrades existing 139 seeds before expanding scope",
        },
        {
            "task_id": "Task904",
            "lane": "data_corpus",
            "title": "Source-Time Seed Acquisition for 62 Missing Symbols",
            "input": "Task902 contract and Task895 missing-seed queue",
            "output": "new_source_time_seed_panel",
            "success_criteria": "source-time rows collected by provider contract; no synthetic/replay-derived rows admitted",
            "blocked_by": "Task902",
            "why_now": "broadens universe coverage without contaminating vertical slice",
        },
        {
            "task_id": "Task905",
            "lane": "data_corpus",
            "title": "Coverage Validator and Gap Dashboard",
            "input": "Task903 and Task904 panels",
            "output": "source_coverage_dashboard_and_validator",
            "success_criteria": "coverage by theme/symbol/source_family/period is measurable; missing does not become negative",
            "blocked_by": "Task903;Task904",
            "why_now": "keeps data management progressing while brain slice moves",
        },
        {
            "task_id": "Task906",
            "lane": "integration",
            "title": "Merge Data Corpus into Vertical Slice",
            "input": "Task901 dry decision gate and Task905 coverage validator",
            "output": "next_go_no_go_for_brain_backtest",
            "success_criteria": "explicit decision: expand L2/L3 to 70 symbols, keep slice only, or unblock controlled trade-spec adapter",
            "blocked_by": "Task901;Task905",
            "why_now": "prevents the two lanes from drifting apart",
        },
    ]


def build_expert_panel() -> list[dict[str, object]]:
    return [
        {"role": "Goldman Sachs GPT quant PM", "critique": "Do not wait for perfect data; require a thin falsifiable slice.", "plan_requirement": "Task897-901 must produce traceable brain outputs before more governance."},
        {"role": "Morgan Stanley GPT risk strategist", "critique": "Source gaps can become hidden risk if not explicit.", "plan_requirement": "Every L2/L3 row must propagate raw_source_gap flags."},
        {"role": "JPMorgan GPT macro strategist", "critique": "Macro/policy context must be time-stamped and separate from price outcome.", "plan_requirement": "Task902 source families include macro/policy releases with published/received timestamps."},
        {"role": "BofA GPT equity strategist", "critique": "Sector breadth matters, but the first pass should not dilute signal quality.", "plan_requirement": "Use 8 seed symbols for slice; expand via Task904 only after provider contract."},
        {"role": "Citi GPT data governance", "critique": "Random downloads will create irreconcilable lineage debt.", "plan_requirement": "Task902 freezes raw source schema before acquisition."},
        {"role": "UBS GPT portfolio construction", "critique": "Candidate theses are not positions.", "plan_requirement": "Task900 forbids side/entry/exit/position_size."},
        {"role": "Barclays GPT rates/policy", "critique": "Policy edges need release-time discipline.", "plan_requirement": "Task899 relation edges require edge_asof <= decision_asof."},
        {"role": "Deutsche Bank GPT execution risk", "critique": "Backtest adapter must not infer trades from narrative.", "plan_requirement": "Task901 remains dry decision gate unless explicit adapter fields exist."},
        {"role": "Jefferies GPT growth equity", "critique": "AI/cloud/semi slice is enough to prove the brain loop mechanics.", "plan_requirement": "Prioritize seed symbols NVDA, AMD, AVGO, MSFT, GOOGL, AMZN, META, TSLA."},
        {"role": "Point72-style GPT analyst", "critique": "A trader brain needs conflict and uncertainty, not just bullish evidence.", "plan_requirement": "Task898/899 must emit uncertainty and contradiction states."},
        {"role": "Economist GPT", "critique": "Economic meaning must distinguish demand, margin, rates, policy, and capex channels.", "plan_requirement": "Task898 meaning taxonomy uses economic channels, not price labels."},
        {"role": "Politics/policy GPT", "critique": "Policy shocks must not be backfilled from later knowledge.", "plan_requirement": "Task902 records published_ts and received_ts for policy sources."},
        {"role": "Semiconductor GPT", "critique": "Semis require capex, export control, foundry, and supply-chain edges.", "plan_requirement": "Task899 relation fixtures start with AI semiconductor seed symbols."},
        {"role": "AI/cloud GPT", "critique": "Cloud AI demand and capex must connect across suppliers and hyperscalers.", "plan_requirement": "Task899 supports cross-symbol relation edges among NVDA, AVGO, MSFT, GOOGL, AMZN, META."},
        {"role": "Space/defense GPT", "critique": "No seed coverage yet; do not invent defense/space evidence.", "plan_requirement": "Defense/space stays in Task904 data lane until source-time seeds exist."},
    ]


def build_stop_doing_rules() -> list[dict[str, object]]:
    return [
        {"rule_id": "stop_001", "rule": "Do not create another pure diagnosis task unless it changes an execution gate.", "reason": "prevents project-management churn"},
        {"rule_id": "stop_002", "rule": "Do not expand beyond Task897-906 until Task901 and Task905 both exist.", "reason": "keeps vertical slice and data lane synchronized"},
        {"rule_id": "stop_003", "rule": "Do not run a brain backtest before L5 dry decisions create explicit adapter fields.", "reason": "prevents narrative-to-trade leakage"},
        {"rule_id": "stop_004", "rule": "Do not broad-download sources outside Task902 provider contract.", "reason": "keeps data management auditable"},
        {"rule_id": "stop_005", "rule": "Do not treat missing source coverage as bearish/negative evidence.", "reason": "preserves non-negotiable quant rule"},
        {"rule_id": "stop_006", "rule": "If Task897 primitive acceptance is below 80 percent, stop Task898-901 and repair primitives first.", "reason": "prevents garbage primitive to polished graph failure"},
        {"rule_id": "stop_007", "rule": "If raw source linkage is below 95 percent for a promoted subset, do not promote relation graph outputs beyond provisional.", "reason": "prevents lineage illusion"},
        {"rule_id": "stop_008", "rule": "If uncertainty propagation is missing, do not generate candidate thesis packets.", "reason": "prevents overconfident thesis creation"},
        {"rule_id": "stop_009", "rule": "Do not freeze architecture before Task904 and Task906 re-review the 62 missing-seed symbols.", "reason": "prevents seed bias from eight mega-cap technology symbols"},
    ]


def build_external_gpt_review_synthesis() -> list[dict[str, object]]:
    return [
        {
            "finding_id": "gpt_review_001",
            "label": "interpretation",
            "finding": "Current state is closer to brain data-model validation than brain-driven backtest readiness.",
            "required_plan_change": "Keep Task896 status as pre-L2/pre-backtest and make Task897 the immediate bottleneck.",
            "owner_task": "Task897",
        },
        {
            "finding_id": "gpt_review_002",
            "label": "implementation_requirement",
            "finding": "Task897 must require source span, as_of timestamp, deterministic generation rule, reproducibility, and uncertainty per primitive.",
            "required_plan_change": "Harden Task897 success criteria.",
            "owner_task": "Task897",
        },
        {
            "finding_id": "gpt_review_003",
            "label": "implementation_requirement",
            "finding": "Task902 must separate source_time, publish_time, ingest_time, effective_time, revision policy, and source priority.",
            "required_plan_change": "Harden Task902 as source-time architecture, not just provider list.",
            "owner_task": "Task902",
        },
        {
            "finding_id": "gpt_review_004",
            "label": "implementation_requirement",
            "finding": "Task903 small corpus reality check should happen before Task898 meaning promotion.",
            "required_plan_change": "Make Task898 blocked by Task897 and Task903.",
            "owner_task": "Task898;Task903",
        },
        {
            "finding_id": "gpt_review_005",
            "label": "source_gap",
            "finding": "The eight-symbol slice is mega-cap technology biased and cannot freeze architecture for all sectors.",
            "required_plan_change": "Add architecture-freeze stop rule until Task904/906 re-review missing-seed symbols.",
            "owner_task": "Task904;Task906",
        },
        {
            "finding_id": "gpt_review_006",
            "label": "implementation_requirement",
            "finding": "Primitive quality is more important than relation graph polish.",
            "required_plan_change": "Add stop rule: primitive acceptance below 80 percent blocks Task898-901.",
            "owner_task": "Task897",
        },
        {
            "finding_id": "gpt_review_007",
            "label": "implementation_requirement",
            "finding": "Raw source linkage below 95 percent should prevent relation graph promotion beyond provisional.",
            "required_plan_change": "Add raw-source linkage stop rule.",
            "owner_task": "Task902;Task903;Task899",
        },
        {
            "finding_id": "gpt_review_008",
            "label": "implementation_requirement",
            "finding": "Uncertainty propagation must be required before candidate thesis generation.",
            "required_plan_change": "Add uncertainty stop rule before Task900.",
            "owner_task": "Task898;Task900",
        },
    ]


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    task894 = json.loads(TASK894_SUMMARY.read_text(encoding="utf-8"))
    task895 = json.loads(TASK895_SUMMARY.read_text(encoding="utf-8"))
    coverage = rows(TASK894_COVERAGE)
    queue = rows(TASK895_QUEUE)

    scorecard = build_scorecard(task894, task895)
    parallel_plan = build_parallel_plan()
    expert_panel = build_expert_panel()
    stop_rules = build_stop_doing_rules()
    external_gpt_review = build_external_gpt_review_synthesis()

    seed_symbols = sorted(row["symbol"] for row in coverage if row["coverage_state"] == "l1_seed_available")
    missing_symbols = sorted(row["symbol"] for row in coverage if row["coverage_state"] == "missing_l1_source_seed")
    lane_counts: dict[str, int] = {}
    for item in parallel_plan:
        lane_counts[item["lane"]] = lane_counts.get(item["lane"], 0) + 1

    write_csv(out_dir / "end_goal_progress_scorecard.csv", scorecard, ["stage", "end_goal_requirement", "current_state", "gap", "next_move", "status"])
    write_csv(out_dir / "parallel_execution_plan_task897_906.csv", parallel_plan, ["task_id", "lane", "title", "input", "output", "success_criteria", "blocked_by", "why_now"])
    write_csv(out_dir / "expert_panel_review_synthesis.csv", expert_panel, ["role", "critique", "plan_requirement"])
    write_csv(out_dir / "external_gpt_review_synthesis.csv", external_gpt_review, ["finding_id", "label", "finding", "required_plan_change", "owner_task"])
    write_csv(out_dir / "stop_doing_rules.csv", stop_rules, ["rule_id", "rule", "reason"])
    write_csv(
        out_dir / "parallel_lane_symbol_scope.csv",
        [
            {"lane": "vertical_slice", "symbol_count": len(seed_symbols), "symbols": ";".join(seed_symbols), "purpose": "prove L1-L5 brain mechanics without waiting for full corpus"},
            {"lane": "data_corpus", "symbol_count": len(missing_symbols), "symbols": ";".join(missing_symbols), "purpose": "fill source-time coverage under provider contract"},
        ],
        ["lane", "symbol_count", "symbols", "purpose"],
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task896",
        "operating_mode": "parallel_vertical_slice_plus_data_corpus",
        "end_goal": "US equity quant trading automation via source evidence -> economic meaning -> relationship graph -> candidate thesis -> validated backtest -> paper/live gate",
        "current_position": "L1 seed/local-lineage attached; L2-L5 and brain-driven backtest not yet implemented",
        "vertical_slice_symbols": len(seed_symbols),
        "data_corpus_missing_seed_symbols": len(missing_symbols),
        "raw_external_documents_attached": task895["raw_external_documents_attached"],
        "raw_external_documents_missing": task895["raw_external_documents_missing"],
        "parallel_plan_task_count": len(parallel_plan),
        "lane_counts": lane_counts,
        "expert_roles": len(expert_panel),
        "external_gpt_review_captured": True,
        "external_gpt_review_findings": len(external_gpt_review),
        "first_next_task": "Task897",
        "stop_rule_count": len(stop_rules),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_896_parallel_end_goal_operating_plan_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_896_PARALLEL_END_GOAL_PLAN_OK] "
        f"mode={summary['operating_mode']} tasks={summary['parallel_plan_task_count']} "
        f"slice_symbols={summary['vertical_slice_symbols']} data_missing={summary['data_corpus_missing_seed_symbols']}"
    )


if __name__ == "__main__":
    main()
