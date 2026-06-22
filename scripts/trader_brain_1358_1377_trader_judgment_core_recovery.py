from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
SEC_ZIP = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip"
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
TASK1338 = ROOT / "data/artifacts/task_1338_1357_full_candidate_replacement_replay"
OUT_DIR = ROOT / "data/artifacts/task_1358_1377_trader_judgment_core_recovery"
REPORT_DIR = ROOT / "docs/reports/task_1358_1377_trader_judgment_core_recovery"

AUTHORITY = "DIAGNOSTIC_TRADER_JUDGMENT_CORE_RECOVERY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
POLICIES = {
    "payoff_core_top5_v1": {"slot_cap": 5, "mode": "pure_payoff"},
    "payoff_core_top10_v1": {"slot_cap": 10, "mode": "pure_payoff"},
    "payoff_hurdle_top10_v1": {"slot_cap": 10, "mode": "preserve_original_with_hurdle"},
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace(".000Z", "+00:00").replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def load_price(symbol: str) -> pd.DataFrame | None:
    path = PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if "Date" not in frame.columns or "Close" not in frame.columns:
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    return frame.sort_values("Date")


def price_on_or_after(frame: pd.DataFrame | None, d: date) -> tuple[str, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] >= d]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["Date"].isoformat(), float(row["Close"])


def split_for_decision(decision_ts: str) -> str:
    y = int(decision_ts[:4])
    if y <= 2023:
        return "train_2021_2023"
    if y == 2024:
        return "validation_2024"
    return "oos_2025_2026q1"


def build_requirement_map() -> list[dict[str, object]]:
    items = [
        ("materiality", "L2", "restore_core", "event must estimate business impact not only source existence"),
        ("surprise_expectation", "L2", "restore_core", "event must compare against prior guidance or proxy expectation"),
        ("source_independence", "L2", "restore_core", "issuer claim must be separated from market customer analyst regulator confirmation"),
        ("mechanism_edge", "L3", "restore_core", "edge must explain why repricing remains"),
        ("payoff_ranker", "L4", "restore_core", "rank by expected payoff path not source richness"),
        ("dynamic_exit_receipt", "L5", "restore_core", "exit must be tied to post-entry source receipt when possible"),
        ("oos_split_freeze", "validation", "restore_core", "policy tuning must be separated from OOS evaluation"),
        ("overfit_guard", "validation", "restore_core", "variant and replacement attempts must be ledgered"),
        ("replacement_pair_audit", "diagnostic", "restore_core", "replaced and kept candidates need outcome-only decomposition"),
    ]
    return [
        {
            "task_id": "Task1358",
            "requirement_id": f"CORE1358-{idx:03d}",
            "core_requirement": name,
            "brain_layer": layer,
            "recovery_state": state,
            "implementation_contract": contract,
            "authority": AUTHORITY,
        }
        for idx, (name, layer, state, contract) in enumerate(items, 1)
    ]


