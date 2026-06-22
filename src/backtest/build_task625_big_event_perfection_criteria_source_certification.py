from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Callable

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel
from src.backtest.build_task623_big_event_interpretation_scoring_sidecar import (
    BIG_EVENT_LANES,
    build_task623_big_event_interpretation_scoring_sidecar,
    linked_events_for_entry,
)


TASK_ID = "Task625"
REPORT_DIR = Path("docs/reports/task_625_big_event_perfection_criteria_source_certification")
RAW_TEXT_DIR = Path("data/raw/task_625_big_event_source_text")
USER_AGENT = "Mozilla/5.0 Task625 source certification research"

FetchResult = tuple[int, str, str]
Fetcher = Callable[[str], FetchResult]


def build_task625_big_event_perfection_criteria_source_certification(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
    raw_text_dir: Path = RAW_TEXT_DIR,
    fetch_live: bool = True,
    max_events: int | None = None,
    fetcher: Fetcher | None = None,
) -> dict[str, pd.DataFrame]:
    task623 = build_task623_big_event_interpretation_scoring_sidecar()
    scored = task623["event_interpretation_scores"]
    panel = load_panel(task617_panel_path)
    nonzero = select_nonzero_big_events(scored, max_events=max_events)
    linked_ids = linked_recent_aerospace_high_impact_event_ids(panel, scored)
    certification = certify_event_sources(nonzero, raw_text_dir=raw_text_dir, fetch_live=fetch_live, fetcher=fetcher)
    criteria = build_perfection_criteria(scored, nonzero, certification, linked_ids)
    plan = build_implementation_plan()
    decision = build_decision(criteria, certification, linked_ids)
    gpt_review = build_gpt_review_status()

    out_dir.mkdir(parents=True, exist_ok=True)
    certification.to_csv(out_dir / "task_625_source_certification_matrix.csv", index=False)
    criteria.to_csv(out_dir / "task_625_perfection_criteria_matrix.csv", index=False)
    plan.to_csv(out_dir / "task_625_implementation_plan.csv", index=False)
    decision.to_csv(out_dir / "task_625_decision.csv", index=False)
    gpt_review.to_csv(out_dir / "task_625_gpt_perfection_review_status.csv", index=False)
    (out_dir / "task_625_big_event_perfection_criteria_source_certification.md").write_text(
        render_report(criteria, certification, plan, decision, gpt_review, linked_ids),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_625_source_certification_matrix": certification,
        "task_625_perfection_criteria_matrix": criteria,
        "task_625_implementation_plan": plan,
        "task_625_decision": decision,
        "task_625_gpt_perfection_review_status": gpt_review,
    }


def select_nonzero_big_events(scored: pd.DataFrame, *, max_events: int | None) -> pd.DataFrame:
    nonzero = scored[
        scored["source_lane"].astype(str).isin(BIG_EVENT_LANES)
        & scored["composite_interpretation_score"].astype(float).abs().gt(0.0)
    ].copy()
    nonzero = nonzero.drop_duplicates("event_id").sort_values(["event_date", "event_id"]).reset_index(drop=True)
    if max_events is not None:
        nonzero = nonzero.head(max_events).copy()
    return nonzero


def linked_recent_aerospace_high_impact_event_ids(panel: pd.DataFrame, scored: pd.DataFrame) -> set[str]:
    recent = panel[
        panel["split_name"].astype(str).eq("recent_oos")
        & panel["theme_id"].astype(str).eq("aerospace_defense_space")
    ].copy()
    ids: set[str] = set()
    for _, entry in recent.iterrows():
        linked = linked_events_for_entry(scored, entry)
        linked = linked[linked["risk_off_certified_flag"].astype(int).eq(1)]
        ids.update(linked["event_id"].astype(str).tolist())
    return ids


