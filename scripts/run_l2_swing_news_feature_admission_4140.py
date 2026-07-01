from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TASK-4140"
SLUG = "task_4140_swing_news_macro_newswire_feature_admission"
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "l2_swing_news_feature_admission_contract.yaml"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def bool_text(value: object) -> str:
    return "1" if bool(value) else "0"


def build_family_rows(contract: dict[str, object]) -> list[dict[str, object]]:
    core = contract["core_policy"]  # type: ignore[index]
    families = contract["families"]  # type: ignore[index]
    existing_gate = {
        row["source_family"]: row
        for row in read_csv(ROOT / "data" / "artifacts" / "task_4136_l2_intake_feature_admission" / "l2_feature_admission_gate.csv")
    }
    rows: list[dict[str, object]] = []
    for source_family, item in families.items():  # type: ignore[union-attr]
        gate = existing_gate.get(source_family, {})
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": source_family,
                "strategy_timeframe": contract["strategy_timeframe"],
                "average_holding_period": contract["average_holding_period"],
                "swing_feature_candidate_now": bool_text(item["swing_feature_candidate_now"]),
                "blocked_by_intraday_timestamp": bool_text(item["blocked_by_intraday_timestamp"]),
                "minute_second_timestamp_required": bool_text(core["minute_second_timestamp_required_for_swing"]),
                "daily_publication_date_can_be_sufficient": bool_text(core["daily_publication_date_can_be_sufficient"]),
                "activation_policy": core["default_activation_policy"],
                "required_time_basis": item["required_time_basis"],
                "mapping_scope_required": item["mapping_scope_required"],
                "dedup_required": bool_text(item["dedup_required"]),
                "stale_policy_required": bool_text(item["stale_policy_required"]),
                "effect_window_required": bool_text(item["effect_window_required"]),
                "primary_effect_window": core["primary_effect_window"],
                "secondary_effect_windows": "|".join(core["secondary_effect_windows"]),
                "feature_materialization_allowed_now": bool_text(contract["feature_materialization_allowed_now"]),
                "l2_prior_state": gate.get("current_state", ""),
                "plain_korean": item["plain_korean"],
            }
        )
    return rows


def build_activation_rows(contract: dict[str, object]) -> list[dict[str, object]]:
    core = contract["core_policy"]  # type: ignore[index]
    return [
        {
            "task_id": TASK_ID,
            "time_case": "published_at_exact",
            "swing_policy": "정확한 시각이 있으면 보존하되, 스윙 feature에서는 다음 거래일/다음 일봉 의사결정 기준으로 반영한다.",
            "activation_policy": core["default_activation_policy"],
            "minute_second_required": "0",
            "feature_candidate_allowed": "1",
        },
        {
            "task_id": TASK_ID,
            "time_case": "published_date_only",
            "swing_policy": "날짜만 있어도 그 날짜 이후 의사결정에서 알 수 있었는지 확인되면 스윙 feature 후보로 허용한다.",
            "activation_policy": core["default_activation_policy"],
            "minute_second_required": "0",
            "feature_candidate_allowed": "1",
        },
        {
            "task_id": TASK_ID,
            "time_case": "wikimedia_day_imputed_noon",
            "swing_policy": "정오 보정은 실제 공개시각이 아니라 순서 정렬용이다. 스윙 macro context 후보는 가능하되 단독 strict timestamp로 쓰지 않는다.",
            "activation_policy": core["default_activation_policy"],
            "minute_second_required": "0",
            "feature_candidate_allowed": "1",
        },
        {
            "task_id": TASK_ID,
            "time_case": "month_or_year_only",
            "swing_policy": "월/연 단위는 너무 넓다. 스윙 trading feature가 아니라 장기 context로만 둔다.",
            "activation_policy": "CONTEXT_ONLY",
            "minute_second_required": "0",
            "feature_candidate_allowed": "0",
        },
    ]


