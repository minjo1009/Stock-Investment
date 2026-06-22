from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task614_p0_intelligence_source_attachment import (
    normalize_event_frame,
    relevant_events,
    tag_contains,
)


TASK_ID = "Task622"
REPORT_DIR = Path("docs/reports/task_622_source_semantic_interpretation_sidecar")
EVENT_STORE = Path("data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv")
TASK617_PANEL = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv")

SCHEMA_FIELDS = [
    "company_specificity",
    "catalyst_economic_link",
    "market_timing_risk",
    "actionability",
    "evidence_quality",
    "timestamp_validity",
    "economic_direction",
    "materiality_level",
    "classification_confidence",
    "review_status",
    "reason_code",
    "source_gap_flag",
]


def build_task622_source_semantic_interpretation_sidecar(
    *,
    event_store_path: Path = EVENT_STORE,
    task617_panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    events = load_events(event_store_path)
    labels = semantic_label_events(events)
    panel = load_panel(task617_panel_path)
    recent_aerospace = build_recent_aerospace_semantic_attachment(panel, labels)
    source_gap = build_source_gap_report(labels)
    pass_fail = build_pass_fail(labels, recent_aerospace)
    gpt_review = build_gpt_review_status()
    decision = build_decision(labels, recent_aerospace, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    labels.to_csv(out_dir / "source_semantic_labels.csv", index=False)
    recent_aerospace.to_csv(out_dir / "recent_aerospace_semantic_attachment.csv", index=False)
    source_gap.to_csv(out_dir / "source_gap_report.csv", index=False)
    pass_fail.to_csv(out_dir / "task_622_pass_fail_matrix.csv", index=False)
    gpt_review.to_csv(out_dir / "task_622_gpt_semantic_schema_review_status.csv", index=False)
    decision.to_csv(out_dir / "task_622_decision.csv", index=False)
    (out_dir / "task_622_source_semantic_interpretation_sidecar.md").write_text(
        render_report(labels, recent_aerospace, source_gap, pass_fail, gpt_review, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "source_semantic_labels": labels,
        "recent_aerospace_semantic_attachment": recent_aerospace,
        "source_gap_report": source_gap,
        "task_622_pass_fail_matrix": pass_fail,
        "task_622_gpt_semantic_schema_review_status": gpt_review,
        "task_622_decision": decision,
    }


def load_events(path: Path) -> pd.DataFrame:
    events = normalize_event_frame(pd.read_csv(path))
    events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp_utc"], utc=True, errors="coerce")
    return events


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["trade_date"] = pd.to_datetime(panel["trade_date"], errors="coerce").dt.date
    return panel


def semantic_label_events(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        row = event.to_dict()
        row.update(classify_event(event))
        row["gpt_or_plugin_used_as_source_flag"] = 0
        rows.append(row)
    return pd.DataFrame(rows)


def classify_event(event: pd.Series) -> dict[str, Any]:
    title = str(event.get("event_title", "") or "")
    title_lower = title.lower()
    category = str(event.get("event_category", "") or "")
    lane = str(event.get("source_lane", "") or "")
    source_name = str(event.get("source_name", "") or "")

    label = {
        "company_specificity": "unclear",
        "catalyst_economic_link": "unknown",
        "market_timing_risk": "unknown",
        "actionability": "uninterpretable_do_not_trade",
        "evidence_quality": "title_only",
        "timestamp_validity": "before_entry_unknown_until_joined",
        "economic_direction": "unknown",
        "materiality_level": "unknown",
        "classification_confidence": "low",
        "review_status": "auto_classified",
        "reason_code": "default_uninterpretable",
        "source_gap_flag": 1,
    }

    if lane == "trump_major_person_political_statements":
        label.update(
            company_specificity="macro_policy_general",
            catalyst_economic_link="broad_policy_or_geopolitical_background",
            actionability="hold_until_confirmed",
            economic_direction="unknown",
            materiality_level="unknown",
            classification_confidence="medium",
            reason_code="broad_policy_context_not_stock_entry_support",
            source_gap_flag=0,
        )
        return label

    if lane == "war_geopolitical_conflict_events":
        label.update(
            company_specificity="macro_policy_general",
            catalyst_economic_link="broad_policy_or_geopolitical_background",
            actionability="hold_until_confirmed",
            economic_direction="unknown",
            materiality_level="unknown",
            classification_confidence="medium",
            reason_code="geopolitical_context_not_company_catalyst",
            source_gap_flag=0,
        )
        return label

    if category in {"insider_or_sale_notice", "passive_13g", "activist_13d"} or re.search(r"\bform\s*4\b|\bprimary document\b|\b13g\b|\b13d\b", title_lower):
        label.update(
            company_specificity="company_direct",
            catalyst_economic_link="insider_sale_or_ownership_only",
            actionability="hold_until_confirmed",
            evidence_quality="generic_filing_or_ownership_only",
            economic_direction="unknown",
            materiality_level="unknown",
            classification_confidence="medium",
            reason_code="ownership_or_insider_filing_not_bullish_by_default",
            source_gap_flag=0,
        )
        return label

    if category == "company_ir_proxy" or re.search(r"\b8-k\b|\b6-k\b", title_lower):
        if has_direct_economic_language(title_lower):
            label.update(
                company_specificity="company_direct",
                catalyst_economic_link=direct_link_type(title_lower),
                actionability="support_entry",
                evidence_quality="title_contains_specific_economic_language",
                economic_direction="positive_or_material_unknown_requires_review",
                materiality_level="potentially_material",
                classification_confidence="medium",
                review_status="needs_human_review",
                reason_code="title_contains_specific_company_economic_language",
                source_gap_flag=0,
            )
            return label
        label.update(
            company_specificity="company_direct",
            catalyst_economic_link="unknown",
            actionability="uninterpretable_do_not_trade",
            evidence_quality="generic_filing_only",
            economic_direction="unknown",
            materiality_level="unknown",
            classification_confidence="low",
            review_status="rejected_uninterpretable",
            reason_code="generic_8k_or_ir_proxy_title_without_content",
            source_gap_flag=1,
        )
        return label

    if source_name.startswith("sec_"):
        label.update(
            company_specificity="company_direct",
            evidence_quality="title_only",
            actionability="uninterpretable_do_not_trade",
            review_status="rejected_uninterpretable",
            reason_code="sec_event_title_lacks_interpretable_economic_content",
            source_gap_flag=1,
        )
    return label


def has_direct_economic_language(title_lower: str) -> bool:
    patterns = [
        "contract",
        "award",
        "order",
        "backlog",
        "revenue",
        "sales",
        "guidance",
        "earnings",
        "results",
        "financial",
        "financing",
        "offering",
        "liquidity",
        "approval",
        "restriction",
    ]
    return any(p in title_lower for p in patterns)


def direct_link_type(title_lower: str) -> str:
    if any(p in title_lower for p in ["contract", "award", "order", "backlog", "revenue", "sales"]):
        return "direct_revenue_contract_order_backlog"
    if any(p in title_lower for p in ["guidance", "earnings", "results", "financial"]):
        return "guidance_or_financial_update"
    if any(p in title_lower for p in ["financing", "offering", "liquidity"]):
        return "financing_liquidity_dilution"
    if any(p in title_lower for p in ["approval", "restriction"]):
        return "regulatory_approval_or_restriction"
    return "unknown"


def build_recent_aerospace_semantic_attachment(panel: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    recent = panel[
        panel["split_name"].astype(str).eq("recent_oos")
        & panel["theme_id"].astype(str).eq("aerospace_defense_space")
    ].copy()
    rows = []
    for _, entry in recent.iterrows():
        known = labels[
            (labels["event_date_obj"] < entry["trade_date"])
            | (
                labels["event_date_obj"].eq(entry["trade_date"])
                & labels["time_precision"].eq("timestamp")
                & labels["event_timestamp_dt"].notna()
                & (labels["event_timestamp_dt"] <= entry["entry_ts"])
            )
        ]
        symbol = str(entry["symbol"])
        theme = str(entry["theme_id"])
        political = relevant_events(within_window(known, entry["trade_date"], 7), "trump_major_person_political_statements", symbol, theme)
        geopolitical = relevant_events(within_window(known, entry["trade_date"], 7), "war_geopolitical_conflict_events", symbol, theme)
        institution_window = within_window(known, entry["trade_date"], 30)
        ceo_ir_window = within_window(known, entry["trade_date"], 14)
        institution = institution_window[
            institution_window["source_lane"].eq("institution_investment_actions") & tag_contains(institution_window["symbol_tags"], symbol)
        ]
        ceo_ir = ceo_ir_window[
            ceo_ir_window["source_lane"].eq("ceo_ir_transcripts_and_presentations") & tag_contains(ceo_ir_window["symbol_tags"], symbol)
        ]
        linked = pd.concat([political, geopolitical, institution, ceo_ir], ignore_index=True)
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "symbol": entry["symbol"],
                "entry_ts": entry["entry_ts"],
                "net_return_from_entry": entry["net_return_from_entry"],
                "event_count": int(len(linked)),
                "support_entry_count": int(linked["actionability"].astype(str).eq("support_entry").sum()) if not linked.empty else 0,
                "hold_until_confirmed_count": int(linked["actionability"].astype(str).eq("hold_until_confirmed").sum()) if not linked.empty else 0,
                "uninterpretable_count": int(linked["actionability"].astype(str).eq("uninterpretable_do_not_trade").sum()) if not linked.empty else 0,
                "source_gap_count": int(linked["source_gap_flag"].fillna(0).astype(int).sum()) if not linked.empty else 0,
                "company_direct_support_entry_count": int(
                    (
                        linked["company_specificity"].astype(str).eq("company_direct")
                        & linked["actionability"].astype(str).eq("support_entry")
                    ).sum()
                )
                if not linked.empty
                else 0,
                "semantic_source_certified_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def within_window(events: pd.DataFrame, entry_date: Any, days: int) -> pd.DataFrame:
    entry_ts = pd.Timestamp(entry_date)
    start_date = (entry_ts - pd.Timedelta(days=days)).date()
    end_date = entry_ts.date()
    return events[
        events["event_date_obj"].notna()
        & (events["event_date_obj"] >= start_date)
        & (events["event_date_obj"] <= end_date)
    ]


def build_source_gap_report(labels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in labels.groupby(["source_lane", "event_category", "actionability", "reason_code"], dropna=False):
        rows.append(
            {
                "source_lane": keys[0],
                "event_category": keys[1],
                "actionability": keys[2],
                "reason_code": keys[3],
                "event_count": int(len(group)),
                "source_gap_rate": float(group["source_gap_flag"].fillna(0).astype(int).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("event_count", ascending=False).reset_index(drop=True)


def build_pass_fail(labels: pd.DataFrame, recent_aerospace: pd.DataFrame) -> pd.DataFrame:
    generic_support = labels[
        labels["evidence_quality"].astype(str).isin(["generic_filing_only", "generic_filing_or_ownership_only"])
        & labels["actionability"].astype(str).eq("support_entry")
    ]
    broad_support = labels[
        labels["catalyst_economic_link"].astype(str).eq("broad_policy_or_geopolitical_background")
        & labels["actionability"].astype(str).eq("support_entry")
    ]
    recent_support_total = int(recent_aerospace["company_direct_support_entry_count"].sum()) if not recent_aerospace.empty else 0
    return pd.DataFrame(
        [
            {
                "gate": "schema_fields_complete",
                "pass_flag": int(set(SCHEMA_FIELDS).issubset(labels.columns)),
                "observed_value": ",".join([field for field in SCHEMA_FIELDS if field in labels.columns]),
                "required_value": "all semantic schema fields present",
            },
            {
                "gate": "generic_filings_not_support_entry",
                "pass_flag": int(generic_support.empty),
                "observed_value": f"generic_support_count={len(generic_support)}",
                "required_value": "generic 8-K/Form4/title-only filings cannot be support_entry",
            },
            {
                "gate": "broad_policy_not_direct_stock_support",
                "pass_flag": int(broad_support.empty),
                "observed_value": f"broad_support_count={len(broad_support)}",
                "required_value": "broad policy/geopolitical events cannot be direct stock entry support",
            },
            {
                "gate": "recent_aerospace_source_certification",
                "pass_flag": 0,
                "observed_value": f"company_direct_support_entry_count={recent_support_total}",
                "required_value": "recent aerospace needs company-direct interpretable support before entry can be restored",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "semantic sidecar only; not score input",
                "required_value": "semantic labels must pass OOS/cost/source gates before assignment use",
            },
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT agreed binary source presence is insufficient and recommended evidence quality, timestamp validity, economic direction, materiality, confidence, and review status fields.",
            }
        ]
    )


def build_decision(labels: pd.DataFrame, recent_aerospace: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    source_pass = int(pass_fail[pass_fail["gate"].eq("recent_aerospace_source_certification")]["pass_flag"].iloc[0])
    source_gap_rate = float(labels["source_gap_flag"].fillna(0).astype(int).mean()) if not labels.empty else 1.0
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "IMPLEMENT_SEMANTIC_SOURCE_SIDECAR_FAIL_AEROSPACE_CERTIFICATION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "semantic_source_sidecar_status": "IMPLEMENTED_EVALUATION_ONLY",
                "recent_aerospace_trade_count": int(len(recent_aerospace)),
                "recent_aerospace_source_certification_pass_flag": source_pass,
                "source_gap_rate": source_gap_rate,
                "semantic_labels_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Fetch or parse full official source text for aerospace/space events, then rerun semantic certification before restoring entry.",
            }
        ]
    )


def render_report(
    labels: pd.DataFrame,
    recent_aerospace: pd.DataFrame,
    source_gap: pd.DataFrame,
    pass_fail: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task622 Source Semantic Interpretation Sidecar",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- This is evaluation-only. Semantic labels are not trading score inputs.",
        f"- Recent aerospace source certification pass: {int(d['recent_aerospace_source_certification_pass_flag'])}",
        "",
        "## Quant Expert Report",
        "",
        "### Semantic Schema Fields",
        "",
        "| Field | Purpose |",
        "|---|---|",
    ]
    for field in SCHEMA_FIELDS:
        lines.append(f"| `{field}` | source interpretation field |")
    lines.extend(
        [
            "",
            "### Recent Aerospace Semantic Attachment",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| recent aerospace trades | {int(len(recent_aerospace))} |",
            f"| company-direct support-entry count | {int(recent_aerospace['company_direct_support_entry_count'].sum()) if not recent_aerospace.empty else 0} |",
            f"| source gap count | {int(recent_aerospace['source_gap_count'].sum()) if not recent_aerospace.empty else 0} |",
            "",
            "### Top Source Gaps",
            "",
            "| Lane | Category | Actionability | Reason | Events | Gap Rate |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for _, row in source_gap.head(12).iterrows():
        lines.append(
            f"| `{row['source_lane']}` | `{row['event_category']}` | `{row['actionability']}` | "
            f"`{row['reason_code']}` | {int(row['event_count'])} | {float(row['source_gap_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "### GPT Review",
            "",
            f"- Captured status: `{gpt_review.iloc[0]['captured_status']}`",
            f"- Summary: {gpt_review.iloc[0]['summary_point']}",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Source is no longer yes/no.",
            "- Generic 8-K, Form 4, broad policy, and source density cannot support entry.",
            "- If the content cannot be interpreted, it becomes source gap and cannot trade.",
            "- Aerospace/space entry remains blocked until full source text proves a real company-specific catalyst.",
            "",
            "## Pass/Fail Matrix",
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
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `source_semantic_labels.csv`",
            "- `recent_aerospace_semantic_attachment.csv`",
            "- `source_gap_report.csv`",
            "- `task_622_pass_fail_matrix.csv`",
            "- `task_622_gpt_semantic_schema_review_status.csv`",
            "- `task_622_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task622_source_semantic_interpretation_sidecar`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task622_source_semantic_interpretation_sidecar(out_dir=args.out_dir)
    row = artifacts["task_622_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={row['decision']} source_gap_rate={float(row['source_gap_rate']):.2%}")


if __name__ == "__main__":
    main()
