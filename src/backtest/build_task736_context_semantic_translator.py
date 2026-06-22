from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.context_semantic_translator import translate_context
from src.backtest.source_circuit_interpreters import interpret_source_event


TASK_ID = "Task736"
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_736_context_semantic_translator")


def build_task736(*, event_detail_path: Path = EVENT_DETAIL, out_dir: Path = OUT_DIR) -> dict[str, pd.DataFrame]:
    events = pd.read_csv(event_detail_path)
    contexts = build_current_contexts(events)
    translations = pd.DataFrame([translate_context(row) for _, row in contexts.iterrows()])
    semantic_distribution = build_semantic_distribution(translations)
    transmission_distribution = build_transmission_distribution(translations)
    layer_edges = build_layer_modifier_edges(translations)
    guardrail = build_guardrail(translations)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(translations, layer_edges, guardrail)
    pass_fail = build_pass_fail(translations, semantic_distribution, transmission_distribution, layer_edges, guardrail)
    outputs = {
        "task736_semantic_translation.csv": translations,
        "task736_semantic_state_distribution.csv": semantic_distribution,
        "task736_transmission_channel_distribution.csv": transmission_distribution,
        "task736_layer_modifier_edges.csv": layer_edges,
        "task736_guardrail.csv": guardrail,
        "task736_gpt_review_summary.csv": gpt_review,
        "task_736_decision.csv": decision,
        "task_736_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, translations, layer_edges, decision, pass_fail)
    return {
        "events": events,
        "contexts": contexts,
        "translations": translations,
        "semantic_distribution": semantic_distribution,
        "transmission_distribution": transmission_distribution,
        "layer_edges": layer_edges,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_current_contexts(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, row in events.iterrows():
        context, _ = interpret_source_event(row, row_index=int(idx))
        rows.append(context)
    return pd.DataFrame(rows)


def build_semantic_distribution(translations: pd.DataFrame) -> pd.DataFrame:
    grouped = translations.groupby(["context_type", "semantic_polarity", "semantic_state"], dropna=False)
    rows = []
    for keys, group in grouped:
        context_type, polarity, semantic_state = keys
        rows.append(
            {
                "context_type": context_type,
                "semantic_polarity": polarity,
                "semantic_state": semantic_state,
                "event_count": len(group),
                "used_for_trading_count": int(group["used_for_trading_flag"].sum()),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["context_type", "event_count"], ascending=[True, False]).reset_index(drop=True)


def build_transmission_distribution(translations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in translations.iterrows():
        channels = split_pipe(row.get("transmission_channel"))
        effects = split_pipe(row.get("edge_effect"))
        layers = split_pipe(row.get("target_layer"))
        for channel in channels:
            rows.append(
                {
                    "context_type": row["context_type"],
                    "transmission_channel": channel,
                    "edge_effect": "|".join(effects),
                    "target_layer": "|".join(layers),
                    "event_count": 1,
                    "backtest_eligible_count": int(row["backtest_eligible_flag"]),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    grouped = frame.groupby(["context_type", "transmission_channel", "edge_effect", "target_layer"], dropna=False).agg(
        event_count=("event_count", "sum"),
        backtest_eligible_count=("backtest_eligible_count", "sum"),
    )
    return grouped.reset_index().sort_values(["context_type", "event_count"], ascending=[True, False]).reset_index(drop=True)


def build_layer_modifier_edges(translations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in translations.iterrows():
        for layer in split_pipe(row.get("target_layer")):
            rows.append(
                {
                    "event_id": row["event_id"],
                    "lifecycle_id": row["lifecycle_id"],
                    "symbol": row["symbol"],
                    "theme_id": row["theme_id"],
                    "entry_ts": row["entry_ts"],
                    "split_name": row["split_name"],
                    "source_form_family": row["source_form_family"],
                    "context_type": row["context_type"],
                    "semantic_state": row["semantic_state"],
                    "semantic_polarity": row["semantic_polarity"],
                    "target_layer": layer,
                    "edge_effect": row["edge_effect"],
                    "transmission_channel": row["transmission_channel"],
                    "rule_id": row["rule_id"],
                    "used_for_trading_flag": 0,
                    "backtest_eligible_flag": 0,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_guardrail(translations: pd.DataFrame) -> pd.DataFrame:
    missing = translations[translations["semantic_state"].fillna("").astype(str).str.len() == 0]
    missing_rule = translations[translations["rule_id"].fillna("").astype(str).str.len() == 0]
    missing_channel = translations[translations["transmission_channel"].fillna("").astype(str).str.len() == 0]
    action = translations[
        (translations["buy_sell_signal_created_flag"] != 0)
        | (translations["actionability_created_flag"] != 0)
        | (translations["used_for_trading_flag"] != 0)
        | (translations["backtest_eligible_flag"] != 0)
    ]
    operating = translations[translations["operating_connection_supported_flag"] != 0]
    missing_adverse = translations[
        translations["semantic_state"].astype(str).str.contains("unknown", na=False)
        & translations["semantic_polarity"].astype(str).eq("adverse")
    ]
    return pd.DataFrame(
        [
            gate("all_events_translated", len(translations) == 5302, f"rows={len(translations)}", "5302"),
            gate("semantic_state_present", missing.empty, f"missing={len(missing)}", "0"),
            gate("rule_id_present", missing_rule.empty, f"missing={len(missing_rule)}", "0"),
            gate("transmission_channel_present", missing_channel.empty, f"missing={len(missing_channel)}", "0"),
            gate("no_actionability_created", action.empty, f"rows={len(action)}", "0"),
            gate("no_operating_supported_created", operating.empty, f"rows={len(operating)}", "0"),
            gate("missing_unknown_not_adverse", missing_adverse.empty, f"rows={len(missing_adverse)}", "0"),
            gate("polarity_multiple_states", translations["semantic_polarity"].nunique() >= 4, f"states={translations['semantic_polarity'].nunique()}", ">=4"),
        ]
    )


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review approved Task736 as a semantic translator and modifier layer: non-operating context should become semantic_state, transmission_channel, edge_effect, and layer modifier, not direct actionability.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT detail review specified constructive/adverse/neutral/mixed/conditional/unknown semantic polarity, source-family states for financing, strategic investment, M&A, insider, governance, ownership, 13F, and macro, and guardrails forbidding buy/sell, backtest eligibility, outcome labels, and operating catalyst creation.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(translations: pd.DataFrame, layer_edges: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "CONTEXT_SEMANTIC_TRANSLATOR_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "translation_count": len(translations),
                "semantic_state_count": translations["semantic_state"].nunique(),
                "semantic_polarity_count": translations["semantic_polarity"].nunique(),
                "layer_edge_count": len(layer_edges),
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Attach semantic modifier edges into candidate bundles and audit whether constructive/adverse/mixed modifiers change confidence, risk, slot priority, or research queues without creating direct buy/sell rules.",
            }
        ]
    )


def build_pass_fail(
    translations: pd.DataFrame,
    semantic_distribution: pd.DataFrame,
    transmission_distribution: pd.DataFrame,
    layer_edges: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("semantic_translation_created", len(translations) == 5302, f"rows={len(translations)}", "5302"),
            gate("semantic_distribution_created", len(semantic_distribution) > 0, f"rows={len(semantic_distribution)}", ">0"),
            gate("transmission_distribution_created", len(transmission_distribution) > 0, f"rows={len(transmission_distribution)}", ">0"),
            gate("layer_edges_created", len(layer_edges) >= len(translations), f"rows={len(layer_edges)}", ">= translations"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "semantic translator review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    translations: pd.DataFrame,
    layer_edges: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task736_semantic_translation.jsonl", translations)
    write_jsonl(out_dir / "task736_layer_modifier_edges.jsonl", layer_edges)
    (out_dir / "task_736_context_semantic_translator.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task736 Context Semantic Translator",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Translations: {int(d['translation_count'])}",
        f"- Semantic states: {int(d['semantic_state_count'])}",
        f"- Semantic polarities: {int(d['semantic_polarity_count'])}",
        f"- Layer modifier edges: {int(d['layer_edge_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task736 adds a semantic translator on top of source circuit contexts. It translates financing, strategic investment, M&A, insider, governance, ownership, institutional positioning, and macro/policy contexts into constructive, adverse, neutral, mixed, conditional, or unknown states. It emits modifier edges only. It does not create buy/sell, actionability, operating catalyst support, backtest eligibility, or capital permission.",
        "",
        "### Semantic State Distribution",
        "",
        frame_to_markdown(outputs["task736_semantic_state_distribution.csv"]),
        "",
        "### Transmission Channel Distribution",
        "",
        frame_to_markdown(outputs["task736_transmission_channel_distribution.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task736_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task736_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: blocked/non-operating information is now translated, not thrown away.",
        "- Financing can be growth funding, dilution overhang, liquidity rescue, refinance, or unknown.",
        "- M&A and strategic investment stay alive as conditional strategic/risk modifiers.",
        "- Insider sales/buys and governance changes become confidence or risk modifiers.",
        "- None of this is a buy rule yet.",
        "",
        "## Pass/Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
        "",
        "## Artifact Manifest",
        "",
    ]
    for filename in outputs:
        lines.append(f"- `{filename}`")
    lines.append("- `task736_semantic_translation.jsonl`")
    lines.append("- `task736_layer_modifier_edges.jsonl`")
    lines.append("- `artifact_manifest.csv`")
    return "\n".join(lines)


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    cols = [str(c) for c in frame.columns]
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join([markdown_cell(row.get(col, "")) for col in frame.columns]) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def split_pipe(value: object) -> list[str]:
    text = "" if value is None or pd.isna(value) else str(value)
    return [part for part in text.split("|") if part] or ["context_only"]


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task736(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} translations={decision['translation_count']} "
        f"semantic_states={decision['semantic_state_count']} backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