def build_effect_window_rows(contract: dict[str, object]) -> list[dict[str, object]]:
    core = contract["core_policy"]  # type: ignore[index]
    windows = [core["primary_effect_window"], *core["secondary_effect_windows"]]
    meaning = {
        "1D": "단기 반응 확인용",
        "5D": "뉴스 소화 초기 구간",
        "20D": "평균 보유기간 한 달에 가까운 주 검증 구간",
        "60D": "늦게 반영되는 매크로/섹터 효과 확인용",
    }
    return [
        {
            "task_id": TASK_ID,
            "effect_window": window,
            "is_primary": "1" if window == core["primary_effect_window"] else "0",
            "plain_korean": meaning.get(str(window), "보조 검증 구간"),
            "allowed_for_news": "1",
            "allowed_for_macro": "1",
            "allowed_for_newswire": "1",
        }
        for window in windows
    ]


def build_mapping_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": TASK_ID,
            "mapping_scope": "TICKER",
            "swing_feature_allowed": "1",
            "minimum_evidence": "명확한 티커 또는 고신뢰 엔티티-티커 연결",
            "ambiguous_action": "BLOCK_SYMBOL_FEATURE_OR_MANUAL_REVIEW",
        },
        {
            "task_id": TASK_ID,
            "mapping_scope": "ENTITY",
            "swing_feature_allowed": "1",
            "minimum_evidence": "회사명/브랜드/자회사 관계가 기록되어야 함",
            "ambiguous_action": "ALLOW_ENTITY_CONTEXT_BLOCK_SYMBOL_FEATURE",
        },
        {
            "task_id": TASK_ID,
            "mapping_scope": "SECTOR",
            "swing_feature_allowed": "1",
            "minimum_evidence": "섹터/산업 범위가 명시되어야 함",
            "ambiguous_action": "ALLOW_SECTOR_FEATURE_ONLY",
        },
        {
            "task_id": TASK_ID,
            "mapping_scope": "MACRO",
            "swing_feature_allowed": "1",
            "minimum_evidence": "금리, 물가, 고용, 규제, 지정학 등 macro scope가 명시되어야 함",
            "ambiguous_action": "ALLOW_MACRO_FEATURE_ONLY",
        },
        {
            "task_id": TASK_ID,
            "mapping_scope": "UNKNOWN",
            "swing_feature_allowed": "0",
            "minimum_evidence": "연결 대상이 불명확함",
            "ambiguous_action": "BLOCK_FEATURE_ADMISSION",
        },
    ]


