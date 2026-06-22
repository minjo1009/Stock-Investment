from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_shadow_integration_360 import generate_shadow_artifacts
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _prepare_corrected_entry_master
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH, _load_intraday_bars
from src.backtest.continuation_intraday_events import build_continuation_intraday_events, build_intraday_event_summary
from src.backtest.continuation_lifecycle_replay import run_lifecycle_replay
from src.backtest.continuation_setup_identity import build_setup_identity_frame, build_setup_identity_summary
from src.backtest.continuation_timeline_builder import build_event_timelines_dataframe
from src.backtest.exposure_evolution_snapshot import build_exposure_evolution_snapshots


DEFAULT_OUT_DIR = Path("docs/reports/task_366_multi_event_dataset")


@dataclass(frozen=True)
class MultiEventReplayDatasetArtifacts:
    multi_event_replay_dataset: pd.DataFrame
    event_timelines: pd.DataFrame
    exposure_evolution: pd.DataFrame
    setup_identity_summary: pd.DataFrame
    intraday_event_summary: pd.DataFrame
    setup_frame: pd.DataFrame
    lifecycle_rows: pd.DataFrame
    replay_trace: pd.DataFrame


def build_multi_event_replay_dataset(
    shadow_log_df: pd.DataFrame | None = None,
    corrected_master_df: pd.DataFrame | None = None,
    intraday_bars_df: pd.DataFrame | None = None,
) -> MultiEventReplayDatasetArtifacts:
    shadow_log = shadow_log_df.copy() if shadow_log_df is not None else generate_shadow_artifacts(enable_shadow_state_engine=True).shadow_log.copy()
    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    intraday_bars = intraday_bars_df.copy() if intraday_bars_df is not None else _load_intraday_bars(DB_PATH).copy()

    lifecycle_rows_df, replay_trace_df, _transition_matrix_df, _lifecycle_summary_df = run_lifecycle_replay(shadow_log)
    setup_frame = build_setup_identity_frame(
        shadow_log,
        replay_trace_df,
        lifecycle_rows_df,
        corrected_master,
    )
    events_df = build_continuation_intraday_events(setup_frame, intraday_bars)
    timelines_df = build_event_timelines_dataframe(events_df)
    exposure_df = build_exposure_evolution_snapshots(events_df)
    setup_summary_df = build_setup_identity_summary(setup_frame)
    event_summary_df = build_intraday_event_summary(events_df)

    dataset_df = events_df.merge(
        exposure_df[
            [
                "event_id",
                "current_size_multiplier",
                "cumulative_add_count",
                "persistence_duration_minutes",
            ]
        ],
        on="event_id",
        how="left",
    )

    return MultiEventReplayDatasetArtifacts(
        multi_event_replay_dataset=dataset_df,
        event_timelines=timelines_df,
        exposure_evolution=exposure_df,
        setup_identity_summary=setup_summary_df,
        intraday_event_summary=event_summary_df,
        setup_frame=setup_frame,
        lifecycle_rows=lifecycle_rows_df,
        replay_trace=replay_trace_df,
    )


def write_multi_event_replay_dataset(
    artifacts: MultiEventReplayDatasetArtifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.multi_event_replay_dataset.to_csv(out_dir / "task_366_multi_event_replay_dataset.csv", index=False)
    artifacts.event_timelines.to_csv(out_dir / "task_366_event_timelines.csv", index=False)
    artifacts.exposure_evolution.to_csv(out_dir / "task_366_exposure_evolution.csv", index=False)
    artifacts.setup_identity_summary.to_csv(out_dir / "task_366_setup_identity_summary.csv", index=False)
    artifacts.intraday_event_summary.to_csv(out_dir / "task_366_intraday_event_summary.csv", index=False)
