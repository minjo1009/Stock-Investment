from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "graphify-out" / "graph.json"
GRAPH_HTML_PATH = ROOT / "graphify-out" / "graph.html"
OUT_DIR = ROOT / "docs" / "graphify"
AUDIT_DIR = ROOT / "docs" / "audits"


def _norm(path: str) -> str:
    return path.replace("/", "\\")


def _community_label(top_files: list[str], cid: int) -> str:
    s = " | ".join(top_files).lower()
    if (
        "github source" in s
        or "tradingview sourcecode" in s
        or "참고 context" in s
        or "李멸퀬 context" in s
    ):
        return f"External Reference Corpus / Community {cid}"
    if "src\\ui\\app.py" in s or "src\\ui\\" in s:
        return "UI / Streamlit Review"
    if "task_091a_controlled_broker_lifecycle.py" in s or "src\\integration\\kis_client.py" in s:
        return "Execution / Broker Lifecycle"
    if "src\\state\\store.py" in s or "src\\execution\\cancel_loop.py" in s:
        return "State / Reconciliation / Safety"
    if (
        "task_087_pilot_evidence.py" in s
        or "task_088_evidence_decision.py" in s
        or "task_089_market_data_signal_refresh.py" in s
    ):
        return "Paper Ops / Evidence Loop"
    if "src\\backtest\\engine_full.py" in s or "src\\backtest\\engine.py" in s:
        return "Backtest / Strategy Engine"
    if "src\\backtest\\analysis_" in s:
        return "Backtest Analytics / Task Reports"
    if "src\\backtest\\entry_gates.py" in s or "analysis_minimal_regime_entry_gate_076.py" in s:
        return "Entry Gate / Regime Analysis"
    if "tests\\unit\\test_structure.py" in s:
        return "Foundation / Contract Tests"
    if "tests\\" in s:
        return "Tests / Regression"
    if "data\\catalog.py" in s or "data\\quality.py" in s:
        return "Data Catalog / Quality"
    if "docs\\" in s:
        return "Docs / Reporting"
    if top_files:
        top = top_files[0].replace("/", "\\")
        parts = [p for p in top.split("\\") if p]
        if len(parts) >= 2:
            return f"{parts[0]} / {parts[1]} Cluster"
        if parts:
            return f"{parts[0]} Cluster"
    return f"Community {cid} Cluster"


