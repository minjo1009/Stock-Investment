from __future__ import annotations

import csv
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK1141_RAW = ROOT / "data/raw/task_1141_1150_external_sources"
TASK1141_ART = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"
OUT_DIR = ROOT / "data/artifacts/task_1151_1160_official_universe_redefinition"
REPORT_DIR = ROOT / "docs/reports/task_1151_1160_official_universe_redefinition"

AUTHORITY = "DIAGNOSTIC_OFFICIAL_UNIVERSE_REDEFINITION_ONLY"
HIST_START = date(2021, 1, 1)
HIST_END = date(2026, 3, 31)
USER_AGENT = "minjo-trader-brain-research contact@example.com"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def head_url(url: str, timeout: int = 30) -> dict[str, object]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    requested_at = now_utc()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return {
                "url": url,
                "head_status": "ok",
                "http_status": getattr(response, "status", 200),
                "content_length": response.headers.get("Content-Length", ""),
                "content_type": response.headers.get("Content-Type", ""),
                "checked_at_utc": requested_at,
                "error": "",
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "head_status": "failed",
            "http_status": "",
            "content_length": "",
            "content_type": "",
            "checked_at_utc": requested_at,
            "error": str(exc)[:500],
        }


def month_ends(start: date, end: date) -> list[date]:
    dates: list[date] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        if m == 12:
            next_month = date(y + 1, 1, 1)
        else:
            next_month = date(y, m + 1, 1)
        d = next_month.fromordinal(next_month.toordinal() - 1)
        if d < start:
            d = start
        if d > end:
            d = end
        dates.append(d)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return dates


def load_sec_exchange_universe() -> tuple[list[dict[str, object]], Path]:
    path = TASK1141_RAW / "sec_company_tickers_exchange/sec_company_tickers_exchange.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    fields = payload["fields"]
    rows: list[dict[str, object]] = []
    for idx, values in enumerate(payload["data"], start=1):
        mapped = {str(fields[i]): values[i] for i in range(min(len(fields), len(values)))}
        ticker = str(mapped.get("ticker", "")).strip().upper()
        exchange = str(mapped.get("exchange", "")).strip()
        if not ticker or not exchange:
            continue
        rows.append(
            {
                "task_id": "Task1153",
                "official_universe_row_id": f"OFFUNIV1153-{idx:05d}",
                "cik": str(mapped.get("cik", "")).zfill(10),
                "symbol": ticker,
                "company_name": mapped.get("name", ""),
                "exchange": exchange,
                "source_url": "https://www.sec.gov/files/company_tickers_exchange.json",
                "raw_source_path": rel(path),
                "source_hash": sha256(path),
                "source_snapshot_type": "current_sec_exchange_identity_snapshot",
                "selection_candidate_source": "1",
                "historical_listing_pit_pass": "0",
                "historical_listing_block_reason": "current_sec_exchange_snapshot_not_historical_listing_membership",
                "authority": AUTHORITY,
            }
        )
    return rows, path


def task1151_universe_basis_decision() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1151",
            "decision_id": "UNIVERSE-BASIS-1151-001",
            "old_basis": "custom_10x7_theme_universe",
            "old_basis_state": "invalid_for_selection_basis_without_pit_creation_or_membership_evidence",
            "new_basis": "official_public_listing_or_public_filer_universe_asof",
            "new_basis_rule": "brain_selects_from_official_universe_first_then_theme_labels_are_features_not_candidate_membership",
            "custom_10x7_allowed_use": "theme_label_training_and_diagnostics_only",
            "custom_10x7_for_selection_allowed": "0",
            "replay_executed": "0",
            "authority": AUTHORITY,
        }
    ]


def task1152_source_feasibility() -> list[dict[str, object]]:
    sec_bulk = head_url("https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip")
    return [
        {
            "task_id": "Task1152",
            "source_id": "sec_company_tickers_exchange",
            "source_url": "https://www.sec.gov/files/company_tickers_exchange.json",
            "source_state": "downloaded_task1141",
            "official": "1",
            "free_access": "1",
            "historical_listing_membership": "0",
            "usable_for": "current_official_identity_and_exchange_snapshot",
            "limitation": "does_not_prove_exchange_membership_on_each_2021_2026_decision_date",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1152",
            "source_id": "nasdaq_trader_symbol_directory",
            "source_url": "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt",
            "source_state": "downloaded_task1141_current_file",
            "official": "1",
            "free_access": "1",
            "historical_listing_membership": "0",
            "usable_for": "current_symbol_directory_crosscheck",
            "limitation": "nasdaq_documentation_states_symbol_lookup_is_current_trading_day",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1152",
            "source_id": "sec_bulk_submissions_zip",
            "source_url": sec_bulk["url"],
            "source_state": sec_bulk["head_status"],
            "official": "1",
            "free_access": "1",
            "historical_listing_membership": "partial_public_filer_asof_not_listing",
            "usable_for": "accepted_datetime_public_filer_universe_proxy",
            "limitation": "large_file_and_still_not_exchange_listing_membership_by_itself",
            "content_length_bytes": sec_bulk["content_length"],
            "checked_at_utc": sec_bulk["checked_at_utc"],
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1152",
            "source_id": "nyse_historical_market_data",
            "source_url": "https://www.nyse.com/market-data/historical",
            "source_state": "identified_external_paid_or_permissioned",
            "official": "1",
            "free_access": "0",
            "historical_listing_membership": "candidate_vendor_or_exchange_feed",
            "usable_for": "true_exchange_historical_listing_membership_if_acquired",
            "limitation": "not_downloaded_in_this_task",
            "authority": AUTHORITY,
        },
    ]


