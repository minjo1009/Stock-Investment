from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OUT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_task742_remote_artifact_availability_audit.csv")
RAW_BASE = "https://raw.githubusercontent.com/minjo1009/Stock-Investment/main"
REMOTE_ARTIFACTS = (
    (
        "task740_extracted_primitives.csv",
        "docs/reports/task_740_engineering_high_resolver_completion/task740_extracted_primitives.csv",
        "ea482665790794c9f311224e77d0218e7e307a7ae2e30494be05dc0fc7bb56ae",
    ),
    (
        "task740_resolver_outputs.csv",
        "docs/reports/task_740_engineering_high_resolver_completion/task740_resolver_outputs.csv",
        "2727631de5a1af0e20e197eca69a28041d68920a036f59bd5dfdb23f7c44cbb7",
    ),
    (
        "task741_economic_meaning_packets.csv",
        "docs/reports/task_741_economic_denominator_meaning_layer/task741_economic_meaning_packets.csv",
        "e1599c4a161a5bcec1f58fa8f41f2edbbb7419c8db70a5f106483d9e57a1c2cf",
    ),
    (
        "task742_pragmatic_economic_meaning_packets.csv",
        "docs/reports/task_742_pragmatic_economic_meaning_layer/task742_pragmatic_economic_meaning_packets.csv",
        "73a736a87213a0b88d314400b194dc374335876b0366a3949b026a19f701e389",
    ),
    (
        "task742_pragmatic_economic_meaning_packets.jsonl",
        "docs/reports/task_742_pragmatic_economic_meaning_layer/task742_pragmatic_economic_meaning_packets.jsonl",
        "d36d8de31cba452e80d5d915df3cc3f6627da66058e71a119ee5d16bb8a4ee39",
    ),
)


@dataclass(frozen=True)
class RemoteArtifactAvailabilityAuditRow:
    artifact_name: str
    remote_path: str
    manifest_sha256: str
    raw_url: str
    http_status: str
    downloadable_flag: int
    usable_for_task742_packet_bridge_flag: int
    blocker_reason: str


def main() -> None:
    rows = []
    for artifact_name, remote_path, sha256 in REMOTE_ARTIFACTS:
        raw_url = f"{RAW_BASE}/{remote_path}"
        status = _status(raw_url)
        downloadable = int(status == "200")
        rows.append(
            RemoteArtifactAvailabilityAuditRow(
                artifact_name=artifact_name,
                remote_path=remote_path,
                manifest_sha256=sha256,
                raw_url=raw_url,
                http_status=status,
                downloadable_flag=downloadable,
                usable_for_task742_packet_bridge_flag=downloadable,
                blocker_reason="available" if downloadable else "manifest_references_artifact_but_raw_url_not_downloadable",
            )
        )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT_PATH, [asdict(row) for row in rows])
    available = sum(row.downloadable_flag for row in rows)
    print(f"[L3_TASK742_REMOTE_ARTIFACT_AUDIT] artifacts={len(rows)} downloadable={available} out={OUT_PATH}")


def _status(url: str) -> str:
    request = Request(url, method="GET", headers={"User-Agent": "codex-l3-audit"})
    try:
        with urlopen(request, timeout=20) as response:
            return str(response.status)
    except HTTPError as exc:
        return str(exc.code)
    except URLError as exc:
        return f"URL_ERROR:{exc.reason}"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
