from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.risk.healthy_expansion_policy import HealthyExpansionPolicyConfig
from src.risk.participation_quality import ParticipationQualityConfig
from src.risk.staged_gate import StagedGateConfig
from src.risk.state_detector import StateDetectorConfig


DEFAULT_OUT_DIR = Path("docs/reports/task_373_definition_audit")


@dataclass(frozen=True)
class DefinitionAudit373Artifacts:
    good_breakout_definition: pd.DataFrame
    good_entry_definition: pd.DataFrame
    good_flow_definition: pd.DataFrame
    definition_forward_vs_expost_matrix: pd.DataFrame
    definition_conservatism_audit: pd.DataFrame


def _rule_row(
    *,
    definition_scope: str,
    rule_id: str,
    rule_name: str,
    source_path: str,
    source_function: str,
    rule_type: str,
    temporal_classification: str,
    conservatism_flag: str,
    logic_issue_flag: str,
    fields_used: str,
    thresholds: str,
    operational_message: str,
    audit_note: str,
) -> dict[str, Any]:
    return {
        "definition_scope": definition_scope,
        "rule_id": rule_id,
        "rule_name": rule_name,
        "source_path": source_path,
        "source_function": source_function,
        "rule_type": rule_type,
        "temporal_classification": temporal_classification,
        "forward_clean_flag": temporal_classification == "forward_clean",
        "conservatism_flag": conservatism_flag,
        "logic_issue_flag": logic_issue_flag,
        "fields_used": fields_used,
        "thresholds": thresholds,
        "operational_message": operational_message,
        "audit_note": audit_note,
    }


def _breakout_definition_rows() -> list[dict[str, Any]]:
    tactical_path = "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py"
    task360_path = "src/backtest/analysis_structural_breakout_shadow_integration_360.py"
    return [
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.execution_quality_score",
            rule_name="execution_quality_score",
            source_path=tactical_path,
            source_function="_execution_quality_score",
            rule_type="forward_filter",
            temporal_classification="mixed",
            conservatism_flag="medium",
            logic_issue_flag="outcome_leakage_risk",
            fields_used=(
                "vwap_response, price_vs_session_vwap_at_breakout, breakout_response, "
                "breakout_hold_duration_bars, volume_persistence_3bars_band348, "
                "breakout_window_volume_surge_band348, adverse_excursion_next_3bars_band348, "
                "intraday_pullback_depth_3bars_band348"
            ),
            thresholds="strong if score>=2; weak if score<=0; mixed otherwise",
            operational_message="좋은 breakout은 VWAP/브레이크아웃 유지 + 거래량 지속 + 초기 역행 얕음으로 간주된다.",
            audit_note="next_3bars와 hold_duration 기반 필드가 섞여 있어 forward-clean breakout 정의로 쓰기 어렵다.",
        ),
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.vwap_hold",
            rule_name="vwap_hold_support",
            source_path=tactical_path,
            source_function="_execution_quality_score",
            rule_type="forward_filter",
            temporal_classification="mixed",
            conservatism_flag="medium",
            logic_issue_flag="mixed_semantics",
            fields_used="vwap_response, price_vs_session_vwap_at_breakout",
            thresholds="vwap_response == 'vwap_hold' OR price_vs_session_vwap_at_breakout > 0",
            operational_message="브레이크아웃 직후 VWAP 위를 지키는 흐름을 좋은 breakout 쪽으로 본다.",
            audit_note="가격 위치는 즉시 관찰 가능하지만 vwap_response 텍스트는 사후 요약 성격이 섞일 수 있다.",
        ),
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.breakout_hold",
            rule_name="breakout_hold_support",
            source_path=tactical_path,
            source_function="_execution_quality_score",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="medium",
            logic_issue_flag="outcome_leakage_risk",
            fields_used="breakout_response, breakout_hold_duration_bars",
            thresholds="breakout_response == 'breakout_hold' OR breakout_hold_duration_bars >= 1",
            operational_message="실제로 한 바 이상 버틴 breakout을 좋은 breakout으로 본다.",
            audit_note="좋은 breakout 정의에 이미 '버틴 결과'가 들어가 있어 진입 전 판단과 사후 설명이 섞인다.",
        ),
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.volume_support",
            rule_name="volume_persistence_or_surge",
            source_path=tactical_path,
            source_function="_execution_quality_score",
            rule_type="forward_filter",
            temporal_classification="mixed",
            conservatism_flag="low",
            logic_issue_flag="none",
            fields_used="volume_persistence_3bars_band348, breakout_window_volume_surge_band348",
            thresholds="either band == 'high'",
            operational_message="좋은 breakout은 거래량 surge 또는 초기 지속이 있어야 한다.",
            audit_note="volume surge는 비교적 직관적이지만 persistence_3bars는 사후 관찰 필드다.",
        ),
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.adverse_excursion_penalty",
            rule_name="early_adverse_excursion_penalty",
            source_path=tactical_path,
            source_function="_execution_quality_score",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="high",
            logic_issue_flag="outcome_leakage_risk",
            fields_used="adverse_excursion_next_3bars_band348, intraday_pullback_depth_3bars_band348",
            thresholds="subtract 1 if either band == 'high'",
            operational_message="초기 3 bars 안에서 역행/풀백이 깊으면 좋은 breakout에서 제외한다.",
            audit_note="완전히 사후 관찰 필드라 live breakout 정의로는 부적절하다.",
        ),
        _rule_row(
            definition_scope="good_breakout",
            rule_id="breakout.quality_aware_add_path",
            rule_name="healthy_expansion_stage2_path",
            source_path=task360_path,
            source_function="_quality_aware_policy",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="participation_quality_label, staged_gate_stage",
            thresholds="HEALTHY_EXPANSION + stage_2_add => ADD_ALLOWED",
            operational_message="좋은 breakout은 결국 healthy participation과 stage_2_add를 동시에 받아야 add path가 열린다.",
            audit_note="breakout 정의가 execution 자체보다 정책 스택의 결과로 재해석되는 지점이다.",
        ),
    ]


