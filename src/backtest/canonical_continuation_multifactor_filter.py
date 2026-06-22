from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


BLOCKED_ONLINE_FIELDS = {
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_reason",
    "return_from_entry",
    "net_return_from_entry",
    "positive_return_flag",
    "post_cost_positive_return_flag",
    "add_scale_flag",
    "failure_group",
    "lifecycle_path",
    "hindsight_strict_regime_gate_flag",
    "theme_day_return",
    "theme_rank",
    "theme_leadership_regime",
    "breadth_positive_rate",
    "avg_intraday_range",
    "liquidity_ratio_20d",
}

POLICY_WEIGHTS = {
    "scorecard_v1_75_25": {
        "market_participation": 0.25,
        "theme_leadership": 0.25,
        "entry_quality": 0.25,
        "liquidity_tradability": 0.09,
        "cost_friction": 0.08,
        "symbol_quality_prior": 0.04,
        "time_of_day_prior": 0.04,
    },
    "scorecard_v1_65_35": {
        "market_participation": 0.20,
        "theme_leadership": 0.20,
        "entry_quality": 0.25,
        "liquidity_tradability": 0.15,
        "cost_friction": 0.10,
        "symbol_quality_prior": 0.05,
        "time_of_day_prior": 0.05,
    },
    "scorecard_v1_55_45": {
        "market_participation": 0.17,
        "theme_leadership": 0.17,
        "entry_quality": 0.21,
        "liquidity_tradability": 0.19,
        "cost_friction": 0.14,
        "symbol_quality_prior": 0.06,
        "time_of_day_prior": 0.06,
    },
    "scorecard_v1_defensive_friction": {
        "market_participation": 0.14,
        "theme_leadership": 0.14,
        "entry_quality": 0.17,
        "liquidity_tradability": 0.23,
        "cost_friction": 0.18,
        "symbol_quality_prior": 0.07,
        "time_of_day_prior": 0.07,
    },
}

DEFAULT_POLICY_VERSION = "scorecard_v1_65_35"
DEFAULT_THRESHOLD_SET_ID = "task401_scorecard_v1_fixed_research_prior"
DEFAULT_FEATURE_SET_VERSION = "task401_forward_live_decision_snapshot_v1"


@dataclass(frozen=True)
class MultiFactorDecision:
    raw_factors: dict[str, Any]
    norm_factors: dict[str, Any]
    component_scores: dict[str, float]
    final_score_q: float
    bucket: str
    decision_action: str
    hard_gate_fail: bool
    reason_codes: list[str]
    policy_version: str
    threshold_set_id: str
    feature_set_version: str
    source_hash: str


def evaluate_multifactor_continuation_filter(
    features: dict[str, Any],
    *,
    decision_kind: str = "ENTRY",
    policy_version: str = DEFAULT_POLICY_VERSION,
    threshold_set_id: str = DEFAULT_THRESHOLD_SET_ID,
    feature_set_version: str = DEFAULT_FEATURE_SET_VERSION,
) -> MultiFactorDecision:
    blocked = sorted(BLOCKED_ONLINE_FIELDS.intersection(features))
    if blocked:
        raise ValueError(f"blocked online feature fields present: {', '.join(blocked)}")
    if policy_version not in POLICY_WEIGHTS:
        raise ValueError(f"unknown policy_version: {policy_version}")

    raw = _raw_factor_view(features)
    norm = _norm_factor_view(raw)
    components = _component_scores(raw, norm)
    hard_gate, hard_reasons = _hard_gate(raw)
    score = round(
        sum(components[name] * weight for name, weight in POLICY_WEIGHTS[policy_version].items()),
        6,
    )
    if hard_gate:
        bucket = "REJECT"
    elif score >= 0.35:
        bucket = "ALLOW"
    elif score >= 0.10:
        bucket = "WATCH"
    else:
        bucket = "REJECT"
    action = _decision_action(decision_kind, bucket)
    reasons = hard_reasons + _score_reason_codes(components, bucket)
    return MultiFactorDecision(
        raw_factors=raw,
        norm_factors=norm,
        component_scores=components,
        final_score_q=score,
        bucket=bucket,
        decision_action=action,
        hard_gate_fail=hard_gate,
        reason_codes=reasons,
        policy_version=policy_version,
        threshold_set_id=threshold_set_id,
        feature_set_version=feature_set_version,
        source_hash=_stable_hash(raw),
    )


