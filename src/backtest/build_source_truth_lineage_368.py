from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _prepare_corrected_entry_master
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH, _load_intraday_bars
from src.backtest.add_scale_lineage import build_add_scale_lineage
from src.backtest.build_multi_event_replay_dataset_366 import (
    MultiEventReplayDatasetArtifacts,
    build_multi_event_replay_dataset,
)
from src.backtest.build_source_truth_replay_dataset_367 import (
    SourceTruthReplayArtifacts,
    build_source_truth_replay_dataset,
)
from src.backtest.persistence_lineage_timeline import build_persistence_lineage_timeline
from src.backtest.source_setup_identity import build_source_setup_identity
from src.backtest.source_truth_lineage import build_source_truth_lineage


DEFAULT_OUT_DIR = Path("docs/reports/task_368_source_truth_lineage")


@dataclass(frozen=True)
class SourceTruthLineageArtifacts:
    lineage_summary: pd.DataFrame
    persistence_timeline: pd.DataFrame
    persistence_summary: pd.DataFrame
    add_scale_evolution: pd.DataFrame
    replay_fidelity: pd.DataFrame
    lineage_confidence: pd.DataFrame
    setup_identity: pd.DataFrame
    setup_identity_summary: pd.DataFrame
    lineage_rows: pd.DataFrame
    source_truth_replay_dataset: pd.DataFrame
    upstream_367: SourceTruthReplayArtifacts
    upstream_366: MultiEventReplayDatasetArtifacts


def build_source_truth_lineage_dataset(
    source_truth_artifacts: SourceTruthReplayArtifacts | None = None,
    multi_event_artifacts: MultiEventReplayDatasetArtifacts | None = None,
    corrected_master_df: pd.DataFrame | None = None,
    intraday_bars_df: pd.DataFrame | None = None,
) -> SourceTruthLineageArtifacts:
    upstream_366 = multi_event_artifacts if multi_event_artifacts is not None else build_multi_event_replay_dataset()
    upstream_367 = source_truth_artifacts if source_truth_artifacts is not None else build_source_truth_replay_dataset(
        multi_event_artifacts=upstream_366,
        corrected_master_df=corrected_master_df,
        intraday_bars_df=intraday_bars_df,
    )
    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    intraday_bars = intraday_bars_df.copy() if intraday_bars_df is not None else _load_intraday_bars(DB_PATH).copy()

    setup_identity_df, setup_identity_summary_df = build_source_setup_identity(
        upstream_366.setup_frame,
        upstream_366.multi_event_replay_dataset,
        corrected_master,
        intraday_bars,
    )
    lineage_rows_df, lineage_summary_df, replay_fidelity_df, lineage_confidence_df = build_source_truth_lineage(
        upstream_367.source_truth_replay_dataset,
        setup_identity_df,
    )
    add_scale_evolution_df = build_add_scale_lineage(lineage_rows_df)
    persistence_timeline_df, persistence_summary_df = build_persistence_lineage_timeline(lineage_rows_df)

    lineage_summary_df = lineage_summary_df.merge(
        add_scale_evolution_df.groupby("continuation_id", dropna=False)
        .agg(
            final_add_depth=("add_depth", "max"),
            final_scale_depth=("scale_depth", "max"),
            max_cumulative_size_multiplier=("cumulative_size_multiplier", "max"),
        )
        .reset_index(),
        on="continuation_id",
        how="left",
    ).merge(
        persistence_summary_df,
        on=["continuation_id", "setup_id"],
        how="left",
    )

    return SourceTruthLineageArtifacts(
        lineage_summary=lineage_summary_df,
        persistence_timeline=persistence_timeline_df,
        persistence_summary=persistence_summary_df,
        add_scale_evolution=add_scale_evolution_df,
        replay_fidelity=replay_fidelity_df,
        lineage_confidence=lineage_confidence_df,
        setup_identity=setup_identity_df,
        setup_identity_summary=setup_identity_summary_df,
        lineage_rows=lineage_rows_df,
        source_truth_replay_dataset=upstream_367.source_truth_replay_dataset,
        upstream_367=upstream_367,
        upstream_366=upstream_366,
    )


def write_source_truth_lineage_dataset(
    artifacts: SourceTruthLineageArtifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.lineage_summary.to_csv(out_dir / "task_368_lineage_summary.csv", index=False)
    artifacts.persistence_timeline.to_csv(out_dir / "task_368_persistence_timeline.csv", index=False)
    artifacts.add_scale_evolution.to_csv(out_dir / "task_368_add_scale_evolution.csv", index=False)
    artifacts.replay_fidelity.to_csv(out_dir / "task_368_replay_fidelity.csv", index=False)
    artifacts.lineage_confidence.to_csv(out_dir / "task_368_lineage_confidence.csv", index=False)
