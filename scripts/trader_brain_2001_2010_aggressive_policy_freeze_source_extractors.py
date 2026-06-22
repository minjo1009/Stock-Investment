from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1961 = ROOT / "data/artifacts/task_1961_1970_free_source_acquisition"
TASK1971 = ROOT / "data/artifacts/task_1971_1980_free_source_l0_l5_replay"
TASK1991 = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
OUT_DIR = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
REPORT_DIR = ROOT / "docs/reports/task_2001_2010_aggressive_policy_freeze_source_extractors"
REPORT = REPORT_DIR / "task_2001_2010_aggressive_policy_freeze_source_extractors.md"
DECISION = REPORT_DIR / "task_2001_2010_decision.csv"
AUTHORITY = "DIAGNOSTIC_POLICY_FREEZE_AND_SOURCE_EXTRACTOR_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def parse_ts(value: str) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_inputs() -> dict[str, object]:
    return {
        "metrics": read_csv(TASK1991 / "task1998_winner_acceleration_replay_metrics.csv"),
        "trades": read_csv(TASK1991 / "task1997_winner_acceleration_replay_trades.csv"),
        "l1": read_csv(TASK1991 / "task1992_l1_winner_acceleration_packets.csv"),
        "l2": read_csv(TASK1991 / "task1993_l2_winner_acceleration_semantics.csv"),
        "l3": read_csv(TASK1991 / "task1994_l3_winner_acceleration_edges.csv"),
        "l4": read_csv(TASK1991 / "task1995_l4_winner_acceleration_thesis_cards.csv"),
        "l5": read_csv(TASK1991 / "task1996_l5_winner_acceleration_decisions.csv"),
        "sec_guidance": read_csv(TASK1961 / "task1965_sec_guidance_expanded_receipt_ledger.csv"),
        "free_l2": read_csv(TASK1971 / "task1973_l2_free_source_semantics.csv"),
        "sec_packets": read_csv(TASK1834 / "task1836_sec_financing_dilution_source_packets.csv"),
        "sec_dilution": read_csv(TASK1834 / "task1837_financing_dilution_extractor_contract.csv"),
        "sec_dilution_links": read_csv(TASK1834 / "task1842_sec_dilution_decision_asof_links.csv"),
    }


