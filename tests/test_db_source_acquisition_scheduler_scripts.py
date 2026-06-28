from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.validate_news_ops_scope_a_b import validate as validate_news_ops
from tools.db.apply_management_schema import apply_management_schema
from tools.db.source_acquisition.scheduler_override import load_effective_scheduler_config


class DbSourceAcquisitionSchedulerScriptsTest(unittest.TestCase):
    def test_news_ops_validator_modes_pass(self) -> None:
        self.assertEqual(validate_news_ops("conservative"), [])
        self.assertEqual(validate_news_ops("news_enabled_diagnostic"), [])

    def test_management_schema_reconciles_operator_override_without_permission_opening(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "scheduler.db"
            apply_management_schema(
                db_path=db_path,
                override_path=Path("configs/local_templates/db_source_acquisition_scheduler.override.example.json"),
            )
            conn = sqlite3.connect(db_path)
            try:
                row = conn.execute(
                    """
                    select enabled, allow_network, diagnostic_only, execution_permitted,
                           broker_mutation_permitted, paper_promotion_permitted, real_capital_permitted
                    from source_scheduler_registry
                    where job_name='official_news_sources_15m'
                    """
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(row, (1, 1, 1, 0, 0, 0, 0))

    def test_effective_config_audit_preserves_closed_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.json"
            load_effective_scheduler_config(audit_path=audit_path)
            text = audit_path.read_text(encoding="utf-8")
            self.assertIn('"permissions_closed": true', text)
            self.assertIn('"status_preserved": true', text)


if __name__ == "__main__":
    unittest.main()
