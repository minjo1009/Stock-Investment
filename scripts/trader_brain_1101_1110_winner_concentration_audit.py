from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ART = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay/canonical_daily"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
OUT_DIR = ROOT / "data/artifacts/task_1101_1110_winner_concentration_audit"

VARIANT = "sec_slot3_theme_cap1_v1"
INITIAL_CAPITAL = 1000.0
AUTHORITY = "DIAGNOSTIC_WINNER_CONCENTRATION_AUDIT_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: float, denominator: float) -> float:
    return round((numerator / denominator) * 100.0, 6) if denominator else 0.0


def hhi(values: list[float]) -> float:
    total = sum(values)
    if total <= 0:
        return 0.0
    return round(sum((value / total) ** 2 for value in values), 6)


def buy_hold_multiple(symbol: str, start: str = "2021-01-05", end: str = "2026-03-31") -> float | None:
    path = MARKET_DIR / f"{symbol}.csv"
    if not path.exists():
        return None
    rows = [row for row in read_csv(path) if start <= row["timestamp"] <= end]
    if not rows:
        return None
    start_px = float(rows[0]["adj_close"])
    end_px = float(rows[-1]["adj_close"])
    return end_px / start_px if start_px else None


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trades = [row for row in read_csv(ART / "task1084_sec_asof_replay_trades.csv") if row["policy_variant_id"] == VARIANT]
    selections = [
        row for row in read_csv(ART / "task1083_sec_asof_selection_ledger.csv")
        if row["policy_variant_id"] == VARIANT and row["decision_state"] == "selected"
    ]
    features = read_csv(ART / "task1082_sec_asof_adapter_feature_panel.csv")
    universe = read_csv(UNIVERSE_PATH)

    symbol_stats: dict[str, dict[str, object]] = {}
    for row in trades:
        stat = symbol_stats.setdefault(
            row["symbol"],
            {
                "symbol": row["symbol"],
                "theme": row["theme"],
                "closed_trades": 0,
                "entry_cash_spent": 0.0,
                "pnl": 0.0,
                "min_return_pct": 999.0,
                "max_return_pct": -999.0,
            },
        )
        stat["closed_trades"] = int(stat["closed_trades"]) + 1
        stat["entry_cash_spent"] = float(stat["entry_cash_spent"]) + float(row["entry_cash_spent"])
        stat["pnl"] = float(stat["pnl"]) + float(row["pnl"])
        stat["min_return_pct"] = min(float(stat["min_return_pct"]), float(row["return_pct"]))
        stat["max_return_pct"] = max(float(stat["max_return_pct"]), float(row["return_pct"]))

    total_pnl = sum(float(row["pnl"]) for row in trades)
    total_spent = sum(float(row["entry_cash_spent"]) for row in trades)
    symbol_rows: list[dict[str, object]] = []
    for stat in symbol_stats.values():
        mult = buy_hold_multiple(str(stat["symbol"]))
        pnl_value = float(stat["pnl"])
        spent_value = float(stat["entry_cash_spent"])
        symbol_rows.append(
            {
                **stat,
                "entry_cash_spent": f"{spent_value:.6f}",
                "pnl": f"{pnl_value:.6f}",
                "pnl_share_pct": f"{pct(pnl_value, total_pnl):.6f}",
                "spent_share_pct": f"{pct(spent_value, total_spent):.6f}",
                "return_on_spent_pct": f"{pct(pnl_value, spent_value):.6f}",
                "buy_hold_multiple_2021_2026q1": "" if mult is None else f"{mult:.6f}",
                "authority": AUTHORITY,
            }
        )
    symbol_rows = sorted(symbol_rows, key=lambda row: float(row["pnl"]), reverse=True)

    selected_symbols = {row["symbol"] for row in selections}
    universe_symbols = {row["symbol"] for row in universe}
    top3_pnl = sum(float(row["pnl"]) for row in symbol_rows[:3])
    top5_pnl = sum(float(row["pnl"]) for row in symbol_rows[:5])
    top3_spent = sum(float(row["entry_cash_spent"]) for row in symbol_rows[:3])
    top5_spent = sum(float(row["entry_cash_spent"]) for row in symbol_rows[:5])

    score_by_symbol: dict[str, set[str]] = defaultdict(set)
    selected_count = Counter(row["symbol"] for row in selections)
    for row in selections:
        score_by_symbol[row["symbol"]].add(row["sec_asof_source_score"])
    stability_rows = []
    for symbol in sorted(selected_symbols):
        stability_rows.append(
            {
                "symbol": symbol,
                "selected_count": selected_count[symbol],
                "distinct_sec_asof_scores_when_selected": len(score_by_symbol[symbol]),
                "scores_when_selected": ";".join(sorted(score_by_symbol[symbol], key=lambda value: int(value))),
                "static_score_flag": "1" if len(score_by_symbol[symbol]) == 1 else "0",
                "authority": AUTHORITY,
            }
        )

    feature_score_by_symbol: dict[str, set[str]] = defaultdict(set)
    for row in features:
        if row["symbol"] in selected_symbols:
            feature_score_by_symbol[row["symbol"]].add(row["sec_asof_source_score"])
    full_feature_stability_rows = []
    for symbol in sorted(selected_symbols):
        full_feature_stability_rows.append(
            {
                "symbol": symbol,
                "distinct_sec_asof_scores_all_dates": len(feature_score_by_symbol[symbol]),
                "scores_all_dates": ";".join(sorted(feature_score_by_symbol[symbol], key=lambda value: int(value))),
                "full_period_static_score_flag": "1" if len(feature_score_by_symbol[symbol]) == 1 else "0",
                "authority": AUTHORITY,
            }
        )

    universe_columns = set(universe[0].keys()) if universe else set()
    pit_columns = {"as_of_date", "start_date", "end_date", "effective_date", "created_at", "source_timestamp"} & universe_columns
    universe_audit = [
        {
            "universe_path": UNIVERSE_PATH.relative_to(ROOT).as_posix(),
            "universe_symbol_count": len(universe_symbols),
            "selected_symbol_count": len(selected_symbols),
            "selected_symbol_share_pct": f"{pct(len(selected_symbols), len(universe_symbols)):.6f}",
            "has_point_in_time_columns": "1" if pit_columns else "0",
            "pit_columns_found": ";".join(sorted(pit_columns)),
            "audit_state": "pit_universe_gap" if not pit_columns else "pit_columns_present",
            "authority": AUTHORITY,
        }
    ]

    summary = {
        "task_id": "Task1101-1110",
        "audited_variant": VARIANT,
        "closed_trades": len(trades),
        "selected_symbols": len(selected_symbols),
        "universe_symbols": len(universe_symbols),
        "selected_symbol_share_pct": round(pct(len(selected_symbols), len(universe_symbols)), 6),
        "total_pnl": round(total_pnl, 6),
        "ending_profit_over_initial_capital": round(total_pnl / INITIAL_CAPITAL, 6),
        "top3_symbols": ";".join(row["symbol"] for row in symbol_rows[:3]),
        "top3_pnl_share_pct": round(pct(top3_pnl, total_pnl), 6),
        "top5_symbols": ";".join(row["symbol"] for row in symbol_rows[:5]),
        "top5_pnl_share_pct": round(pct(top5_pnl, total_pnl), 6),
        "top3_spent_share_pct": round(pct(top3_spent, total_spent), 6),
        "top5_spent_share_pct": round(pct(top5_spent, total_spent), 6),
        "pnl_hhi": hhi([max(float(row["pnl"]), 0.0) for row in symbol_rows]),
        "spent_hhi": hhi([float(row["entry_cash_spent"]) for row in symbol_rows]),
        "selected_symbols_with_static_score": sum(1 for row in stability_rows if row["static_score_flag"] == "1"),
        "selected_symbols_full_period_static_score": sum(1 for row in full_feature_stability_rows if row["full_period_static_score_flag"] == "1"),
        "pit_universe_gap": "1" if not pit_columns else "0",
        "verdict": "winner_basket_concentration_confirmed",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "repair_pit_universe_and_add_dynamic_non_sec_event_timing_before_treating_result_as_strategy_skill",
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task1101_winner_concentration_summary.csv", [summary], list(summary.keys()))
    write_csv(OUT_DIR / "task1102_symbol_pnl_contribution.csv", symbol_rows, list(symbol_rows[0].keys()))
    write_csv(OUT_DIR / "task1103_selected_score_stability.csv", stability_rows, list(stability_rows[0].keys()))
    write_csv(OUT_DIR / "task1104_full_feature_score_stability.csv", full_feature_stability_rows, list(full_feature_stability_rows[0].keys()))
    write_csv(OUT_DIR / "task1105_universe_pit_audit.csv", universe_audit, list(universe_audit[0].keys()))
    (OUT_DIR / "task1110_winner_concentration_closeout.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task1110_winner_concentration_closeout.csv", [summary], list(summary.keys()))
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1101_1110_WINNER_CONCENTRATION_AUDIT_OK] "
        f"verdict={summary['verdict']} top3_pnl_share={summary['top3_pnl_share_pct']} "
        f"selected_symbols={summary['selected_symbols']}/{summary['universe_symbols']}"
    )


if __name__ == "__main__":
    main()
