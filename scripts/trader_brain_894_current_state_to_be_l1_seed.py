from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
RECOVERED_PANEL = ROOT / "data/artifacts/task_893_source_time_recovery/recovered_source_time_panel.csv"
DECISION_CALENDAR = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv"

FORBIDDEN_TRADING_FIELDS = {"side", "entry", "exit", "position_size", "rank", "score", "future_return", "realized_return", "pnl"}


THEME_SOURCE_REQUIREMENTS = {
    "ai_semiconductors": "earnings_transcript;capex_news;export_control_policy;sec_filings",
    "cloud_ai_platforms": "earnings_transcript;ai_product_news;capex_news;sec_filings",
    "cybersecurity": "earnings_transcript;breach_news;enterprise_spend_news;sec_filings",
    "data_devops_software": "earnings_transcript;product_usage_news;enterprise_spend_news;sec_filings",
    "ev_autonomy_mobility": "earnings_transcript;delivery_news;regulatory_news;sec_filings",
    "power_grid_electrification": "earnings_transcript;power_demand_news;utility_policy;sec_filings",
    "biotech_glp1_healthcare": "earnings_transcript;clinical_regulatory_news;pricing_policy;sec_filings",
    "crypto_fintech": "earnings_transcript;crypto_policy;asset_price_context;sec_filings",
    "aerospace_defense_space": "earnings_transcript;defense_budget_policy;launch_contract_news;sec_filings",
    "industrial_automation_robotics": "earnings_transcript;industrial_cycle_news;automation_capex_news;sec_filings",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_universe() -> list[dict[str, str]]:
    return rows(UNIVERSE_PATH)


def build_symbol_coverage(universe: list[dict[str, str]], recovered: list[dict[str, str]]) -> list[dict[str, object]]:
    by_symbol: dict[str, list[dict[str, str]]] = {}
    for row in recovered:
        by_symbol.setdefault(row["symbol"], []).append(row)
    coverage: list[dict[str, object]] = []
    for item in universe:
        symbol = item["symbol"]
        evidence = sorted(by_symbol.get(symbol, []), key=lambda row: row["available_to_brain_ts"])
        coverage.append(
            {
                "theme": item["theme"],
                "symbol": symbol,
                "role": item["role"],
                "recovered_event_rows": len(evidence),
                "first_available_to_brain_ts": evidence[0]["available_to_brain_ts"] if evidence else "",
                "last_available_to_brain_ts": evidence[-1]["available_to_brain_ts"] if evidence else "",
                "coverage_state": "l1_seed_available" if evidence else "missing_l1_source_seed",
                "raw_external_document_state": "missing_for_seed_rows" if evidence else "missing",
                "required_source_families": THEME_SOURCE_REQUIREMENTS.get(item["theme"], "earnings_transcript;news;sec_filings"),
                "next_action": "attach_raw_external_sources_to_seed_rows" if evidence else "acquire_source_time_seed_rows",
            }
        )
    return coverage


def build_decision_coverage(universe: list[dict[str, str]], decisions: list[dict[str, str]], recovered: list[dict[str, str]]) -> list[dict[str, object]]:
    by_symbol: dict[str, list[dict[str, str]]] = {}
    for row in recovered:
        by_symbol.setdefault(row["symbol"], []).append(row)
    panel: list[dict[str, object]] = []
    for decision in decisions:
        decision_asof = parse_ts(decision["decision_asof_ts"])
        for item in universe:
            symbol = item["symbol"]
            available = [row for row in by_symbol.get(symbol, []) if parse_ts(row["available_to_brain_ts"]) <= decision_asof]
            panel.append(
                {
                    "decision_id": decision["decision_id"],
                    "decision_asof_ts": decision["decision_asof_ts"],
                    "split_id": decision["split_id"],
                    "theme": item["theme"],
                    "symbol": symbol,
                    "available_l1_seed_count": len(available),
                    "has_l1_seed": int(bool(available)),
                    "coverage_state": "asof_l1_seed_available" if available else "asof_missing_l1_source_seed",
                    "source_gap_flag": "raw_external_document_missing" if available else "source_seed_missing",
                    "does_not_mean": "trade signal, candidate bundle, score, rank, or strategy acceptance",
                }
            )
    return panel


def first_eligible_decision(evidence_ts: str, decisions: list[dict[str, str]]) -> dict[str, str] | None:
    evidence_time = parse_ts(evidence_ts)
    for decision in decisions:
        if parse_ts(decision["decision_asof_ts"]) >= evidence_time:
            return decision
    return None


def build_l1_seed_state(recovered: list[dict[str, str]], decisions: list[dict[str, str]], universe_symbols: set[str]) -> list[dict[str, object]]:
    states: list[dict[str, object]] = []
    for index, row in enumerate(sorted(recovered, key=lambda item: (item["available_to_brain_ts"], item["symbol"], item["evidence_id"])), start=1):
        first_decision = first_eligible_decision(row["available_to_brain_ts"], decisions)
        in_universe = row["symbol"] in universe_symbols
        states.append(
            {
                "l1_state_id": f"L1SEED894-{index:05d}",
                "evidence_id": row["evidence_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "in_10x7_universe": int(in_universe),
                "available_to_brain_ts": row["available_to_brain_ts"],
                "first_eligible_decision_id": first_decision["decision_id"] if first_decision else "",
                "first_eligible_decision_asof_ts": first_decision["decision_asof_ts"] if first_decision else "",
                "source_family": row["source_family"],
                "source_gap_flag": row["source_gap_flag"],
                "bridge_authority": row["bridge_authority"],
                "brain_layer": "L1_SOURCE_EVIDENCE_SEED",
                "primitive_fact_state": "not_generated",
                "economic_meaning_state": "not_generated",
                "relation_state": "not_generated",
                "eligibility_state": "usable_for_l1_seed_only" if in_universe else "outside_10x7_backtest_universe_reference_only",
                "does_not_mean": "L2 meaning, L3 relation, candidate bundle, trade spec, or accepted strategy",
            }
        )
    return states


def build_diagnosis(coverage: list[dict[str, object]], l1_states: list[dict[str, object]], decision_panel: list[dict[str, object]]) -> list[dict[str, object]]:
    seed_symbols = sum(1 for row in coverage if row["coverage_state"] == "l1_seed_available")
    return [
        {
            "area": "universe",
            "as_is": "70 symbols across 10 themes fixed as diagnostic research universe",
            "to_be": "70 symbols have explicit source-time coverage state and acquisition requirement",
            "gap": f"{70 - seed_symbols} symbols still have no L1 source seed",
            "implemented_remediation": "source_time_symbol_coverage_matrix.csv",
            "status_after_task894": "structured_partial",
        },
        {
            "area": "source_time",
            "as_is": "139 recovered internal source-capture rows with raw external document gaps",
            "to_be": "each used evidence row has raw source document or URL hash attached",
            "gap": "raw external source is still missing for recovered seed rows",
            "implemented_remediation": "source-time seed rows are preserved with raw_external_document_missing flag",
            "status_after_task894": "seed_panel_ready_for_l1_only",
        },
        {
            "area": "asof_decision_coverage",
            "as_is": f"{len(decision_panel)} decision-symbol coverage rows were not materialized before",
            "to_be": "every monthly decision sees only evidence available at or before decision_asof_ts",
            "gap": "not all decision-symbol pairs have evidence",
            "implemented_remediation": "source_time_decision_coverage_panel.csv",
            "status_after_task894": "implemented",
        },
        {
            "area": "l1_brain_seed",
            "as_is": "Task893 recovered evidence but did not emit brain-layer state rows",
            "to_be": "L1 state exists without generating L2/L3/candidate/trade semantics",
            "gap": "L2 primitive facts and L3 relations still require separate guarded builders",
            "implemented_remediation": f"{len(l1_states)} L1 seed rows emitted with L2/L3 states blocked",
            "status_after_task894": "implemented_l1_only",
        },
    ]


def build_acquisition_queue(coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    queue: list[dict[str, object]] = []
    for row in coverage:
        missing_seed = row["coverage_state"] == "missing_l1_source_seed"
        priority = 1 if missing_seed else 2
        queue.append(
            {
                "priority": priority,
                "theme": row["theme"],
                "symbol": row["symbol"],
                "role": row["role"],
                "current_state": row["coverage_state"],
                "recovered_event_rows": row["recovered_event_rows"],
                "required_source_families": row["required_source_families"],
                "implementation_step": "collect_historical_source_time_seed" if missing_seed else "attach_raw_external_document_hashes",
                "guardrail": "no synthetic rows, no price/outcome inference, no missing label as negative",
            }
        )
    return sorted(queue, key=lambda row: (int(row["priority"]), str(row["theme"]), str(row["symbol"])))


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    universe = load_universe()
    recovered = rows(RECOVERED_PANEL)
    decisions = rows(DECISION_CALENDAR)
    universe_symbols = {row["symbol"] for row in universe}

    coverage = build_symbol_coverage(universe, recovered)
    decision_panel = build_decision_coverage(universe, decisions, recovered)
    l1_states = build_l1_seed_state(recovered, decisions, universe_symbols)
    diagnosis = build_diagnosis(coverage, l1_states, decision_panel)
    acquisition_queue = build_acquisition_queue(coverage)

    write_csv(
        out_dir / "current_state_to_be_diagnosis.csv",
        diagnosis,
        ["area", "as_is", "to_be", "gap", "implemented_remediation", "status_after_task894"],
    )
    write_csv(
        out_dir / "source_time_symbol_coverage_matrix.csv",
        coverage,
        [
            "theme",
            "symbol",
            "role",
            "recovered_event_rows",
            "first_available_to_brain_ts",
            "last_available_to_brain_ts",
            "coverage_state",
            "raw_external_document_state",
            "required_source_families",
            "next_action",
        ],
    )
    write_csv(
        out_dir / "source_time_decision_coverage_panel.csv",
        decision_panel,
        [
            "decision_id",
            "decision_asof_ts",
            "split_id",
            "theme",
            "symbol",
            "available_l1_seed_count",
            "has_l1_seed",
            "coverage_state",
            "source_gap_flag",
            "does_not_mean",
        ],
    )
    write_csv(
        out_dir / "l1_source_evidence_seed_state.csv",
        l1_states,
        [
            "l1_state_id",
            "evidence_id",
            "symbol",
            "theme",
            "in_10x7_universe",
            "available_to_brain_ts",
            "first_eligible_decision_id",
            "first_eligible_decision_asof_ts",
            "source_family",
            "source_gap_flag",
            "bridge_authority",
            "brain_layer",
            "primitive_fact_state",
            "economic_meaning_state",
            "relation_state",
            "eligibility_state",
            "does_not_mean",
        ],
    )
    write_csv(
        out_dir / "missing_source_acquisition_queue.csv",
        acquisition_queue,
        ["priority", "theme", "symbol", "role", "current_state", "recovered_event_rows", "required_source_families", "implementation_step", "guardrail"],
    )

    seed_symbols = sum(1 for row in coverage if row["coverage_state"] == "l1_seed_available")
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task894",
        "universe_symbols": len(universe),
        "decision_count": len(decisions),
        "decision_symbol_rows": len(decision_panel),
        "recovered_l1_seed_rows": len(l1_states),
        "universe_symbols_with_l1_seed": seed_symbols,
        "universe_symbols_missing_l1_seed": len(universe) - seed_symbols,
        "forbidden_trading_fields_present": sorted(FORBIDDEN_TRADING_FIELDS & set(l1_states[0].keys())) if l1_states else [],
        "brain_layer_status": "L1_SOURCE_EVIDENCE_SEED_ONLY",
        "next_required_layer": "L2_primitive_fact_builder_with_raw_source_attachment",
        "first_real_historical_brain_replay": "no_go_until_l2_l3_candidate_trade_spec_gates_pass",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_894_current_state_to_be_l1_seed_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_894_CURRENT_STATE_TO_BE_L1_SEED_OK] "
        f"universe={summary['universe_symbols']} seed_symbols={summary['universe_symbols_with_l1_seed']} "
        f"l1_rows={summary['recovered_l1_seed_rows']} decision_symbol_rows={summary['decision_symbol_rows']}"
    )


if __name__ == "__main__":
    main()
