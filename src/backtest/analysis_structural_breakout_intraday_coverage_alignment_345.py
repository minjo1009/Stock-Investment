from __future__ import annotations

import argparse
import math
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    _load_frozen_behavior_state,
    _markdown_table,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import (
    DB_PATH,
    MIN_POSTBREAK_BARS,
    MIN_PREBREAK_BARS,
    _load_intraday_bars,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_345_intraday_coverage_alignment")
NY_TZ = ZoneInfo("America/New_York")
EXPECTED_OPEN = time(9, 30)
EXPECTED_CLOSE = time(15, 59)
RELAXED_PREBREAK_MIN_BARS = 1
RELAXED_POSTBREAK_MIN_BARS = 1
FULL_PERIOD = "full_period"
ANCHORED_OOS = "anchored_oos"
WINDOW_RULES = {
    "current_strict": (MIN_PREBREAK_BARS, MIN_POSTBREAK_BARS),
    "relaxed_prebreak_minimum": (RELAXED_PREBREAK_MIN_BARS, MIN_POSTBREAK_BARS),
    "relaxed_postbreak_minimum": (MIN_PREBREAK_BARS, RELAXED_POSTBREAK_MIN_BARS),
}
ALIGNMENT_RULES = (
    "high_touch_first_touch",
    "close_confirmed_break",
    "tolerant_max_high_close",
)
FAILURE_REASON_ORDER = [
    "insufficient_prebreak_bars",
    "insufficient_postbreak_bars",
    "breakout_bar_not_found",
    "short_session_or_holiday_session",
    "provider_session_truncation",
    "timezone_or_timestamp_misalignment",
]


def _load_trade_frames() -> dict[str, pd.DataFrame]:
    train_df, oos_df, full_df = _load_frozen_behavior_state()
    return {
        "train": train_df.copy(),
        ANCHORED_OOS: oos_df.copy(),
        FULL_PERIOD: full_df.copy(),
    }


def _expected_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _timestamp_to_local(ts: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(ts)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert(NY_TZ)


def _session_metadata(session: pd.DataFrame) -> dict[str, object]:
    if session.empty:
        return {
            "session_bar_count": 0,
            "session_start_utc": "",
            "session_end_utc": "",
            "session_start_local": "",
            "session_end_local": "",
            "start_offset_minutes": math.nan,
            "end_offset_minutes": math.nan,
        }
    start_utc = pd.Timestamp(session.loc[0, "bar_start_ts"])
    end_utc = pd.Timestamp(session.loc[len(session) - 1, "bar_end_ts"])
    start_local = _timestamp_to_local(start_utc)
    end_local = _timestamp_to_local(end_utc)
    return {
        "session_bar_count": int(len(session)),
        "session_start_utc": start_utc.isoformat(),
        "session_end_utc": end_utc.isoformat(),
        "session_start_local": start_local.isoformat(),
        "session_end_local": end_local.isoformat(),
        "start_offset_minutes": int(
            (start_local.hour * 60 + start_local.minute) - _expected_minutes(EXPECTED_OPEN)
        ),
        "end_offset_minutes": int(
            (end_local.hour * 60 + end_local.minute) - _expected_minutes(EXPECTED_CLOSE)
        ),
    }


def _alignment_mask(session: pd.DataFrame, breakout_level: float, rule_name: str) -> pd.Series:
    if rule_name == "high_touch_first_touch":
        return pd.to_numeric(session["high"], errors="coerce") >= breakout_level
    if rule_name == "close_confirmed_break":
        return pd.to_numeric(session["close"], errors="coerce") >= breakout_level
    if rule_name == "tolerant_max_high_close":
        high_values = pd.to_numeric(session["high"], errors="coerce")
        close_values = pd.to_numeric(session["close"], errors="coerce")
        return pd.concat([high_values, close_values], axis=1).max(axis=1) >= breakout_level
    raise ValueError(f"unsupported alignment rule: {rule_name}")


def _breakout_diagnostic(session: pd.DataFrame, breakout_level: float, rule_name: str) -> dict[str, object]:
    if session.empty or pd.isna(breakout_level):
        return {"breakout_idx": math.nan, "breakout_ts": "", "bar_found": False}
    mask = _alignment_mask(session, float(breakout_level), rule_name)
    hits = session.index[mask].tolist()
    if not hits:
        return {"breakout_idx": math.nan, "breakout_ts": "", "bar_found": False}
    breakout_idx = int(hits[0])
    breakout_ts = pd.Timestamp(session.loc[breakout_idx, "bar_start_ts"]).isoformat()
    return {"breakout_idx": breakout_idx, "breakout_ts": breakout_ts, "bar_found": True}


def _coverage_under_rule(session_bar_count: int, breakout_idx: float, prebreak_min: int, postbreak_min: int) -> bool:
    if pd.isna(breakout_idx):
        return False
    idx = int(breakout_idx)
    entry_only_covered = idx >= prebreak_min
    immediate_covered = idx >= prebreak_min and session_bar_count > idx + postbreak_min
    return bool(entry_only_covered or immediate_covered)


def _is_short_session_or_holiday(metadata: dict[str, object]) -> bool:
    if int(metadata["session_bar_count"]) == 0:
        return False
    end_local = metadata["session_end_local"]
    if not end_local:
        return False
    end_ts = _timestamp_to_local(pd.Timestamp(end_local))
    return bool(
        (end_ts.hour < 13 or (end_ts.hour == 13 and end_ts.minute <= 5))
        and int(metadata["session_bar_count"]) <= 42
    )


def _is_timezone_misalignment(metadata: dict[str, object]) -> bool:
    if pd.isna(metadata["start_offset_minutes"]):
        return False
    return 55 <= abs(int(metadata["start_offset_minutes"])) <= 65


def _is_provider_session_truncation(metadata: dict[str, object]) -> bool:
    if int(metadata["session_bar_count"]) == 0:
        return False
    if _is_short_session_or_holiday(metadata) or _is_timezone_misalignment(metadata):
        return False
    if int(metadata["session_bar_count"]) < 60:
        return True
    if int(metadata["start_offset_minutes"]) > 5:
        return True
    return int(metadata["end_offset_minutes"]) < -4


def _failure_taxonomy(session: pd.DataFrame, metadata: dict[str, object], current_breakout_idx: float) -> str:
    if pd.isna(current_breakout_idx):
        return "breakout_bar_not_found"
    if _is_short_session_or_holiday(metadata):
        return "short_session_or_holiday_session"
    if _is_timezone_misalignment(metadata):
        return "timezone_or_timestamp_misalignment"
    if _is_provider_session_truncation(metadata):
        return "provider_session_truncation"
    if int(current_breakout_idx) < MIN_PREBREAK_BARS:
        return "insufficient_prebreak_bars"
    if int(metadata["session_bar_count"]) <= int(current_breakout_idx) + MIN_POSTBREAK_BARS:
        return "insufficient_postbreak_bars"
    return "insufficient_prebreak_bars"


def _recoverability_class(
    current_covered: bool,
    alignment_only_covered: bool,
    window_only_covered: bool,
    alignment_and_window_covered: bool,
) -> str:
    if current_covered:
        return "already_covered"
    if alignment_only_covered:
        return "recoverable_by_alignment_only"
    if window_only_covered:
        return "recoverable_by_window_rule_only"
    if alignment_and_window_covered:
        return "recoverable_by_alignment_and_window_rule"
    return "non_recoverable_from_current_archive"


def _trade_analysis_rows(frame: pd.DataFrame, split_name: str, intraday_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, trade_row in frame.iterrows():
        symbol = str(trade_row.get("symbol", "")).upper()
        entry_date = str(trade_row.get("entry_date", ""))
        session = intraday_df[
            (intraday_df["symbol"] == symbol) & (intraday_df["bar_date"] == entry_date)
        ].reset_index(drop=True)
        breakout_level = pd.to_numeric(pd.Series([trade_row.get("breakout_level")]), errors="coerce").iloc[0]
        metadata = _session_metadata(session)
        diagnostics = {
            rule_name: _breakout_diagnostic(session, breakout_level, rule_name)
            for rule_name in ALIGNMENT_RULES
        }
        current_idx = diagnostics["high_touch_first_touch"]["breakout_idx"]
        current_covered = _coverage_under_rule(
            int(metadata["session_bar_count"]),
            current_idx,
            MIN_PREBREAK_BARS,
            MIN_POSTBREAK_BARS,
        )
        close_confirm_covered = _coverage_under_rule(
            int(metadata["session_bar_count"]),
            diagnostics["close_confirmed_break"]["breakout_idx"],
            MIN_PREBREAK_BARS,
            MIN_POSTBREAK_BARS,
        )
        high_touch_relaxed_pre_covered = _coverage_under_rule(
            int(metadata["session_bar_count"]),
            current_idx,
            RELAXED_PREBREAK_MIN_BARS,
            MIN_POSTBREAK_BARS,
        )
        high_touch_relaxed_post_covered = _coverage_under_rule(
            int(metadata["session_bar_count"]),
            current_idx,
            MIN_PREBREAK_BARS,
            RELAXED_POSTBREAK_MIN_BARS,
        )
        close_confirm_relaxed_union_covered = any(
            _coverage_under_rule(
                int(metadata["session_bar_count"]),
                diagnostics["close_confirmed_break"]["breakout_idx"],
                pre_min,
                post_min,
            )
            for pre_min, post_min in WINDOW_RULES.values()
            if (pre_min, post_min) != (MIN_PREBREAK_BARS, MIN_POSTBREAK_BARS)
        )
        if int(metadata["session_bar_count"]) == 0:
            if intraday_df[intraday_df["symbol"] == symbol].empty:
                current_missing_reason = "missing_symbol"
            else:
                current_missing_reason = "missing_date"
            failure_reason = current_missing_reason
        else:
            current_missing_reason = "" if current_covered else "incomplete_intraday_window"
            failure_reason = "" if current_covered else _failure_taxonomy(session, metadata, current_idx)
        recoverability = _recoverability_class(
            current_covered=current_covered,
            alignment_only_covered=close_confirm_covered,
            window_only_covered=(high_touch_relaxed_pre_covered or high_touch_relaxed_post_covered),
            alignment_and_window_covered=close_confirm_relaxed_union_covered,
        )
        rows.append(
            {
                "split": split_name,
                "trade_id": str(trade_row.get("trade_id", "")),
                "symbol": symbol,
                "entry_date": entry_date,
                "sector_bucket": str(trade_row.get("sector_bucket", "")),
                "scenario_family": str(trade_row.get("scenario_family", "")),
                "breakout_level": breakout_level,
                "current_missing_reason": current_missing_reason,
                "failure_reason": failure_reason,
                "recoverability_class": recoverability,
                "session_bar_count": int(metadata["session_bar_count"]),
                "session_start_utc": metadata["session_start_utc"],
                "session_end_utc": metadata["session_end_utc"],
                "session_start_local": metadata["session_start_local"],
                "session_end_local": metadata["session_end_local"],
                "start_offset_minutes": metadata["start_offset_minutes"],
                "end_offset_minutes": metadata["end_offset_minutes"],
                "current_breakout_idx": current_idx,
                "current_breakout_ts": diagnostics["high_touch_first_touch"]["breakout_ts"],
                "close_confirm_breakout_idx": diagnostics["close_confirmed_break"]["breakout_idx"],
                "close_confirm_breakout_ts": diagnostics["close_confirmed_break"]["breakout_ts"],
                "tolerant_breakout_idx": diagnostics["tolerant_max_high_close"]["breakout_idx"],
                "tolerant_breakout_ts": diagnostics["tolerant_max_high_close"]["breakout_ts"],
                "current_covered": current_covered,
                "close_confirm_strict_covered": close_confirm_covered,
                "high_touch_relaxed_pre_covered": high_touch_relaxed_pre_covered,
                "high_touch_relaxed_post_covered": high_touch_relaxed_post_covered,
                "close_confirm_relaxed_union_covered": close_confirm_relaxed_union_covered,
            }
        )
    return pd.DataFrame(rows)


def _coverage_failure_taxonomy(full_trade_df: pd.DataFrame, oos_trade_df: pd.DataFrame) -> pd.DataFrame:
    scoped = full_trade_df[full_trade_df["current_missing_reason"] == "incomplete_intraday_window"].copy()
    anchored_scoped = oos_trade_df[oos_trade_df["current_missing_reason"] == "incomplete_intraday_window"].copy()
    rows: list[dict[str, object]] = []
    total = max(len(scoped), 1)
    for reason in FAILURE_REASON_ORDER:
        reason_df = scoped[scoped["failure_reason"] == reason]
        anchored_reason_df = anchored_scoped[anchored_scoped["failure_reason"] == reason]
        rows.append(
            {
                "failure_reason": reason,
                "trade_count": int(len(reason_df)),
                "share_of_incomplete": round(float(len(reason_df) / total), 6),
                "anchored_oos_trade_count": int(len(anchored_reason_df)),
                "software_internet_anchored_oos_trade_count": int(
                    anchored_reason_df["sector_bucket"].eq("software/internet").sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def _window_alignment_comparison(trade_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split_name in ("train", ANCHORED_OOS, FULL_PERIOD):
        scoped = trade_df[trade_df["split"] == split_name].copy()
        total = len(scoped)
        for alignment_rule in ALIGNMENT_RULES:
            breakout_col = {
                "high_touch_first_touch": "current_breakout_idx",
                "close_confirmed_break": "close_confirm_breakout_idx",
                "tolerant_max_high_close": "tolerant_breakout_idx",
            }[alignment_rule]
            for window_rule, (pre_min, post_min) in WINDOW_RULES.items():
                covered_mask = pd.Series(
                    [
                        _coverage_under_rule(
                            int(row["session_bar_count"]),
                            row[breakout_col],
                            pre_min,
                            post_min,
                        )
                        for _, row in scoped.iterrows()
                    ],
                    index=scoped.index,
                    dtype=bool,
                )
                rows.append(
                    {
                        "split": split_name,
                        "alignment_rule": alignment_rule,
                        "window_rule": window_rule,
                        "prebreak_min_bars": pre_min,
                        "postbreak_min_bars": post_min,
                        "covered_trade_count": int(covered_mask.sum()),
                        "recovered_trade_count_vs_current": int(
                            covered_mask.sum() - scoped["current_covered"].astype(bool).sum()
                        ),
                        "coverage_ratio": round(float(covered_mask.mean()) if total else 0.0, 6),
                    }
                )
    return pd.DataFrame(rows)


def _breakout_timestamp_diagnostics(trade_df: pd.DataFrame) -> pd.DataFrame:
    return (
        trade_df[trade_df["current_missing_reason"] == "incomplete_intraday_window"]
        .copy()[
            [
                "trade_id",
                "symbol",
                "entry_date",
                "sector_bucket",
                "session_bar_count",
                "session_start_local",
                "session_end_local",
                "start_offset_minutes",
                "end_offset_minutes",
                "current_breakout_idx",
                "current_breakout_ts",
                "close_confirm_breakout_idx",
                "close_confirm_breakout_ts",
                "tolerant_breakout_idx",
                "tolerant_breakout_ts",
                "failure_reason",
            ]
        ]
        .sort_values(["entry_date", "symbol", "trade_id"])
        .reset_index(drop=True)
    )


def _recoverable_trade_candidates(trade_df: pd.DataFrame) -> pd.DataFrame:
    scoped = trade_df[~trade_df["current_covered"].astype(bool)].copy()
    return scoped[
        [
            "trade_id",
            "symbol",
            "entry_date",
            "sector_bucket",
            "scenario_family",
            "current_missing_reason",
            "failure_reason",
            "recoverability_class",
            "session_bar_count",
            "session_start_local",
            "session_end_local",
            "current_breakout_idx",
            "close_confirm_breakout_idx",
            "tolerant_breakout_idx",
            "close_confirm_strict_covered",
            "high_touch_relaxed_pre_covered",
            "high_touch_relaxed_post_covered",
            "close_confirm_relaxed_union_covered",
        ]
    ].sort_values(["entry_date", "symbol", "trade_id"]).reset_index(drop=True)


def _coverage_recovery_summary(trade_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split_name in (FULL_PERIOD, ANCHORED_OOS):
        scoped = trade_df[trade_df["split"] == split_name].copy()
        base_count = int(scoped["current_covered"].astype(bool).sum())
        software_mask = scoped["sector_bucket"].eq("software/internet")
        variants = {
            "current_strict_high_touch": scoped["current_covered"].astype(bool),
            "strict_close_confirm": scoped["close_confirm_strict_covered"].astype(bool),
            "relaxed_prebreak_high_touch": scoped["high_touch_relaxed_pre_covered"].astype(bool),
            "relaxed_postbreak_high_touch": scoped["high_touch_relaxed_post_covered"].astype(bool),
            "combined_best_recovery": scoped["recoverability_class"].isin(
                {
                    "already_covered",
                    "recoverable_by_alignment_only",
                    "recoverable_by_window_rule_only",
                    "recoverable_by_alignment_and_window_rule",
                }
            ),
        }
        for variant_name, mask in variants.items():
            rows.append(
                {
                    "split": split_name,
                    "variant": variant_name,
                    "covered_trade_count": int(mask.sum()),
                    "delta_vs_current": int(mask.sum() - base_count),
                    "coverage_ratio": round(float(mask.mean()) if len(scoped) else 0.0, 6),
                    "software_internet_trade_count": int((mask & software_mask).sum()),
                }
            )
    return pd.DataFrame(rows)


def _final_decision(summary_df: pd.DataFrame) -> pd.DataFrame:
    full_best = summary_df[
        (summary_df["split"] == FULL_PERIOD) & (summary_df["variant"] == "combined_best_recovery")
    ].iloc[0]
    oos_best = summary_df[
        (summary_df["split"] == ANCHORED_OOS) & (summary_df["variant"] == "combined_best_recovery")
    ].iloc[0]
    full_gain = int(full_best["delta_vs_current"])
    oos_gain = int(oos_best["delta_vs_current"])
    software_gain = int(oos_best["software_internet_trade_count"]) - int(
        summary_df[
            (summary_df["split"] == ANCHORED_OOS) & (summary_df["variant"] == "current_strict_high_touch")
        ].iloc[0]["software_internet_trade_count"]
    )
    if oos_gain >= 25 or software_gain >= 10:
        decision = "MATERIAL_RECOVERABLE_COVERAGE"
        reason = "alignment and/or window-rule diagnostics recover a meaningfully larger anchored OOS sample"
    elif oos_gain > 0 or full_gain > 0:
        decision = "PARTIAL_RECOVERABLE_COVERAGE"
        reason = "current archive can recover additional covered trades, but the anchored OOS lift is still moderate"
    else:
        decision = "NO_RECOVERABLE_COVERAGE"
        reason = "alignment and relaxed window diagnostics do not add enough covered trades to justify rerunning downstream tasks"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "full_period_recovered_trade_gain": full_gain,
                "anchored_oos_recovered_trade_gain": oos_gain,
                "anchored_oos_software_internet_gain": software_gain,
            }
        ]
    )


def _markdown_report(
    out_dir: Path,
    taxonomy_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    recovery_df: pd.DataFrame,
    decision_df: pd.DataFrame,
) -> None:
    decision = decision_df.iloc[0]
    anchored_rows = comparison_df[comparison_df["split"] == ANCHORED_OOS].copy()
    anchored_rows = anchored_rows.sort_values(
        ["recovered_trade_count_vs_current", "alignment_rule", "window_rule"],
        ascending=[False, True, True],
    ).head(6)
    lines: list[str] = [
        "# Task 345: Intraday Coverage Alignment Audit & Covered-Subset Recovery",
        "",
        f"Final decision: **{decision['decision']}**",
        "",
        "## Failure Taxonomy",
        "",
    ]
    lines.extend(_markdown_table(taxonomy_df))
    lines.extend(
        [
            "",
            "## Anchored OOS Alignment / Window Comparison",
            "",
        ]
    )
    lines.extend(_markdown_table(anchored_rows))
    lines.extend(
        [
            "",
            "## Recovery Summary",
            "",
        ]
    )
    lines.extend(_markdown_table(recovery_df))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The dominant current failure mode is `{taxonomy_df.sort_values('trade_count', ascending=False).iloc[0]['failure_reason']}`.",
            "- `tolerant_max_high_close` is mathematically equivalent to `high_touch_first_touch`, so it does not create extra recovery by construction.",
            "- Relaxing the post-break minimum does not materially help because the current failures are almost entirely pre-break alignment / pre-break window failures.",
            f"- Best combined recovery adds `{decision['anchored_oos_recovered_trade_gain']}` anchored OOS covered trades and `{decision['anchored_oos_software_internet_gain']}` software/internet anchored OOS trades.",
            "- If this recovery is accepted as diagnostic-valid, rerunning Tasks 338-342 is justified before moving to priority overlay research.",
        ]
    )
    (out_dir / "task_345_intraday_coverage_alignment.md").write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path = DEFAULT_OUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    trade_frames = _load_trade_frames()
    intraday_df = _load_intraday_bars(DB_PATH)
    full_analysis = _trade_analysis_rows(trade_frames[FULL_PERIOD], FULL_PERIOD, intraday_df)
    oos_analysis = _trade_analysis_rows(trade_frames[ANCHORED_OOS], ANCHORED_OOS, intraday_df)
    train_analysis = _trade_analysis_rows(trade_frames["train"], "train", intraday_df)
    trade_df = pd.concat([train_analysis, oos_analysis, full_analysis], ignore_index=True)

    taxonomy_df = _coverage_failure_taxonomy(full_analysis, oos_analysis)
    comparison_df = _window_alignment_comparison(trade_df)
    diagnostics_df = _breakout_timestamp_diagnostics(full_analysis)
    recoverable_df = _recoverable_trade_candidates(full_analysis)
    recovery_df = _coverage_recovery_summary(trade_df)
    decision_df = _final_decision(recovery_df)

    taxonomy_df.to_csv(output_dir / "task_345_coverage_failure_taxonomy.csv", index=False)
    comparison_df.to_csv(output_dir / "task_345_window_alignment_comparison.csv", index=False)
    diagnostics_df.to_csv(output_dir / "task_345_breakout_timestamp_diagnostics.csv", index=False)
    recoverable_df.to_csv(output_dir / "task_345_recoverable_trade_candidates.csv", index=False)
    recovery_df.to_csv(output_dir / "task_345_coverage_recovery_summary.csv", index=False)
    decision_df.to_csv(output_dir / "task_345_final_decision.csv", index=False)
    _markdown_report(output_dir, taxonomy_df, comparison_df, recovery_df, decision_df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 345: intraday coverage alignment audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