def task1154_asof_contract() -> list[dict[str, object]]:
    required = [
        ("symbol", "ticker visible to selection engine"),
        ("cik", "issuer identifier where SEC source exists"),
        ("exchange", "official exchange or public-filer venue field"),
        ("effective_start_ts", "date membership starts"),
        ("effective_end_ts", "date membership ends or empty if active"),
        ("published_ts", "official source publication or acceptance time"),
        ("received_ts", "project/vendor receipt time"),
        ("available_to_brain_ts", "max of published and received where required"),
        ("raw_source_path", "downloaded official source file"),
        ("source_hash", "sha256 of raw source"),
        ("source_authority", "official_exchange vendor official_sec or proxy"),
        ("pit_membership_pass", "1 only if row-level as-of membership is proven"),
    ]
    return [
        {
            "task_id": "Task1154",
            "field": field,
            "meaning": meaning,
            "required_for_true_official_listed_universe": "1",
            "fallback_allowed": "0",
            "authority": AUTHORITY,
        }
        for field, meaning in required
    ]


def task1155_decision_calendar() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1155",
            "decision_date": d.isoformat(),
            "decision_asof_ts": f"{d.isoformat()}T21:00:00+00:00",
            "window": "2021_2026q1_month_end",
            "authority": AUTHORITY,
        }
        for d in month_ends(HIST_START, HIST_END)
    ]


def task1156_seed_panel(universe_rows: list[dict[str, object]], calendar_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    sample_symbols = universe_rows[:1000]
    rows: list[dict[str, object]] = []
    idx = 0
    for cal in calendar_rows:
        for item in sample_symbols:
            idx += 1
            rows.append(
                {
                    "task_id": "Task1156",
                    "seed_panel_id": f"OFFSEED1156-{idx:08d}",
                    "decision_asof_ts": cal["decision_asof_ts"],
                    "symbol": item["symbol"],
                    "cik": item["cik"],
                    "exchange": item["exchange"],
                    "source_snapshot_type": item["source_snapshot_type"],
                    "eligible_for_brain_selection": "0",
                    "eligibility_state": "blocked_until_historical_listing_or_public_filer_asof_membership_is_built",
                    "replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def task1157_theme_label_policy() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1157",
            "policy_id": "THEME-LABEL-POLICY-1157-001",
            "theme_label_source": "custom_10x7_and_future_external_extractors",
            "allowed_use": "feature_or_explanation_label_after_official_universe_membership",
            "forbidden_use": "preselecting_candidate_symbols_or_defining_backtest_universe",
            "selection_basis": "official_universe_membership_first",
            "authority": AUTHORITY,
        }
    ]


def task1158_selection_contract() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1158",
            "selection_contract_id": "OFFICIAL-UNIVERSE-SELECTION-1158-001",
            "step_order": 1,
            "rule": "build_asof_official_universe",
            "must_pass": "pit_membership_pass",
            "replay_allowed_if_fail": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1158",
            "selection_contract_id": "OFFICIAL-UNIVERSE-SELECTION-1158-002",
            "step_order": 2,
            "rule": "run_l1_l5_features_only_on_asof_universe_members",
            "must_pass": "source_time_and_no_future_leakage",
            "replay_allowed_if_fail": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1158",
            "selection_contract_id": "OFFICIAL-UNIVERSE-SELECTION-1158-003",
            "step_order": 3,
            "rule": "slot_cap_select_top_3_5_10_from_ranked_asof_universe",
            "must_pass": "pre_registered_policy",
            "replay_allowed_if_fail": "0",
            "authority": AUTHORITY,
        },
    ]


