from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class ExperimentMetrics:
    pf: float
    net_pnl: float
    mdd: float
    sharpe: float


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    strategy: str
    execution_policy: str
    risk_policy: str
    fee: float
    slippage: float
    universe: str
    dataset_version: str
    metrics: ExperimentMetrics
    decision: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = asdict(self.metrics)
        return payload


def save_records(path: str | Path, records: list[ExperimentRecord]) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record.to_dict() for record in records]
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return out_path
