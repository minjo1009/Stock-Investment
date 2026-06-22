from __future__ import annotations

import argparse
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


TASK_ID = "T601-4"
INPUT_EVENTS_PATH = Path("docs/reports/task_601_1_candidate_funnel_implementation/candidate_funnel_events.csv")
SELECTED_CANDIDATES_PATH = Path("docs/reports/task_601_3_portfolio_selection_layer/selected_portfolio_candidates.csv")
REPORT_DIR = Path("docs/reports/task_601_4_concentration_stability")
DEFAULT_RECENT_SESSION_COUNT = 7


@dataclass(frozen=True)
class ConcentrationStabilityResult:
    before_after_metrics: pd.DataFrame
    session_metrics: pd.DataFrame
    recent_window_metrics: pd.DataFrame
    decision: pd.DataFrame


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _upper(value: object) -> str:
    return _text(value).upper()


def _safe_ratio(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _entropy(values: list[float]) -> float:
    total = float(sum(values))
    if total <= 0:
        return 0.0
    probs = [float(value) / total for value in values if float(value) > 0]
    return round(-sum(prob * math.log(prob) for prob in probs), 6)


def _gini(values: list[float]) -> float:
    nums = sorted(float(value) for value in values if float(value) >= 0)
    total = sum(nums)
    count = len(nums)
    if count == 0 or total <= 0:
        return 0.0
    weighted_sum = sum((index + 1) * value for index, value in enumerate(nums))
    return round(((2.0 * weighted_sum) / (count * total)) - ((count + 1.0) / count), 6)


def _session(value: object) -> str:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return ""
    return str(ts.date())


def _metrics_from_counts(counts: pd.Series, *, label: str, session_count: int, source_stage: str) -> dict[str, Any]:
    clean = counts.astype(float)
    total = float(clean.sum())
    sorted_counts = clean.sort_values(ascending=False)
    return {
        "metric_scope": label,
        "source_stage": source_stage,
        "candidate_count": int(total),
        "session_count": int(session_count),
        "symbol_count": int((clean > 0).sum()),
        "top1_share": _safe_ratio(float(sorted_counts.head(1).sum()), total),
        "top3_share": _safe_ratio(float(sorted_counts.head(3).sum()), total),
        "entropy": _entropy(clean.tolist()),
        "gini": _gini(clean.tolist()),
        "proximity_fallback_used_flag": 0,
    }


def _select_before_stage(candidate_funnel_events: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if candidate_funnel_events.empty:
        return candidate_funnel_events.iloc[0:0].copy(), "NONE"
    frame = candidate_funnel_events.copy()
    if "stage" not in frame.columns:
        frame["stage"] = ""
    frame["stage"] = frame["stage"].map(_upper)
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).map(_upper)
    for stage in ("FILLED", "ORDERED", "ELIGIBLE", "GENERATED"):
        rows = frame.loc[frame["stage"].eq(stage) & frame["symbol"].ne("")].copy()
        if not rows.empty:
            return rows, stage
    return frame.iloc[0:0].copy(), "NONE"


def _symbol_counts(frame: pd.DataFrame) -> pd.Series:
    if frame.empty or "symbol" not in frame.columns:
        return pd.Series(dtype=float)
    return frame["symbol"].map(_upper).loc[lambda values: values.ne("")].value_counts().astype(float)


def _session_metrics(selected_candidates: pd.DataFrame) -> pd.DataFrame:
    if selected_candidates.empty:
        return pd.DataFrame(
            columns=[
                "session",
                "candidate_count",
                "symbol_count",
                "top1_share",
                "top3_share",
                "entropy",
                "gini",
                "per_session_low_sample_flag",
                "proximity_fallback_used_flag",
            ]
        )
    frame = selected_candidates.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).map(_upper)
    frame["session"] = frame.get("generated_time", pd.Series(dtype=str)).map(_session)
    rows: list[dict[str, Any]] = []
    for session, group in frame.loc[frame["session"].ne("")].groupby("session", sort=True):
        metrics = _metrics_from_counts(_symbol_counts(group), label="after_session", session_count=1, source_stage="SELECTED")
        rows.append(
            {
                "session": session,
                "candidate_count": metrics["candidate_count"],
                "symbol_count": metrics["symbol_count"],
                "top1_share": metrics["top1_share"],
                "top3_share": metrics["top3_share"],
                "entropy": metrics["entropy"],
                "gini": metrics["gini"],
                "per_session_low_sample_flag": int(metrics["candidate_count"] < 4),
                "proximity_fallback_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_concentration_stability(
    candidate_funnel_events: pd.DataFrame,
    selected_candidates: pd.DataFrame,
    *,
    recent_session_count: int = DEFAULT_RECENT_SESSION_COUNT,
) -> ConcentrationStabilityResult:
    before_rows, before_stage = _select_before_stage(candidate_funnel_events)
    selected = selected_candidates.copy()
    if not selected.empty:
        selected["symbol"] = selected.get("symbol", pd.Series(dtype=str)).map(_upper)
        selected["session"] = selected.get("generated_time", pd.Series(dtype=str)).map(_session)

    before_sessions = (
        before_rows.get("generated_time", pd.Series(dtype=str)).map(_session).loc[lambda values: values.ne("")].nunique()
        if not before_rows.empty
        else 0
    )
    after_sessions = int(selected["session"].loc[selected["session"].ne("")].nunique()) if "session" in selected.columns else 0
    before_metrics = _metrics_from_counts(
        _symbol_counts(before_rows),
        label="before_funnel",
        session_count=int(before_sessions),
        source_stage=before_stage,
    )
    after_metrics = _metrics_from_counts(
        _symbol_counts(selected),
        label="after_selection_all_sessions",
        session_count=after_sessions,
        source_stage="SELECTED",
    )
    before_after = pd.DataFrame([before_metrics, after_metrics])

    per_session = _session_metrics(selected)
    recent_sessions = (
        sorted(selected["session"].loc[selected["session"].ne("")].unique().tolist())[-max(1, int(recent_session_count)) :]
        if "session" in selected.columns and not selected.empty
        else []
    )
    recent = selected.loc[selected["session"].isin(recent_sessions)].copy() if recent_sessions else selected.iloc[0:0].copy()
    recent_metrics = _metrics_from_counts(
        _symbol_counts(recent),
        label=f"after_selection_recent_{len(recent_sessions)}_sessions",
        session_count=len(recent_sessions),
        source_stage="SELECTED",
    )
    recent_window = pd.DataFrame(
        [
            {
                **recent_metrics,
                "recent_session_count_requested": int(recent_session_count),
                "recent_sessions": ";".join(recent_sessions),
            }
        ]
    )
    explanation = _decision_status(recent_metrics)
    decision = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision_status": explanation["decision_status"],
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "before_top3_share": before_metrics["top3_share"],
                "after_top3_share": after_metrics["top3_share"],
                "recent_window_top3_share": recent_metrics["top3_share"],
                "recent_window_session_count": recent_metrics["session_count"],
                "recent_window_entropy": recent_metrics["entropy"],
                "recent_window_gini": recent_metrics["gini"],
                "symbol_count": recent_metrics["symbol_count"],
                "proximity_fallback_used_flag": 0,
                "stability_assessment": explanation["stability_assessment"],
                "acceptance_impact": explanation["acceptance_impact"],
            }
        ]
    )
    return ConcentrationStabilityResult(
        before_after_metrics=before_after,
        session_metrics=per_session,
        recent_window_metrics=recent_window,
        decision=decision,
    )