def task1159_replay_gate(universe_rows: list[dict[str, object]], seed_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    true_pit = sum(1 for row in universe_rows if row["historical_listing_pit_pass"] == "1")
    return [
        {
            "task_id": "Task1159",
            "gate_id": "OFFICIAL-UNIVERSE-GATE-1159-001",
            "official_current_universe_rows": len(universe_rows),
            "seed_panel_rows": len(seed_rows),
            "true_historical_listing_pit_rows": true_pit,
            "official_universe_replay_ready": "1" if true_pit > 0 else "0",
            "policy_preregistration_allowed": "0",
            "replay_executed": "0",
            "selection_promoted": "0",
            "block_reason": "official_current_universe_built_but_historical_listing_membership_not_yet_acquired",
            "authority": AUTHORITY,
        }
    ]


def task1160_closeout(gate_rows: list[dict[str, object]]) -> dict[str, object]:
    gate = gate_rows[0]
    return {
        "task_id": "Task1151-1160",
        "verdict": "official_universe_basis_defined_replay_blocked_until_historical_listing_membership",
        "official_current_universe_rows": gate["official_current_universe_rows"],
        "seed_panel_rows": gate["seed_panel_rows"],
        "true_historical_listing_pit_rows": gate["true_historical_listing_pit_rows"],
        "custom_10x7_selection_basis_allowed": "0",
        "policy_preregistration_allowed": "0",
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "acquire_sec_bulk_public_filer_asof_or_vendor_exchange_historical_listing_feed_then_build_full_asof_selection_universe",
        "authority": AUTHORITY,
    }


def write_report(decision: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1151_1160_official_universe_redefinition.md"
    lines = [
        "# Task1151-1160 Official Universe Redefinition",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision['verdict']}`.",
        "- Custom 10x7 universe is no longer allowed as the selection universe.",
        "- It may only be used as diagnostic theme labels after official universe membership.",
        f"- Official current SEC exchange universe rows: {decision['official_current_universe_rows']}.",
        f"- Seed panel rows: {decision['seed_panel_rows']}.",
        f"- True historical listing PIT rows: {decision['true_historical_listing_pit_rows']}.",
        "- Replay executed: 0.",
        "- Selection promoted: 0.",
        "",
        "## Quant Expert Report",
        "",
        "The target architecture changes from handpicked candidates to a broad official universe.",
        "",
        "New rule:",
        "",
        "1. Build an official as-of universe first.",
        "2. Run L1-L5 features only inside that universe.",
        "3. Select 3, 5, or 10 names from the ranked universe.",
        "4. Theme labels are explanatory features, not candidate admission rules.",
        "",
        "Source finding:",
        "",
        "- SEC `company_tickers_exchange.json` is useful for current official identity and exchange mapping.",
        "- Nasdaq Trader symbol directory is official but current-day only.",
        "- SEC bulk submissions can support public-filer as-of membership through filing acceptance times, but it is not a pure exchange-listing feed.",
        "- A true official historical listed universe likely requires exchange/vendor historical listing data.",
        "",
        "Leakage decision:",
        "",
        "- No current snapshot is promoted into historical membership.",
        "- No replay was executed.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We changed the game board.",
        "",
        "Before: the model picked from a handpicked 70-stock theme basket.",
        "",
        "After: the model must pick from an official market universe first. The theme basket can explain ideas, but it cannot decide who is eligible.",
        "",
        "This fixes the biggest conceptual flaw. It does not yet produce a valid historical backtest because the true 2021-2026 historical listing feed is not built yet.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1151_universe_basis_decision.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1152_official_source_feasibility.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1153_current_sec_exchange_universe.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1154_historical_asof_universe_contract.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1155_decision_calendar.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1156_official_universe_seed_panel.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1157_theme_label_policy.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1158_selection_policy_contract.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1159_official_universe_replay_gate.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1160_official_universe_redefinition_closeout.csv`",
        "- `data/artifacts/task_1151_1160_official_universe_redefinition/task1160_official_universe_redefinition_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1151_1160_decision.csv", [decision])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    basis_rows = task1151_universe_basis_decision()
    feasibility_rows = task1152_source_feasibility()
    universe_rows, _ = load_sec_exchange_universe()
    contract_rows = task1154_asof_contract()
    calendar_rows = task1155_decision_calendar()
    seed_rows = task1156_seed_panel(universe_rows, calendar_rows)
    theme_policy_rows = task1157_theme_label_policy()
    selection_rows = task1158_selection_contract()
    gate_rows = task1159_replay_gate(universe_rows, seed_rows)
    decision = task1160_closeout(gate_rows)

    write_csv(OUT_DIR / "task1151_universe_basis_decision.csv", basis_rows)
    write_csv(OUT_DIR / "task1152_official_source_feasibility.csv", feasibility_rows)
    write_csv(OUT_DIR / "task1153_current_sec_exchange_universe.csv", universe_rows)
    write_csv(OUT_DIR / "task1154_historical_asof_universe_contract.csv", contract_rows)
    write_csv(OUT_DIR / "task1155_decision_calendar.csv", calendar_rows)
    write_csv(OUT_DIR / "task1156_official_universe_seed_panel.csv", seed_rows)
    write_csv(OUT_DIR / "task1157_theme_label_policy.csv", theme_policy_rows)
    write_csv(OUT_DIR / "task1158_selection_policy_contract.csv", selection_rows)
    write_csv(OUT_DIR / "task1159_official_universe_replay_gate.csv", gate_rows)
    write_csv(OUT_DIR / "task1160_official_universe_redefinition_closeout.csv", [decision])
    write_json(OUT_DIR / "task1160_official_universe_redefinition_closeout.json", decision)
    write_report(decision)

    print(
        "[TRADER_BRAIN_1151_1160_OFFICIAL_UNIVERSE_REDEFINITION_OK] "
        f"official_current_universe={decision['official_current_universe_rows']} "
        f"seed_panel={decision['seed_panel_rows']} "
        f"true_pit={decision['true_historical_listing_pit_rows']} "
        "custom10x7_selection=0 replay=0"
    )


if __name__ == "__main__":
    main()
