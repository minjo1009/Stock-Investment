from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


REGISTRY_COLUMNS = [
    "task_id",
    "task_name",
    "owner_team",
    "review_status",
    "lifecycle_status",
    "strategy_acceptance",
    "data_readiness",
    "upstream_task",
    "report_path",
    "decision_path",
    "artifact_dir",
    "validation_command",
    "summary",
]


@dataclass(frozen=True)
class CatalogPaths:
    task_registry: Path = Path("tasks/task_registry.csv")
    reports_root: Path = Path("docs/reports")


def load_task_registry(path: Path = CatalogPaths().task_registry) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    rows: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip():
            continue
        parts = raw.split(",", len(REGISTRY_COLUMNS) - 1)
        if len(parts) < len(REGISTRY_COLUMNS):
            parts += [""] * (len(REGISTRY_COLUMNS) - len(parts))
        rows.append(parts[: len(REGISTRY_COLUMNS)])
    frame = pd.DataFrame(rows, columns=REGISTRY_COLUMNS)
    frame = frame[frame["task_id"].astype(str).str.startswith("Task")].copy()
    return frame.reset_index(drop=True)


def build_research_task_catalog(paths: CatalogPaths = CatalogPaths()) -> pd.DataFrame:
    registry = load_task_registry(paths.task_registry)
    rows: list[dict[str, object]] = []
    for row in registry.to_dict(orient="records"):
        report_path = Path(str(row.get("report_path", "")))
        decision_path = Path(str(row.get("decision_path", "")))
        artifact_dir = Path(str(row.get("artifact_dir", "")))
        manifest_path = artifact_dir / "artifact_manifest.csv"
        decision = _read_decision(decision_path)
        rows.append(
            {
                **row,
                "report_exists_flag": int(report_path.exists()),
                "decision_exists_flag": int(decision_path.exists()),
                "artifact_manifest_exists_flag": int(manifest_path.exists()),
                "decision_badge": _decision_badge(decision, row),
                "deployment_ready_flag": int(float(decision.get("deployment_ready_flag", 0) or 0)) if decision else 0,
                "key_metric_count": _first_present(decision, ["shadow_assignment_count", "selected_count", "lifecycle_count", "walk_forward_total_count"]),
                "key_metric_avg_net": _first_present(decision, ["selected_avg_net_pct", "walk_forward_avg_net_pct", "selected_entry_reduce_rate"]),
                "blocker_hint": _blocker_hint(decision, row),
            }
        )
    return pd.DataFrame(rows)


def load_artifact_manifest(artifact_dir: str | Path) -> pd.DataFrame:
    path = Path(artifact_dir) / "artifact_manifest.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _read_decision(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        frame = pd.read_csv(path)
    except Exception:
        return {}
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _decision_badge(decision: dict[str, object], row: dict[str, object]) -> str:
    for key in ["strategy_acceptance_status", "promotion_decision", "promotion_decision_v2", "edge_status"]:
        value = decision.get(key)
        if pd.notna(value) if value is not None else False:
            return str(value)
    return str(row.get("strategy_acceptance", "UNKNOWN"))


def _first_present(decision: dict[str, object], keys: list[str]) -> object:
    for key in keys:
        value = decision.get(key)
        if value is not None and pd.notna(value):
            return value
    return pd.NA


def _blocker_hint(decision: dict[str, object], row: dict[str, object]) -> str:
    readiness = str(row.get("data_readiness", ""))
    if "blocked" in readiness:
        return "data_blocked"
    if int(float(decision.get("deployment_ready_flag", 0) or 0)) == 0:
        return "not_deployment_ready"
    return "none"
