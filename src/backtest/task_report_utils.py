from __future__ import annotations

from pathlib import Path

import pandas as pd


def yes_no(value: object) -> str:
    return "YES" if bool(value) else "NO"


def write_standard_report(
    path: Path,
    *,
    title: str,
    decision_summary: list[str],
    quant_expert_lines: list[str],
    decision_maker_lines: list[str],
    artifact_manifest_note: str = "See `artifact_manifest.csv`.",
) -> None:
    sections = [
        f"# {title}",
        "",
        "## Decision Summary",
        "",
        *[f"- {line}" for line in decision_summary],
        "",
        "## Quant Expert Report",
        "",
        *quant_expert_lines,
        "",
        "## No-Background Decision-Maker Report",
        "",
        *decision_maker_lines,
        "",
        "## Artifact Manifest",
        "",
        artifact_manifest_note,
        "",
    ]
    path.write_text("\n".join(sections), encoding="utf-8")


def first_record(frame: pd.DataFrame) -> dict[str, object]:
    return frame.iloc[0].to_dict() if not frame.empty else {}
