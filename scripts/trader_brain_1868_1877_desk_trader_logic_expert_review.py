from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1848 = ROOT / "data/artifacts/task_1848_1867_source_attached_policy_replay"
OUT_DIR = ROOT / "data/artifacts/task_1868_1877_desk_trader_logic_expert_review"
REPORT_DIR = ROOT / "docs/reports/task_1868_1877_desk_trader_logic_expert_review"
REPORT = REPORT_DIR / "task_1868_1877_desk_trader_logic_expert_review.md"
DECISION = REPORT_DIR / "task_1868_1877_decision.csv"
AUTHORITY = "DIAGNOSTIC_DESK_TRADER_LOGIC_EXPERT_REVIEW_ONLY"


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


def source_context_rows() -> list[dict[str, object]]:
    rows = [
        (
            "winner_compounder",
            "AQR Quality Minus Junk",
            "https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Monthly",
            "Quality is built from profitability, growth, safety, and payout; winner desk needs quality defense before macro trim.",
        ),
        (
            "winner_compounder",
            "AQR Value and Momentum Everywhere",
            "https://www.aqr.com/Insights/Datasets/Value-and-Momentum-Everywhere-Factors-Monthly",
            "Momentum is a persistent cross-market phenomenon; winner volatility must be separated from thesis break.",
        ),
        (
            "winner_compounder",
            "Fama-French 5 Factors",
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_5_factors_2x3.html",
            "Profitability and investment context should support quality-beta and overinvestment risk checks.",
        ),
        (
            "cyclical_beta",
            "FRED DGS10",
            "https://fred.stlouisfed.org/series/DGS10",
            "Rates regime is valid for cyclical and duration-sensitive sleeves, but must be applied as regime context not blanket trim.",
        ),
        (
            "cyclical_beta",
            "ALFRED",
            "https://alfred.stlouisfed.org/",
            "True vintage macro data should replace latest-vintage rates before any acceptance claim.",
        ),
        (
            "speculative_event",
            "SEC Form 8-K",
            "https://www.sec.gov/files/form8-k.pdf",
            "Items like financing obligations and unregistered equity sales matter, but form presence alone is not active dilution.",
        ),
        (
            "speculative_event",
            "SEC EDGAR APIs",
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
            "Exact filing source timestamps and accession lineage should remain the source-of-truth.",
        ),
        (
            "defensive_quality",
            "FINRA Margin Statistics",
            "https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics",
            "Liquidity/leverage context can help defensive desk, but current local feed is snapshot-only and cannot drive daily PIT claims.",
        ),
        (
            "all_desks",
            "MacKinlay Event Studies",
            "https://www.jstor.org/stable/2329131",
            "Event impact should be judged by abnormal-return logic and event windows, not by source presence alone.",
        ),
    ]
    return [
        {
            "task_id": "Task1869",
            "source_context_id": f"DESKSRC-1869-{idx:03d}",
            "desk": desk,
            "source_name": name,
            "source_url": url,
            "review_implication": implication,
            "authority": AUTHORITY,
        }
        for idx, (desk, name, url, implication) in enumerate(rows, 1)
    ]


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("PM/CIO", "7-how direction is right, but must become desk-specific permission logic, not global trim.", "adopt_with_rewrite"),
        ("Winner Trader", "Winner desk needs thesis-intact override: macro stress alone cannot trim high-quality winner.", "critical_gap"),
        ("Rates Trader", "Rates are regime context; use only when sleeve is rate-sensitive or liquidity stress is confirmed.", "tighten"),
        ("Capital Markets Trader", "SEC active financing pressure is over-broad; distinguish live offering, shelf capacity, historical closed financing, boilerplate.", "critical_gap"),
        ("Earnings Analyst", "Winner desk cannot become trader-grade without PIT revision/guidance; until then earnings stays source_gap, not negative.", "blocked"),
        ("Sector Specialist", "Sector breadth must distinguish isolated issuer break from broad theme drawdown.", "required_next"),
        ("Risk Officer", "MDD improved but CAGR loss means current guard is too blunt; require damage specificity before trim.", "tighten"),
        ("Backend Validator", "No outcome/PnL/drawdown fields can enter next assignment. Use source flags and frozen rule only.", "adopt"),
    ]
    return [
        {
            "task_id": "Task1868",
            "expert_review_id": f"DESKEXPERT-1868-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "verdict": verdict,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, verdict) in enumerate(rows, 1)
    ]


def current_failure_rows() -> list[dict[str, object]]:
    budget = read_csv(TASK1848 / "task1855_l5_source_attached_budget.csv")
    metrics = read_csv(TASK1848 / "task1858_source_attached_replay_metrics.csv")
    by_sleeve_action = Counter((row["strategy_sleeve"], row["source_attached_action"]) for row in budget)
    by_sleeve_dilution = Counter((row["strategy_sleeve"], row["dilution_pressure_state"]) for row in budget)
    rows: list[dict[str, object]] = []
    idx = 1
    for (sleeve, action), count in sorted(by_sleeve_action.items()):
        rows.append(
            {
                "task_id": "Task1870",
                "diagnosis_id": f"DESKDIAG-1870-{idx:03d}",
                "diagnosis_type": "sleeve_action_distribution",
                "desk": sleeve,
                "bucket": action,
                "row_count": count,
                "diagnosis": "over_trim_risk" if action == "trim" and sleeve == "winner_compounder" else "review",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for (sleeve, state), count in sorted(by_sleeve_dilution.items()):
        rows.append(
            {
                "task_id": "Task1870",
                "diagnosis_id": f"DESKDIAG-1870-{idx:03d}",
                "diagnosis_type": "sleeve_dilution_distribution",
                "desk": sleeve,
                "bucket": state,
                "row_count": count,
                "diagnosis": "sec_signal_too_broad" if state == "active_financing_pressure" and count > 20 else "review",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for metric in metrics:
        rows.append(
            {
                "task_id": "Task1870",
                "diagnosis_id": f"DESKDIAG-1870-{idx:03d}",
                "diagnosis_type": "replay_metric",
                "desk": metric["policy_variant_id"],
                "bucket": "source_attached_vs_baseline",
                "row_count": metric["trade_count"],
                "diagnosis": f"final_delta={metric['delta_final_equity']};mdd_delta={metric['delta_mdd']}",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def seven_how_matrix_rows() -> list[dict[str, object]]:
    rows = [
        (1, "desk mission fixed", "valid", "must map each desk to allowed source families and forbidden actions"),
        (2, "desk question differs", "valid", "needs explicit input checklist per desk"),
        (3, "same info interpreted differently", "valid_but_underimplemented", "current SEC financing penalizes almost every desk too broadly"),
        (4, "L2/L3 cause decomposition", "critical", "must split macro selloff thesis intact vs issuer damage vs live financing overhang"),
        (5, "L4 desk checklist", "critical", "winner/speculative/cyclical/defensive cards need separate required fields"),
        (6, "L5 thesis-state action", "valid_but_underimplemented", "current trim is source-state broad, not thesis-state specific"),
        (7, "desk attribution learning", "valid", "use outcome only for audit and rule design, not assignment"),
    ]
    return [
        {
            "task_id": "Task1871",
            "how_step": step,
            "how_name": name,
            "expert_verdict": verdict,
            "required_upgrade": upgrade,
            "authority": AUTHORITY,
        }
        for step, name, verdict, upgrade in rows
    ]


def desk_requirement_rows() -> list[dict[str, object]]:
    rows = [
        ("winner_compounder", "thesis_intact_override", "quality_beta + momentum + revenue/guidance confirmation + no live dilution", "hold_or_add_allowed_even_under_macro_stress"),
        ("winner_compounder", "thesis_break_detector", "issuer-specific reversal + guidance/revision break + margin/cash deterioration", "trim_reduce_only_when_break_confirmed"),
        ("cyclical_beta", "regime_permission", "rates trend + liquidity + sector breadth + relative strength", "enter_only_when_regime_confirms"),
        ("cyclical_beta", "macro_exit", "valuation compression + sector breadth deterioration", "trim_reduce_when_regime_turns"),
        ("speculative_event", "live_financing_block", "SEC active offering/ATM/convertible/warrant + cash runway", "cap_or_no_entry"),
        ("speculative_event", "catalyst_quality", "customer/regulator/contract confirmation + event date", "small_size_hold_only_if_catalyst_valid"),
        ("defensive_quality", "buffer_validation", "low vol + liquidity + profitability/cash stability", "hold_as_buffer"),
        ("defensive_quality", "defensive_failure", "defensive stock falls with no buffer behavior", "remove_from_defensive_sleeve"),
    ]
    return [
        {
            "task_id": "Task1872",
            "desk_requirement_id": f"DESKREQ-1872-{idx:03d}",
            "desk": desk,
            "requirement": requirement,
            "required_inputs": inputs,
            "allowed_action_effect": action,
            "authority": AUTHORITY,
        }
        for idx, (desk, requirement, inputs, action) in enumerate(rows, 1)
    ]


def acceptance_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("no_global_trim", "winner_compounder cannot be trim by default under neutral/supportive liquidity"),
        ("sec_specificity", "active_financing_pressure must require live/current financing terms or remain watch/source_gap"),
        ("earnings_block", "earnings revision remains blocked until PIT vendor/public timestamped feed exists"),
        ("sector_breadth_required", "cyclical and winner volatility diagnosis needs sector breadth from existing OHLC first"),
        ("audit_only_outcomes", "PnL/drawdown/result deltas are audit-only and cannot enter assignment"),
        ("frozen_policy_before_replay", "next replay needs one preregistered desk-specific policy"),
    ]
    return [
        {
            "task_id": "Task1873",
            "acceptance_rule_id": f"DESKGATE-1873-{idx:03d}",
            "rule": rule,
            "meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (rule, meaning) in enumerate(rows, 1)
    ]


def next_task_rows() -> list[dict[str, object]]:
    rows = [
        ("Task1878", "SEC Financing Specificity Repair", "Capital Markets / Quant Engineering", "Split active/live financing from historical closed financing and boilerplate"),
        ("Task1879", "Winner Thesis Intact Override", "Winner Desk", "Prevent macro/source broad trim when quality/momentum/thesis intact"),
        ("Task1880", "Sector Breadth Local Attachment", "Regime Research", "Build sector/theme breadth from existing OHLC and predeclared mappings"),
        ("Task1881", "Cyclical Regime Permission", "Rates/Cyclical Desk", "Require rate/liquidity/sector confirmation for cyclical beta"),
        ("Task1882", "Speculative Live Financing Block", "Capital Markets Desk", "No-entry/cap only when live dilution/financing pressure is source-specific"),
        ("Task1883", "Defensive Buffer Validation", "Risk Desk", "Validate defensive sleeve behaves as buffer, not weak-stock parking lot"),
        ("Task1884", "Desk-Specific Frozen Policy", "Research Governance", "Freeze one desk-specific policy before replay"),
        ("Task1885", "Controlled Desk Replay", "Backtest & Simulation Infra", "Run one controlled replay after Task1878-1884 pass"),
    ]
    return [
        {
            "task_id": task,
            "title": title,
            "owner_team": owner,
            "goal": goal,
            "status": "planned",
            "authority": AUTHORITY,
        }
        for task, title, owner, goal in rows
    ]


def closeout_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1877",
            "verdict": "desk_trader_logic_expert_source_review_complete",
            "main_conclusion": "7-how direction is right but current implementation is too broad; repair SEC specificity and winner thesis-intact override before next replay",
            "next_action": "Task1878 SEC specificity and Task1879 winner thesis-intact override",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    closeout = closeout_rows()[0]
    lines = [
        "# Task1868-1877 Desk Trader Logic Expert Review",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        "- What changed: expert/source review of the 7-how desk trader logic upgrade.",
        "- Key conclusion: direction is right, but implementation must become desk-specific and source-specific before another policy replay.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        f"- Next action: {closeout['next_action']}.",
        "",
        "## Quant Expert Report",
        "",
        "Current failure diagnosis:",
        "",
        "- `winner_compounder` was trimmed too broadly in Task1848-1867.",
        "- SEC `active_financing_pressure` was too broad and appeared across almost every desk.",
        "- MDD improved but CAGR fell, so the guard worked as a blunt brake rather than trader judgment.",
        "",
        "Professional source implications:",
        "",
        "- AQR QMJ supports winner-quality defense using profitability, growth, safety, and payout.",
        "- AQR momentum evidence supports not treating all winner volatility as damage.",
        "- Fama-French 5-factor context supports profitability/investment checks for quality and overinvestment risk.",
        "- SEC Form 8-K supports financing-event detection, but form presence alone is not active dilution.",
        "- FINRA margin remains useful liquidity context, but current local data is snapshot-only.",
        "",
        "Leakage audit:",
        "",
        "- This task is review-only.",
        "- PnL and drawdown are used only to diagnose over-trim, not to assign future rules.",
        "- GPT/subagent review is not source-of-truth.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "1. 7 how 방향은 맞습니다.",
        "2. 하지만 지금 구현은 trader처럼 정교한 게 아니라 너무 넓게 줄였습니다.",
        "3. 제일 먼저 고칠 것은 SEC financing 신호의 과잉 판정입니다.",
        "4. 두 번째는 winner가 살아있으면 macro stress에서도 버티게 하는 예외 규칙입니다.",
        "5. 그 다음 sector breadth와 desk별 replay입니다.",
        "",
        "## Artifact Manifest",
        "",
        "- `task1868_expert_review.csv`",
        "- `task1869_professional_source_context.csv`",
        "- `task1870_current_failure_diagnosis.csv`",
        "- `task1871_7how_validation_matrix.csv`",
        "- `task1872_desk_specific_requirements.csv`",
        "- `task1873_implementation_acceptance_contract.csv`",
        "- `task1874_1877_next_task_plan.csv`",
        "- `task1877_closeout.csv/json`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1868_1877_desk_trader_logic_expert_review_validate.py`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        ("task1868_expert_review.csv", expert_review_rows()),
        ("task1869_professional_source_context.csv", source_context_rows()),
        ("task1870_current_failure_diagnosis.csv", current_failure_rows()),
        ("task1871_7how_validation_matrix.csv", seven_how_matrix_rows()),
        ("task1872_desk_specific_requirements.csv", desk_requirement_rows()),
        ("task1873_implementation_acceptance_contract.csv", acceptance_contract_rows()),
        ("task1874_1877_next_task_plan.csv", next_task_rows()),
        ("task1877_closeout.csv", closeout_rows()),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout_rows())
    write_json(OUT_DIR / "task1877_closeout.json", closeout_rows()[0])
    write_report()
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1868_1877] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
