from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task609P"
REPORT_DIR = Path("docs/reports/task_609p_plugin_utilization_map")


def build_task609p_plugin_utilization_map(
    *,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    plugin_priority = build_plugin_priority()
    workflow_map = build_workflow_map()
    source_lane_map = build_source_lane_map()
    guardrails = build_guardrails()
    decision = build_decision(plugin_priority, workflow_map, source_lane_map, guardrails)

    out_dir.mkdir(parents=True, exist_ok=True)
    plugin_priority.to_csv(out_dir / "plugin_priority_map.csv", index=False)
    workflow_map.to_csv(out_dir / "project_workflow_plugin_map.csv", index=False)
    source_lane_map.to_csv(out_dir / "task609_source_lane_plugin_map.csv", index=False)
    guardrails.to_csv(out_dir / "plugin_guardrails.csv", index=False)
    decision.to_csv(out_dir / "task_609p_decision.csv", index=False)
    (out_dir / "task_609p_plugin_utilization_map.md").write_text(
        render_report(plugin_priority, workflow_map, source_lane_map, guardrails, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "plugin_priority_map": plugin_priority,
        "project_workflow_plugin_map": workflow_map,
        "task609_source_lane_plugin_map": source_lane_map,
        "plugin_guardrails": guardrails,
        "task_609p_decision": decision,
    }


def build_plugin_priority() -> pd.DataFrame:
    rows = [
        {
            "plugin": "Public Equity Investing",
            "priority": "P0",
            "best_use": "listed-equity catalyst, earnings, IR, valuation context, price/quote evidence",
            "project_fit": "direct_fit",
            "main_tools_or_apps": "Quartr; Alpaca; Slack; Gmail",
            "use_now": "YES_FOR_TASK609_AND_TASK610",
            "why": "Our strategy trades listed US equities, so this is the closest domain owner.",
        },
        {
            "plugin": "Data Analytics",
            "priority": "P0",
            "best_use": "backtest diagnostics, KPI gates, data quality, reports, dashboards, validation views",
            "project_fit": "direct_fit",
            "main_tools_or_apps": "datascienceWidgets; GitHub; Slack; Gmail; Google Calendar",
            "use_now": "YES_FOR_BACKTEST_AND_FRONTEND_REPORTING",
            "why": "It turns backtest and live-capture outputs into auditable tables, charts, and dashboards.",
        },
        {
            "plugin": "Investment Banking",
            "priority": "P2",
            "best_use": "transaction, financing, deal memo, board package, valuation pack",
            "project_fit": "limited_fit",
            "main_tools_or_apps": "Quartr; Slack; Gmail",
            "use_now": "ONLY_FOR_SPECIAL_DEEP_DIVE_OR_CAPITAL_MARKETS_CONTEXT",
            "why": "It is useful for issuer/deal context, but daily trading work should not route through banking workflows.",
        },
    ]
    return pd.DataFrame(rows)


def build_workflow_map() -> pd.DataFrame:
    rows = [
        {
            "project_workflow": "Task609A realtime intelligence source capture",
            "primary_plugin": "Public Equity Investing",
            "support_plugin": "Data Analytics",
            "owner_team": "Data & Market Microstructure",
            "action": "Use Quartr for first-party IR events and Alpaca for market snapshots when a workflow needs current evidence.",
            "promotion_rule": "Captured source id and timestamp must exist before any paper gate uses it.",
        },
        {
            "project_workflow": "Task610 historical intelligence replay",
            "primary_plugin": "Public Equity Investing",
            "support_plugin": "Data Analytics",
            "owner_team": "Backtest & Simulation Infra",
            "action": "Replay Task608 failures against event windows from IR, filings, news metadata, and price/quote state.",
            "promotion_rule": "No symbol/date proximity fallback; exact event ids and captured timestamps only.",
        },
        {
            "project_workflow": "Task611 paper-only gate simulation",
            "primary_plugin": "Data Analytics",
            "support_plugin": "Public Equity Investing",
            "owner_team": "Intraday Continuation Research",
            "action": "Measure block/wait/size-down effects with clean-winner damage, cost stress, and fold-forward checks.",
            "promotion_rule": "Gate must improve failures without cutting large clean winners.",
        },
        {
            "project_workflow": "Frontend trade explanation view",
            "primary_plugin": "Data Analytics",
            "support_plugin": "Public Equity Investing",
            "owner_team": "Frontend/UI",
            "action": "Expose price reason, news reason, source confidence, missing evidence, and gate result.",
            "promotion_rule": "Every visible explanation must map to a stored artifact row.",
        },
        {
            "project_workflow": "Deep issuer or capital-markets context",
            "primary_plugin": "Public Equity Investing",
            "support_plugin": "Investment Banking",
            "owner_team": "Regime Research",
            "action": "Use banking only when financing, issuance, M&A, covenant, or board-package context affects theme risk.",
            "promotion_rule": "Must stay context-only unless converted into repo-native source artifacts.",
        },
    ]
    return pd.DataFrame(rows)


def build_source_lane_map() -> pd.DataFrame:
    rows = [
        {
            "task609_source_lane": "regulatory_filing",
            "preferred_plugin": "Public Equity Investing",
            "preferred_app_or_tool": "Quartr",
            "project_use": "filing and report metadata for catalyst validation",
            "readiness_status": "AVAILABLE_TOOL_DISCOVERED_NOT_SOURCE_CERTIFIED",
        },
        {
            "task609_source_lane": "official_company_release_or_ir_event",
            "preferred_plugin": "Public Equity Investing",
            "preferred_app_or_tool": "Quartr",
            "project_use": "earnings calls, investor days, guidance, presentation, transcript context",
            "readiness_status": "AVAILABLE_TOOL_DISCOVERED_NOT_SOURCE_CERTIFIED",
        },
        {
            "task609_source_lane": "stock_quote_snapshot",
            "preferred_plugin": "Public Equity Investing",
            "preferred_app_or_tool": "Alpaca",
            "project_use": "latest quote, snapshot, minute bar, daily bar, previous daily bar",
            "readiness_status": "AVAILABLE_TOOL_DISCOVERED_NOT_SOURCE_CERTIFIED",
        },
        {
            "task609_source_lane": "backtest_diagnostic_report",
            "preferred_plugin": "Data Analytics",
            "preferred_app_or_tool": "datascienceWidgets",
            "project_use": "validated report/dashboard artifacts after bounded snapshot checks",
            "readiness_status": "AVAILABLE_TOOL_DISCOVERED_NOT_SOURCE_CERTIFIED",
        },
        {
            "task609_source_lane": "deal_or_financing_context",
            "preferred_plugin": "Investment Banking",
            "preferred_app_or_tool": "Quartr plus banking workflows",
            "project_use": "context-only review for issuance, M&A, restructuring, or financing risk",
            "readiness_status": "LOW_PRIORITY_CONTEXT_ONLY",
        },
    ]
    return pd.DataFrame(rows)


def build_guardrails() -> pd.DataFrame:
    rows = [
        {
            "guardrail": "no_plugin_changes_acceptance",
            "rule": "Plugins cannot change NOT_ACCEPTED, deployment readiness, broker truth, or replay status without repo-native artifacts and validation.",
            "severity": "P0",
        },
        {
            "guardrail": "no_llm_direct_trade",
            "rule": "No plugin or LLM output may place, recommend, or trigger live trades directly.",
            "severity": "P0",
        },
        {
            "guardrail": "quartr_provider_sequence",
            "rule": "Before any Quartr tool call, load the Quartr provider guide and follow its citation and connector playbook rules.",
            "severity": "P0",
        },
        {
            "guardrail": "alpaca_market_data_not_broker_truth",
            "rule": "Alpaca price or quote output can support market evidence, but it is not broker-truth execution evidence.",
            "severity": "P0",
        },
        {
            "guardrail": "data_analytics_validate_before_render",
            "rule": "Validate Data Analytics report/dashboard manifests before rendering hosted artifacts.",
            "severity": "P1",
        },
        {
            "guardrail": "investment_banking_context_only",
            "rule": "Investment Banking routes are for deal, financing, valuation, or board context; they are not the default trading workflow.",
            "severity": "P2",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(
    plugin_priority: pd.DataFrame,
    workflow_map: pd.DataFrame,
    source_lane_map: pd.DataFrame,
    guardrails: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "USE_PUBLIC_EQUITY_AND_DATA_ANALYTICS_AS_P0_IB_AS_P2_CONTEXT",
                "pass_flag": 1,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "p0_plugin_count": int(plugin_priority["priority"].astype(str).eq("P0").sum()),
                "workflow_count": int(len(workflow_map)),
                "source_lane_count": int(len(source_lane_map)),
                "guardrail_count": int(len(guardrails)),
                "real_capital_status": "FORBIDDEN",
                "next_task": "Task609A source capture using Public Equity routes plus Data Analytics validation surface",
            }
        ]
    )


def render_report(
    plugin_priority: pd.DataFrame,
    workflow_map: pd.DataFrame,
    source_lane_map: pd.DataFrame,
    guardrails: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    decision_row = decision.iloc[0]
    p0_plugins = plugin_priority.loc[plugin_priority["priority"].eq("P0"), "plugin"].tolist()
    lines = [
        "# Task609P Plugin Utilization Map",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision_row['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        f"- P0 plugins: {', '.join(p0_plugins)}",
        "- Investment Banking: P2 context-only, not a daily trading workflow.",
        "- Next action: use Public Equity routes for source capture and Data Analytics for replay/report validation.",
        "",
        "## Quant Expert Report",
        "",
        "### Plugin Roles",
        "",
        "- Public Equity Investing owns listed-equity research context, catalysts, earnings, IR documents, and price/quote evidence.",
        "- Data Analytics owns backtest diagnostics, KPI gates, reports, dashboards, and validation surfaces.",
        "- Investment Banking is useful only when issuer financing, deal, M&A, restructuring, or board context matters.",
        "",
        "### Source Readiness",
        "",
        "- Tools were discovered, but this task does not certify any source feed as production-ready.",
        "- Public Equity and Investment Banking saved setup context is missing, so workflows should attempt real reads only when needed.",
        "- Data Analytics source-routing preferences and semantic layers are missing; use project files until onboarding or explicit source setup exists.",
        "",
        "### Exact Join Keys",
        "",
        "- Any plugin output must become repo-native rows before strategy use.",
        "- Required keys remain `source_id`, `published_at_utc`, `captured_at_utc`, `symbol`, `theme_id`, and `evidence_hash`.",
        "- No symbol/date proximity fallback is allowed.",
        "",
        "### Leakage Audit",
        "",
        "- Plugin analysis cannot see future trade outcome labels during assignment.",
        "- Quartr/Alpaca/Data Analytics outputs are evidence or review inputs, not strategy acceptance evidence by themselves.",
        "- Broker truth remains separate from market data snapshots.",
        "",
        "### Remaining Blockers",
        "",
        "- No live source capture loop is connected yet.",
        "- No Task608 failure has been replayed against plugin-derived event windows yet.",
        "- No dashboard/report artifact has been rendered for the intelligence layer yet.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 사장님, 제일 쓸만한 건 Public Equity와 Data Analytics입니다.",
        "- Public Equity는 뉴스/실적콜/IR/가격 근거를 가져오는 쪽입니다.",
        "- Data Analytics는 그 근거가 진짜 성과를 개선했는지 표와 차트로 검증하는 쪽입니다.",
        "- Investment Banking은 평소에는 쓰지 말고, 기업의 자금조달/인수합병/구조조정 이슈가 테마를 흔들 때만 씁니다.",
        "- 이 플러그인들이 있어도 전략은 아직 미승인입니다.",
        "",
        "## Artifact Manifest",
        "",
        "### Inputs",
        "",
        "- Public Equity Investing, Investment Banking, and Data Analytics plugin skill/router instructions.",
        "- Discovered Alpaca, Quartr, and Data Analytics widget tool surfaces.",
        "",
        "### Outputs",
        "",
        "- `plugin_priority_map.csv`",
        "- `project_workflow_plugin_map.csv`",
        "- `task609_source_lane_plugin_map.csv`",
        "- `plugin_guardrails.csv`",
        "- `task_609p_decision.csv`",
        "- `artifact_manifest.csv`",
        "",
        "### Row Counts",
        "",
        f"- plugin_priority_rows: {len(plugin_priority)}",
        f"- workflow_rows: {len(workflow_map)}",
        f"- source_lane_rows: {len(source_lane_map)}",
        f"- guardrail_rows: {len(guardrails)}",
        "",
        "### Validation Commands",
        "",
        "- `python -m unittest tests.test_task609p_plugin_utilization_map`",
        "- `python scripts/task_registry_validate.py`",
        "- `python scripts/operating_closeout_validate.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task609p_plugin_utilization_map(out_dir=args.out_dir)
    decision = artifacts["task_609p_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