def _build_context_packs() -> dict[str, Any]:
    return {
        "T092_SIGNAL_ALIGNMENT": {
            "purpose": "Verify runtime/backtest consistency for data-feature-selection-signal.",
            "core_files": [
                "src/backtest/engine_full.py",
                "src/strategy/conditions.py",
                "src/app/run_trade_once.py",
                "src/app/task_089_market_data_signal_refresh.py",
                "src/ui/trade_review_model.py",
                "src/ui/app.py",
                "docs/reports/task_092/task_092_signal_alignment.md",
            ],
            "related_tests": [
                "tests/test_run_trade_once_runtime_signal.py",
                "tests/test_engine_entry_gate_off.py",
            ],
        },
        "T094_RISK_OVERLAY": {
            "purpose": "Non-alpha risk overlay evaluation and attribution.",
            "core_files": [
                "src/backtest/analysis_drawdown_control_094.py",
                "src/backtest/analysis_risk_component_review_094.py",
                "src/backtest/analysis_risk_adoption_095.py",
                "src/backtest/analysis_capital_backtest_093.py",
                "src/backtest/analysis_capital_failure_review_093.py",
                "docs/reports/task_093_review/task_093_review_failure_analysis.md",
                "docs/reports/task_094/task_094_risk_architecture.md",
                "docs/reports/task_094_review/task_094_review_component_attribution.md",
                "docs/reports/task_095/task_095_risk_adoption.md",
            ],
            "related_tests": [],
        },
        "BROKER_LIFECYCLE": {
            "purpose": "Order submit/cancel/reconcile/late-fill safety path.",
            "core_files": [
                "src/app/task_091a_controlled_broker_lifecycle.py",
                "src/integration/kis_client.py",
                "src/execution/cancel_loop.py",
                "src/app/reconciliation.py",
                "src/state/store.py",
                "docs/contracts/execution_state_contract.md",
                "docs/contracts/cancel_reconcile_loop_contract.md",
                "docs/reports/task_091a/task_091a_controlled_lifecycle.md",
            ],
            "related_tests": [
                "tests/test_cancel_loop.py",
                "tests/test_kis_cancel_contract.py",
                "tests/test_task_091a_controlled_lifecycle.py",
            ],
        },
        "PHASE5_PAPER_OPS": {
            "purpose": "Realtime market refresh + evidence collection + aggregate decision loop.",
            "core_files": [
                "scripts/run_task_089_market_refresh.ps1",
                "scripts/run_phase5_paper_loop.ps1",
                "src/app/task_089_market_data_signal_refresh.py",
                "src/app/task_087_pilot_evidence.py",
                "src/app/task_088_evidence_decision.py",
                "src/app/run_trade_once.py",
                "docs/reports/task_086/task_086_risk_guard_lock.md",
                "docs/reports/task_086/task_086_sample_plan.md",
                "docs/reports/task_088/task_088_evidence_summary.md",
            ],
            "related_tests": [
                "tests/test_task_087_evidence_schema.py",
                "tests/test_task_088_evidence_decision.py",
                "tests/test_phase5_orchestration_script.py",
            ],
        },
        "UI_REPORTING": {
            "purpose": "Streamlit rendering and report ingestion boundaries.",
            "core_files": [
                "src/ui/app.py",
                "src/ui/trade_review_model.py",
                "docs/INDEX.md",
                "docs/reports",
                "docs/audits",
            ],
            "related_tests": [],
        },
    }


def _apply_labels_to_graph_html(community_labels: list[dict[str, Any]]) -> str:
    if not GRAPH_HTML_PATH.exists():
        return "missing_graph_html"

    html = GRAPH_HTML_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"const RAW_NODES = (.*?);\s*const RAW_EDGES =", re.DOTALL)
    m = pattern.search(html)
    if not m:
        return "raw_nodes_block_not_found"

    raw_nodes_json = m.group(1)
    try:
        raw_nodes = json.loads(raw_nodes_json)
    except json.JSONDecodeError:
        return "raw_nodes_json_decode_failed"

    label_map = {
        int(row["community_id"]): str(row["label"])
        for row in community_labels
        if "community_id" in row and "label" in row
    }

    changed_nodes = 0
    for node in raw_nodes:
        cid = node.get("community")
        if isinstance(cid, int) and cid in label_map:
            new_label = label_map[cid]
            if node.get("community_name") != new_label:
                node["community_name"] = new_label
                changed_nodes += 1

    new_nodes_json = json.dumps(raw_nodes, ensure_ascii=False, separators=(",", ":"))
    new_html = html[: m.start(1)] + new_nodes_json + html[m.end(1) :]

    legend_pattern = re.compile(r"const LEGEND = (.*?);", re.DOTALL)
    lm = legend_pattern.search(new_html)
    changed_legend = 0
    if lm:
        try:
            legend = json.loads(lm.group(1))
            for row in legend:
                cid = row.get("cid")
                if isinstance(cid, int) and cid in label_map:
                    new_label = label_map[cid]
                    if row.get("label") != new_label:
                        row["label"] = new_label
                        changed_legend += 1
            new_legend_json = json.dumps(legend, ensure_ascii=False, separators=(",", ":"))
            new_html = new_html[: lm.start(1)] + new_legend_json + new_html[lm.end(1) :]
        except json.JSONDecodeError:
            pass

    GRAPH_HTML_PATH.write_text(new_html, encoding="utf-8")
    labeled_copy = GRAPH_HTML_PATH.with_name("graph_labeled.html")
    labeled_copy.write_text(new_html, encoding="utf-8")
    return f"ok_changed_nodes={changed_nodes};legend_labels_changed={changed_legend}"