def build_split_freeze() -> list[dict[str, object]]:
    rows = []
    decisions = sorted({row["decision_asof_ts"] for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")})
    for idx, decision_ts in enumerate(decisions, 1):
        split_id = split_for_decision(decision_ts)
        rows.append(
            {
                "task_id": "Task1359",
                "split_row_id": f"SPLIT1359-{idx:03d}",
                "decision_asof_ts": decision_ts,
                "split_id": split_id,
                "policy_parameter_tuning_allowed": "1" if split_id == "train_2021_2023" else "0",
                "validation_selection_allowed": "1" if split_id == "validation_2024" else "0",
                "oos_score_only": "1" if split_id == "oos_2025_2026q1" else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def evidence_lookup() -> dict[str, dict[str, str]]:
    return {row["evidence_id"]: row for row in read_csv(TASK1318 / "task1323_accession_source_evidence.csv")}


def materiality_from_evidence(evidence: dict[str, str] | None, state: str) -> tuple[float, str]:
    if not evidence:
        return 0.0, "materiality_unknown"
    excerpt = evidence.get("excerpt", "").lower()
    base = to_float(evidence.get("source_score"), 0.0)
    numeric = 1 if re.search(r"\$?\d+(\.\d+)?\s*(million|billion|%)", excerpt) else 0
    revenue_terms = sum(1 for token in ["revenue", "backlog", "customer", "order", "award", "purchase order", "margin", "cash flow"] if token in excerpt)
    financing_noise = 1 if any(token in excerpt for token in ["senior notes", "offering", "warrant", "convertible", "atm", "shelf registration"]) else 0
    score = min(100.0, 15.0 * base + 18.0 * numeric + 5.0 * revenue_terms)
    if state == "validated_contract_or_order":
        score += 18.0
    if state == "contract_watch_needs_materiality":
        score += 6.0
    if financing_noise:
        score -= 24.0
    score = max(0.0, min(100.0, score))
    if score >= 70:
        return score, "high_materiality"
    if score >= 40:
        return score, "medium_materiality"
    if score > 0:
        return score, "low_materiality"
    return score, "materiality_unknown"


def build_l2_core_primitives() -> list[dict[str, object]]:
    evidence = evidence_lookup()
    l1 = {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1324_candidate_l1_source_bindings.csv")}
    l2_rows = read_csv(TASK1318 / "task1325_candidate_l2_interpretation.csv")
    repeat_seen: dict[tuple[str, str], int] = defaultdict(int)
    rows = []
    for row in sorted(l2_rows, key=lambda item: (item["decision_asof_ts"], item["symbol"], int(item["candidate_rank"]))):
        cid = row["candidate_source_id"]
        bind = l1[cid]
        contract_ev = evidence.get(bind["contract_evidence_id"])
        ir_ev = evidence.get(bind["management_evidence_id"])
        contract_materiality, materiality_state = materiality_from_evidence(contract_ev, row["contract_revenue_state"])
        ir_materiality, _ = materiality_from_evidence(ir_ev, row["management_narrative_state"])
        materiality_score = max(contract_materiality, ir_materiality)

        key = (row["symbol"], row["full_candidate_composite_interpretation"])
        prior_repeat_count = repeat_seen[key]
        repeat_seen[key] += 1
        novelty_score = max(0.0, 32.0 - prior_repeat_count * 5.0)
        expectation_score = 0.0
        expectation_state = "analyst_gap_proxy_only"
        if row["contract_revenue_state"] == "validated_contract_or_order":
            expectation_score += 14.0
        if row["management_narrative_state"] == "specific_management_narrative":
            expectation_score += 10.0
        if row["market_acceptance_state"] == "price_gate_attached":
            expectation_score += 8.0
        surprise_score = max(0.0, min(100.0, novelty_score + expectation_score))
        if surprise_score >= 55:
            surprise_state = "fresh_expectation_change_proxy"
        elif surprise_score >= 25:
            surprise_state = "moderate_surprise_proxy"
        else:
            surprise_state = "stale_or_low_surprise_proxy"

        independent_sources = 0
        issuer_claim = 1 if bind["management_evidence_id"] or bind["contract_evidence_id"] or bind["survival_evidence_id"] else 0
        market_confirmed = 1 if row["market_acceptance_state"] == "price_gate_attached" else 0
        analyst_confirmed = 0
        customer_confirmed = 0
        regulator_confirmed = 1 if bind["survival_evidence_id"] and row["sec_survival_state"] == "terminal_distress" else 0
        independent_sources = issuer_claim + market_confirmed + analyst_confirmed + customer_confirmed + regulator_confirmed
        independence_score = min(100.0, independent_sources * 22.0)
        independence_state = "issuer_plus_market_only" if issuer_claim and market_confirmed else "issuer_only_or_gap"

        survival_penalty = 55.0 if row["sec_survival_state"] == "terminal_distress" else 12.0 if row["sec_survival_state"] == "watch_distress" else 0.0
        payoff_score = max(
            0.0,
            min(
                100.0,
                0.34 * materiality_score + 0.28 * surprise_score + 0.24 * independence_score + 0.14 * (100 - min(100, int(row["candidate_rank"]) * 2)) - survival_penalty,
            ),
        )
        if payoff_score >= 70:
            payoff_state = "high_payoff_candidate"
        elif payoff_score >= 45:
            payoff_state = "medium_payoff_candidate"
        elif payoff_score >= 25:
            payoff_state = "low_payoff_watch"
        else:
            payoff_state = "payoff_not_established"
        rows.append(
            {
                "task_id": "Task1361",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "full_candidate_composite_interpretation": row["full_candidate_composite_interpretation"],
                "materiality_score": round(materiality_score, 6),
                "materiality_state": materiality_state,
                "surprise_score": round(surprise_score, 6),
                "surprise_state": surprise_state,
                "expectation_state": expectation_state,
                "source_independence_score": round(independence_score, 6),
                "source_independence_state": independence_state,
                "issuer_claim_present": issuer_claim,
                "market_confirmed": market_confirmed,
                "analyst_confirmed": analyst_confirmed,
                "customer_confirmed": customer_confirmed,
                "regulator_confirmed": regulator_confirmed,
                "prior_repeat_count": prior_repeat_count,
                "payoff_score": round(payoff_score, 6),
                "payoff_state": payoff_state,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l3_mechanism_edges(primitives: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in primitives:
        mechanisms = [
            ("materiality", "contract_validates_revenue_acceleration" if row["materiality_state"] in {"high_materiality", "medium_materiality"} else "materiality_gap_caps_conviction"),
            ("surprise", "fresh_event_breaks_prior_expectation_proxy" if row["surprise_state"] == "fresh_expectation_change_proxy" else "stale_or_known_information_caps_alpha"),
            ("independence", "market_confirmation_adds_independent_vote" if row["market_confirmed"] == 1 else "issuer_only_claim_needs_confirmation"),
            ("survival", "hard_survival_event_invalidates_payoff" if row["full_candidate_composite_interpretation"] == "hard_survival_review_required" else "survival_watch_conditions_payoff"),
            ("payoff", "payoff_path_rankable" if row["payoff_state"] in {"high_payoff_candidate", "medium_payoff_candidate"} else "payoff_path_not_established"),
        ]
        for family, mechanism in mechanisms:
            rows.append(
                {
                    "task_id": "Task1362",
                    "mechanism_edge_id": f"MECH1362-{len(rows)+1:07d}",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "mechanism_family": family,
                    "mechanism_primitive": mechanism,
                    "relation_action": "reinforces" if "rankable" in mechanism or "validates" in mechanism or "confirmation" in mechanism or "fresh_event" in mechanism else "caps_confidence",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_replacement_pair_audit() -> list[dict[str, object]]:
    trades = read_csv(TASK1338 / "task1341_replay_trades.csv")
    old_by_decision = {row["decision_asof_ts"]: [] for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    for row in read_csv(TASK1201 / "task1205_slot_selections.csv"):
        if row["policy_variant_id"] == "l0_l3_slot10_v1":
            old_by_decision[row["decision_asof_ts"]].append(row["trade_spec_id"])
    trade_return = {row["trade_spec_id"]: to_float(row["net_return"]) for row in trades if row["policy_variant_id"] == "full_candidate_l2l3_replace_top10_v1"}
    spec_by_id = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    price = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    new_by_decision: dict[str, list[str]] = defaultdict(list)
    for row in trades:
        if row["policy_variant_id"] == "full_candidate_l2l3_replace_top10_v1":
            new_by_decision[row["decision_asof_ts"]].append(row["trade_spec_id"])
    rows = []
    for decision_ts, new_ids in sorted(new_by_decision.items()):
        old_ids = set(old_by_decision.get(decision_ts, [])[:10])
        new_set = set(new_ids)
        for trade_spec_id in sorted(new_set - old_ids):
            ret = trade_return.get(trade_spec_id, 0.0)
            rows.append(
                {
                    "task_id": "Task1360",
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": trade_spec_id,
                    "symbol": spec_by_id[trade_spec_id]["symbol"],
                    "audit_bucket": "new_replacement_winner" if ret > 0 else "new_replacement_loser",
                    "evaluation_net_return": round(ret, 8),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
        for trade_spec_id in sorted(old_ids - new_set):
            pg = price.get(trade_spec_id, {})
            ret = to_float(pg.get("exit_price")) / to_float(pg.get("entry_price")) - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if to_float(pg.get("entry_price")) > 0 else 0.0
            rows.append(
                {
                    "task_id": "Task1360",
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": trade_spec_id,
                    "symbol": spec_by_id[trade_spec_id]["symbol"],
                    "audit_bucket": "dropped_missed_winner" if ret > 0 else "dropped_correct_loser",
                    "evaluation_net_return": round(ret, 8),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_payoff_rank_panel(primitives: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in primitives:
        rank_preservation = max(0.0, 51.0 - to_float(row["candidate_rank"])) * 0.45
        score = to_float(row["payoff_score"]) * 0.72 + rank_preservation
        if row["source_independence_state"] == "issuer_only_or_gap":
            score -= 7.0
        if row["expectation_state"] == "analyst_gap_proxy_only":
            score -= 3.0
        by_decision[str(row["decision_asof_ts"])].append({**row, "payoff_rank_score": round(score, 6)})
    out = []
    for decision_ts, items in sorted(by_decision.items()):
        ranked = sorted(items, key=lambda row: (-to_float(row["payoff_rank_score"]), int(row["candidate_rank"]), str(row["symbol"])))
        for rank, row in enumerate(ranked, 1):
            out.append(
                {
                    "task_id": "Task1363",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "candidate_rank": row["candidate_rank"],
                    "derived_theme": row["derived_theme"],
                    "materiality_state": row["materiality_state"],
                    "surprise_state": row["surprise_state"],
                    "source_independence_state": row["source_independence_state"],
                    "payoff_state": row["payoff_state"],
                    "payoff_rank_score": row["payoff_rank_score"],
                    "payoff_rank_within_decision": rank,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return out


def load_submission_filings_for_cik(zip_file: zipfile.ZipFile, cik: str) -> list[dict[str, str]]:
    name = f"CIK{int(cik):010d}.json"
    if name not in zip_file.namelist():
        return []
    data = json.loads(zip_file.read(name))
    recent = data.get("filings", {}).get("recent", {})
    length = len(recent.get("accessionNumber", []))
    rows = []
    for i in range(length):
        form = str(recent.get("form", [""] * length)[i])
        rows.append(
            {
                "accession": recent.get("accessionNumber", [""] * length)[i],
                "form": form,
                "items": recent.get("items", [""] * length)[i],
                "acceptance_datetime": recent.get("acceptanceDateTime", [""] * length)[i],
            }
        )
    return rows


def build_dynamic_exit_receipts(policy_specs: list[dict[str, object]]) -> list[dict[str, object]]:
    selected = [row for row in policy_specs if row["selected_for_replay"] == "1"]
    ciks = {str(row["cik"]) for row in selected}
    with zipfile.ZipFile(SEC_ZIP) as zip_file:
        filings_by_cik = {cik: load_submission_filings_for_cik(zip_file, cik) for cik in ciks}
    rows = []
    for row in selected:
        entry = datetime.fromisoformat(str(row["entry_date"])).replace(tzinfo=timezone.utc)
        exit_dt = datetime.fromisoformat(str(row["exit_date"])).replace(tzinfo=timezone.utc)
        hard_event = None
        for filing in filings_by_cik.get(str(row["cik"]), []):
            accepted = parse_ts(filing["acceptance_datetime"])
            if not accepted or accepted <= entry or accepted >= exit_dt:
                continue
            items = filing.get("items", "")
            if filing["form"].startswith("8-K") and any(item in items for item in ["3.01", "2.04", "4.02", "2.05"]):
                hard_event = filing
                break
        rows.append(
            {
                "task_id": "Task1364",
                "policy_variant_id": row["policy_variant_id"],
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "entry_date": row["entry_date"],
                "scheduled_exit_date": row["exit_date"],
                "dynamic_exit_trigger": "post_entry_hard_sec_event" if hard_event else "scheduled_exit_no_post_entry_hard_event",
                "trigger_accession": hard_event["accession"] if hard_event else "",
                "trigger_form": hard_event["form"] if hard_event else "",
                "trigger_items": hard_event["items"] if hard_event else "",
                "trigger_available_to_brain_ts": hard_event["acceptance_datetime"] if hard_event else "",
                "dynamic_exit_ready": "1" if hard_event else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def select_policy_specs(rank_panel: list[dict[str, object]]) -> list[dict[str, object]]:
    base_specs = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    price_gate = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    old_top10: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(TASK1201 / "task1205_slot_selections.csv"):
        if row["policy_variant_id"] == "l0_l3_slot10_v1":
            old_top10[row["decision_asof_ts"]].append(row["trade_spec_id"])
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rank_panel:
        by_decision[str(row["decision_asof_ts"])].append(row)
    rows = []
    for policy_id, policy in POLICIES.items():
        slot_cap = int(policy["slot_cap"])
        for decision_ts, items in sorted(by_decision.items()):
            ranked = sorted(items, key=lambda row: int(row["payoff_rank_within_decision"]))
            if policy["mode"] == "pure_payoff":
                selected_ids = {row["trade_spec_id"] for row in ranked[:slot_cap]}
            else:
                selected_ids = set(old_top10.get(decision_ts, [])[:slot_cap])
                current = {row["trade_spec_id"]: row for row in ranked if row["trade_spec_id"] in selected_ids}
                contenders = [row for row in ranked if row["trade_spec_id"] not in selected_ids and row["payoff_state"] in {"high_payoff_candidate", "medium_payoff_candidate"}]
                for contender in contenders:
                    if not selected_ids:
                        break
                    weakest_id = min(selected_ids, key=lambda tid: to_float(current.get(tid, {"payoff_rank_score": 0})["payoff_rank_score"]))
                    weakest_score = to_float(current.get(weakest_id, {"payoff_rank_score": 0})["payoff_rank_score"])
                    if to_float(contender["payoff_rank_score"]) >= weakest_score + 18.0:
                        selected_ids.remove(weakest_id)
                        selected_ids.add(str(contender["trade_spec_id"]))
                        current[str(contender["trade_spec_id"])] = contender
                    if len(selected_ids) >= slot_cap:
                        selected_ids = set(sorted(selected_ids)[:slot_cap]) if len(selected_ids) > slot_cap else selected_ids
            for item in ranked:
                spec = base_specs[str(item["trade_spec_id"])]
                price = price_gate[str(item["trade_spec_id"])]
                rows.append(
                    {
                        "task_id": "Task1367",
                        "policy_spec_id": f"COREL5-1367-{len(rows)+1:07d}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": item["candidate_source_id"],
                        "trade_spec_id": item["trade_spec_id"],
                        "symbol": item["symbol"],
                        "cik": spec["cik"],
                        "decision_asof_ts": decision_ts,
                        "candidate_rank": item["candidate_rank"],
                        "payoff_rank_within_decision": item["payoff_rank_within_decision"],
                        "payoff_rank_score": item["payoff_rank_score"],
                        "payoff_state": item["payoff_state"],
                        "selected_for_replay": "1" if item["trade_spec_id"] in selected_ids else "0",
                        "entry_date": price["entry_date"],
                        "entry_price": price["entry_price"],
                        "exit_date": price["exit_date"],
                        "exit_price": price["exit_price"],
                        "price_gate_pass": price["price_gate_pass"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return rows


def run_replay(policy_specs: list[dict[str, object]], exit_receipts: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    receipt = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in exit_receipts}
    price_cache: dict[str, pd.DataFrame | None] = {}
    selected = [row for row in policy_specs if row["selected_for_replay"] == "1" and row["price_gate_pass"] == "1"]
    by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selected:
        by_policy[str(row["policy_variant_id"])].append(row)
    trades = []
    equity = []
    for policy_id, specs in sorted(by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            per_position = capital / len(items) if items else 0.0
            period_pnl = 0.0
            new_capital = 0.0
            for item in items:
                symbol = str(item["symbol"])
                if symbol not in price_cache:
                    price_cache[symbol] = load_price(symbol)
                dynamic = receipt.get((policy_id, item["trade_spec_id"]), {})
                exit_date = str(item["exit_date"])
                exit_price = to_float(item["exit_price"])
                exit_reason = "scheduled_exit"
                if dynamic.get("dynamic_exit_ready") == "1":
                    trigger_ts = parse_ts(str(dynamic["trigger_available_to_brain_ts"]))
                    if trigger_ts:
                        triggered = price_on_or_after(price_cache[symbol], trigger_ts.date() + timedelta(days=1))
                        if triggered:
                            exit_date, exit_price = triggered
                            exit_reason = "dynamic_exit_post_entry_hard_sec_event"
                entry = to_float(item["entry_price"])
                gross_return = exit_price / entry - 1.0 if entry > 0 else 0.0
                net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                pnl = per_position * net_return
                period_pnl += pnl
                new_capital += per_position + pnl
                trades.append(
                    {
                        "task_id": "Task1368",
                        "trade_id": f"CORETRADE1368-{len(trades)+1:07d}",
                        **item,
                        "actual_exit_date": exit_date,
                        "actual_exit_price": round(exit_price, 6),
                        "exit_reason": exit_reason,
                        "capital_allocated": round(per_position, 4),
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "exit_uses_post_entry_price_path": "1",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1369",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1201 / "task1207_replay_metrics.csv")}
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        slot = str(POLICIES[policy_id]["slot_cap"])
        baseline = base_metrics.get(f"l0_l3_slot{slot}_v1", base_metrics["l0_l3_slot5_v1"])
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        end = max(datetime.fromisoformat(str(row["actual_exit_date"])).date() for row in tr_rows)
        cagr_value = cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1370",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "baseline_slot_variant": baseline["policy_variant_id"],
                "baseline_final_equity": baseline["final_equity"],
                "baseline_delta": round(final - to_float(baseline["final_equity"]), 4),
                "beats_baseline_slot": "1" if final > to_float(baseline["final_equity"]) else "0",
                "benchmark_symbol": baseline["benchmark_symbol"],
                "benchmark_final_equity": baseline["benchmark_final_equity"],
                "benchmark_cagr": baseline["benchmark_cagr"],
                "beats_benchmark": "1" if final > to_float(baseline["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_overfit_guard(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    prior_variants = []
    for path in [
        TASK1201 / "task1207_replay_metrics.csv",
        ROOT / "data/artifacts/task_1288_1297_multisource_policy_replay/task1292_replay_metrics.csv",
        ROOT / "data/artifacts/task_1298_1317_l0_l5_trading_rule_strengthening/task1308_replay_metrics.csv",
        TASK1338 / "task1343_replay_metrics.csv",
    ]:
        if path.exists():
            prior_variants.extend(read_csv(path))
    rows = [
        {
            "task_id": "Task1365",
            "guard_id": "OVERFIT1365-001",
            "guard_name": "policy_attempt_count",
            "observed_value": len(prior_variants) + len(metrics),
            "risk_state": "high_overfit_risk_requires_oos_freeze",
            "action": "record policy freeze and do not tune on OOS metrics",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1365",
            "guard_id": "OVERFIT1365-002",
            "guard_name": "oos_tuning_block",
            "observed_value": "2025_2026q1_oos_score_only",
            "risk_state": "guard_active",
            "action": "OOS split rows cannot authorize parameter changes",
            "authority": AUTHORITY,
        },
    ]
    return rows


def write_report(metrics: list[dict[str, object]], gate: dict[str, object]) -> None:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task1358-1377 Trader Judgment Core Recovery

## Decision Summary

- Verdict: `trader_judgment_core_recovery_implemented_diagnostic_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: materiality, surprise/expectation proxy, source independence, mechanism edges, payoff rank, replacement audit, split freeze, overfit guard, and limited dynamic exit receipt were implemented.
- Next action: replace proxy surprise with PIT analyst/estimate data and expand dynamic exit beyond hard SEC events.

## Quant Expert Report

- Data source and source readiness: Task1318 full-candidate source evidence, Task1201 trade specs/price gates, SEC submissions metadata for post-entry hard-event receipt.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`, `evidence_id`.
- Leakage audit: L2-L4 assignment does not use future return, realized PnL, or exit price. Replacement outcome rows are marked audit-only. L5 dynamic exits use only post-entry SEC filing receipt before execution date.
- Split/OOS metrics: split calendar is frozen into train 2021-2023, validation 2024, OOS 2025-2026Q1. OOS tuning is blocked.
- Failure decomposition: analyst PIT, customer confirmation, and true expectation surprise remain gaps.
- Cost/slippage stress: round-trip cost remains {ROUND_TRIP_COST_BPS} bps.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['beats_baseline_slot']} | {row['beats_benchmark']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += """
## No-Background Decision-Maker Report

We restored the missing trader-judgment core as a diagnostic layer.

It now asks whether an event is material, fresh, independently confirmed, and tied to a payoff path.

The replay still does not approve the strategy.

## Artifact Manifest

- `task1358_core_requirement_map.csv`
- `task1359_split_freeze.csv`
- `task1360_replacement_pair_audit.csv`
- `task1361_l2_materiality_surprise_primitives.csv`
- `task1362_l3_mechanism_edges.csv`
- `task1363_l4_payoff_rank_panel.csv`
- `task1364_l5_dynamic_exit_receipts.csv`
- `task1365_overfit_guard_ledger.csv`
- `task1366_policy_catalog.csv`
- `task1367_l5_policy_specs.csv`
- `task1368_replay_trades.csv`
- `task1369_replay_equity.csv`
- `task1370_replay_metrics.csv`
- `task1372_acceptance_gate.csv`
- `task1377_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1358_1377_trader_judgment_core_recovery_validate.py`
- `python -m unittest tests.test_trader_brain_1358_1377_trader_judgment_core_recovery`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1358_1377_trader_judgment_core_recovery.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1358_1377_decision.csv", [gate])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    requirement = build_requirement_map()
    split = build_split_freeze()
    primitives = build_l2_core_primitives()
    mechanism = build_l3_mechanism_edges(primitives)
    replacement_audit = build_replacement_pair_audit()
    rank_panel = build_payoff_rank_panel(primitives)
    policy_catalog = [
        {
            "task_id": "Task1366",
            "policy_variant_id": policy_id,
            "slot_cap": spec["slot_cap"],
            "mode": spec["mode"],
            "assignment_inputs": "materiality;surprise_proxy;source_independence;payoff_score;candidate_rank",
            "forbidden_inputs": "future_return;realized_return;pnl;post_entry_price_path",
            "authority": AUTHORITY,
        }
        for policy_id, spec in POLICIES.items()
    ]
    policy_specs = select_policy_specs(rank_panel)
    dynamic_exit = build_dynamic_exit_receipts(policy_specs)
    trades, equity = run_replay(policy_specs, dynamic_exit)
    metrics = build_metrics(trades, equity)
    overfit = build_overfit_guard(metrics)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = {
        "task_id": "Task1372",
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "target_cagr_30pct_met": best["target_cagr_30pct_met"],
        "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "decision": "diagnostic_core_recovery_not_accepted",
        "authority": AUTHORITY,
    }
    closeout = {
        "task_id": "Task1377",
        "verdict": "trader_judgment_core_recovery_implemented_diagnostic_not_accepted",
        **gate,
        "l2_rows": len(primitives),
        "l3_rows": len(mechanism),
        "trade_rows": len(trades),
        "next_action": "attach PIT analyst expectation data and richer dynamic exit source receipts",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1358_core_requirement_map.csv", requirement)
    write_csv(OUT_DIR / "task1359_split_freeze.csv", split)
    write_csv(OUT_DIR / "task1360_replacement_pair_audit.csv", replacement_audit)
    write_csv(OUT_DIR / "task1361_l2_materiality_surprise_primitives.csv", primitives)
    write_csv(OUT_DIR / "task1362_l3_mechanism_edges.csv", mechanism)
    write_csv(OUT_DIR / "task1363_l4_payoff_rank_panel.csv", rank_panel)
    write_csv(OUT_DIR / "task1364_l5_dynamic_exit_receipts.csv", dynamic_exit)
    write_csv(OUT_DIR / "task1365_overfit_guard_ledger.csv", overfit)
    write_csv(OUT_DIR / "task1366_policy_catalog.csv", policy_catalog)
    write_csv(OUT_DIR / "task1367_l5_policy_specs.csv", policy_specs)
    write_csv(OUT_DIR / "task1368_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1369_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1370_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1372_acceptance_gate.csv", [gate])
    write_csv(OUT_DIR / "task1377_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1377_closeout.json", closeout)
    write_report(metrics, gate)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
