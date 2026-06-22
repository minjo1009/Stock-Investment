from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _prepare_corrected_entry_master
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH, _load_intraday_bars
from src.backtest.build_multi_event_replay_dataset_366 import (
    MultiEventReplayDatasetArtifacts,
    build_multi_event_replay_dataset,
)
from src.backtest.continuation_event_lineage import build_continuation_event_lineage
from src.backtest.source_truth_continuation_identity import build_source_truth_continuation_identity


DEFAULT_OUT_DIR = Path("docs/reports/task_367_source_truth_replay")


@dataclass(frozen=True)
class SourceTruthReplayArtifacts:
    source_truth_replay_dataset: pd.DataFrame
    event_lineage: pd.DataFrame
    continuation_depth: pd.DataFrame
    replay_fidelity: pd.DataFrame
    continuation_identity: pd.DataFrame
    continuation_lineage: pd.DataFrame
    upstream_366: MultiEventReplayDatasetArtifacts


def build_source_truth_replay_dataset(
    multi_event_artifacts: MultiEventReplayDatasetArtifacts | None = None,
    corrected_master_df: pd.DataFrame | None = None,
    intraday_bars_df: pd.DataFrame | None = None,
) -> SourceTruthReplayArtifacts:
    upstream = multi_event_artifacts if multi_event_artifacts is not None else build_multi_event_replay_dataset()
    corrected_master = corrected_master_df.copy() if corrected_master_df is not None else _prepare_corrected_entry_master().copy()
    intraday_bars = intraday_bars_df.copy() if intraday_bars_df is not None else _load_intraday_bars(DB_PATH).copy()

    row_identity_df, continuation_identity_df = build_source_truth_continuation_identity(
        upstream.multi_event_replay_dataset,
        upstream.setup_frame,
        corrected_master,
        intraday_bars,
    )
    event_lineage_df, continuation_lineage_df, continuation_depth_df, replay_fidelity_df = build_continuation_event_lineage(
        upstream.multi_event_replay_dataset,
        row_identity_df,
        continuation_identity_df,
    )

    dataset_df = upstream.multi_event_replay_dataset.merge(
        event_lineage_df[
            [
                "continuation_id",
                "event_id",
                "linkage_source",
                "lineage_confidence",
                "lineage_quality",
                "lineage_break_reason",
                "source_linked_flag",
            ]
        ].drop_duplicates(subset=["continuation_id", "event_id"], keep="first"),
        on=["continuation_id", "event_id"],
        how="left",
    )
    return SourceTruthReplayArtifacts(
        source_truth_replay_dataset=dataset_df,
        event_lineage=event_lineage_df,
        continuation_depth=continuation_depth_df,
        replay_fidelity=replay_fidelity_df,
        continuation_identity=continuation_identity_df,
        continuation_lineage=continuation_lineage_df,
        upstream_366=upstream,
    )


def write_source_truth_replay_dataset(
    artifacts: SourceTruthReplayArtifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.source_truth_replay_dataset.to_csv(out_dir / "task_367_source_truth_replay_dataset.csv", index=False)
    artifacts.event_lineage.to_csv(out_dir / "task_367_event_lineage.csv", index=False)
    artifacts.continuation_depth.to_csv(out_dir / "task_367_continuation_depth.csv", index=False)
    artifacts.replay_fidelity.to_csv(out_dir / "task_367_replay_fidelity.csv", index=False)
