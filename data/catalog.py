from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class DatasetCatalog:
    dataset_id: str
    source: str
    data_dir: str
    symbols: list[str]
    start_date: str
    end_date: str
    row_count: int
    generated_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def save_catalog(path: str | Path, catalog: DatasetCatalog) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(catalog.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
    return out_path