def certify_event_sources(
    events: pd.DataFrame,
    *,
    raw_text_dir: Path,
    fetch_live: bool,
    fetcher: Fetcher | None,
) -> pd.DataFrame:
    raw_text_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    cache: dict[str, FetchResult] = {}
    for _, event in events.iterrows():
        url = str(event.get("source_url", "") or "").strip()
        if not url:
            result = (0, "", "")
        elif url in cache:
            result = cache[url]
        elif fetcher is not None:
            result = fetcher(url)
            cache[url] = result
        elif fetch_live:
            result = fetch_official_text(url)
            cache[url] = result
        else:
            result = (0, "", "")
        status_code, final_url, text = result
        normalized_text = normalize_text(text)
        text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest() if normalized_text else ""
        raw_text_path = ""
        if normalized_text:
            safe_id = hashlib.sha256(str(event["event_id"]).encode("utf-8")).hexdigest()[:16]
            raw_file = raw_text_dir / f"{safe_id}_{text_hash[:12]}.txt"
            raw_file.write_text(normalized_text, encoding="utf-8")
            raw_text_path = raw_file.as_posix()
        title = str(event.get("event_title", "") or "")
        title_hits = title_token_hit_count(title, normalized_text)
        certified = int(status_code == 200 and len(normalized_text) >= 500 and title_hits >= 1)
        rows.append(
            {
                "event_id": event["event_id"],
                "source_lane": event["source_lane"],
                "event_date": event["event_date"],
                "event_title": title,
                "source_url": url,
                "final_url": final_url,
                "http_status": int(status_code),
                "official_source_url_flag": int(is_official_source_url(url)),
                "source_text_char_count": int(len(normalized_text)),
                "source_text_hash": text_hash,
                "raw_text_path": raw_text_path,
                "title_token_hit_count": int(title_hits),
                "source_text_certified_flag": certified,
                "composite_interpretation_score": float(event["composite_interpretation_score"]),
                "score_action": event["score_action"],
                "source_presence_only_used_flag": 0,
                "gpt_score_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def fetch_official_text(url: str) -> FetchResult:
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
    except requests.RequestException:
        return (0, url, "")
    return (int(response.status_code), response.url, extract_visible_text(response.text))


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    container = soup.find("main") or soup.find("article") or soup.find("body") or soup
    return normalize_text(container.get_text(" "))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def title_token_hit_count(title: str, text: str) -> int:
    if not text:
        return 0
    text_lower = text.lower()
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z-]{3,}", title)
        if token.lower() not in {"with", "from", "that", "this", "related", "update", "updates"}
    ]
    return sum(1 for token in sorted(set(tokens)) if token in text_lower)


def is_official_source_url(url: str) -> bool:
    return "ofac.treasury.gov" in url or "whitehouse.gov" in url or "sec.gov" in url


def build_perfection_criteria(
    scored: pd.DataFrame,
    nonzero: pd.DataFrame,
    certification: pd.DataFrame,
    linked_ids: set[str],
) -> pd.DataFrame:
    nonzero_count = int(len(nonzero))
    certified_count = int(certification["source_text_certified_flag"].sum()) if not certification.empty else 0
    linked = certification[certification["event_id"].astype(str).isin(linked_ids)] if not certification.empty else pd.DataFrame()
    linked_certified = int(linked["source_text_certified_flag"].sum()) if not linked.empty else 0
    broad_support = scored[
        scored["event_scope"].astype(str).isin(["macro_policy_general", "theme_or_sector"])
        & scored["support_entry_certified_flag"].astype(int).eq(1)
    ]
    return pd.DataFrame(
        [
            {
                "gate": "perfect_criteria_defined",
                "pass_flag": 1,
                "observed_value": "source integrity, timing integrity, semantic action integrity, OOS integrity, cost/account integrity",
                "required_value": "firm-grade perfection gates are explicit and testable",
            },
            {
                "gate": "nonzero_scores_have_source_urls",
                "pass_flag": int(nonzero_count > 0 and nonzero["source_url"].astype(str).str.len().gt(0).all()),
                "observed_value": f"nonzero_events={nonzero_count}",
                "required_value": "every nonzero event score must have a source URL",
            },
            {
                "gate": "nonzero_scores_have_certified_source_text",
                "pass_flag": int(nonzero_count > 0 and certified_count == nonzero_count),
                "observed_value": f"certified={certified_count}/{nonzero_count}",
                "required_value": "every nonzero event score must have official source text and hash",
            },
            {
                "gate": "linked_recent_aerospace_high_impact_certified",
                "pass_flag": int(len(linked_ids) > 0 and linked_certified == len(linked_ids)),
                "observed_value": f"certified={linked_certified}/{len(linked_ids)}",
                "required_value": "all high-impact events attached to recent aerospace risk-off must be source certified",
            },
            {
                "gate": "broad_events_not_direct_support_entry",
                "pass_flag": int(broad_support.empty),
                "observed_value": f"broad_support_entry_count={len(broad_support)}",
                "required_value": "macro and sector events cannot become direct support-entry",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "perfection criteria and source certification layer only",
                "required_value": "source-certified scoring must be rerun through OOS, cost, and account gates before trading use",
            },
        ]
    )


def build_implementation_plan() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "priority": "P0",
                "work_item": "official_source_text_certification",
                "implementation": "certify every nonzero big-event score with source_url, final_url, http_status, source_text_hash, raw_text_path, and title-token evidence",
                "acceptance_gate": "nonzero_scores_have_certified_source_text",
            },
            {
                "priority": "P0",
                "work_item": "high_impact_linked_event_certification",
                "implementation": "separately certify events actually linked to recent aerospace risk-off trades",
                "acceptance_gate": "linked_recent_aerospace_high_impact_certified",
            },
            {
                "priority": "P1",
                "work_item": "source_text_semantic_rescore",
                "implementation": "rescore direction, transmission, directness, materiality, and evidence quality from certified text rather than title only",
                "acceptance_gate": "same input yields deterministic score and action",
            },
            {
                "priority": "P2",
                "work_item": "cost_account_rerun",
                "implementation": "rerun Task624-style action validation under cost stress and same-capital account simulation",
                "acceptance_gate": "full, validation, and recent OOS gates pass without direct support leakage",
            },
        ]
    )