def _entry_definition_rows() -> list[dict[str, Any]]:
    pq = ParticipationQualityConfig()
    hp = HealthyExpansionPolicyConfig()
    sg = StagedGateConfig()
    sd = StateDetectorConfig()
    return [
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.ker_gate",
            rule_name="ker_trend_gate",
            source_path="src/backtest/entry_gates.py",
            source_function="evaluate_entry_gate",
            rule_type="forward_filter",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="ker",
            thresholds=f"TREND if ker>{0.50:.2f}; block if ker<{0.30:.2f}; mixed blocked by default",
            operational_message="좋은 entry는 mean-reversion이 아닌 trend regime으로 분류돼야 한다.",
            audit_note="ker_allow_mixed 기본값이 False라 mixed regime도 기본적으로 차단된다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.volume_gate",
            rule_name="volume_percentile_gate",
            source_path="src/backtest/entry_gates.py",
            source_function="evaluate_entry_gate",
            rule_type="forward_filter",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="volume_percentile",
            thresholds="block if volume_percentile < 0.60",
            operational_message="좋은 entry는 하위 40% 거래량 percentile이면 안 된다.",
            audit_note="generic volume floor는 간단하지만 지속형 breakout만 따로 구분하진 못한다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.daily_bias_gate",
            rule_name="daily_bias_bullish_only",
            source_path="src/backtest/entry_gates.py",
            source_function="evaluate_entry_gate",
            rule_type="forward_filter",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="close, daily_sma20, daily_sma50",
            thresholds="allow only BULLISH or STRONG_BULLISH",
            operational_message="좋은 entry는 최소한 daily bias가 bullish해야 한다.",
            audit_note="중기 추세 필터이므로 continuation보다 broader trend filter에 가깝다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.participation_quality_label",
            rule_name="healthy_participation_label",
            source_path="src/risk/participation_quality.py",
            source_function="evaluate_participation_quality",
            rule_type="state_classifier",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used=(
                "breadth_change, breadth_participation_ratio, liquidity_change, dip_absorption_score, "
                "reversal_stability_score, factor_concentration_score, same_day_signal_crowding, "
                "volatility_expansion_score, continuation_persistence_score, session_timing_score"
            ),
            thresholds=(
                f"healthy if expansion-fragility >= {pq.neutral_band:.2f} and expansion >= {pq.healthy_label_threshold:.2f}"
            ),
            operational_message="좋은 entry의 환경 품질은 healthy expansion인지로 먼저 태깅된다.",
            audit_note="label 정의 자체는 비교적 느슨하지만 실제 정책행동 기준과는 다르다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.healthy_action_threshold",
            rule_name="healthy_enough_to_act",
            source_path="src/risk/healthy_expansion_policy.py",
            source_function="evaluate_healthy_expansion_policy",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="threshold_mismatch",
            fields_used="quality_label, expansion_score, fragility_score, confidence",
            thresholds=(
                f"relax only if expansion >= {hp.healthy_expansion_min_score:.2f}, "
                f"fragility <= {hp.max_fragility_for_relax:.2f}, confidence >= {hp.min_confidence_for_relax:.2f}"
            ),
            operational_message="실제로 size/add를 열어주는 좋은 entry는 label만 healthy가 아니라 더 강한 healthy threshold를 넘어야 한다.",
            audit_note="HEALTHY_EXPANSION label threshold 0.45와 actionable threshold 0.65가 달라 직관을 흐린다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.hard_suppressions",
            rule_name="fragile_unknown_dislocation_hard_block",
            source_path="src/risk/healthy_expansion_policy.py",
            source_function="evaluate_healthy_expansion_policy",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="none",
            fields_used="state_label, quality_label, factor_budget_allowed",
            thresholds="DISLOCATION or FRAGILE_CROWDING or UNKNOWN or factor budget blocked => KEEP_SUPPRESSED",
            operational_message="좋은 entry가 아니라고 판단되면 거의 절대적으로 억제한다.",
            audit_note="특히 UNKNOWN을 hard suppression으로 두는 점이 데이터 부족을 지나치게 보수적으로 처리할 수 있다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.state_classifier",
            rule_name="normal_vs_crowded_state",
            source_path="src/risk/state_detector.py",
            source_function="classify_row_state",
            rule_type="state_classifier",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="mixed_semantics",
            fields_used=(
                "sector_group, session_timing_bucket, execution_quality_bucket, gap_environment_state, "
                "market_breadth_state, sector_leadership_state, same_day_candidate_count, "
                "same_day_sector_candidate_count, dispersion_20d, mean_pairwise_corr, semis_concentration_ratio"
            ),
            thresholds=(
                f"crowded if crowded_triggers >= {sd.crowded_trigger_threshold}; "
                f"normal if normal_triggers >= {sd.normal_trigger_threshold}"
            ),
            operational_message="좋은 entry는 crowded/dislocation이 아니라 normal continuation state로 분류돼야 한다.",
            audit_note="strong execution이 상황에 따라 crowded trigger와 normal trigger 둘 다 될 수 있어 의미가 섞인다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.stage_gate",
            rule_name="stage_2_add_vs_probe",
            source_path="src/risk/staged_gate.py",
            source_function="evaluate_staged_gate",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="none",
            fields_used="row_state, execution_quality_bucket, session_timing_bucket",
            thresholds=(
                "stage_2_add if normal state + strong/mixed execution; "
                f"stage_1_probe if crowded or session in {sg.first_stage_session_buckets}"
            ),
            operational_message="좋은 entry는 probe가 아니라 바로 stage_2_add까지 열려야 한다.",
            audit_note="first_30m/unknown이 강한 불이익을 받아 초기 강한 breakout을 과도하게 probe로 내릴 수 있다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.execution_signal_inconsistency",
            rule_name="state_vs_stage_execution_signal_mismatch",
            source_path="src/risk/shadow_adapter.py",
            source_function="_build_observations",
            rule_type="state_classifier",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="signal_inconsistency",
            fields_used="execution_quality_bucket",
            thresholds="shadow state observations hard-code execution_quality_bucket='unknown'",
            operational_message="state 판단은 execution quality를 실질적으로 못 쓰는데, staged gate는 execution bucket을 사용한다.",
            audit_note="같은 좋은 entry 판단 스택 안에서 execution signal 사용 일관성이 깨진다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.allow_add_risk_gate",
            rule_name="add_relax_requires_low_risk",
            source_path="src/risk/healthy_expansion_policy.py",
            source_function="evaluate_healthy_expansion_policy",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="none",
            fields_used="state_label, continuation_risk_score, staged_add_allowed",
            thresholds=f"allow add only if state in NORMAL/ELEVATED and risk <= {hp.max_risk_score_for_add_relax:.2f}",
            operational_message="좋은 entry 중에서도 더 좋은 것만 add relaxation을 받을 수 있다.",
            audit_note="entry quality라기보다 add eligibility 정의에 더 가깝다.",
        ),
        _rule_row(
            definition_scope="good_entry",
            rule_id="entry.healthy_add_floor_ordering",
            rule_name="healthy_add_floor_lower_than_size_floor",
            source_path="src/risk/healthy_expansion_policy.py",
            source_function="evaluate_healthy_expansion_policy",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="threshold_mismatch",
            fields_used="healthy_size_floor, healthy_add_size_floor",
            thresholds=f"healthy_size_floor={hp.healthy_size_floor:.2f}; healthy_add_size_floor={hp.healthy_add_size_floor:.2f}",
            operational_message="좋은 entry에서 add가 허용돼도 size floor가 size-only relax보다 더 낮다.",
            audit_note="좋은 흐름에 더 적극적이어야 할 add path가 오히려 보수적인 floor를 가져 직관과 어긋난다.",
        ),
    ]


