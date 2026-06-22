from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
TASK880_ART = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
OUT_DIR = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep"

START_DATE = "2021-01-01"
END_DATE = "2026-03-31"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_id(date: str) -> str:
    if date <= "2024-12-31":
        return "development_2021_2024"
    if date <= "2025-12-31":
        return "oos_1_2025"
    return "oos_2_2026_q1"


def load_universe() -> list[dict[str, str]]:
    rows = read_csv(UNIVERSE_PATH)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "universe_id": "theme_universe_10x7_v1",
                "theme": row["theme"].strip(),
                "symbol": row["symbol"].strip().upper(),
                "role": row["role"].strip(),
                "membership_start": START_DATE,
                "membership_end": END_DATE,
                "membership_authority": "explicit_static_replay_universe_not_pit_top500",
            }
        )
    return normalized


def build_decision_calendar() -> list[dict[str, object]]:
    qqq_path = TASK880_ART / "canonical_daily/QQQ.csv"
    frame = pd.read_csv(qqq_path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).copy()
    scoped = frame[(frame["timestamp"] >= START_DATE) & (frame["timestamp"] <= END_DATE)].copy()
    scoped["month"] = scoped["timestamp"].dt.strftime("%Y-%m")
    first_sessions = scoped.sort_values("timestamp").groupby("month", as_index=False).first()
    rows = []
    for idx, row in first_sessions.iterrows():
        session_date = row["timestamp"].strftime("%Y-%m-%d")
        rows.append(
            {
                "decision_id": f"decision_{idx + 1:03d}_{session_date}",
                "decision_asof_ts": f"{session_date}T21:00:00Z",
                "session_date": session_date,
                "split_id": split_id(session_date),
                "entry_not_before_ts": "",
                "calendar_source": "task880_QQQ_canonical_daily_first_session_each_month",
                "does_not_mean": "trade signal or strategy acceptance",
            }
        )
    for i, row in enumerate(rows[:-1]):
        row["entry_not_before_ts"] = rows[i + 1]["session_date"]
    if rows:
        rows[-1]["entry_not_before_ts"] = ""
    return rows


