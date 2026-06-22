from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StandardReport:
    title: str
    decision_summary: list[str]
    quant_expert_report: list[str]
    decision_maker_report: list[str]
    artifact_manifest: pd.DataFrame

    def render(self) -> str:
        return "\n".join(
            [
                f"# {self.title}",
                "",
                "## Decision Summary",
                "",
                *self.decision_summary,
                "",
                "## Quant Expert Report",
                "",
                *self.quant_expert_report,
                "",
                "## No-Background Decision-Maker Report",
                "",
                *self.decision_maker_report,
                "",
                "## Artifact Manifest",
                "",
                _csv_block(self.artifact_manifest),
            ]
        )


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"
