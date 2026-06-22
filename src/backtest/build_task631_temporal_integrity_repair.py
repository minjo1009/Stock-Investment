from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel


TASK_ID = "Task631"
REPORT_DIR = Path("docs/reports/task_631_temporal_integrity_repair")
TASK630_DIR = Path("docs/reports/task_630_block_hold_coverage_and_exact_delay_replay")
TASK630_ATTACHMENT_PATH = TASK630_DIR / "task_630_expanded_trade_action_attachment.csv"
TASK630_LINKAGE_PATH = TASK630_DIR / "task_630_expanded_event_linkage_registry.csv"
TASK630_DELAY_REPLAY_PATH = TASK630_DIR / "task_630_exact_delayed_entry_replay.csv"
SCOPES = ("full_panel", "validation", "recent_oos")
MAX_POSITIONS = (5, 10, 20, 50)
DELAY_MINUTES = (15, 30, 60)
DECISION_COST_BPS = 50
INITIAL_CAPITAL_USD = 1000.0

STRONG_ACTIONS = {"BLOCK_HOLD", "SIZE_DOWN", "DELAY_ENTRY"}
TIMESTAMP_FRESH_MAX_HOURS = 72.0
TIMESTAMP_FRESH_MAX_CALENDAR_DAYS = 3


def build_task631_temporal_integrity_repair(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    task630_attachment_path: Path = TASK630_ATTACHMENT_PATH,
    task630_linkage_path: Path = TASK630_LINKAGE_PATH,
    task630_delay_replay_path: Path = TASK630_DELAY_REPLAY_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task617_panel_path)
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["entry_price"] = pd.to_numeric(panel["entry_price"], errors="coerce")
    panel["simulated_exit_price"] = pd.to_numeric(panel["simulated_exit_price"], errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")

    attachment = pd.read_csv(task630_attachment_path)
    linkage = pd.read_csv(task630_linkage_path)
    delay_replay = pd.read_csv(task630_delay_replay_path)
    temporal = build_temporal_attachment(panel, attachment, linkage)
    policy_eval = build_policy_evaluation(panel, temporal, delay_replay)
    cost_account = build_cost_account_matrix(panel, temporal, delay_replay)
    source_audit = build_source_time_audit(temporal)
    pass_fail = build_pass_fail(temporal, policy_eval, cost_account)
    decision = build_decision(temporal, policy_eval, cost_account, pass_fail)
    gpt_review = build_gpt_review_record()

    out_dir.mkdir(parents=True, exist_ok=True)
    temporal.to_csv(out_dir / "task_631_temporal_action_attachment.csv", index=False)
    policy_eval.to_csv(out_dir / "task_631_policy_variant_evaluation.csv", index=False)
    cost_account.to_csv(out_dir / "task_631_cost_account_matrix.csv", index=False)
    source_audit.to_csv(out_dir / "task_631_source_time_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_631_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_631_decision.csv", index=False)
    gpt_review.to_csv(out_dir / "task_631_gpt_review_capture.csv", index=False)
    (out_dir / "task_631_temporal_integrity_repair.md").write_text(
        render_report(source_audit, policy_eval, cost_account, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_631_temporal_action_attachment": temporal,
        "task_631_policy_variant_evaluation": policy_eval,
        "task_631_cost_account_matrix": cost_account,
        "task_631_source_time_audit": source_audit,
        "task_631_pass_fail_matrix": pass_fail,
        "task_631_decision": decision,
        "task_631_gpt_review_capture": gpt_review,
    }


def build_temporal_attachment(panel: pd.DataFrame, attachment: pd.DataFrame, linkage: pd.DataFrame) -> pd.DataFrame:
    linkage = linkage.copy()
    linkage["event_timestamp_dt"] = pd.to_datetime(linkage["event_timestamp_dt"], utc=True, errors="coerce")
    linkage["event_date_obj"] = pd.to_datetime(linkage["event_date_obj"], errors="coerce")
    link_cols = [
        "event_id",
        "symbol",
        "event_title",
        "source_lane",
        "source_name",
        "time_precision",
        "event_date_obj",
        "event_timestamp_dt",
    ]
    link_key = linkage[[c for c in link_cols if c in linkage.columns]].drop_duplicates(["event_id", "symbol"])
    base = panel[["lifecycle_id", "symbol", "trade_date", "entry_ts", "split_name"]].merge(
        attachment.drop(columns=["symbol"], errors="ignore"),
        on="lifecycle_id",
        how="left",
    )
    base = base.merge(
        link_key,
        left_on=["selected_event_id", "symbol"],
        right_on=["event_id", "symbol"],
        how="left",
    )
    rows = []
    for item in base.to_dict(orient="records"):
        rows.append(temporal_row(item))
    return pd.DataFrame(rows)


def temporal_row(item: dict[str, object]) -> dict[str, object]:
    original_action = str(item.get("action_bucket", "NO_ACTION") or "NO_ACTION")
    entry_ts = pd.Timestamp(item["entry_ts"])
    event_ts = pd.to_datetime(item.get("event_timestamp_dt"), utc=True, errors="coerce")
    event_date = pd.to_datetime(item.get("event_date_obj"), errors="coerce")
    precision = str(item.get("time_precision", "") or "unknown")
    has_event = bool(str(item.get("selected_event_id", "") or ""))

    lag_hours = pd.NA
    lag_calendar_days = pd.NA
    timestamp_after_entry = 0
    time_certified = int(precision == "timestamp" and pd.notna(event_ts))
    if pd.notna(event_ts):
        lag_hours = (entry_ts - event_ts).total_seconds() / 3600.0
        timestamp_after_entry = int(event_ts > entry_ts)
    if pd.notna(event_date):
        lag_calendar_days = (pd.Timestamp(item["trade_date"]) - event_date).days

    date_only_flag = int(precision == "date")
    time_gap_flag = int(has_event and not time_certified)
    entry_eligible = int(time_certified and timestamp_after_entry == 0)
    fresh_action_eligible = int(
        entry_eligible
        and pd.notna(lag_hours)
        and float(lag_hours) >= 0.0
        and float(lag_hours) <= TIMESTAMP_FRESH_MAX_HOURS
        and pd.notna(lag_calendar_days)
        and int(lag_calendar_days) <= TIMESTAMP_FRESH_MAX_CALENDAR_DAYS
    )

    temporal_action, reason = temporal_action_from_original(
        original_action=original_action,
        has_event=has_event,
        date_only_flag=date_only_flag,
        time_gap_flag=time_gap_flag,
        entry_eligible=entry_eligible,
        fresh_action_eligible=fresh_action_eligible,
        timestamp_after_entry=timestamp_after_entry,
    )
    return {
        "lifecycle_id": item["lifecycle_id"],
        "symbol": item["symbol"],
        "split_name": item["split_name"],
        "trade_date": item["trade_date"],
        "entry_ts": entry_ts,
        "selected_event_id": item.get("selected_event_id", ""),
        "event_title": item.get("event_title", ""),
        "source_lane": item.get("source_lane", ""),
        "source_name": item.get("source_name", ""),
        "original_action_bucket": original_action,
        "temporal_action_bucket": temporal_action,
        "temporal_reason": reason,
        "time_precision": precision if precision else "unknown",
        "event_date_obj": event_date,
        "event_timestamp_dt": event_ts,
        "tradable_after_ts": event_ts if time_certified else pd.NaT,
        "lag_hours_if_timestamp": lag_hours,
        "lag_calendar_days": lag_calendar_days,
        "date_only_event_flag": date_only_flag,
        "time_certified_flag": time_certified,
        "entry_eligible_flag": entry_eligible,
        "fresh_action_eligible_flag": fresh_action_eligible,
        "timestamp_after_entry_flag": timestamp_after_entry,
        "source_time_gap_flag": int(temporal_action == "SOURCE_TIME_GAP"),
        "stale_event_gap_flag": int(temporal_action == "STALE_EVENT_GAP"),
        "strong_action_allowed_flag": int(temporal_action in STRONG_ACTIONS),
        "strong_date_only_action_flag": int(date_only_flag == 1 and original_action in STRONG_ACTIONS),
        "source_presence_only_used_flag_task631": 0,
        "gpt_score_used_as_source_flag_task631": 0,
        "label_used_in_assignment_flag_task631": 0,
    }


def temporal_action_from_original(
    *,
    original_action: str,
    has_event: bool,
    date_only_flag: int,
    time_gap_flag: int,
    entry_eligible: int,
    fresh_action_eligible: int,
    timestamp_after_entry: int,
) -> tuple[str, str]:
    if original_action == "NO_ACTION" or not has_event:
        return "NO_ACTION", "no_event_action"
    if timestamp_after_entry:
        return "SOURCE_TIME_GAP", "timestamp_after_entry_blocked"
    if date_only_flag or time_gap_flag:
        return "SOURCE_TIME_GAP", "date_only_or_missing_timestamp_no_strong_action"
    if not entry_eligible:
        return "SOURCE_TIME_GAP", "not_tradable_before_entry"
    if not fresh_action_eligible:
        return "STALE_EVENT_GAP", "timestamp_certified_but_stale_for_action"
    return original_action, "timestamp_certified_fresh_action_allowed"


def build_source_time_audit(temporal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    action_rows = temporal[temporal["original_action_bucket"].ne("NO_ACTION")].copy()
    for group_name, group in [("ALL_ACTION_ROWS", action_rows), *list(action_rows.groupby("original_action_bucket", sort=True))]:
        if isinstance(group_name, tuple):
            name = str(group_name[0])
        else:
            name = str(group_name)
        rows.append(
            {
                "bucket": name,
                "row_count": int(len(group)),
                "date_only_count": int(group["date_only_event_flag"].sum()) if not group.empty else 0,
                "time_certified_count": int(group["time_certified_flag"].sum()) if not group.empty else 0,
                "fresh_action_eligible_count": int(group["fresh_action_eligible_flag"].sum()) if not group.empty else 0,
                "source_time_gap_count": int(group["source_time_gap_flag"].sum()) if not group.empty else 0,
                "stale_event_gap_count": int(group["stale_event_gap_flag"].sum()) if not group.empty else 0,
                "strong_date_only_action_count": int(group["strong_date_only_action_flag"].sum()) if not group.empty else 0,
                "timestamp_after_entry_count": int(group["timestamp_after_entry_flag"].sum()) if not group.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def build_policy_evaluation(panel: pd.DataFrame, temporal: pd.DataFrame, delay_replay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    variants = {"original_turboquant": panel}
    for delay in DELAY_MINUTES:
        variants[f"temporal_strict_exact_delay_{delay}m"] = apply_temporal_policy(panel, temporal, delay_replay, delay)
    for name, frame in variants.items():
        for split in SCOPES:
            group = frame if split == "full_panel" else frame[frame["split_name"].astype(str).eq(split)]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "policy_variant": name,
                    "split_name": split,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def apply_temporal_policy(panel: pd.DataFrame, temporal: pd.DataFrame, delay_replay: pd.DataFrame, delay: int) -> pd.DataFrame:
    frame = panel.merge(
        temporal[["lifecycle_id", "temporal_action_bucket"]],
        on="lifecycle_id",
        how="left",
    ).copy()
    frame["temporal_action_bucket"] = frame["temporal_action_bucket"].fillna("NO_ACTION")
    frame = frame[~frame["temporal_action_bucket"].eq("BLOCK_HOLD")].copy()
    size_down = frame["temporal_action_bucket"].eq("SIZE_DOWN")
    frame.loc[size_down, "net_return_from_entry"] = pd.to_numeric(frame.loc[size_down, "net_return_from_entry"], errors="coerce") * 0.5

    replay = delay_replay[
        delay_replay["delay_minutes"].astype(int).eq(delay)
        & delay_replay["delayed_price_available_flag"].astype(int).eq(1)
    ][["lifecycle_id", "delayed_return"]]
    frame = frame.merge(replay, on="lifecycle_id", how="left")
    delay_rows = frame["temporal_action_bucket"].eq("DELAY_ENTRY")
    frame.loc[delay_rows & frame["delayed_return"].notna(), "net_return_from_entry"] = pd.to_numeric(
        frame.loc[delay_rows & frame["delayed_return"].notna(), "delayed_return"],
        errors="coerce",
    )
    return frame.drop(columns=["delayed_return"], errors="ignore")


def build_cost_account_matrix(panel: pd.DataFrame, temporal: pd.DataFrame, delay_replay: pd.DataFrame) -> pd.DataFrame:
    variants = {"turboquant_original": panel}
    for delay in DELAY_MINUTES:
        variants[f"temporal_strict_exact_delay_{delay}m"] = apply_temporal_policy(panel, temporal, delay_replay, delay)
    rows = []
    for universe, base in variants.items():
        for scope in SCOPES:
            scoped = base if scope == "full_panel" else base[base["split_name"].astype(str).eq(scope)]
            costed = scoped.copy()
            costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - (
                DECISION_COST_BPS / 10000.0
            )
            for max_positions in MAX_POSITIONS:
                quality, accepted, _curve = simulate_deterministic_portfolio(costed, max_positions=max_positions)
                rows.append(
                    {
                        "universe": universe,
                        "scope": scope,
                        "round_trip_cost_bps": DECISION_COST_BPS,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "max_positions": int(max_positions),
                        "source_trade_count": int(len(scoped)),
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
                        "capital_return_pct": float(quality["capital_pnl_pct"]),
                        "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                        "win_rate": float(quality["win_rate"]),
                        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                        "label_used_in_assignment_flag": 0,
                        "gpt_score_used_as_source_flag": 0,
                    }
                )
    return pd.DataFrame(rows)


def best_delay_variant(policy_eval: pd.DataFrame) -> str:
    rows = policy_eval[
        policy_eval["policy_variant"].str.startswith("temporal_strict_exact_delay_")
        & policy_eval["split_name"].eq("recent_oos")
    ].copy()
    rows = rows.sort_values("avg_net_return_pct", ascending=False)
    return str(rows.iloc[0]["policy_variant"])


def metric(policy_eval: pd.DataFrame, variant: str, split: str, column: str) -> float:
    return float(policy_eval[policy_eval["policy_variant"].eq(variant) & policy_eval["split_name"].eq(split)].iloc[0][column])


def capital_wins(cost_account: pd.DataFrame, universe: str, scope: str) -> tuple[int, str]:
    original = cost_account[cost_account["universe"].eq("turboquant_original") & cost_account["scope"].eq(scope)]
    variant = cost_account[cost_account["universe"].eq(universe) & cost_account["scope"].eq(scope)]
    merged = variant[["max_positions", "final_capital_usd"]].merge(
        original[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_variant", "_original"),
    )
    wins = int((merged["final_capital_usd_variant"] > merged["final_capital_usd_original"]).sum())
    pairs = "; ".join(
        f"max{int(r.max_positions)} variant=${float(r.final_capital_usd_variant):.2f} original=${float(r.final_capital_usd_original):.2f}"
        for r in merged.itertuples()
    )
    return wins, pairs


def build_pass_fail(temporal: pd.DataFrame, policy_eval: pd.DataFrame, cost_account: pd.DataFrame) -> pd.DataFrame:
    action_rows = temporal[temporal["original_action_bucket"].ne("NO_ACTION")]
    strong_date_only_after_gate = temporal[
        temporal["temporal_action_bucket"].isin(STRONG_ACTIONS)
        & temporal["date_only_event_flag"].astype(int).eq(1)
    ]
    future_after_gate = temporal[
        temporal["temporal_action_bucket"].isin(STRONG_ACTIONS)
        & temporal["timestamp_after_entry_flag"].astype(int).eq(1)
    ]
    stale_strong_after_gate = temporal[
        temporal["temporal_action_bucket"].isin(STRONG_ACTIONS)
        & temporal["fresh_action_eligible_flag"].astype(int).ne(1)
    ]
    best_variant = best_delay_variant(policy_eval)
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    best_recent = metric(policy_eval, best_variant, "recent_oos", "avg_net_return_pct")
    original_validation = metric(policy_eval, "original_turboquant", "validation", "avg_net_return_pct")
    best_validation = metric(policy_eval, best_variant, "validation", "avg_net_return_pct")
    recent_wins, recent_pairs = capital_wins(cost_account, best_variant, "recent_oos")
    validation_wins, validation_pairs = capital_wins(cost_account, best_variant, "validation")
    full_wins, full_pairs = capital_wins(cost_account, best_variant, "full_panel")
    return pd.DataFrame(
        [
            {
                "gate": "date_only_strong_action_blocked",
                "pass_flag": int(len(strong_date_only_after_gate) == 0),
                "observed_value": f"strong_date_only_after_gate={len(strong_date_only_after_gate)}; original_action_date_only={int(action_rows['date_only_event_flag'].sum())}",
                "required_value": "date-only events cannot create BLOCK_HOLD, SIZE_DOWN, or DELAY_ENTRY",
            },
            {
                "gate": "future_event_action_blocked",
                "pass_flag": int(len(future_after_gate) == 0),
                "observed_value": f"future_strong_actions_after_gate={len(future_after_gate)}",
                "required_value": "tradable_after_ts must be before or equal to entry_ts",
            },
            {
                "gate": "stale_strong_action_blocked",
                "pass_flag": int(len(stale_strong_after_gate) == 0),
                "observed_value": f"stale_strong_actions_after_gate={len(stale_strong_after_gate)}",
                "required_value": "strong actions require timestamp-certified fresh events",
            },
            {
                "gate": "source_time_gap_reported",
                "pass_flag": int(temporal["source_time_gap_flag"].sum() > 0),
                "observed_value": f"source_time_gap_rows={int(temporal['source_time_gap_flag'].sum())}",
                "required_value": "missing/date-only time gaps must be reported rather than treated as positive or negative",
            },
            {
                "gate": "recent_oos_not_worse_gross",
                "pass_flag": int(best_recent >= original_recent),
                "observed_value": f"{best_variant} recent {best_recent:.2f}% vs original {original_recent:.2f}%",
                "required_value": "temporal strict policy should not reduce recent OOS gross average",
            },
            {
                "gate": "validation_not_broken_gross",
                "pass_flag": int(best_validation >= original_validation),
                "observed_value": f"{best_variant} validation {best_validation:.2f}% vs original {original_validation:.2f}%",
                "required_value": "temporal strict policy should not reduce validation gross average",
            },
            {
                "gate": "recent_oos_50bp_account_edge",
                "pass_flag": int(recent_wins >= 3),
                "observed_value": f"{best_variant} wins={recent_wins}/4; {recent_pairs}",
                "required_value": "temporal strict policy beats original in at least 3 of 4 recent-OOS capacities at 50bp",
            },
            {
                "gate": "validation_50bp_not_broken",
                "pass_flag": int(validation_wins >= 2),
                "observed_value": f"{best_variant} wins={validation_wins}/4; {validation_pairs}",
                "required_value": "temporal strict policy is at least mixed on validation account performance at 50bp",
            },
            {
                "gate": "full_panel_50bp_account_edge",
                "pass_flag": int(full_wins >= 2),
                "observed_value": f"{best_variant} wins={full_wins}/4; {full_pairs}",
                "required_value": "temporal strict policy is at least mixed on full-panel account performance at 50bp",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "temporal repair diagnostic only",
                "required_value": "requires live received_at/published_at capture and confirmation-gated entry before promotion",
            },
        ]
    )


def build_decision(
    temporal: pd.DataFrame,
    policy_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    best = best_delay_variant(policy_eval)
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")]["pass_flag"].iloc[0])
    validation_pass = int(pass_fail[pass_fail["gate"].eq("validation_50bp_not_broken")]["pass_flag"].iloc[0])
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_edge")]["pass_flag"].iloc[0])
    counts = temporal["temporal_action_bucket"].value_counts().to_dict()
    decision = "FAIL_TEMPORAL_STRICT_ACTION_NOT_ACCEPTED"
    if recent_pass and validation_pass and full_pass:
        decision = "PASS_TEMPORAL_STRICT_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "best_temporal_variant": best,
                "temporal_block_hold_count": int(counts.get("BLOCK_HOLD", 0)),
                "temporal_size_down_count": int(counts.get("SIZE_DOWN", 0)),
                "temporal_delay_entry_count": int(counts.get("DELAY_ENTRY", 0)),
                "temporal_confirmation_required_count": int(counts.get("CONFIRMATION_REQUIRED", 0)),
                "temporal_source_time_gap_count": int(counts.get("SOURCE_TIME_GAP", 0)),
                "temporal_stale_event_gap_count": int(counts.get("STALE_EVENT_GAP", 0)),
                "temporal_no_action_count": int(counts.get("NO_ACTION", 0)),
                "date_only_original_action_count": int(
                    temporal[temporal["original_action_bucket"].ne("NO_ACTION")]["date_only_event_flag"].sum()
                ),
                "strong_date_only_after_gate_count": int(
                    len(temporal[temporal["temporal_action_bucket"].isin(STRONG_ACTIONS) & temporal["date_only_event_flag"].astype(int).eq(1)])
                ),
                "recent_oos_50bp_account_edge_pass_flag": recent_pass,
                "validation_50bp_not_broken_pass_flag": validation_pass,
                "full_panel_50bp_account_edge_pass_flag": full_pass,
                "source_presence_only_used_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "label_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Add live received_at/published_at/tradable_after_ts capture and build confirmation-gated entry; keep date-only events out of strong actions.",
            }
        ]
    )


def build_gpt_review_record() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT 1. coding/investment tab",
                "captured_at_kst": "2026-06-07",
                "source_type": "external_model_interpretation_not_source_truth",
                "used_as_source_flag": 0,
                "review_summary": (
                    "Firm-grade temporal integrity requires published_at/received_at/tradable_after_ts, "
                    "date-only strong action bans, source-specific windows, stale action decay, and explicit SOURCE_TIME_GAP reporting."
                ),
            }
        ]
    )


def render_report(
    source_audit: pd.DataFrame,
    policy_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task631 Temporal Integrity Repair",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- GPT/Chrome was used only as review input, not source truth or score input.",
        f"- Date-only original action rows: {int(d['date_only_original_action_count'])}",
        f"- Strong date-only actions after gate: {int(d['strong_date_only_after_gate_count'])}",
        f"- Temporal actions: BLOCK/HOLD {int(d['temporal_block_hold_count'])}, SIZE_DOWN {int(d['temporal_size_down_count'])}, DELAY_ENTRY {int(d['temporal_delay_entry_count'])}, SOURCE_TIME_GAP {int(d['temporal_source_time_gap_count'])}, STALE_EVENT_GAP {int(d['temporal_stale_event_gap_count'])}.",
        "",
        "## Quant Expert Report",
        "",
        "Task631 turns time alignment into a hard gate. Date-only events cannot create `BLOCK_HOLD`, `SIZE_DOWN`, or `DELAY_ENTRY`. Timestamped events must be tradable before entry and fresh enough for action.",
        "",
        "### Source Time Audit",
        "",
        "| Bucket | Rows | Date-only | Time Certified | Fresh Eligible | Source Time Gap | Stale Gap | Strong Date-only Original | Future Timestamp |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in source_audit.iterrows():
        lines.append(
            f"| `{row['bucket']}` | {int(row['row_count'])} | {int(row['date_only_count'])} | "
            f"{int(row['time_certified_count'])} | {int(row['fresh_action_eligible_count'])} | "
            f"{int(row['source_time_gap_count'])} | {int(row['stale_event_gap_count'])} | "
            f"{int(row['strong_date_only_action_count'])} | {int(row['timestamp_after_entry_count'])} |"
        )
    lines.extend(
        [
            "",
            "### Gross Evaluation",
            "",
            "| Variant | Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in policy_eval.iterrows():
        lines.append(
            f"| `{row['policy_variant']}` | `{row['split_name']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']):.2f}% | {float(row['entry_reduce_failure_rate']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### 50bp Account Matrix",
            "",
            "| Scope | Universe | Max Positions | Final $ | Return |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in cost_account.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- 사장님 지적대로 시간축을 고쳤습니다.",
            "- 날짜만 있는 뉴스는 강한 매매 액션을 만들 수 없습니다.",
            "- 7일 창으로 붙은 이벤트는 `SOURCE_TIME_GAP` 또는 `STALE_EVENT_GAP`으로 빠집니다.",
            "- 이 수정은 성과를 예쁘게 만들기 위한 게 아니라, 틀린 시간 연결을 막기 위한 겁니다.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_expanded_trade_action_attachment.csv`",
            "- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_expanded_event_linkage_registry.csv`",
            "- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_exact_delayed_entry_replay.csv`",
            "",
            "### Outputs",
            "",
            "- `task_631_temporal_action_attachment.csv`",
            "- `task_631_policy_variant_evaluation.csv`",
            "- `task_631_cost_account_matrix.csv`",
            "- `task_631_source_time_audit.csv`",
            "- `task_631_pass_fail_matrix.csv`",
            "- `task_631_decision.csv`",
            "- `task_631_gpt_review_capture.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task631_temporal_integrity_repair`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
            "- `python scripts/governance_completion_audit.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task631_temporal_integrity_repair(out_dir=args.out_dir)
    row = artifacts["task_631_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"date_only_original_actions={int(row['date_only_original_action_count'])} "
        f"strong_date_only_after_gate={int(row['strong_date_only_after_gate_count'])}"
    )


if __name__ == "__main__":
    main()
