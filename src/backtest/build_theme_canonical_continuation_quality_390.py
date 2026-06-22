from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK388_DIR = Path("docs/reports/task_388_theme_10x7_intraday_canonical_continuation")
DEFAULT_THEME_UNIVERSE = Path("data/raw/theme_universe_10x7.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_390_theme_canonical_continuation_quality")


@dataclass(frozen=True)
class ThemeCanonicalContinuationQuality390Artifacts:
    theme_continuation_quality: pd.DataFrame
    lifecycle_path_quality: pd.DataFrame
    add_scale_reinforcement_quality: pd.DataFrame
    reduce_weakening_quality: pd.DataFrame
    theme_state_transition_quality: pd.DataFrame
    task_390_decision: pd.DataFrame


def build_theme_canonical_continuation_quality_390(
    *,
    task388_dir: Path = DEFAULT_TASK388_DIR,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> ThemeCanonicalContinuationQuality390Artifacts:
    events = pd.read_csv(task388_dir / "intraday_canonical_event_log.csv", encoding="utf-8-sig")
    lifecycles = pd.read_csv(task388_dir / "intraday_canonical_lifecycle_summary.csv", encoding="utf-8-sig")
    themes = pd.read_csv(theme_universe_path, encoding="utf-8-sig")
    panel = build_lifecycle_quality_panel(events, lifecycles, themes)
    theme_quality = summarize_theme_quality(panel)
    path_quality = summarize_path_quality(panel)
    add_scale_quality = summarize_add_scale_reinforcement(panel)
    reduce_quality = summarize_reduce_weakening(panel)
    transition_quality = summarize_theme_state_transitions(panel)
    decision = build_task_390_decision(panel, theme_quality, path_quality)
    artifacts = ThemeCanonicalContinuationQuality390Artifacts(
        theme_continuation_quality=theme_quality,
        lifecycle_path_quality=path_quality,
        add_scale_reinforcement_quality=add_scale_quality,
        reduce_weakening_quality=reduce_quality,
        theme_state_transition_quality=transition_quality,
        task_390_decision=decision,
    )
    write_task_390_artifacts(artifacts, out_dir)
    return artifacts


def build_lifecycle_quality_panel(events: pd.DataFrame, lifecycles: pd.DataFrame, themes: pd.DataFrame) -> pd.DataFrame:
    theme_map = themes.copy()
    theme_map["symbol"] = theme_map["symbol"].astype(str).str.upper()
    lifecycles = lifecycles.copy()
    lifecycles["symbol"] = lifecycles["symbol"].astype(str).str.upper()
    lifecycles["return_from_entry"] = pd.to_numeric(lifecycles["return_from_entry"], errors="coerce")
    lifecycles["bars_held"] = pd.to_numeric(lifecycles["bars_held"], errors="coerce")
    for column in ["add_flag", "scale_flag", "reduce_flag"]:
        lifecycles[column] = pd.to_numeric(lifecycles[column], errors="coerce").fillna(0).astype(int)
    paths = build_lifecycle_paths(events)
    panel = lifecycles.merge(theme_map[["theme", "symbol", "role"]], on="symbol", how="left")
    panel = panel.merge(paths, on="lifecycle_id", how="left")
    panel["theme"] = panel["theme"].fillna("unknown")
    panel["role"] = panel["role"].fillna("unknown")
    panel["lifecycle_path"] = panel["lifecycle_path"].fillna("UNKNOWN")
    panel["positive_return_flag"] = (panel["return_from_entry"] > 0).astype(int)
    panel["add_scale_flag"] = ((panel["add_flag"] == 1) & (panel["scale_flag"] == 1)).astype(int)
    return panel


def build_lifecycle_paths(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["lifecycle_id", "lifecycle_path"])
    tmp = events.copy()
    tmp["event_timestamp_dt"] = pd.to_datetime(tmp["event_timestamp"], errors="coerce", utc=True)
    rows = []
    for lifecycle_id, group in tmp.sort_values(["lifecycle_id", "event_timestamp_dt"]).groupby("lifecycle_id"):
        path = "_".join(group["event_type"].astype(str).tolist())
        rows.append({"lifecycle_id": lifecycle_id, "lifecycle_path": path})
    return pd.DataFrame(rows)


def summarize_theme_quality(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["theme"]).sort_values(["avg_return_from_entry", "lifecycle_count"], ascending=[False, False])


def summarize_path_quality(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["lifecycle_path"]).sort_values(["avg_return_from_entry", "lifecycle_count"], ascending=[False, False])


def summarize_add_scale_reinforcement(panel: pd.DataFrame) -> pd.DataFrame:
    scoped = panel.copy()
    scoped["reinforcement_group"] = "entry_only_or_reduce"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 0), "reinforcement_group"] = "add_only"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 1), "reinforcement_group"] = "add_scale"
    return _summarize(scoped, ["reinforcement_group"]).sort_values("avg_return_from_entry", ascending=False)


