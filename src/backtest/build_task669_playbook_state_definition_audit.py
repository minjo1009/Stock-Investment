from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task669"
TASK668_DIR = Path("docs/reports/task_668_regime_theme_playbook")
REPORT_DIR = Path("docs/reports/task_669_playbook_state_definition_audit")


def build_task669_playbook_state_definition_audit(
    *,
    task668_dir: Path = TASK668_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(task668_dir / "task668_playbook_panel.csv")
    accepted = pd.read_csv(task668_dir / "task668_accepted_trades.csv")
    perf = pd.read_csv(task668_dir / "task668_playbook_performance.csv")
    mdd = pd.read_csv(task668_dir / "task668_mdd_interval_audit.csv")

    component = build_component_mix(panel)
    purity = build_state_purity_audit(panel)
    perf_audit = build_performance_audit(perf)
    mdd_audit = build_mdd_state_audit(mdd)
    catalyst_matrix = build_playbook_catalyst_matrix(accepted)
    redefinition = build_redefinition_candidates(purity, perf_audit, mdd_audit)
    decision = build_decision(purity, redefinition)
    pass_fail = build_pass_fail(component, purity, perf_audit, mdd_audit, catalyst_matrix, redefinition)

    component.to_csv(out_dir / "task669_state_component_mix.csv", index=False, encoding="utf-8-sig")
    purity.to_csv(out_dir / "task669_state_purity_audit.csv", index=False, encoding="utf-8-sig")
    perf_audit.to_csv(out_dir / "task669_state_performance_audit.csv", index=False, encoding="utf-8-sig")
    mdd_audit.to_csv(out_dir / "task669_mdd_state_audit.csv", index=False, encoding="utf-8-sig")
    catalyst_matrix.to_csv(out_dir / "task669_playbook_catalyst_matrix.csv", index=False, encoding="utf-8-sig")
    redefinition.to_csv(out_dir / "task669_redefinition_candidates.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_669_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_669_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, purity, perf_audit, mdd_audit, catalyst_matrix, redefinition, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "component": component,
        "purity": purity,
        "perf_audit": perf_audit,
        "mdd_audit": mdd_audit,
        "catalyst_matrix": catalyst_matrix,
        "redefinition": redefinition,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_component_mix(panel: pd.DataFrame) -> pd.DataFrame:
    cols = ["playbook_id", "market_state", "theme_state", "mechanism_relation_state", "catalyst_quality_tier", "price_acceptance_state"]
    return panel.groupby(cols, dropna=False).size().reset_index(name="candidate_count").sort_values(["playbook_id", "candidate_count"], ascending=[True, False]).reset_index(drop=True)


def build_state_purity_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(panel)
    for playbook, group in panel.groupby("playbook_id", dropna=False):
        top_mix = (
            group.groupby(["market_state", "theme_state", "mechanism_relation_state", "catalyst_quality_tier", "price_acceptance_state"], dropna=False)
            .size()
            .sort_values(ascending=False)
        )
        top_count = int(top_mix.iloc[0]) if len(top_mix) else 0
        rows.append(
            {
                "playbook_id": playbook,
                "candidate_count": int(len(group)),
                "candidate_share": float(len(group) / max(total, 1)),
                "unique_market_states": int(group["market_state"].nunique()),
                "unique_theme_states": int(group["theme_state"].nunique()),
                "unique_relation_states": int(group["mechanism_relation_state"].nunique()),
                "unique_catalyst_tiers": int(group["catalyst_quality_tier"].nunique()),
                "unique_price_states": int(group["price_acceptance_state"].nunique()),
                "top_component_count": top_count,
                "top_component_share": float(top_count / max(len(group), 1)),
                "mixed_state_flag": int(
                    group["theme_state"].nunique() > 2
                    or group["mechanism_relation_state"].nunique() > 3
                    or group["catalyst_quality_tier"].nunique() > 3
                    or top_count / max(len(group), 1) < 0.35
                ),
                "sparse_sample_flag": int(len(group) < 30),
            }
        )
    return pd.DataFrame(rows).sort_values(["mixed_state_flag", "candidate_count"], ascending=[False, False]).reset_index(drop=True)


def build_performance_audit(perf: pd.DataFrame) -> pd.DataFrame:
    active = perf[(perf["candidate_name"].eq("active_relation_cap3_reference")) & (perf["split_scope"].eq("all"))].copy()
    if active.empty:
        return pd.DataFrame()
    active["high_return_state_flag"] = (pd.to_numeric(active["avg_return_pct"], errors="coerce") >= 50.0).astype(int)
    active["high_failure_state_flag"] = (pd.to_numeric(active["entry_reduce_failure_rate"], errors="coerce") >= 0.40).astype(int)
    active["sparse_performance_flag"] = (pd.to_numeric(active["trade_count"], errors="coerce") < 5).astype(int)
    return active.sort_values("avg_return_pct", ascending=False).reset_index(drop=True)


def build_mdd_state_audit(mdd: pd.DataFrame) -> pd.DataFrame:
    active = mdd[mdd["candidate_name"].eq("active_relation_cap3_reference")].copy()
    if active.empty:
        return pd.DataFrame()
    active["negative_mdd_exposure_flag"] = (pd.to_numeric(active["avg_return_costed_pct"], errors="coerce") < 0.0).astype(int)
    return active.sort_values(["audit_group", "active_trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_playbook_catalyst_matrix(accepted: pd.DataFrame) -> pd.DataFrame:
    active = accepted[(accepted["candidate_name"].eq("active_relation_cap3_reference")) & (accepted["split_scope"].eq("all"))].copy()
    if active.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in active.groupby(["playbook_id", "catalyst_quality_tier", "mechanism_relation_state", "theme_state"], dropna=False):
        playbook, catalyst, relation, theme_state = keys
        returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
        rows.append(
            {
                "playbook_id": playbook,
                "catalyst_quality_tier": catalyst,
                "mechanism_relation_state": relation,
                "theme_state": theme_state,
                "trade_count": int(len(group)),
                "avg_return_pct": float(returns.mean() * 100.0),
                "win_rate": float(returns.gt(0).mean()),
                "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["playbook_id", "trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_redefinition_candidates(purity: pd.DataFrame, perf: pd.DataFrame, mdd: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mixed = set(purity[purity["mixed_state_flag"].eq(1)]["playbook_id"].astype(str))
    high_return = set(perf[pd.to_numeric(perf["high_return_state_flag"], errors="coerce").eq(1)]["playbook_id"].astype(str)) if not perf.empty else set()
    high_failure = set(perf[pd.to_numeric(perf["high_failure_state_flag"], errors="coerce").eq(1)]["playbook_id"].astype(str)) if not perf.empty else set()
    negative_mdd = set(
        mdd[(mdd["audit_group"].eq("playbook_id")) & (pd.to_numeric(mdd["negative_mdd_exposure_flag"], errors="coerce").eq(1))]["group_value"].astype(str)
    ) if not mdd.empty else set()
    for playbook in sorted(mixed | high_return | high_failure | negative_mdd):
        reasons = []
        if playbook in mixed:
            reasons.append("mixed_components")
        if playbook in high_return:
            reasons.append("name_may_understate_positive_payoff")
        if playbook in high_failure:
            reasons.append("high_entry_reduce_failure")
        if playbook in negative_mdd:
            reasons.append("negative_mdd_exposure")
        rows.append(
            {
                "playbook_id": playbook,
                "redefinition_required_flag": 1,
                "reason": "+".join(reasons),
                "promotion_allowed_flag": 0,
                "recommended_next_check": "split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping",
            }
        )
    return pd.DataFrame(rows)


def build_decision(purity: pd.DataFrame, redefinition: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PLAYBOOK_STATE_DEFINITION_AUDIT_REDEFINITION_REQUIRED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "mixed_state_count": int(pd.to_numeric(purity["mixed_state_flag"], errors="coerce").sum()) if not purity.empty else 0,
                "redefinition_candidate_count": int(len(redefinition)),
                "trading_promotion_pass_flag": 0,
                "next_action": "Redefine playbook states before adding new action rules; especially audit confirmation_required and normal_participation.",
            }
        ]
    )


def build_pass_fail(component: pd.DataFrame, purity: pd.DataFrame, perf: pd.DataFrame, mdd: pd.DataFrame, catalyst: pd.DataFrame, redefinition: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"gate": "component_mix_built", "pass_flag": int(not component.empty), "observed_value": f"rows={len(component)}", "required_value": "playbook component mix exists"},
            {"gate": "state_purity_audit_built", "pass_flag": int(not purity.empty), "observed_value": f"rows={len(purity)}", "required_value": "state purity audit exists"},
            {"gate": "performance_audit_built", "pass_flag": int(not perf.empty), "observed_value": f"rows={len(perf)}", "required_value": "playbook performance audit exists"},
            {"gate": "mdd_state_audit_built", "pass_flag": int(not mdd.empty), "observed_value": f"rows={len(mdd)}", "required_value": "MDD state audit exists"},
            {"gate": "catalyst_matrix_built", "pass_flag": int(not catalyst.empty), "observed_value": f"rows={len(catalyst)}", "required_value": "playbook catalyst matrix exists"},
            {"gate": "redefinition_required", "pass_flag": int(len(redefinition) > 0), "observed_value": f"states={len(redefinition)}", "required_value": "mixed or misleading states are identified"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def write_report(out_dir: Path, decision: pd.DataFrame, purity: pd.DataFrame, perf: pd.DataFrame, mdd: pd.DataFrame, catalyst: pd.DataFrame, redefinition: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task669 Playbook State Definition Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Mixed states: `{int(d['mixed_state_count'])}`",
        f"- Redefinition candidates: `{int(d['redefinition_candidate_count'])}`",
        "",
        "## Quant Expert Report",
        "",
        "Task669 audits whether Task668 playbook names represent coherent states. It does not add a new trading rule.",
        "",
        "### State Purity Audit",
        "",
        table(purity),
        "",
        "### Performance Audit",
        "",
        table(perf),
        "",
        "### MDD State Audit",
        "",
        table(mdd),
        "",
        "### Playbook Catalyst Matrix",
        "",
        table(catalyst),
        "",
        "### Redefinition Candidates",
        "",
        table(redefinition),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "현재 playbook 이름들이 아직 충분히 깨끗하지 않습니다.",
        "",
        "`confirmation_required`만 문제가 아니라 `normal_participation`, `rotation_selective`, `research_only_sparse`도 여러 상태가 섞여 있습니다.",
        "",
        "그래서 지금 단계에서 새 매매룰을 더 붙이면 과최적화 위험이 큽니다. 먼저 상태 정의를 다시 쪼개야 합니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task669_state_component_mix.csv`",
        "- `task669_state_purity_audit.csv`",
        "- `task669_state_performance_audit.csv`",
        "- `task669_mdd_state_audit.csv`",
        "- `task669_playbook_catalyst_matrix.csv`",
        "- `task669_redefinition_candidates.csv`",
        "- `task_669_gpt_review_packet.md`",
        "- `task_669_gpt_review_response.md`",
        "- `task_669_decision.csv`",
        "- `task_669_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_669_playbook_state_definition_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    lines = ["| " + " | ".join(map(str, clipped.columns)) + " |", "| " + " | ".join(["---"] * len(clipped.columns)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(cell(row.get(c, "")) for c in clipped.columns) + " |")
    return "\n".join(lines)


def cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task669_playbook_state_definition_audit(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"mixed={int(decision['mixed_state_count'])} "
        f"redefinition={int(decision['redefinition_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
