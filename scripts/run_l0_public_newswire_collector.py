from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.public_newswire_collector import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