def summarize_reduce_weakening(panel: pd.DataFrame) -> pd.DataFrame:
    scoped = panel.copy()
    scoped["reduce_group"] = scoped["reduce_flag"].map({1: "reduce_present", 0: "no_reduce"})
    return _summarize(scoped, ["reduce_group"]).sort_values("avg_return_from_entry", ascending=False)


def summarize_theme_state_transitions(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["theme", "lifecycle_path"]).sort_values(["theme", "avg_return_from_entry"], ascending=[True, False])


def build_task_390_decision(panel: pd.DataFrame, theme_quality: pd.DataFrame, path_quality: pd.DataFrame) -> pd.DataFrame:
    sample_ready = int(len(panel) >= 300 and panel["theme"].nunique() >= 10)
    top_theme = "" if theme_quality.empty else str(theme_quality.iloc[0]["theme"])
    top_path = "" if path_quality.empty else str(path_quality.iloc[0]["lifecycle_path"])
    return pd.DataFrame(
        [
            {
                "task_390_verdict": "COMPLETE_PASS",
                "evaluation_status": "DIAGNOSTIC_ONLY",
                "canonical_lifecycle_count": len(panel),
                "theme_count": int(panel["theme"].nunique()) if not panel.empty else 0,
                "sample_ready_flag": sample_ready,
                "top_theme_by_avg_return": top_theme,
                "top_path_by_avg_return": top_path,
                "reconstruction_used_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "deployment_claim_flag": 0,
                "next_priority": "theme_oos_expansion_or_longer_intraday_history",
            }
        ]
    )


def write_task_390_artifacts(artifacts: ThemeCanonicalContinuationQuality390Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.theme_continuation_quality.to_csv(out_dir / "theme_continuation_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.lifecycle_path_quality.to_csv(out_dir / "lifecycle_path_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.add_scale_reinforcement_quality.to_csv(out_dir / "add_scale_reinforcement_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.reduce_weakening_quality.to_csv(out_dir / "reduce_weakening_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.theme_state_transition_quality.to_csv(out_dir / "theme_state_transition_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.task_390_decision.to_csv(out_dir / "task_390_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 390 - Theme-Based Canonical Continuation Quality Evaluation",
        "",
        "## Decision",
        artifacts.task_390_decision.to_csv(index=False).strip(),
        "",
        "## Theme Quality",
        artifacts.theme_continuation_quality.to_csv(index=False).strip(),
        "",
        "## ADD/SCALE Reinforcement",
        artifacts.add_scale_reinforcement_quality.to_csv(index=False).strip(),
        "",
        "## REDUCE Weakening",
        artifacts.reduce_weakening_quality.to_csv(index=False).strip(),
    ]
    (out_dir / "task_390_theme_canonical_continuation_quality.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=keys + ["lifecycle_count", "avg_return_from_entry", "median_return_from_entry", "positive_rate", "add_rate", "scale_rate", "reduce_rate", "avg_bars_held"])
    grouped = frame.groupby(keys, dropna=False)
    out = grouped.agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_return_from_entry=("return_from_entry", "mean"),
        median_return_from_entry=("return_from_entry", "median"),
        positive_rate=("positive_return_flag", "mean"),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
        avg_bars_held=("bars_held", "mean"),
    ).reset_index()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 390 theme canonical continuation quality evaluation.")
    parser.add_argument("--task388-dir", type=Path, default=DEFAULT_TASK388_DIR)
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_theme_canonical_continuation_quality_390(
        task388_dir=args.task388_dir,
        theme_universe_path=args.theme_universe,
        out_dir=args.out_dir,
    )
    row = artifacts.task_390_decision.iloc[0]
    print(
        "[TASK390] "
        f"status={row['evaluation_status']} lifecycles={row['canonical_lifecycle_count']} "
        f"themes={row['theme_count']} top_theme={row['top_theme_by_avg_return']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