def policy_freeze_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    metric = next(row for row in inputs["metrics"] if row["policy_variant_id"] == POLICY_ID)
    frozen_spec = {
        "policy_variant_id": POLICY_ID,
        "source_policy_variant_id": "winner_defense_budget_top5_v1",
        "candidate_pool": "top5_pool",
        "select_top_n": 2,
        "base_divisor": 2,
        "concentration_mode": "top5_pool_top2_convex",
        "rank_order": ["winner_acceleration_rank_score", "winner_acceleration_score"],
        "max_multiplier": 1.42,
        "thesis_break_exit_rule": "cap_raw_multiplier_to_0_45_when_thesis_break_exit_flag_is_1",
        "no_post_result_tuning": True,
        "source_depth_status": "requires_full_external_extractor_before_paper_shadow_promotion",
    }
    spec_hash = stable_hash(frozen_spec)
    return [
        {
            "task_id": "Task2001",
            "freeze_id": "POLICYFREEZE-2001-001",
            "policy_variant_id": POLICY_ID,
            "frozen_policy_spec_hash": spec_hash,
            "source_policy_variant_id": frozen_spec["source_policy_variant_id"],
            "select_top_n": frozen_spec["select_top_n"],
            "base_divisor": frozen_spec["base_divisor"],
            "max_multiplier": frozen_spec["max_multiplier"],
            "concentration_mode": frozen_spec["concentration_mode"],
            "frozen_final_equity": metric["final_equity"],
            "frozen_cagr": metric["cagr"],
            "frozen_max_drawdown": metric["max_drawdown"],
            "policy_change_permission": "blocked_without_new_task_and_new_hash",
            "paper_shadow_permission": "blocked_until_source_extractor_gate_passes",
            "real_capital_permission": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def freeze_manifest_rows() -> list[dict[str, object]]:
    paths = [
        TASK1991 / "task1997_winner_acceleration_replay_trades.csv",
        TASK1991 / "task1997_winner_acceleration_replay_equity.csv",
        TASK1991 / "task1998_winner_acceleration_replay_metrics.csv",
        TASK1991 / "task1995_l4_winner_acceleration_thesis_cards.csv",
        TASK1991 / "task1996_l5_winner_acceleration_decisions.csv",
        ROOT / "scripts/trader_brain_1991_2000_winner_acceleration_surgery.py",
    ]
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "task_id": "Task2002",
                "freeze_manifest_id": f"FREEZEMANIFEST-2002-{idx:03d}",
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "exists": "1" if path.exists() else "0",
                "sha256": file_hash(path) if path.exists() else "",
                "freeze_role": "policy_replay_dependency",
                "mutation_allowed": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_family_contract_rows() -> list[dict[str, object]]:
    families = [
        ("sec_guidance", "issuer-public SEC filing text", "active_extractor_attached", "support_only_not_analyst_revision"),
        ("sec_financing_dilution", "SEC financing/dilution raw filing text", "active_extractor_attached", "risk_and_invalidation"),
        ("alfred_fred_macro", "FRED/ALFRED vintage macro state", "active_prior_task_attached", "risk_budget_context_only"),
        ("price_volume", "Yahoo public daily price cross-check", "audit_only_attached", "not_assignment_grade_market_receipt"),
        ("ir_ceo_press_release", "issuer IR/CEO public statements", "source_gap_gate", "required_before_paper_shadow_promotion"),
        ("earnings_call_transcript", "earnings call and Q&A transcript", "source_gap_gate", "required_before_paper_shadow_promotion"),
        ("contract_customer_confirmation", "customer-side contract/order confirmation", "source_gap_gate", "required_before_paper_shadow_promotion"),
        ("policy_news_external_catalyst", "policy/news/geopolitical catalyst", "source_gap_gate", "required_before_paper_shadow_promotion"),
        ("analyst_revision_consensus", "PIT analyst revision/consensus", "vendor_gate", "not_free_certified"),
    ]
    return [
        {
            "task_id": "Task2003",
            "source_family_contract_id": f"SRCFAM-2003-{idx:03d}",
            "source_family": family,
            "definition": definition,
            "extractor_status": status,
            "permission_or_blocker": blocker,
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, definition, status, blocker) in enumerate(families, start=1)
    ]


def first_or_empty(rows: list[dict[str, str]]) -> dict[str, str]:
    return rows[0] if rows else {}


def source_indexes(inputs: dict[str, object]) -> dict[str, object]:
    by_spec = defaultdict(list)
    for row in inputs["sec_guidance"]:
        by_spec[row["trade_spec_id"]].append(row)
    sec_packets = defaultdict(list)
    for row in inputs["sec_packets"]:
        sec_packets[row["trade_spec_id"]].append(row)
    dilution_by_packet = {row["financing_source_packet_id"]: row for row in inputs["sec_dilution"]}
    dilution_link = {row["trade_spec_id"]: row for row in inputs["sec_dilution_links"]}
    free_l2 = {row["trade_spec_id"]: row for row in inputs["free_l2"]}
    l1 = {row["trade_spec_id"]: row for row in inputs["l1"]}
    l2 = {row["trade_spec_id"]: row for row in inputs["l2"]}
    l4 = {row["trade_spec_id"]: row for row in inputs["l4"]}
    l5 = {row["trade_spec_id"]: row for row in inputs["l5"]}
    return {
        "sec_guidance": by_spec,
        "sec_packets": sec_packets,
        "dilution_by_packet": dilution_by_packet,
        "dilution_link": dilution_link,
        "free_l2": free_l2,
        "l1": l1,
        "l2": l2,
        "l4": l4,
        "l5": l5,
    }


def extraction_rows(inputs: dict[str, object], idxs: dict[str, object]) -> list[dict[str, object]]:
    policy_trades = [row for row in inputs["trades"] if row["policy_variant_id"] == POLICY_ID]
    rows = []
    for idx, trade in enumerate(policy_trades, start=1):
        spec = trade["trade_spec_id"]
        decision = parse_ts(trade["decision_asof_ts"])
        sec_guidance = idxs["sec_guidance"].get(spec, [])
        guidance_before = [
            row for row in sec_guidance
            if row.get("asof_guard_pass") == "1" and parse_ts(row.get("available_to_brain_ts", "")) and decision and parse_ts(row["available_to_brain_ts"]) <= decision
        ]
        guidance = first_or_empty(guidance_before)

        packet_link = idxs["dilution_link"].get(spec, {})
        packet = {}
        dil = {}
        if packet_link and packet_link.get("latest_financing_source_packet_id"):
            packet_id = packet_link["latest_financing_source_packet_id"]
            packet = first_or_empty([row for row in idxs["sec_packets"].get(spec, []) if row["financing_source_packet_id"] == packet_id])
            dil = idxs["dilution_by_packet"].get(packet_id, {})
        free = idxs["free_l2"].get(spec, {})
        l1 = idxs["l1"].get(spec, {})
        l2 = idxs["l2"].get(spec, {})
        l4 = idxs["l4"].get(spec, {})
        l5 = idxs["l5"].get(spec, {})

        family_count = 0
        family_count += 1 if guidance_before else 0
        family_count += 1 if dil else 0
        family_count += 1 if free.get("macro_assignment_permission") == "active_small_adjustment_certified_fred_only" else 0
        family_count += 1 if free.get("price_crosscheck_state") and free.get("price_crosscheck_state") != "price_crosscheck_gap" else 0

        rows.append(
            {
                "task_id": "Task2004",
                "source_extraction_id": f"SRCEXTRACT-2004-{idx:06d}",
                "policy_variant_id": POLICY_ID,
                "trade_spec_id": spec,
                "candidate_source_id": trade["candidate_source_id"],
                "symbol": trade["symbol"],
                "decision_asof_ts": trade["decision_asof_ts"],
                "beneficiary_chain": trade["beneficiary_chain"],
                "winner_acceleration_state": trade["winner_acceleration_state"],
                "winner_thesis_state": trade["winner_thesis_state"],
                "sec_guidance_extractor_state": "attached_asof" if guidance_before else "source_gap",
                "sec_guidance_packet_count": len(guidance_before),
                "sec_guidance_keyword_families": guidance.get("guidance_keyword_families", ""),
                "sec_guidance_available_to_brain_ts": guidance.get("available_to_brain_ts", ""),
                "sec_guidance_local_path": guidance.get("local_path", ""),
                "sec_guidance_sha256": guidance.get("sha256", ""),
                "sec_dilution_extractor_state": dil.get("dilution_pressure_state", "source_gap"),
                "sec_dilution_signal_families": dil.get("dilution_signal_families", ""),
                "sec_dilution_available_to_brain_ts": packet.get("available_to_brain_ts", ""),
                "sec_dilution_local_path": packet.get("local_path", ""),
                "sec_dilution_sha256": packet.get("sha256", ""),
                "macro_extractor_state": free.get("macro_assignment_permission", "source_gap"),
                "macro_rate_state": free.get("macro_rate_state", ""),
                "macro_liquidity_state": free.get("macro_liquidity_state", ""),
                "price_volume_extractor_state": "audit_only_" + free.get("price_crosscheck_state", "source_gap"),
                "analyst_revision_certified": free.get("analyst_revision_certified", "0"),
                "ir_ceo_extractor_state": "source_gap_gate",
                "earnings_call_extractor_state": "source_gap_gate",
                "contract_customer_extractor_state": "source_gap_gate",
                "policy_news_extractor_state": "source_gap_gate",
                "active_or_audit_family_count": family_count,
                "l1_packet_id": l1.get("l1_packet_id", ""),
                "l2_semantic_id": l2.get("l2_semantic_id", ""),
                "l4_thesis_id": l4.get("l4_thesis_id", ""),
                "l5_decision_id": l5.get("l5_decision_id", ""),
                "source_depth_gate_pass": "1" if family_count >= 3 and guidance_before and free.get("macro_assignment_permission") == "active_small_adjustment_certified_fred_only" else "0",
                "paper_shadow_source_gate_pass": "0",
                "current_2026_direct_input_used": "0",
                "inferred_matching_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def l0_l5_bridge_rows(extracts: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    l1_rows = []
    l2_rows = []
    l3_rows = []
    l4_rows = []
    l5_rows = []
    edge_idx = 1
    for idx, row in enumerate(extracts, start=1):
        l1_rows.append(
            {
                "task_id": "Task2005",
                "l1_full_source_packet_id": f"FULLL1-2005-{idx:06d}",
                "source_extraction_id": row["source_extraction_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "attached_source_families": "|".join(
                    family for family, state in [
                        ("sec_guidance", row["sec_guidance_extractor_state"]),
                        ("sec_dilution", row["sec_dilution_extractor_state"]),
                        ("macro", row["macro_extractor_state"]),
                        ("price_volume_audit", row["price_volume_extractor_state"]),
                    ]
                    if state and "gap" not in str(state)
                ),
                "active_or_audit_family_count": row["active_or_audit_family_count"],
                "source_depth_gate_pass": row["source_depth_gate_pass"],
                "paper_shadow_source_gate_pass": row["paper_shadow_source_gate_pass"],
                "current_2026_direct_input_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        positive = 0
        negative = 0
        if row["sec_guidance_extractor_state"] == "attached_asof":
            positive += 1
        if row["macro_extractor_state"] == "active_small_adjustment_certified_fred_only":
            positive += 1
        if row["sec_dilution_extractor_state"] in {"active_financing_pressure", "dilution_pressure"}:
            negative += 1
        if "raw_price_sustained_acceptance" in str(row["price_volume_extractor_state"]):
            positive += 1
        l2_state = "source_supported_winner_acceleration" if positive >= 2 and negative == 0 else "mixed_or_incomplete_source_support"
        if negative >= 1:
            l2_state = "source_supported_risk_cap"
        l2_rows.append(
            {
                "task_id": "Task2006",
                "l2_full_source_semantic_id": f"FULLL2-2006-{idx:06d}",
                "source_extraction_id": row["source_extraction_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "semantic_state": l2_state,
                "positive_source_family_count": positive,
                "negative_source_family_count": negative,
                "source_gap_family_count": 4 - min(4, int(row["active_or_audit_family_count"])),
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        mechanisms = []
        if row["sec_guidance_extractor_state"] == "attached_asof":
            mechanisms.append(("issuer_guidance_supports_winner_thesis", "supports"))
        if row["macro_extractor_state"] == "active_small_adjustment_certified_fred_only":
            mechanisms.append(("macro_vintage_context_routes_risk_budget", "routes"))
        if row["sec_dilution_extractor_state"] in {"active_financing_pressure", "dilution_pressure"}:
            mechanisms.append(("financing_dilution_caps_concentration", "caps"))
        if "raw_price_sustained_acceptance" in str(row["price_volume_extractor_state"]):
            mechanisms.append(("price_acceptance_audit_confirms_but_not_assignment", "audit_support"))
        if not mechanisms:
            mechanisms.append(("source_gap_blocks_paper_shadow_promotion", "blocks"))
        for mechanism, relation in mechanisms:
            l3_rows.append(
                {
                    "task_id": "Task2007",
                    "l3_full_source_edge_id": f"FULLL3-2007-{edge_idx:07d}",
                    "source_extraction_id": row["source_extraction_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "mechanism_edge": mechanism,
                    "relation_type": relation,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            edge_idx += 1
        l4_rows.append(
            {
                "task_id": "Task2008",
                "l4_full_source_thesis_id": f"FULLL4-2008-{idx:06d}",
                "source_extraction_id": row["source_extraction_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "winner_thesis_state": row["winner_thesis_state"],
                "full_source_thesis_state": "paper_shadow_blocked_source_gaps" if row["paper_shadow_source_gate_pass"] == "0" else "paper_shadow_source_supported",
                "primary_blocker": "missing_ir_call_customer_policy_news_or_assignment_grade_price" if row["paper_shadow_source_gate_pass"] == "0" else "",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l5_rows.append(
            {
                "task_id": "Task2009",
                "l5_paper_shadow_readiness_id": f"PAPERGATE-2009-{idx:06d}",
                "source_extraction_id": row["source_extraction_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "frozen_policy_variant_id": POLICY_ID,
                "frozen_policy_trade_allowed_in_diagnostic_replay": "1",
                "paper_shadow_trade_allowed": row["paper_shadow_source_gate_pass"],
                "real_capital_trade_allowed": "0",
                "blocker": "full_source_extractor_gate_not_complete" if row["paper_shadow_source_gate_pass"] == "0" else "",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return l1_rows, l2_rows, l3_rows, l4_rows, l5_rows


def summary_rows(extracts: list[dict[str, object]], policy_freeze: list[dict[str, object]]) -> list[dict[str, object]]:
    total = len(extracts)
    sec_guidance = sum(1 for row in extracts if row["sec_guidance_extractor_state"] == "attached_asof")
    dilution = sum(1 for row in extracts if row["sec_dilution_extractor_state"] not in {"source_gap", ""})
    macro = sum(1 for row in extracts if row["macro_extractor_state"] == "active_small_adjustment_certified_fred_only")
    price = sum(1 for row in extracts if "gap" not in str(row["price_volume_extractor_state"]))
    depth_pass = sum(1 for row in extracts if row["source_depth_gate_pass"] == "1")
    paper_pass = sum(1 for row in extracts if row["paper_shadow_source_gate_pass"] == "1")
    return [
        {
            "task_id": "Task2010",
            "verdict": "aggressive_policy_frozen_full_source_extractor_bridge_partial",
            "frozen_policy_variant_id": POLICY_ID,
            "frozen_policy_spec_hash": policy_freeze[0]["frozen_policy_spec_hash"],
            "aggressive_trade_count": total,
            "sec_guidance_attached_rows": sec_guidance,
            "sec_dilution_attached_rows": dilution,
            "macro_attached_rows": macro,
            "price_volume_audit_rows": price,
            "source_depth_gate_pass_rows": depth_pass,
            "paper_shadow_source_gate_pass_rows": paper_pass,
            "paper_shadow_policy_status": "BLOCKED_UNTIL_FULL_SOURCE_EXTRACTOR_GATE",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(summary: dict[str, object], policy_freeze: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Task2001-2010 Aggressive Policy Freeze And Source Extractors

## Decision Summary

- Verdict: `{summary['verdict']}`.
- Frozen policy: `{POLICY_ID}`.
- Frozen policy hash: `{policy_freeze['frozen_policy_spec_hash']}`.
- Frozen result: final {policy_freeze['frozen_final_equity']}, CAGR {policy_freeze['frozen_cagr']}, MDD {policy_freeze['frozen_max_drawdown']}.
- Aggressive replay trades checked: {summary['aggressive_trade_count']}.
- SEC guidance attached rows: {summary['sec_guidance_attached_rows']}.
- SEC dilution/financing attached rows: {summary['sec_dilution_attached_rows']}.
- ALFRED/FRED macro attached rows: {summary['macro_attached_rows']}.
- Price/volume audit rows: {summary['price_volume_audit_rows']}.
- Paper shadow source gate pass rows: {summary['paper_shadow_source_gate_pass_rows']}.
- Paper shadow policy status: `{summary['paper_shadow_policy_status']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

The aggressive policy is now frozen. Rule, dependency, and replay artifact hashes are recorded so later work cannot silently tune the policy after seeing results.

Source extractor status:

- SEC issuer guidance extractor is attached where exact trade-spec/CIK/accession rows exist.
- SEC financing/dilution extractor is attached where prior Task1834 source packets exist.
- ALFRED/FRED macro state is attached from prior vintage-certified macro logic.
- Price/volume remains audit-only and is not treated as assignment-grade market receipt.
- IR/CEO, earnings call, customer contract confirmation, policy/news, and PIT analyst revision are still gated.

This means the policy is frozen, but not yet eligible for paper-shadow automation under the stricter full-source gate.

## No-Background Decision-Maker Report

1. 공격형 룰은 고정했다.
2. 성과 좋은 숫자를 보고 몰래 룰을 바꾸지 못하게 hash를 찍었다.
3. SEC/FRED/가격감사용 extractor는 붙였다.
4. IR/실적콜/고객확인/뉴스/애널리스트는 아직 부족하다.
5. 그래서 모의계좌 자동투입은 아직 `BLOCKED`다.

## Artifact Manifest

- `task2001_aggressive_policy_freeze.csv`
- `task2002_policy_freeze_manifest.csv`
- `task2003_source_family_contract.csv`
- `task2004_aggressive_source_extraction_panel.csv`
- `task2005_l1_full_source_packets.csv`
- `task2006_l2_full_source_semantics.csv`
- `task2007_l3_full_source_edges.csv`
- `task2008_l4_full_source_thesis.csv`
- `task2009_l5_paper_shadow_readiness.csv`
- `task2010_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2001," in text:
        return
    titles = {
        2001: "Aggressive Policy Freeze",
        2002: "Policy Freeze Manifest",
        2003: "Full Source Family Contract",
        2004: "Aggressive Source Extraction Panel",
        2005: "Full Source L1 Packets",
        2006: "Full Source L2 Semantics",
        2007: "Full Source L3 Edges",
        2008: "Full Source L4 Thesis",
        2009: "Paper Shadow Readiness Gate",
        2010: "Freeze Extractor Closeout",
    }
    rows = []
    for task_num in range(2001, 2011):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / L0-L5 Trader Brain",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "policy-frozen-source-extractor-partial-paper-blocked",
                "parent_task": "Task2000" if task_num == 2001 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2001_2010_aggressive_policy_freeze_source_extractors/task_2001_2010_aggressive_policy_freeze_source_extractors.md",
                "key_decision": "docs/reports/task_2001_2010_aggressive_policy_freeze_source_extractors/task_2001_2010_decision.csv",
                "key_artifacts": "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors",
                "validation_command": "python scripts/trader_brain_2001_2010_aggressive_policy_freeze_source_extractors_validate.py",
                "notes": "Freezes aggressive winner acceleration policy and attaches available source extractors while blocking paper shadow until full source gate passes.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(summary: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "100. Task2001-Task2010"
    row = (
        f"100. Task2001-Task2010 froze aggressive policy `{POLICY_ID}` and attached available full-source extractor bridges: "
        f"{summary['aggressive_trade_count']} aggressive trades checked, SEC guidance {summary['sec_guidance_attached_rows']}, "
        f"SEC financing/dilution {summary['sec_dilution_attached_rows']}, macro {summary['macro_attached_rows']}, "
        f"price audit {summary['price_volume_audit_rows']}, but paper shadow remains BLOCKED until IR/call/customer/news/analyst or equivalent full-source gates are satisfied; "
        "strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker not in text:
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for idx, line in enumerate(lines):
            if line.startswith("99. Task1991-Task2000"):
                insert_at = idx + 1
                break
        lines.insert(insert_at, row)
        path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    idxs = source_indexes(inputs)
    freeze = policy_freeze_rows(inputs)
    freeze_manifest = freeze_manifest_rows()
    source_contract = source_family_contract_rows()
    extracts = extraction_rows(inputs, idxs)
    l1, l2, l3, l4, l5 = l0_l5_bridge_rows(extracts)
    summary = summary_rows(extracts, freeze)

    write_csv(OUT_DIR / "task2001_aggressive_policy_freeze.csv", freeze)
    write_csv(OUT_DIR / "task2002_policy_freeze_manifest.csv", freeze_manifest)
    write_csv(OUT_DIR / "task2003_source_family_contract.csv", source_contract)
    write_csv(OUT_DIR / "task2004_aggressive_source_extraction_panel.csv", extracts)
    write_csv(OUT_DIR / "task2005_l1_full_source_packets.csv", l1)
    write_csv(OUT_DIR / "task2006_l2_full_source_semantics.csv", l2)
    write_csv(OUT_DIR / "task2007_l3_full_source_edges.csv", l3)
    write_csv(OUT_DIR / "task2008_l4_full_source_thesis.csv", l4)
    write_csv(OUT_DIR / "task2009_l5_paper_shadow_readiness.csv", l5)
    write_csv(OUT_DIR / "task2010_closeout.csv", summary)
    write_json(OUT_DIR / "task2010_closeout.json", summary[0])
    write_csv(DECISION, summary)
    write_report(summary[0], freeze[0])
    update_registry()
    update_operating_state(summary[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        f"[TASK2001_2010_OK] frozen={POLICY_ID} trades={summary[0]['aggressive_trade_count']} "
        f"paper_gate={summary[0]['paper_shadow_source_gate_pass_rows']}"
    )


if __name__ == "__main__":
    main()