def _flow_definition_rows() -> list[dict[str, Any]]:
    return [
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.probe_start",
            rule_name="initial_live_probe",
            source_path="src/backtest/continuation_lifecycle_replay.py",
            source_function="_next_state",
            rule_type="state_classifier",
            temporal_classification="forward_clean",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="size_multiplier, participation_quality_label",
            thresholds="from IDLE/EXITED -> PROBE if live position and not FRAGILE_CROWDING",
            operational_message="좋은 flow는 최소한 fragile하지 않은 live probe로 시작해야 한다.",
            audit_note="flow 시작부터 fragile label은 사실상 bad flow로 분류된다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.building_requires_all_add_gates",
            rule_name="build_state_requires_full_add_path",
            source_path="src/backtest/continuation_lifecycle_replay.py",
            source_function="_add_path_open",
            rule_type="policy_gate",
            temporal_classification="forward_clean",
            conservatism_flag="high",
            logic_issue_flag="none",
            fields_used="factor_budget_allowed, exposure_allow_add, staged_gate_stage, staged_add_allowed, final_add_allowed",
            thresholds="all five conditions must hold to enter BUILDING",
            operational_message="좋은 flow에서만 add/building 상태가 열리도록 매우 빡빡하게 묶여 있다.",
            audit_note="flow 질 판단과 정책 허용조건이 사실상 동일시된다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.good_sequence",
            rule_name="ordered_positive_lifecycle_sequence",
            source_path="src/backtest/analysis_structural_breakout_multi_event_dataset_366.py",
            source_function="task_report_logic",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="medium",
            logic_issue_flag="mixed_semantics",
            fields_used="event_type sequence",
            thresholds="PROBE_ENTRY -> ADD_ATTEMPT -> ADD_CONFIRMED -> SIZE_INCREASE -> PERSISTENCE_CONFIRMED",
            operational_message="현재 좋은 flow는 사실상 위 ordered sequence를 밟는 continuation으로 읽힌다.",
            audit_note="예측기라기보다 lifecycle 완성도 기준 outcome taxonomy에 가깝다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.persistence_15m",
            rule_name="persistence_confirmed_after_15m",
            source_path="src/backtest/continuation_intraday_events.py",
            source_function="build_continuation_intraday_events",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="low",
            logic_issue_flag="mixed_semantics",
            fields_used="probe timestamp, session bars",
            thresholds="PERSISTENCE_CONFIRMED after 15 minutes",
            operational_message="좋은 flow의 persistence는 우선 15분 버텼는지로 태깅된다.",
            audit_note="오래 갈 가능성 예측이 아니라 이미 15분이 지난 결과를 라벨링한다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.reducing_on_fragility_or_size_drop",
            rule_name="fragility_or_size_drop_to_reducing",
            source_path="src/backtest/continuation_lifecycle_replay.py",
            source_function="_next_state",
            rule_type="state_classifier",
            temporal_classification="mixed",
            conservatism_flag="medium",
            logic_issue_flag="mixed_semantics",
            fields_used="participation_quality_label, size_multiplier, previous_size",
            thresholds="REDUCING if FRAGILE_CROWDING or size reduced vs previous row",
            operational_message="좋은 flow는 fragile로 찍히거나 size가 줄기 시작하면 약화된 것으로 본다.",
            audit_note="quality label 기반과 realized size step-down 기반이 한 규칙 안에 섞여 있다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.exited_on_zero_or_dislocation",
            rule_name="terminal_exit_conditions",
            source_path="src/backtest/continuation_lifecycle_replay.py",
            source_function="_next_state",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="medium",
            logic_issue_flag="none",
            fields_used="size_multiplier, state_label",
            thresholds="EXITED if size <= 0 or DISLOCATION",
            operational_message="좋은 flow는 terminal dislocation/size-to-zero 이전에만 유지된다.",
            audit_note="flow 질보다 종료 조건 정의다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.fragile_transition_flag",
            rule_name="fragile_transition_any_warning_or_reduction",
            source_path="src/backtest/build_source_time_capture_372.py",
            source_function="lifecycle_panel_builder",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="medium",
            logic_issue_flag="mixed_semantics",
            fields_used="event_type",
            thresholds="fragile_transition_flag = any(FRAGILITY_WARNING, REDUCTION_TRIGGER)",
            operational_message="좋은 flow가 아니게 된 시점을 weakening/reduction event 존재로 본다.",
            audit_note="독립 raw warning이 아니라 reduction 재해석까지 함께 묶는다.",
        ),
        _rule_row(
            definition_scope="good_flow",
            rule_id="flow.source_truth_quality",
            rule_name="source_truth_vs_mixed_vs_synthetic",
            source_path="src/backtest/source_truth_lineage.py",
            source_function="build_source_truth_lineage",
            rule_type="expost_tag",
            temporal_classification="expost",
            conservatism_flag="low",
            logic_issue_flag="none",
            fields_used="event_source",
            thresholds="source_truth if all SOURCE_TRUTH; mixed if SOURCE_TRUTH/SHADOW_INFERRED; else synthetic_only",
            operational_message="좋은 flow 증거의 신뢰도는 source truth lineage인지로 따진다.",
            audit_note="flow quality가 아니라 evidence fidelity 정의다.",
        ),
    ]


