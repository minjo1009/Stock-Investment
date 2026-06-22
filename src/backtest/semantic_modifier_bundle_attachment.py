from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


POLARITIES = ["constructive", "adverse", "neutral", "mixed", "conditional", "unknown"]
EFFECTS = ["confidence_modifier", "risk_modifier", "slot_modifier", "research_escalation", "context_only"]


@dataclass(frozen=True)
class BundleModifierAttachment:
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    bundle_id: str
    source_modifier_count: int
    constructive_count: int
    adverse_count: int
    neutral_count: int
    mixed_count: int
    conditional_count: int
    unknown_count: int
    confidence_modifier_count: int
    risk_modifier_count: int
    slot_modifier_count: int
    research_escalation_count: int
    context_only_count: int
    dominant_modifier_state: str
    conflict_state: str
    queue_transition_state: str
    required_review_focus: str
    semantic_state_set: str
    transmission_channel_set: str
    edge_effect_set: str
    target_layer_set: str
    direct_score_created_flag: int
    buy_sell_signal_created_flag: int
    actionability_created_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


def attach_semantic_modifiers(bundles: pd.DataFrame, translations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = {key: group.copy() for key, group in translations.groupby("lifecycle_id", dropna=False)}
    for _, bundle in bundles.iterrows():
        lifecycle_id = str(bundle.get("lifecycle_id", ""))
        group = grouped.get(lifecycle_id, translations.iloc[0:0].copy())
        rows.append(asdict(build_bundle_attachment(bundle, group)))
    return pd.DataFrame(rows)


def build_bundle_attachment(bundle: pd.Series, group: pd.DataFrame) -> BundleModifierAttachment:
    if group.empty:
        return BundleModifierAttachment(
            lifecycle_id=str(bundle.get("lifecycle_id", "")),
            symbol=str(bundle.get("symbol", "")),
            theme_id=str(bundle.get("theme_id", "")),
            entry_ts=str(bundle.get("entry_ts", "")),
            split_name=str(bundle.get("split_name", "")),
            bundle_id=str(bundle.get("bundle_id", bundle.get("candidate_context_bundle_id", ""))),
            source_modifier_count=0,
            constructive_count=0,
            adverse_count=0,
            neutral_count=0,
            mixed_count=0,
            conditional_count=0,
            unknown_count=0,
            confidence_modifier_count=0,
            risk_modifier_count=0,
            slot_modifier_count=0,
            research_escalation_count=0,
            context_only_count=0,
            dominant_modifier_state="semantic_modifier_absent",
            conflict_state="no_semantic_modifier",
            queue_transition_state="semantic_modifier_absent_not_negative",
            required_review_focus="source-attached semantic translation absent; do not treat as negative or zero score",
            semantic_state_set="",
            transmission_channel_set="",
            edge_effect_set="",
            target_layer_set="",
            direct_score_created_flag=0,
            buy_sell_signal_created_flag=0,
            actionability_created_flag=0,
            backtest_eligible_flag=0,
            outcome_used_for_assignment_flag=0,
        )
    polarity_counts = {polarity: count_equal(group, "semantic_polarity", polarity) for polarity in POLARITIES}
    effect_counts = {effect: count_contains(group, "edge_effect", effect) for effect in EFFECTS}
    channels = set_from_pipe(group.get("transmission_channel", pd.Series(dtype=str)))
    effects = set_from_pipe(group.get("edge_effect", pd.Series(dtype=str)))
    layers = set_from_pipe(group.get("target_layer", pd.Series(dtype=str)))
    semantic_states = set(group.get("semantic_state", pd.Series(dtype=str)).dropna().astype(str))
    conflict = classify_conflict(polarity_counts, channels, effects)
    queue = classify_queue_transition(polarity_counts, effect_counts, conflict)
    return BundleModifierAttachment(
        lifecycle_id=str(bundle.get("lifecycle_id", "")),
        symbol=str(bundle.get("symbol", "")),
        theme_id=str(bundle.get("theme_id", "")),
        entry_ts=str(bundle.get("entry_ts", "")),
        split_name=str(bundle.get("split_name", "")),
        bundle_id=str(bundle.get("bundle_id", bundle.get("candidate_context_bundle_id", ""))),
        source_modifier_count=len(group),
        constructive_count=polarity_counts["constructive"],
        adverse_count=polarity_counts["adverse"],
        neutral_count=polarity_counts["neutral"],
        mixed_count=polarity_counts["mixed"],
        conditional_count=polarity_counts["conditional"],
        unknown_count=polarity_counts["unknown"],
        confidence_modifier_count=effect_counts["confidence_modifier"],
        risk_modifier_count=effect_counts["risk_modifier"],
        slot_modifier_count=effect_counts["slot_modifier"],
        research_escalation_count=effect_counts["research_escalation"],
        context_only_count=effect_counts["context_only"],
        dominant_modifier_state=classify_dominant_modifier(polarity_counts, effect_counts),
        conflict_state=conflict,
        queue_transition_state=queue,
        required_review_focus=required_review_focus(queue, conflict),
        semantic_state_set="|".join(sorted(semantic_states)),
        transmission_channel_set="|".join(sorted(channels)),
        edge_effect_set="|".join(sorted(effects)),
        target_layer_set="|".join(sorted(layers)),
        direct_score_created_flag=0,
        buy_sell_signal_created_flag=0,
        actionability_created_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
    )


def classify_conflict(polarity_counts: dict[str, int], channels: set[str], effects: set[str]) -> str:
    conflict_parts = []
    if polarity_counts["constructive"] > 0 and polarity_counts["adverse"] > 0:
        conflict_parts.append("constructive_adverse_conflict")
    if {"growth_funding", "dilution_overhang"}.issubset(channels):
        conflict_parts.append("growth_funding_dilution_conflict")
    if {"strategic_fit", "integration_risk"}.issubset(channels):
        conflict_parts.append("strategic_fit_integration_risk_conflict")
    if "insider_alignment" in channels and ("risk_modifier" in effects or polarity_counts["adverse"] > 0):
        conflict_parts.append("insider_alignment_risk_conflict")
    if {"policy_tailwind", "regulatory_risk"}.issubset(channels):
        conflict_parts.append("policy_tailwind_regulatory_conflict")
    return "|".join(conflict_parts) if conflict_parts else "no_semantic_conflict_detected"


def classify_dominant_modifier(polarity_counts: dict[str, int], effect_counts: dict[str, int]) -> str:
    if effect_counts["risk_modifier"] > 0 or polarity_counts["adverse"] > 0 or polarity_counts["mixed"] > 0:
        return "risk_or_mixed_modifier_dominant"
    if effect_counts["slot_modifier"] > 0:
        return "slot_modifier_present"
    if effect_counts["confidence_modifier"] > 0 or polarity_counts["constructive"] > 0:
        return "confidence_modifier_present"
    if effect_counts["research_escalation"] > 0 or polarity_counts["conditional"] > 0 or polarity_counts["unknown"] > 0:
        return "research_or_unknown_modifier_dominant"
    return "context_only_no_change"


def classify_queue_transition(polarity_counts: dict[str, int], effect_counts: dict[str, int], conflict: str) -> str:
    if conflict != "no_semantic_conflict_detected":
        return "semantic_conflict_review_needed"
    if effect_counts["risk_modifier"] > 0 or polarity_counts["adverse"] > 0 or polarity_counts["mixed"] > 0:
        return "risk_review_needed"
    if effect_counts["slot_modifier"] > 0:
        return "slot_modifier_review_needed"
    if effect_counts["confidence_modifier"] > 0 or polarity_counts["constructive"] > 0:
        return "confidence_modifier_review_needed"
    if effect_counts["research_escalation"] > 0 or polarity_counts["conditional"] > 0 or polarity_counts["unknown"] > 0:
        return "semantic_enrichment_needed"
    return "context_only_no_change"


def required_review_focus(queue: str, conflict: str) -> str:
    if queue == "semantic_conflict_review_needed":
        return f"resolve {conflict} before slot or risk use"
    return {
        "risk_review_needed": "inspect adverse/mixed risk channels before any candidate promotion",
        "slot_modifier_review_needed": "inspect same-timestamp slot impact without global priority scoring",
        "confidence_modifier_review_needed": "inspect whether constructive modifiers reinforce existing evidence",
        "semantic_enrichment_needed": "collect missing primitive details; unknown is not negative",
        "context_only_no_change": "no bundle change; retain context trace",
    }.get(queue, "review required")


def build_attachment_edges(attachments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in attachments.iterrows():
        for effect in split_pipe(row.get("edge_effect_set")):
            rows.append(
                {
                    "lifecycle_id": row["lifecycle_id"],
                    "symbol": row["symbol"],
                    "theme_id": row["theme_id"],
                    "entry_ts": row["entry_ts"],
                    "split_name": row["split_name"],
                    "bundle_id": row["bundle_id"],
                    "edge_effect": effect,
                    "dominant_modifier_state": row["dominant_modifier_state"],
                    "conflict_state": row["conflict_state"],
                    "queue_transition_state": row["queue_transition_state"],
                    "rule_id": "SEMANTIC_MODIFIER_ATTACHED_TO_BUNDLE_REVIEW_ONLY",
                    "used_for_trading_flag": 0,
                    "backtest_eligible_flag": 0,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def count_equal(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].fillna("").astype(str).eq(value).sum())


def count_contains(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].fillna("").astype(str).str.split("|").apply(lambda parts: value in parts).sum())


def set_from_pipe(series: pd.Series) -> set[str]:
    values: set[str] = set()
    for value in series.dropna().astype(str):
        values.update(part for part in value.split("|") if part)
    return values


def split_pipe(value: object) -> list[str]:
    text = "" if value is None or pd.isna(value) else str(value)
    return [part for part in text.split("|") if part] or ["context_only"]