def write_report(family_rows: list[dict[str, object]], effect_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = "# TASK-4140 Swing News/Macro/Newswire Feature Admission\n\n"
    report += "## 결론\n\n"
    report += "뉴스, 매크로, 뉴스와이어는 trading feature 후보가 맞다. 다만 우리 전략은 평균 보유기간이 약 한 달인 스윙 전략이므로, 분/초 단위 공개시각보다 날짜 기준 as-of, 매핑, 중복 제거, 오래된 정보 처리, 효과기간 검증이 더 중요하다.\n\n"
    report += "| 정리 | 의미 |\n|---|---|\n"
    report += "| feature 후보 | 뉴스/매크로/뉴스와이어 모두 `swing_feature_candidate_now=1` |\n"
    report += "| 분초 집착 제거 | `minute_second_timestamp_required=0` |\n"
    report += "| 날짜 기준 허용 | 공개일/발생일이 의사결정 전에 확인되면 스윙 feature 후보 가능 |\n"
    report += "| 아직 안 하는 것 | 실제 feature table write, 매매 신호, paper/live/order |\n\n"
    report += "## 소스별 판단\n\n"
    report += "| Source | 스윙 feature 후보 | 쉬운 설명 |\n|---|---:|---|\n"
    for row in family_rows:
        report += f"| `{row['source_family']}` | {row['swing_feature_candidate_now']} | {row['plain_korean']} |\n"
    report += "\n## 효과기간\n\n"
    report += "| Window | 용도 |\n|---|---|\n"
    for row in effect_rows:
        report += f"| `{row['effect_window']}` | {row['plain_korean']} |\n"
    report += "\n## 다음 구현 포인트\n\n"
    report += "1. L2에서 뉴스/매크로/뉴스와이어 row를 이 admission queue 기준으로 받아들인다.\n"
    report += "2. L2는 `TICKER`, `ENTITY`, `SECTOR`, `MACRO`, `UNKNOWN` mapping scope를 분리한다.\n"
    report += "3. L3 이상에서 5D/20D/60D 효과를 검증한다.\n"
    report += "4. 통과 전까지는 feature 후보이지, 매매 신호나 주문 권한이 아니다.\n"
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4140 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4140 document registry entries", "modified"),
        ("configs/l2_swing_news_feature_admission_contract.yaml", "config", "Swing/daily news macro newswire feature admission contract", "created"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4140 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4140 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4140 project status note", "modified"),
        ("scripts/run_l2_swing_news_feature_admission_4140.py", "script", "Build TASK-4140 swing feature admission artifacts", "created"),
        ("scripts/validate_l2_swing_news_feature_admission_4140.py", "validator", "Validate TASK-4140 swing feature admission artifacts", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4140 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4140 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4140 validation results", "created"),
        (f"docs/reports/{SLUG}/swing_news_feature_admission_summary.json", "summary", "Machine-readable TASK-4140 summary", "created"),
        (f"data/artifacts/{SLUG}/swing_feature_admission_policy.csv", "artifact", "Source-family swing feature admission policy", "created"),
        (f"data/artifacts/{SLUG}/swing_time_activation_policy.csv", "artifact", "Swing time activation policy", "created"),
        (f"data/artifacts/{SLUG}/swing_effect_window_policy.csv", "artifact", "Effect window policy", "created"),
        (f"data/artifacts/{SLUG}/swing_mapping_scope_policy.csv", "artifact", "Mapping scope policy", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [
            {
                "path": path,
                "type": artifact_type,
                "purpose": purpose,
                "created_or_modified": state,
                "task_id": TASK_ID,
            }
            for path, artifact_type, purpose, state in rows
        ],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def build() -> dict[str, object]:
    contract = read_json(CONFIG_PATH)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    family_rows = build_family_rows(contract)
    activation_rows = build_activation_rows(contract)
    effect_rows = build_effect_window_rows(contract)
    mapping_rows = build_mapping_rows()

    write_csv(
        ARTIFACT_DIR / "swing_feature_admission_policy.csv",
        family_rows,
        [
            "task_id",
            "source_family",
            "strategy_timeframe",
            "average_holding_period",
            "swing_feature_candidate_now",
            "blocked_by_intraday_timestamp",
            "minute_second_timestamp_required",
            "daily_publication_date_can_be_sufficient",
            "activation_policy",
            "required_time_basis",
            "mapping_scope_required",
            "dedup_required",
            "stale_policy_required",
            "effect_window_required",
            "primary_effect_window",
            "secondary_effect_windows",
            "feature_materialization_allowed_now",
            "l2_prior_state",
            "plain_korean",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "swing_time_activation_policy.csv",
        activation_rows,
        ["task_id", "time_case", "swing_policy", "activation_policy", "minute_second_required", "feature_candidate_allowed"],
    )
    write_csv(
        ARTIFACT_DIR / "swing_effect_window_policy.csv",
        effect_rows,
        ["task_id", "effect_window", "is_primary", "plain_korean", "allowed_for_news", "allowed_for_macro", "allowed_for_newswire"],
    )
    write_csv(
        ARTIFACT_DIR / "swing_mapping_scope_policy.csv",
        mapping_rows,
        ["task_id", "mapping_scope", "swing_feature_allowed", "minimum_evidence", "ambiguous_action"],
    )
    write_report(family_rows, effect_rows)
    write_manifest()
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "strategy_timeframe": contract["strategy_timeframe"],
        "average_holding_period": contract["average_holding_period"],
        "swing_feature_candidate_rows": len(family_rows),
        "candidate_rows_with_intraday_timestamp_block": sum(1 for row in family_rows if row["blocked_by_intraday_timestamp"] != "0"),
        "candidate_rows_requiring_minute_second_timestamp": sum(1 for row in family_rows if row["minute_second_timestamp_required"] != "0"),
        "feature_materialization_allowed_now_rows": sum(1 for row in family_rows if row["feature_materialization_allowed_now"] != "0"),
        "primary_effect_window": "20D",
        "paper_live_broker_order_opened": False,
        "trading_authority_opened": False,
    }
    (REPORT_DIR / "swing_news_feature_admission_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