def main() -> int:
    if not GRAPH_PATH.exists():
        raise SystemExit(f"graph.json not found: {GRAPH_PATH}")
    g = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = g.get("nodes", [])
    links = g.get("links", [])

    id2node = {n["id"]: n for n in nodes if "id" in n}
    degree = Counter()
    for e in links:
        s, t = e.get("source"), e.get("target")
        if s in id2node:
            degree[s] += 1
        if t in id2node:
            degree[t] += 1

    comm_files: dict[int, list[str]] = defaultdict(list)
    for n in nodes:
        c = n.get("community")
        sf = n.get("source_file")
        if isinstance(c, int) and sf:
            comm_files[c].append(_norm(sf))

    community_labels: list[dict[str, Any]] = []
    for cid in sorted(comm_files.keys()):
        top_files = [f for f, _ in Counter(comm_files[cid]).most_common(6)]
        community_labels.append(
            {
                "community_id": cid,
                "label": _community_label(top_files, cid),
                "top_files": top_files,
            }
        )

    god_nodes: list[dict[str, Any]] = []
    for nid, deg in degree.most_common(60):
        n = id2node[nid]
        source_file = _norm(str(n.get("source_file", "")))
        lowered = source_file.lower()
        external = ("github source" in lowered) or ("tradingview sourcecode" in lowered) or ("李멸퀬 context" in lowered) or ("참고 context" in lowered)
        god_nodes.append(
            {
                "id": nid,
                "label": n.get("label"),
                "source_file": source_file,
                "degree": int(deg),
                "external_reference": external,
            }
        )
    local_god_nodes = [x for x in god_nodes if not x["external_reference"]][:20]

    context_packs = _build_context_packs()
    html_label_result = _apply_labels_to_graph_html(community_labels)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "community_labels.json").write_text(json.dumps(community_labels, ensure_ascii=True, indent=2), encoding="utf-8")
    (OUT_DIR / "god_nodes_top20_local.json").write_text(json.dumps(local_god_nodes, ensure_ascii=True, indent=2), encoding="utf-8")
    (OUT_DIR / "context_packs.json").write_text(json.dumps(context_packs, ensure_ascii=True, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# Task GRAPHIFY-002 - Community Labeling & Context Packs")
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append(f"- communities labeled: {len(community_labels)}")
    md_lines.append(f"- local god nodes exported: {len(local_god_nodes)}")
    md_lines.append(f"- context packs exported: {len(context_packs)}")
    md_lines.append("")
    md_lines.append("## Top Local God Nodes")
    for row in local_god_nodes[:20]:
        md_lines.append(f"- {row['label']} :: {row['source_file']} (degree={row['degree']})")
    md_lines.append("")
    md_lines.append("## Context Pack Keys")
    for key in context_packs:
        md_lines.append(f"- {key}")
    md_lines.append("")
    md_lines.append("## Graph HTML Label Injection")
    md_lines.append(f"- result: {html_label_result}")
    md_lines.append("- labeled view: graphify-out/graph.html (overwritten)")
    md_lines.append("- labeled copy: graphify-out/graph_labeled.html")
    md_lines.append("")
    (AUDIT_DIR / "task_graphify_002_context_pack.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    json_report = {
        "status": "PASS",
        "community_labels_path": "docs/graphify/community_labels.json",
        "god_nodes_path": "docs/graphify/god_nodes_top20_local.json",
        "context_packs_path": "docs/graphify/context_packs.json",
        "community_count": len(community_labels),
        "local_god_nodes_count": len(local_god_nodes),
        "context_pack_count": len(context_packs),
        "graph_html_label_injection": html_label_result,
    }
    (AUDIT_DIR / "task_graphify_002_context_pack.json").write_text(json.dumps(json_report, ensure_ascii=True, indent=2), encoding="utf-8")

    print("written=docs/graphify/community_labels.json")
    print("written=docs/graphify/god_nodes_top20_local.json")
    print("written=docs/graphify/context_packs.json")
    print("written=docs/audits/task_graphify_002_context_pack.md")
    print("written=docs/audits/task_graphify_002_context_pack.json")
    print(f"graph_html_labels={html_label_result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
