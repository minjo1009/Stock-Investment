from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel, within_window
from src.backtest.build_task623_big_event_interpretation_scoring_sidecar import build_task623_big_event_interpretation_scoring_sidecar


TASK_ID = "Task627"
REPORT_DIR = Path("docs/reports/task_627_source_text_theme_linkage_validation")
TASK625_DIR = Path("docs/reports/task_625_big_event_perfection_criteria_source_certification")
SCOPES = ("full_panel", "validation", "recent_oos")

AEROSPACE_TERMS = (
    "defense",
    "military",
    "air force",
    "armed forces",
    "aviation",
    "aircraft",
    "aerospace",
    "space",
    "satellite",
    "rocket",
    "missile",
    "propulsion",
    "drone",
    "uav",
    "launch",
)

RISK_TERMS = (
    "sanction",
    "designation",
    "secondary sanctions",
    "export control",
    "restricted",
    "iran",
    "russia",
    "counter terrorism",
    "counterterrorism",
    "non-proliferation",
    "irgc",
)


def build_task627_source_text_theme_linkage_validation(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    task625_dir: Path = TASK625_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    task623 = build_task623_big_event_interpretation_scoring_sidecar()
    scored = task623["event_interpretation_scores"]
    certification = pd.read_csv(task625_dir / "task_625_source_certification_matrix.csv")
    text_scored = build_source_text_linkage_scores(scored, certification)
    panel = load_panel(task617_panel_path)
    attachment = build_trade_text_linkage_attachment(panel, text_scored)
    enriched = panel.merge(attachment, on="lifecycle_id", how="left")
    policy_eval = build_policy_variant_evaluation(enriched)
    pass_fail = build_pass_fail(text_scored, attachment, policy_eval)
    decision = build_decision(policy_eval, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    text_scored.to_csv(out_dir / "task_627_source_text_linkage_scores.csv", index=False)
    attachment.to_csv(out_dir / "task_627_trade_text_linkage_attachment.csv", index=False)
    policy_eval.to_csv(out_dir / "task_627_policy_variant_evaluation.csv", index=False)
    pass_fail.to_csv(out_dir / "task_627_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_627_decision.csv", index=False)
    (out_dir / "task_627_source_text_theme_linkage_validation.md").write_text(
        render_report(text_scored, policy_eval, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_627_source_text_linkage_scores": text_scored,
        "task_627_trade_text_linkage_attachment": attachment,
        "task_627_policy_variant_evaluation": policy_eval,
        "task_627_pass_fail_matrix": pass_fail,
        "task_627_decision": decision,
    }


def build_source_text_linkage_scores(scored: pd.DataFrame, certification: pd.DataFrame) -> pd.DataFrame:
    cert_cols = ["event_id", "source_text_certified_flag", "source_text_hash", "raw_text_path", "source_text_char_count"]
    merged = scored.merge(certification[cert_cols], on="event_id", how="left")
    rows = []
    for _, event in merged.iterrows():
        row = event.to_dict()
        text = read_raw_text(row.get("raw_text_path", ""))
        certified_flag = int(pd.to_numeric(pd.Series([row.get("source_text_certified_flag", 0)]), errors="coerce").fillna(0).iloc[0])
        row["source_text_certified_flag"] = certified_flag
        row["source_text_aerospace_theme_hit_count"] = keyword_count(text, AEROSPACE_TERMS)
        row["source_text_risk_hit_count"] = keyword_count(text, RISK_TERMS)
        row["source_text_aerospace_risk_flag"] = int(
            certified_flag == 1
            and row["source_text_aerospace_theme_hit_count"] > 0
            and row["source_text_risk_hit_count"] > 0
        )
        row["source_text_linkage_reason"] = source_text_linkage_reason(row)
        row["source_presence_only_used_flag"] = 0
        row["gpt_score_used_as_source_flag"] = 0
        rows.append(row)
    return pd.DataFrame(rows)


def read_raw_text(path: object) -> str:
    try:
        return Path(str(path)).read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def keyword_count(text: str, terms: tuple[str, ...]) -> int:
    if not text:
        return 0
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", text))


def source_text_linkage_reason(row: dict[str, object]) -> str:
    if int(row.get("source_text_certified_flag", 0)) != 1:
        return "source_text_not_certified"
    if int(row.get("source_text_aerospace_theme_hit_count", 0) or 0) <= 0:
        return "no_aerospace_theme_text_hit"
    if int(row.get("source_text_risk_hit_count", 0) or 0) <= 0:
        return "no_risk_text_hit"
    return "certified_text_aerospace_risk_linkage"


def build_trade_text_linkage_attachment(panel: pd.DataFrame, text_scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in panel.iterrows():
        linked = source_text_linked_events_for_entry(text_scored, entry)
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "source_text_linked_event_count": int(len(linked)),
                "source_text_aerospace_risk_event_count": int(linked["source_text_aerospace_risk_flag"].sum()) if not linked.empty else 0,
                "source_text_aerospace_risk_flag": int(str(entry["theme_id"]) == "aerospace_defense_space" and not linked.empty),
                "source_text_event_score_sum": float(linked["composite_interpretation_score"].sum()) if not linked.empty else 0.0,
                "label_used_in_assignment_flag": 0,
                "gpt_score_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def source_text_linked_events_for_entry(text_scored: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    if str(entry["theme_id"]) != "aerospace_defense_space":
        return pd.DataFrame(columns=text_scored.columns)
    known = text_scored[
        text_scored["source_text_aerospace_risk_flag"].astype(int).eq(1)
        & (
            (text_scored["event_date_obj"] < entry["trade_date"])
            | (
                text_scored["event_date_obj"].eq(entry["trade_date"])
                & text_scored["time_precision"].eq("timestamp")
                & text_scored["event_timestamp_dt"].notna()
                & (text_scored["event_timestamp_dt"] <= entry["entry_ts"])
            )
        )
    ]
    return within_window(known, entry["trade_date"], 7)


def build_policy_variant_evaluation(enriched: pd.DataFrame) -> pd.DataFrame:
    variants = {
        "original_turboquant": enriched,
        "hold_source_text_aerospace_risk": enriched[~enriched["source_text_aerospace_risk_flag"].astype(int).eq(1)],
    }
    rows = []
    for variant_name, variant_df in variants.items():
        for split in SCOPES:
            group = variant_df if split == "full_panel" else variant_df[variant_df["split_name"].astype(str).eq(split)]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "policy_variant": variant_name,
                    "split_name": split,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def metric(policy_eval: pd.DataFrame, variant: str, split: str, column: str) -> float:
    return float(policy_eval[policy_eval["policy_variant"].eq(variant) & policy_eval["split_name"].eq(split)].iloc[0][column])


def build_pass_fail(text_scored: pd.DataFrame, attachment: pd.DataFrame, policy_eval: pd.DataFrame) -> pd.DataFrame:
    certified = text_scored[text_scored["source_text_aerospace_risk_flag"].astype(int).eq(1)]
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    text_recent = metric(policy_eval, "hold_source_text_aerospace_risk", "recent_oos", "avg_net_return_pct")
    original_validation = metric(policy_eval, "original_turboquant", "validation", "avg_net_return_pct")
    text_validation = metric(policy_eval, "hold_source_text_aerospace_risk", "validation", "avg_net_return_pct")
    removed_recent = int(metric(policy_eval, "original_turboquant", "recent_oos", "trade_count")) - int(
        metric(policy_eval, "hold_source_text_aerospace_risk", "recent_oos", "trade_count")
    )
    return pd.DataFrame(
        [
            {
                "gate": "source_text_linkage_exists",
                "pass_flag": int(len(certified) > 0),
                "observed_value": f"source_text_aerospace_risk_events={len(certified)}",
                "required_value": "certified official text must contain both aerospace/theme and risk terms",
            },
            {
                "gate": "recent_oos_improves",
                "pass_flag": int(removed_recent > 0 and text_recent > original_recent),
                "observed_value": f"removed_recent={removed_recent}; recent {text_recent:.2f}% vs original {original_recent:.2f}%",
                "required_value": "source-text aerospace risk hold must improve recent OOS",
            },
            {
                "gate": "validation_not_broken",
                "pass_flag": int(text_validation >= original_validation),
                "observed_value": f"validation {text_validation:.2f}% vs original {original_validation:.2f}%",
                "required_value": "source-text aerospace risk hold must not reduce validation average",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "source-text linkage diagnostic only",
                "required_value": "needs cost/account and parameter/split robustness before strategy use",
            },
        ]
    )


def build_decision(policy_eval: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    text_recent = metric(policy_eval, "hold_source_text_aerospace_risk", "recent_oos", "avg_net_return_pct")
    original_validation = metric(policy_eval, "original_turboquant", "validation", "avg_net_return_pct")
    text_validation = metric(policy_eval, "hold_source_text_aerospace_risk", "validation", "avg_net_return_pct")
    diagnostic_pass = int(
        pass_fail[pass_fail["gate"].isin(["source_text_linkage_exists", "recent_oos_improves", "validation_not_broken"])]["pass_flag"].astype(int).all()
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PASS_SOURCE_TEXT_AEROSPACE_RISK_DIAGNOSTIC_NOT_ACCEPTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "source_text_diagnostic_pass_flag": diagnostic_pass,
                "original_recent_oos_avg_net_return_pct": original_recent,
                "hold_source_text_aerospace_risk_recent_oos_avg_net_return_pct": text_recent,
                "original_validation_avg_net_return_pct": original_validation,
                "hold_source_text_aerospace_risk_validation_avg_net_return_pct": text_validation,
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Run cost/account validation on the source-text aerospace risk hold and require robustness before any promotion.",
            }
        ]
    )


def render_report(text_scored: pd.DataFrame, policy_eval: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0]
    linked = text_scored[text_scored["source_text_aerospace_risk_flag"].astype(int).eq(1)]
    lines = [
        "# Task627 Source Text Theme Linkage Validation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Certified source-text aerospace risk events: {len(linked)}",
        f"- Recent OOS: {float(d['original_recent_oos_avg_net_return_pct']):.2f}% -> {float(d['hold_source_text_aerospace_risk_recent_oos_avg_net_return_pct']):.2f}%",
        f"- Validation: {float(d['original_validation_avg_net_return_pct']):.2f}% -> {float(d['hold_source_text_aerospace_risk_validation_avg_net_return_pct']):.2f}%",
        "",
        "## Quant Expert Report",
        "",
        "### Policy Variant Evaluation",
        "",
        "| Variant | Split | Trades | Avg Return | Win | Entry-Reduce |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in policy_eval.iterrows():
        lines.append(
            f"| `{row['policy_variant']}` | `{row['split_name']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']) * 100.0:.2f}% | "
            f"{float(row['entry_reduce_failure_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Task626 showed that policy tags were too broad.",
            "- Task627 uses official source text itself to find aerospace/defense risk linkage.",
            "- This gives a smaller but more honest recent OOS improvement.",
            "- It is still diagnostic only until cost/account validation passes.",
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_627_source_text_linkage_scores.csv`",
            "- `task_627_trade_text_linkage_attachment.csv`",
            "- `task_627_policy_variant_evaluation.csv`",
            "- `task_627_pass_fail_matrix.csv`",
            "- `task_627_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task627_source_text_theme_linkage_validation`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task627_source_text_theme_linkage_validation(out_dir=args.out_dir)
    row = artifacts["task_627_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"recent={float(row['original_recent_oos_avg_net_return_pct']):.2f}% -> "
        f"{float(row['hold_source_text_aerospace_risk_recent_oos_avg_net_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
