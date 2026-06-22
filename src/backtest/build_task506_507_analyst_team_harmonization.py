from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, quality


DEFAULT_TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
DEFAULT_TASK505_QUALITY = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_quality.csv")
DEFAULT_DATA_RAW = Path("data/raw")
DEFAULT_TASK506_OUT = Path("docs/reports/task_506_analyst_team_source_audit")
DEFAULT_TASK507_OUT = Path("docs/reports/task_507_analyst_harmonized_trading_logic")


@dataclass(frozen=True)
class Task506Artifacts:
    analyst_team_source_audit: pd.DataFrame
    analyst_layer_contract: pd.DataFrame
    task_506_decision: pd.DataFrame


@dataclass(frozen=True)
class Task507Artifacts:
    analyst_harmonized_assignment_panel: pd.DataFrame
    analyst_harmonized_strategy_quality: pd.DataFrame
    analyst_harmonized_split_quality: pd.DataFrame
    analyst_harmonized_source_blocker_audit: pd.DataFrame
    task_507_decision: pd.DataFrame


def build_task506_analyst_team_source_audit(*, data_raw: Path = DEFAULT_DATA_RAW, out_dir: Path = DEFAULT_TASK506_OUT) -> Task506Artifacts:
    audit = analyst_source_audit(data_raw)
    contract = analyst_layer_contract(audit)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task506",
                "analyst_team_count": int(len(audit)),
                "available_team_count": int(audit["usable_for_scoring_flag"].sum()),
                "all_four_analyst_layers_ready_flag": int(audit["usable_for_scoring_flag"].sum() == 4),
                "missing_sources_are_approximated_flag": 0,
                "strategy_acceptance_status": "SOURCE_AUDIT_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out_dir / "analyst_team_source_audit.csv", index=False)
    contract.to_csv(out_dir / "analyst_layer_contract.csv", index=False)
    decision.to_csv(out_dir / "task_506_decision.csv", index=False)
    (out_dir / "task_506_analyst_team_source_audit.md").write_text(build_task506_report(audit, decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return Task506Artifacts(audit, contract, decision)


def analyst_source_audit(data_raw: Path) -> pd.DataFrame:
    paths = {
        "daily_ohlcv": data_raw / "us_daily_breadth_top500",
        "intraday_ohlcv": data_raw / "us_intraday",
        "quote_windows": data_raw / "alpaca_quote_entry_windows" / "task492_raw_quote_entry_windows.csv",
        "fundamental": data_raw / "fundamental",
        "news": data_raw / "news",
        "sentiment": data_raw / "sentiment",
    }
    rows = [
        {
            "analyst_team": "technical",
            "required_raw_source": "daily_ohlcv|intraday_ohlcv|vwap_trade_count",
            "available_raw_source": "daily_ohlcv|intraday_ohlcv",
            "raw_source_paths": f"{paths['daily_ohlcv']}|{paths['intraday_ohlcv']}",
            "raw_source_available_flag": int(paths["daily_ohlcv"].exists() and paths["intraday_ohlcv"].exists()),
            "usable_for_scoring_flag": int(paths["daily_ohlcv"].exists() and paths["intraday_ohlcv"].exists()),
            "missing_source_reason": "",
        },
        {
            "analyst_team": "fundamental",
            "required_raw_source": "financial_statements|earnings_calendar|estimate_revisions|guidance",
            "available_raw_source": "",
            "raw_source_paths": str(paths["fundamental"]),
            "raw_source_available_flag": int(paths["fundamental"].exists()),
            "usable_for_scoring_flag": 0,
            "missing_source_reason": "fundamental_raw_source_missing",
        },
        {
            "analyst_team": "psychology",
            "required_raw_source": "timestamped_sentiment|options_positioning|social_flow|retail_attention",
            "available_raw_source": "",
            "raw_source_paths": str(paths["sentiment"]),
            "raw_source_available_flag": int(paths["sentiment"].exists()),
            "usable_for_scoring_flag": 0,
            "missing_source_reason": "sentiment_psychology_raw_source_missing",
        },
        {
            "analyst_team": "news",
            "required_raw_source": "timestamped_news|event_tags|headline_source|article_receive_timestamp",
            "available_raw_source": "",
            "raw_source_paths": str(paths["news"]),
            "raw_source_available_flag": int(paths["news"].exists()),
            "usable_for_scoring_flag": 0,
            "missing_source_reason": "timestamped_news_raw_source_missing",
        },
    ]
    return pd.DataFrame(rows)


def analyst_layer_contract(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in audit.to_dict(orient="records"):
        team = row["analyst_team"]
        rows.append(
            {
                "analyst_team": team,
                "online_scoring_allowed_flag": int(row["usable_for_scoring_flag"]),
                "score_column": f"{team}_analyst_score",
                "score_status": "enabled_exact_source" if row["usable_for_scoring_flag"] else "blocked_missing_raw_source",
                "fallback_or_inference_allowed_flag": 0,
                "trading_logic_role": "entry_selection_and_risk_context" if team == "technical" else "blocked_until_raw_source_collected",
            }
        )
    return pd.DataFrame(rows)


def build_task507_analyst_harmonized_trading_logic(
    *,
    task505_panel_path: Path = DEFAULT_TASK505_PANEL,
    task505_quality_path: Path = DEFAULT_TASK505_QUALITY,
    task506_out: Path = DEFAULT_TASK506_OUT,
    out_dir: Path = DEFAULT_TASK507_OUT,
) -> Task507Artifacts:
    if not (task506_out / "analyst_team_source_audit.csv").exists():
        build_task506_analyst_team_source_audit(out_dir=task506_out)
    source_audit = pd.read_csv(task506_out / "analyst_team_source_audit.csv")
    panel = pd.read_csv(task505_panel_path)
    panel = add_analyst_columns(panel, source_audit)
    strategy_quality = pd.DataFrame([aggregate(panel)])
    if task505_quality_path.exists():
        base_quality = pd.read_csv(task505_quality_path)
        if not base_quality.empty and "two_year_capital_pnl_pct" in base_quality.columns:
            strategy_quality["baseline_task505_two_year_capital_pnl_pct"] = base_quality.iloc[0]["two_year_capital_pnl_pct"]
    split = quality(panel, ["split_name"]) if "split_name" in panel.columns else pd.DataFrame()
    blockers = source_audit[source_audit["usable_for_scoring_flag"].eq(0)].copy()
    blockers["required_before_four_analyst_harmonization_flag"] = 1
    decision = build_task507_decision(strategy_quality, blockers)
    out_dir.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out_dir / "analyst_harmonized_assignment_panel.csv", index=False)
    strategy_quality.to_csv(out_dir / "analyst_harmonized_strategy_quality.csv", index=False)
    split.to_csv(out_dir / "analyst_harmonized_split_quality.csv", index=False)
    blockers.to_csv(out_dir / "analyst_harmonized_source_blocker_audit.csv", index=False)
    decision.to_csv(out_dir / "task_507_decision.csv", index=False)
    (out_dir / "task_507_analyst_harmonized_trading_logic.md").write_text(build_task507_report(decision, blockers), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return Task507Artifacts(panel, strategy_quality, split, blockers, decision)


def add_analyst_columns(panel: pd.DataFrame, source_audit: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    usable = set(source_audit[source_audit["usable_for_scoring_flag"].eq(1)]["analyst_team"].astype(str))
    out["technical_analyst_score"] = 1.0 if "technical" in usable else pd.NA
    out["fundamental_analyst_score"] = pd.NA
    out["psychology_analyst_score"] = pd.NA
    out["news_analyst_score"] = pd.NA
    out["analyst_harmonized_strategy_name"] = "task507_task505_best_with_available_technical_only"
    out["four_analyst_full_harmonization_ready_flag"] = 0
    out["missing_analyst_source_approximation_used_flag"] = 0
    out["inferred_lifecycle_matching_used_flag"] = 0
    return out


def build_task507_decision(strategy_quality: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    metrics = strategy_quality.iloc[0].to_dict() if not strategy_quality.empty else {}
    return pd.DataFrame(
        [
            {
                "task_id": "Task507",
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "baseline_task505_two_year_capital_pnl_pct": metrics.get("baseline_task505_two_year_capital_pnl_pct", pd.NA),
                "four_analyst_full_harmonization_ready_flag": 0,
                "blocked_analyst_team_count": int(len(blockers)),
                "missing_analyst_source_approximation_used_flag": 0,
                "strategy_acceptance_status": "TECHNICAL_ONLY_DIAGNOSTIC_BLOCKED_FOR_FOUR_ANALYST_SYSTEM",
            }
        ]
    )


def build_task506_report(audit: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 506 - Analyst Team Source Audit",
            "",
            "## Quant Expert Report",
            "",
            "The four-analyst architecture cannot be scored honestly unless each analyst has timestamped raw source data. Current local data supports the technical analyst layer through daily and intraday OHLCV. Fundamental, psychology, and news layers are blocked by missing raw sources and are not approximated.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Usable analyst teams now: {d['available_team_count']} / {d['analyst_team_count']}",
            "- Missing data is not guessed.",
            "- Full four-analyst strategy development is blocked until fundamental, sentiment/psychology, and timestamped news data are collected.",
        ]
    )


def build_task507_report(decision: pd.DataFrame, blockers: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    blocked = ", ".join(blockers["analyst_team"].astype(str).tolist()) if not blockers.empty else "none"
    return "\n".join(
        [
            "# Task 507 - Analyst Harmonized Trading Logic",
            "",
            "## Quant Expert Report",
            "",
            "Task507 wires the analyst contract into the current best Task505 strategy without fabricating unavailable analyst inputs. The result is a technical-only diagnostic overlay, not the requested full four-analyst alpha stack.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Current strategy count / avg / win / entry_reduce: {d['selected_count']} / {float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Four-analyst full system ready: {d['four_analyst_full_harmonization_ready_flag']}",
            f"- Blocked analyst teams: {blocked}",
            "- Next required work: collect exact timestamped raw data for blocked analyst teams before using them in scoring.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-raw", type=Path, default=DEFAULT_DATA_RAW)
    parser.add_argument("--task505-panel", type=Path, default=DEFAULT_TASK505_PANEL)
    args = parser.parse_args()
    build_task506_analyst_team_source_audit(data_raw=args.data_raw)
    artifacts = build_task507_analyst_harmonized_trading_logic(task505_panel_path=args.task505_panel)
    row = artifacts.task_507_decision.iloc[0]
    print(
        "[TASK507] "
        f"count={row['selected_count']} full_four_analyst_ready={row['four_analyst_full_harmonization_ready_flag']} "
        f"blocked={row['blocked_analyst_team_count']}"
    )


if __name__ == "__main__":
    main()