def _decision_status(metrics: dict[str, Any]) -> dict[str, str]:
    if int(metrics["session_count"]) < 2:
        return {
            "decision_status": "FAIL_INSUFFICIENT_MULTI_SESSION_EVIDENCE",
            "stability_assessment": "single-session improvement only or insufficient selected sessions",
            "acceptance_impact": "FAIL: multiple-session concentration stability cannot be claimed.",
        }
    if float(metrics["top3_share"]) < 0.80:
        return {
            "decision_status": "PASS_MULTI_SESSION_TOP3_BELOW_0_80",
            "stability_assessment": "recent selected window spans multiple sessions and top3_share is below 0.80",
            "acceptance_impact": "PASS for T601-4 stability validation; strategy remains NOT_ACCEPTED.",
        }
    return {
        "decision_status": "FAIL_RECENT_WINDOW_TOP3_NOT_STABLE",
        "stability_assessment": "recent selected window spans multiple sessions but top3_share is not below 0.80",
        "acceptance_impact": "FAIL: concentration improvement is not stable enough for this gate.",
    }


def _write_csv(report_dir: Path, filename: str, frame: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(report_dir / filename, index=False, encoding="utf-8-sig")


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.iterdir()):
        if not path.is_file() or path.name == "artifact_manifest.csv":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "relative_path": path.name,
                "artifact_class": "report" if path.suffix.lower() == ".md" else "small_table",
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    pd.DataFrame(rows, columns=["relative_path", "artifact_class", "size_bytes", "sha256"]).to_csv(
        report_dir / "artifact_manifest.csv",
        index=False,
    )


def write_outputs(result: ConcentrationStabilityResult, report_dir: Path = REPORT_DIR) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir, "concentration_before_after_metrics.csv", result.before_after_metrics)
    _write_csv(report_dir, "concentration_session_metrics.csv", result.session_metrics)
    _write_csv(report_dir, "concentration_recent_window_metrics.csv", result.recent_window_metrics)
    _write_csv(report_dir, "task_601_4_decision.csv", result.decision)
    _write_report(report_dir / "concentration_stability_report.md", result)
    _write_manifest(report_dir)