def build_decision(criteria: pd.DataFrame, certification: pd.DataFrame, linked_ids: set[str]) -> pd.DataFrame:
    all_cert_gate = criteria[criteria["gate"].eq("nonzero_scores_have_certified_source_text")].iloc[0]
    linked_gate = criteria[criteria["gate"].eq("linked_recent_aerospace_high_impact_certified")].iloc[0]
    certified_count = int(certification["source_text_certified_flag"].sum()) if not certification.empty else 0
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "LOCK_PERFECTION_CRITERIA_AND_BUILD_SOURCE_CERTIFICATION_LAYER",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "nonzero_event_count": int(len(certification)),
                "source_text_certified_count": certified_count,
                "all_nonzero_source_certification_pass_flag": int(all_cert_gate["pass_flag"]),
                "linked_recent_aerospace_source_certification_pass_flag": int(linked_gate["pass_flag"]),
                "linked_recent_aerospace_high_impact_event_count": int(len(linked_ids)),
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Use certified source text to rescore Task623, then rerun Task624 action validation with cost/account gates.",
            }
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT judged Task623/624 incomplete because title-based semantic scores are not source-certified; perfection requires source integrity, timing integrity, action integrity, OOS robustness, and cost/account reruns.",
            }
        ]
    )


def render_report(
    criteria: pd.DataFrame,
    certification: pd.DataFrame,
    plan: pd.DataFrame,
    decision: pd.DataFrame,
    gpt_review: pd.DataFrame,
    linked_ids: set[str],
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task625 Big Event Perfection Criteria And Source Certification",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Source text certified: {int(d['source_text_certified_count'])} / {int(d['nonzero_event_count'])}",
        f"- Recent aerospace high-impact linked events: {int(d['linked_recent_aerospace_high_impact_event_count'])}",
        "- This locks the perfection standard and adds the first source-certification layer.",
        "",
        "## Quant Expert Report",
        "",
        "### Perfection Criteria",
        "",
        "| Gate | Pass | Observed | Required |",
        "|---|---:|---|---|",
    ]
    for _, row in criteria.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "### Implementation Plan",
            "",
            "| Priority | Work Item | Implementation | Acceptance Gate |",
            "|---|---|---|---|",
        ]
    )
    for _, row in plan.iterrows():
        lines.append(
            f"| `{row['priority']}` | `{row['work_item']}` | {row['implementation']} | `{row['acceptance_gate']}` |"
        )
    lines.extend(
        [
            "",
            "### Certification Sample",
            "",
            "| Event Date | Lane | Certified | Text Chars | Title Hits | Action | Title |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for _, row in certification.head(20).iterrows():
        title = str(row["event_title"]).replace("|", "/")[:100]
        lines.append(
            f"| {row['event_date']} | `{row['source_lane']}` | {int(row['source_text_certified_flag'])} | "
            f"{int(row['source_text_char_count'])} | {int(row['title_token_hit_count'])} | `{row['score_action']}` | {title} |"
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
            "- Task623/624 were not perfect because they scored mostly from titles.",
            "- Perfect means every nonzero score has an official source text and hash.",
            "- We started with source certification and separately track the high-impact aerospace-linked events.",
            "- This still does not approve trading. It prepares the next source-certified rescore.",
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_623_big_event_interpretation_scoring_sidecar/event_interpretation_scores.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_625_source_certification_matrix.csv`",
            "- `task_625_perfection_criteria_matrix.csv`",
            "- `task_625_implementation_plan.csv`",
            "- `task_625_gpt_perfection_review_status.csv`",
            "- `task_625_decision.csv`",
            "- `artifact_manifest.csv`",
            f"- raw source text files under `{RAW_TEXT_DIR.as_posix()}`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task625_big_event_perfection_criteria_source_certification`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--raw-text-dir", type=Path, default=RAW_TEXT_DIR)
    parser.add_argument("--max-events", type=int, default=None)
    parser.add_argument("--no-fetch-live", action="store_true")
    args = parser.parse_args()
    artifacts = build_task625_big_event_perfection_criteria_source_certification(
        out_dir=args.out_dir,
        raw_text_dir=args.raw_text_dir,
        fetch_live=not args.no_fetch_live,
        max_events=args.max_events,
    )
    row = artifacts["task_625_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"certified={int(row['source_text_certified_count'])}/{int(row['nonzero_event_count'])} "
        f"linked_pass={int(row['linked_recent_aerospace_source_certification_pass_flag'])}"
    )


if __name__ == "__main__":
    main()