def build_leakage_audit(columns: list[str] | set[str]) -> list[dict[str, Any]]:
    present = set(columns)
    rows = []
    for field in sorted(BLOCKED_ONLINE_FIELDS):
        rows.append(
            {
                "field": field,
                "present_in_online_snapshot": int(field in present),
                "allowed_as_online_feature": 0,
                "leakage_pass_flag": int(field not in present),
            }
        )
    return rows


def _raw_factor_view(features: dict[str, Any]) -> dict[str, Any]:
    return {
        "feed": str(features.get("feed", "sip")),
        "adjustment": str(features.get("adjustment", "raw")),
        "asof": str(features.get("asof", "-")),
        "session_type": str(features.get("session_type", "regular")),
        "quote_status": str(features.get("quote_status", "unavailable")),
        "luld_status": str(features.get("luld_status", "unavailable")),
        "forward_live_breadth_positive_rate": _float(features.get("forward_live_breadth_positive_rate"), 0.0),
        "forward_live_avg_symbol_return": _float(features.get("forward_live_avg_symbol_return"), 0.0),
        "forward_live_liquidity_ratio": _float(features.get("forward_live_liquidity_ratio"), 1.0),
        "forward_live_theme_return": _float(features.get("forward_live_theme_return"), 0.0),
        "forward_live_theme_rank": _float(features.get("forward_live_theme_rank"), 999.0),
        "forward_live_theme_count": _float(features.get("forward_live_theme_count"), 1.0),
        "forward_live_theme_breadth_positive_rate": _float(features.get("forward_live_theme_breadth_positive_rate"), 0.0),
        "forward_live_theme_leadership_regime": str(features.get("forward_live_theme_leadership_regime", "unknown")),
        "entry_return_so_far": _float(features.get("entry_return_so_far"), 0.0),
        "entry_momentum_2bar": _float(features.get("entry_momentum_2bar"), 0.0),
        "entry_range_pos": _float(features.get("entry_range_pos"), 0.5),
        "entry_range_exp_ratio": _float(features.get("entry_range_exp_ratio"), 1.0),
        "symbol_liquidity_ratio": _float(features.get("symbol_liquidity_ratio"), 1.0),
        "estimated_total_cost": _float(features.get("estimated_total_cost"), 0.00125),
        "cost_to_range": _float(features.get("cost_to_range"), 0.15),
        "role": str(features.get("role", "unknown")),
        "entry_hour": _float(features.get("entry_hour"), 0.0),
    }


def _norm_factor_view(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "breadth_score": _ternary(raw["forward_live_breadth_positive_rate"], low=0.45, high=0.60),
        "market_return_score": _sign_score(raw["forward_live_avg_symbol_return"]),
        "market_liquidity_score": _ternary(raw["forward_live_liquidity_ratio"], low=0.90, high=1.10),
        "theme_return_score": _sign_score(raw["forward_live_theme_return"]),
        "theme_rank_score": 1.0 if raw["forward_live_theme_rank"] <= 3 else (-1.0 if raw["forward_live_theme_rank"] > max(raw["forward_live_theme_count"] * 0.7, 3) else 0.0),
        "theme_breadth_score": _ternary(raw["forward_live_theme_breadth_positive_rate"], low=0.50, high=0.70),
        "entry_return_score": _sign_score(raw["entry_return_so_far"]),
        "entry_momentum_score": _capped_momentum_score(raw["entry_momentum_2bar"]),
        "range_pos_score": 1.0 if 0.70 <= raw["entry_range_pos"] <= 0.95 else (0.0 if 0.55 <= raw["entry_range_pos"] <= 0.99 else -1.0),
        "range_expansion_score": 1.0 if 0.90 <= raw["entry_range_exp_ratio"] <= 1.80 else (0.0 if 0.70 <= raw["entry_range_exp_ratio"] <= 2.50 else -1.0),
        "symbol_liquidity_score": _ternary(raw["symbol_liquidity_ratio"], low=0.80, high=1.20),
        "cost_score": 1.0 if raw["cost_to_range"] < 0.15 else (0.0 if raw["cost_to_range"] <= 0.30 else -1.0),
        "symbol_quality_score": 0.5 if raw["role"] in {"leader", "core"} else 0.0,
        "time_of_day_score": 0.5 if 14 <= raw["entry_hour"] <= 19 else -0.5,
    }