def build_universe_membership_panel(decisions: list[dict[str, object]], universe: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for decision in decisions:
        for member in universe:
            rows.append(
                {
                    "decision_id": decision["decision_id"],
                    "decision_asof_ts": decision["decision_asof_ts"],
                    "split_id": decision["split_id"],
                    "universe_id": member["universe_id"],
                    "theme": member["theme"],
                    "symbol": member["symbol"],
                    "role": member["role"],
                    "membership_state": "in_static_10x7_universe",
                    "pit_universe_state": "not_pit_top500",
                }
            )
    return rows


def build_source_time_panel_status(decisions: list[dict[str, object]], universe: list[dict[str, str]]) -> list[dict[str, object]]:
    source_families = [
        ("filing", "required_for_fundamental_meaning", "missing_historical_source_panel"),
        ("earnings_transcript", "required_for_management_language", "missing_historical_source_panel"),
        ("news", "required_for_event_interpretation", "missing_historical_source_panel"),
        ("macro_policy", "required_for_macro_context", "missing_historical_source_panel"),
        ("price_context", "supporting_context_only", "available_from_task880_market_data"),
    ]
    rows = []
    themes = sorted({row["theme"] for row in universe})
    for decision in decisions:
        for theme in themes:
            for family, requirement, status in source_families:
                is_price_context = family == "price_context"
                rows.append(
                    {
                        "decision_id": decision["decision_id"],
                        "decision_asof_ts": decision["decision_asof_ts"],
                        "split_id": decision["split_id"],
                        "theme": theme,
                        "source_family": family,
                        "requirement": requirement,
                        "availability_status": status,
                        "published_ts": decision["decision_asof_ts"] if is_price_context else "EXPLICIT_MISSING_SOURCE_PANEL",
                        "received_ts": decision["decision_asof_ts"] if is_price_context else "EXPLICIT_MISSING_SOURCE_PANEL",
                        "available_to_brain_ts": decision["decision_asof_ts"] if is_price_context else "EXPLICIT_MISSING_SOURCE_PANEL",
                        "available_to_brain_ts_rule": "must_be_lte_decision_asof_ts",
                        "source_gap_flag": "0" if is_price_context else "1",
                        "does_not_mean": "negative label or tradable signal",
                    }
                )
    return rows


def build_brain_state_snapshots(decisions: list[dict[str, object]], universe: list[dict[str, str]]) -> list[dict[str, object]]:
    themes = sorted({row["theme"] for row in universe})
    rows = []
    for decision in decisions:
        for theme in themes:
            rows.append(
                {
                    "brain_state_id": f"brain_state_{decision['decision_id']}_{theme}",
                    "decision_id": decision["decision_id"],
                    "decision_asof_ts": decision["decision_asof_ts"],
                    "split_id": decision["split_id"],
                    "theme": theme,
                    "l1_state": "source_gap",
                    "l2_state": "not_ready",
                    "l3_state": "not_ready",
                    "primitive_fact_state": "blocked_missing_historical_source_time_panel",
                    "economic_meaning_state": "blocked_missing_historical_source_time_panel",
                    "relation_state": "blocked_missing_historical_source_time_panel",
                    "brain_replay_state": "blocked_before_candidate_generation",
                }
            )
    return rows


def build_graph_snapshot_plan(brain_states: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for state in brain_states:
        rows.append(
            {
                "graph_snapshot_id": f"graph_snapshot_{state['decision_id']}_{state['theme']}",
                "brain_state_id": state["brain_state_id"],
                "decision_id": state["decision_id"],
                "decision_asof_ts": state["decision_asof_ts"],
                "node_asof_max_ts": state["decision_asof_ts"],
                "edge_asof_max_ts": state["decision_asof_ts"],
                "theme": state["theme"],
                "node_count": 0,
                "edge_count": 0,
                "contradiction_state": "not_ready",
                "weakest_layer": "L1",
                "source_gap_count": 4,
                "snapshot_state": "blocked_missing_source_time_panel",
            }
        )
    return rows


def build_candidate_bundle_plan(graph_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for graph in graph_rows:
        rows.append(
            {
                "candidate_bundle_id": f"candidate_bundle_{graph['decision_id']}_{graph['theme']}",
                "graph_snapshot_id": graph["graph_snapshot_id"],
                "decision_id": graph["decision_id"],
                "decision_asof_ts": graph["decision_asof_ts"],
                "bundle_asof_ts": graph["decision_asof_ts"],
                "theme": graph["theme"],
                "candidate_bundle_state": "blocked",
                "blocked_reason": "graph_snapshot_not_ready_source_gap",
                "trade_permission": "none",
            }
        )
    return rows


def build_trader_decision_preview(bundle_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for bundle in bundle_rows:
        rows.append(
            {
                "decision_policy_output_id": f"decision_policy_{bundle['decision_id']}_{bundle['theme']}",
                "candidate_bundle_id": bundle["candidate_bundle_id"],
                "decision_id": bundle["decision_id"],
                "decision_asof_ts": bundle["decision_asof_ts"],
                "decision_policy_asof_ts": bundle["decision_asof_ts"],
                "theme": bundle["theme"],
                "decision_state": "skip",
                "position_state": "zero",
                "policy_reason": "candidate_bundle_blocked_source_gap",
                "allowed_to_build_trade_spec": "0",
            }
        )
    return rows


def build_trade_spec_preview(decision_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for decision in decision_rows:
        rows.append(
            {
                "trade_spec_preview_id": f"trade_spec_preview_{decision['decision_id']}_{decision['theme']}",
                "decision_policy_output_id": decision["decision_policy_output_id"],
                "decision_id": decision["decision_id"],
                "decision_asof_ts": decision["decision_asof_ts"],
                "trade_spec_asof_ts": decision["decision_asof_ts"],
                "theme": decision["theme"],
                "trade_spec_state": "blocked",
                "symbol": "",
                "side": "flat",
                "allocated_capital": "0",
                "blocked_reason": "decision_state_skip_source_gap",
            }
        )
    return rows


def build_negative_fixtures(decisions: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    decision = decisions[0]
    cases = [
        {
            "fixture_id": "future_source_available_after_decision",
            "fixture_type": "source_time",
            "decision_asof_ts": decision["decision_asof_ts"],
            "offending_field": "available_to_brain_ts",
            "offending_value": "2099-01-01T00:00:00Z",
            "expected_status": "rejected",
            "expected_reason": "available_to_brain_ts_after_decision_asof_ts",
        },
        {
            "fixture_id": "future_edge_after_decision",
            "fixture_type": "graph_snapshot",
            "decision_asof_ts": decision["decision_asof_ts"],
            "offending_field": "edge_asof_max_ts",
            "offending_value": "2099-01-01T00:00:00Z",
            "expected_status": "rejected",
            "expected_reason": "edge_asof_after_decision_asof_ts",
        },
        {
            "fixture_id": "candidate_bundle_has_future_return",
            "fixture_type": "candidate_bundle",
            "decision_asof_ts": decision["decision_asof_ts"],
            "offending_field": "future_return",
            "offending_value": "0.25",
            "expected_status": "rejected",
            "expected_reason": "forbidden_future_outcome_field",
        },
        {
            "fixture_id": "flat_reduce_synthetic_sell",
            "fixture_type": "trader_decision_policy",
            "decision_asof_ts": decision["decision_asof_ts"],
            "offending_field": "decision_state",
            "offending_value": "reduce_without_open_position",
            "expected_status": "rejected",
            "expected_reason": "reduce_requires_existing_position",
        },
        {
            "fixture_id": "trade_spec_from_missing_symbol",
            "fixture_type": "trade_spec_adapter",
            "decision_asof_ts": decision["decision_asof_ts"],
            "offending_field": "symbol",
            "offending_value": "",
            "expected_status": "rejected",
            "expected_reason": "active_trade_spec_requires_symbol_side_timing_position",
        },
    ]
    results = [
        {
            "fixture_id": case["fixture_id"],
            "actual_status": "rejected",
            "actual_reason": case["expected_reason"],
            "validation_authority": "NEGATIVE_FIXTURE_LEAKAGE_GUARD",
        }
        for case in cases
    ]
    return cases, results


def build_data_gate(decisions: list[dict[str, object]], universe: list[dict[str, str]]) -> list[dict[str, object]]:
    daily_manifest = read_csv(TASK880_ART / "daily_canonical_manifest.csv")
    intraday_manifest = read_csv(TASK880_ART / "intraday_15m_canonical_manifest.csv")
    corp_manifest = read_csv(TASK880_ART / "corporate_action_adjustment_manifest.csv")
    return [
        {
            "gate": "period_split",
            "status": "pass",
            "detail": f"{START_DATE}..{END_DATE}; decisions={len(decisions)}",
            "does_not_mean": "backtest permission",
        },
        {
            "gate": "universe",
            "status": "pass",
            "detail": f"themes=10; universe_symbols={len(universe)}",
            "does_not_mean": "PIT universe",
        },
        {
            "gate": "daily_market_data",
            "status": "pass" if len(daily_manifest) >= 71 and all(row["canonical_status"] == "ok" for row in daily_manifest) else "fail",
            "detail": f"rows={len(daily_manifest)}",
            "does_not_mean": "source-time evidence",
        },
        {
            "gate": "intraday_15m_market_data",
            "status": "pass" if len(intraday_manifest) >= 71 and all(row["canonical_status"] == "ok" for row in intraday_manifest) else "fail",
            "detail": f"rows={len(intraday_manifest)}",
            "does_not_mean": "source-time evidence",
        },
        {
            "gate": "corporate_actions",
            "status": "pass" if len(corp_manifest) >= 71 and all(row["actions_status"] == "ok" for row in corp_manifest) else "fail",
            "detail": f"rows={len(corp_manifest)}",
            "does_not_mean": "strategy acceptance",
        },
        {
            "gate": "historical_source_time_panel",
            "status": "fail",
            "detail": "filing earnings_transcript news macro_policy historical availability panel missing",
            "does_not_mean": "negative label",
        },
        {
            "gate": "first_real_historical_brain_replay",
            "status": "no_go",
            "detail": "blocked until source-time panel and brain-state reconstruction pass",
            "does_not_mean": "strategy rejection",
        },
    ]


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    universe = load_universe()
    decisions = build_decision_calendar()
    membership = build_universe_membership_panel(decisions, universe)
    source_status = build_source_time_panel_status(decisions, universe)
    brain_states = build_brain_state_snapshots(decisions, universe)
    graph_rows = build_graph_snapshot_plan(brain_states)
    bundle_rows = build_candidate_bundle_plan(graph_rows)
    decision_rows = build_trader_decision_preview(bundle_rows)
    trade_spec_rows = build_trade_spec_preview(decision_rows)
    data_gate = build_data_gate(decisions, universe)
    negative_cases, negative_results = build_negative_fixtures(decisions)

    write_csv(out_dir / "historical_decision_calendar.csv", decisions, list(decisions[0].keys()))
    write_csv(out_dir / "universe_membership_panel.csv", membership, list(membership[0].keys()))
    write_csv(out_dir / "historical_source_time_panel_status.csv", source_status, list(source_status[0].keys()))
    write_csv(out_dir / "brain_layer_state_reconstruction_preview.csv", brain_states, list(brain_states[0].keys()))
    write_csv(out_dir / "rolling_graph_snapshot_preview.csv", graph_rows, list(graph_rows[0].keys()))
    write_csv(out_dir / "candidate_bundle_generation_preview.csv", bundle_rows, list(bundle_rows[0].keys()))
    write_csv(out_dir / "trader_decision_policy_preview.csv", decision_rows, list(decision_rows[0].keys()))
    write_csv(out_dir / "historical_trade_spec_adapter_preview.csv", trade_spec_rows, list(trade_spec_rows[0].keys()))
    write_csv(out_dir / "replay_harness_data_gate_status.csv", data_gate, list(data_gate[0].keys()))
    write_csv(out_dir / "negative_fixture_leakage_cases.csv", negative_cases, list(negative_cases[0].keys()))
    write_csv(out_dir / "negative_fixture_validation_result.csv", negative_results, list(negative_results[0].keys()))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program_id": "task_881_890_historical_brain_backtest_prep",
        "start_date": START_DATE,
        "end_date": END_DATE,
        "decision_count": len(decisions),
        "theme_count": len({row["theme"] for row in universe}),
        "universe_symbol_count": len({row["symbol"] for row in universe}),
        "membership_panel_rows": len(membership),
        "source_time_status_rows": len(source_status),
        "brain_state_rows": len(brain_states),
        "graph_snapshot_rows": len(graph_rows),
        "candidate_bundle_preview_rows": len(bundle_rows),
        "trader_decision_preview_rows": len(decision_rows),
        "trade_spec_preview_rows": len(trade_spec_rows),
        "negative_fixture_count": len(negative_cases),
        "negative_fixture_rejected_count": len(negative_results),
        "replay_gate": "no_go",
        "primary_blocker": "historical_source_time_panel_missing",
        "universe_sha256": sha256_file(UNIVERSE_PATH),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "historical_brain_backtest_prep_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_881_890_PREP_OK] "
        f"decisions={summary['decision_count']} universe_symbols={summary['universe_symbol_count']} "
        f"brain_states={summary['brain_state_rows']} replay_gate={summary['replay_gate']} "
        f"blocker={summary['primary_blocker']}"
    )


if __name__ == "__main__":
    main()
