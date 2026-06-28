from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.validate_l0_microstructure_collection_readiness import validate as validate_microstructure
from scripts.validate_l0_news_enablement_readiness import validate as validate_news
from scripts.validate_news_ops_scope_a_b import validate as validate_news_ops
from tools.db.source_acquisition.scheduler_override import DEFAULT_AUDIT_PATH, load_effective_scheduler_config


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_news(root))
    errors.extend(validate_microstructure(root))
    errors.extend(validate_news_ops("conservative"))
    errors.extend(validate_news_ops("news_enabled_diagnostic"))
    load_effective_scheduler_config(audit_path=root / DEFAULT_AUDIT_PATH)
    audit_path = root / DEFAULT_AUDIT_PATH
    if not audit_path.exists():
        errors.append("effective scheduler config audit was not written")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_SOURCE_ACQUISITION_HARDENING_ERROR] {error}")
        return 1
    print("[L0_SOURCE_ACQUISITION_HARDENING_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