def _component_scores(raw: dict[str, Any], norm: dict[str, Any]) -> dict[str, float]:
    theme_leadership_bonus = 1.0 if raw["forward_live_theme_leadership_regime"] == "theme_leader" else 0.0
    return {
        "market_participation": _mean_score([norm["breadth_score"], norm["market_return_score"], norm["market_liquidity_score"]]),
        "theme_leadership": _mean_score([norm["theme_return_score"], norm["theme_rank_score"], norm["theme_breadth_score"], theme_leadership_bonus]),
        "entry_quality": _mean_score([norm["entry_return_score"], norm["entry_momentum_score"], norm["range_pos_score"], norm["range_expansion_score"]]),
        "liquidity_tradability": _mean_score([norm["symbol_liquidity_score"], norm["market_liquidity_score"]]),
        "cost_friction": norm["cost_score"],
        "symbol_quality_prior": norm["symbol_quality_score"],
        "time_of_day_prior": norm["time_of_day_score"],
    }


def _hard_gate(raw: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    if raw["feed"].lower() not in {"sip", "unavailable"}:
        reasons.append("INVALID_FEED_NOT_SIP")
    if raw["adjustment"].lower() != "raw":
        reasons.append("INVALID_ADJUSTMENT_NOT_RAW")
    if raw["asof"] != "-":
        reasons.append("INVALID_ASOF_MAPPING_ENABLED")
    if raw["session_type"].lower() != "regular":
        reasons.append("INVALID_SESSION_NOT_REGULAR")
    if raw["quote_status"] in {"halt", "pause", "non_firm", "slow_quote"}:
        reasons.append("INVALID_QUOTE_STATUS")
    if raw["luld_status"] in {"halt", "pause", "limit_state"}:
        reasons.append("INVALID_LULD_STATUS")
    if raw["forward_live_breadth_positive_rate"] < 0.45 and raw["forward_live_theme_breadth_positive_rate"] < 0.50:
        reasons.append("LOW_MARKET_AND_THEME_BREADTH")
    if raw["cost_to_range"] > 0.30:
        reasons.append("COST_TOO_HIGH_VS_RANGE")
    if raw["entry_range_pos"] > 0.99 and raw["forward_live_theme_breadth_positive_rate"] <= 0.50:
        reasons.append("OVEREXTENDED_WITHOUT_THEME_BREADTH")
    return bool(reasons), reasons


def _decision_action(decision_kind: str, bucket: str) -> str:
    if bucket == "ALLOW":
        return "ENTRY" if decision_kind == "ENTRY" else decision_kind
    if bucket == "WATCH":
        return "HOLD_NO_ADD"
    return "SKIP" if decision_kind == "ENTRY" else "HOLD_NO_ADD"


def _score_reason_codes(components: dict[str, float], bucket: str) -> list[str]:
    weak = [name.upper() + "_WEAK" for name, score in components.items() if score < -0.25]
    strong = [name.upper() + "_STRONG" for name, score in components.items() if score > 0.25]
    return [f"BUCKET_{bucket}", *strong, *weak]


def _ternary(value: float, *, low: float, high: float) -> float:
    if value < low:
        return -1.0
    if value > high:
        return 1.0
    return 0.0


def _sign_score(value: float) -> float:
    if value > 0:
        return 1.0
    if value < 0:
        return -1.0
    return 0.0


def _capped_momentum_score(value: float) -> float:
    if value <= 0:
        return -1.0
    if value <= 0.025:
        return 1.0
    return 0.5


def _mean_score(values: list[float]) -> float:
    return round(sum(values) / max(len(values), 1), 6)


def _float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _stable_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iso_utc(value: Any) -> str:
    ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return ts.isoformat().replace("+00:00", "Z")
