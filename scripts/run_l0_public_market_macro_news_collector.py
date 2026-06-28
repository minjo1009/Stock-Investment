from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.source_acquisition.public_market_macro_news_collector import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
