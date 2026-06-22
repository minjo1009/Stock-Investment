from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.artifact_migrate_safe import migrate
from scripts.artifact_migration_plan import build_plan


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ArtifactMigrationTest(unittest.TestCase):
    def test_plan_skips_referenced_large_artifacts_and_moves_unreferenced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_dir = root / "docs" / "reports" / "task_old"
            task_dir.mkdir(parents=True)
            (task_dir / "unreferenced.csv").write_text("x\n1\n", encoding="utf-8")
            (task_dir / "referenced.csv").write_text("x\n2\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "consumer.py").write_text(
                "PATH = 'docs/reports/task_old/referenced.csv'\n",
                encoding="utf-8",
            )
            _write_csv(
                task_dir / "artifact_manifest.csv",
                [
                    {"relative_path": "unreferenced.csv", "artifact_class": "large_panel", "size_bytes": 12, "sha256": "a"},
                    {"relative_path": "referenced.csv", "artifact_class": "large_panel", "size_bytes": 12, "sha256": "b"},
                    {"relative_path": "report.md", "artifact_class": "report", "size_bytes": 1, "sha256": "c"},
                ],
                ["relative_path", "artifact_class", "size_bytes", "sha256"],
            )
            _write_csv(
                root / "tasks" / "archive_candidate_registry.csv",
                [
                    {
                        "report_dir": "task_old",
                        "archive_state": "archive_candidate",
                        "recommended_action": "manifest_then_move_large_panels_to_data_artifacts",
                        "file_count": 3,
                        "size_bytes": 25,
                        "manifest_path": "docs/reports/task_old/artifact_manifest.csv",
                    }
                ],
                ["report_dir", "archive_state", "recommended_action", "file_count", "size_bytes", "manifest_path"],
            )

            rows = build_plan(root)
            actions = {row["relative_path"]: row["migration_action"] for row in rows}
            self.assertEqual(actions["unreferenced.csv"], "move_to_data_artifacts")
            self.assertEqual(actions["referenced.csv"], "skip_referenced")
            self.assertEqual(actions["report.md"], "keep_small_or_report_artifact")

            migrate(root)
            result = {row["relative_path"]: row["migration_status"] for row in _read_csv(root / "docs" / "artifact_migration_result.csv")}
            self.assertEqual(result["unreferenced.csv"], "moved")
            self.assertTrue((root / "data" / "artifacts" / "task_old" / "unreferenced.csv").exists())
            self.assertFalse((task_dir / "unreferenced.csv").exists())
            self.assertTrue((task_dir / "unreferenced.csv.migrated.txt").exists())
            self.assertTrue((task_dir / "referenced.csv").exists())


if __name__ == "__main__":
    unittest.main()