def _build_definition_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    return frame.sort_values(["definition_scope", "rule_id"], kind="stable").reset_index(drop=True)


def _forward_vs_expost_matrix(definition_frames: tuple[pd.DataFrame, ...]) -> pd.DataFrame:
    frame = pd.concat(definition_frames, ignore_index=True)
    matrix = frame[
        [
            "definition_scope",
            "rule_id",
            "rule_name",
            "source_path",
            "source_function",
            "rule_type",
            "temporal_classification",
            "forward_clean_flag",
            "logic_issue_flag",
        ]
    ].copy()
    return matrix.sort_values(["definition_scope", "rule_id"], kind="stable").reset_index(drop=True)


def _conservatism_audit(definition_frames: tuple[pd.DataFrame, ...]) -> pd.DataFrame:
    frame = pd.concat(definition_frames, ignore_index=True)
    audit = frame[
        [
            "definition_scope",
            "rule_id",
            "rule_name",
            "source_path",
            "source_function",
            "conservatism_flag",
            "logic_issue_flag",
            "audit_note",
            "thresholds",
            "operational_message",
        ]
    ].copy()
    return audit.sort_values(["conservatism_flag", "definition_scope", "rule_id"], ascending=[False, True, True], kind="stable").reset_index(drop=True)


def build_definition_audit_373() -> DefinitionAudit373Artifacts:
    breakout = _build_definition_frame(_breakout_definition_rows())
    entry = _build_definition_frame(_entry_definition_rows())
    flow = _build_definition_frame(_flow_definition_rows())
    matrix = _forward_vs_expost_matrix((breakout, entry, flow))
    audit = _conservatism_audit((breakout, entry, flow))
    return DefinitionAudit373Artifacts(
        good_breakout_definition=breakout,
        good_entry_definition=entry,
        good_flow_definition=flow,
        definition_forward_vs_expost_matrix=matrix,
        definition_conservatism_audit=audit,
    )


def write_definition_audit_373(
    artifacts: DefinitionAudit373Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.good_breakout_definition.to_csv(out_dir / "good_breakout_definition.csv", index=False, encoding="utf-8-sig")
    artifacts.good_entry_definition.to_csv(out_dir / "good_entry_definition.csv", index=False, encoding="utf-8-sig")
    artifacts.good_flow_definition.to_csv(out_dir / "good_flow_definition.csv", index=False, encoding="utf-8-sig")
    artifacts.definition_forward_vs_expost_matrix.to_csv(
        out_dir / "definition_forward_vs_expost_matrix.csv",
        index=False,
        encoding="utf-8-sig",
    )
    artifacts.definition_conservatism_audit.to_csv(
        out_dir / "definition_conservatism_audit.csv",
        index=False,
        encoding="utf-8-sig",
    )