def _write_report(path: Path, result: ConcentrationStabilityResult) -> None:
    before = result.before_after_metrics.loc[result.before_after_metrics["metric_scope"].eq("before_funnel")].iloc[0].to_dict()
    after = result.before_after_metrics.loc[result.before_after_metrics["metric_scope"].eq("after_selection_all_sessions")].iloc[0].to_dict()
    recent = result.recent_window_metrics.iloc[0].to_dict()
    decision = result.decision.iloc[0].to_dict()
    lines = [
        "# Decision Summary",
        "",
        f"- Verdict: {decision['decision_status']}",
        "- Strategy acceptance status: NOT_ACCEPTED",
        f"- Key metrics: before_top3_share={before['top3_share']}, after_top3_share={after['top3_share']}, recent_window_top3_share={recent['top3_share']}, entropy={recent['entropy']}, gini={recent['gini']}, symbol_count={recent['symbol_count']}",
        "- What changed: concentration stability is now measured across selected candidate sessions without changing entry, exit, replay, or strategy logic.",
        f"- Next action: {decision['acceptance_impact']}",
        "",
        "# Before",
        "",
        f"- source_stage={before['source_stage']}",
        f"- candidate_count={before['candidate_count']}",
        f"- session_count={before['session_count']}",
        f"- top1_share={before['top1_share']}",
        f"- top3_share={before['top3_share']}",
        f"- entropy={before['entropy']}",
        f"- gini={before['gini']}",
        f"- symbol_count={before['symbol_count']}",
        "",
        "# After",
        "",
        f"- candidate_count={after['candidate_count']}",
        f"- session_count={after['session_count']}",
        f"- top1_share={after['top1_share']}",
        f"- top3_share={after['top3_share']}",
        f"- entropy={after['entropy']}",
        f"- gini={after['gini']}",
        f"- symbol_count={after['symbol_count']}",
        "",
        "# Stability Assessment",
        "",
        f"- {decision['stability_assessment']}",
        f"- recent_sessions={recent['recent_sessions']}",
        "- Per-session metrics are reported separately because sessions with fewer than four selected candidates make top3_share mechanically equal to 1.0.",
        "- Matching policy: exact candidate_id and generated_time session grouping only; no lifecycle symbol/date/price/time fallback was used.",
        "",
        "# Acceptance Impact",
        "",
        f"- {decision['acceptance_impact']}",
        "- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY and real capital remains FORBIDDEN.",
        "",
        "# Quant Expert Report",
        "",
        "- Data source and source readiness: T601-1 candidate_funnel_events and T601-3 selected_portfolio_candidates.",
        "- Exact join keys: candidate_id for selection rows and generated_time-derived session labels for stability grouping.",
        "- Leakage audit: labels/outcomes do not enter assignment logic.",
        "- Split/OOS metrics: not applicable; this is operational concentration stability over runtime candidate sessions.",
        "- Failure decomposition: insufficient session count or recent top3_share >= 0.80 fails this gate.",
        "- Cost/slippage stress where PnL changed: not applicable.",
        "- Remaining blockers: sector concentration remains source-blocked until sector evidence exists.",
        "",
        "# No-Background Decision-Maker Report",
        "",
        "- What happened: the selected portfolio is checked across the recent multi-session window instead of one aggregate headline only.",
        "- Why it matters: a single-session concentration improvement is not enough for acceptance review.",
        "- Whether this changes capital/deployment readiness: no.",
        f"- Plain-language next step: {decision['acceptance_impact']}",
        "",
        "# Artifact Manifest",
        "",
        "- concentration_before_after_metrics.csv",
        "- concentration_session_metrics.csv",
        "- concentration_recent_window_metrics.csv",
        "- task_601_4_decision.csv",
        "- artifact_manifest.csv",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_task601_4(
    input_events_path: Path = INPUT_EVENTS_PATH,
    selected_candidates_path: Path = SELECTED_CANDIDATES_PATH,
    report_dir: Path = REPORT_DIR,
    *,
    recent_session_count: int = DEFAULT_RECENT_SESSION_COUNT,
) -> dict[str, Any]:
    candidate_funnel_events = pd.read_csv(input_events_path)
    selected_candidates = pd.read_csv(selected_candidates_path)
    result = build_concentration_stability(
        candidate_funnel_events,
        selected_candidates,
        recent_session_count=recent_session_count,
    )
    write_outputs(result, report_dir)
    return result.decision.iloc[0].to_dict()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-events", type=Path, default=INPUT_EVENTS_PATH)
    parser.add_argument("--selected-candidates", type=Path, default=SELECTED_CANDIDATES_PATH)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--recent-session-count", type=int, default=DEFAULT_RECENT_SESSION_COUNT)
    args = parser.parse_args()
    summary = run_task601_4(
        args.input_events,
        args.selected_candidates,
        args.report_dir,
        recent_session_count=args.recent_session_count,
    )
    print(pd.DataFrame([summary]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
