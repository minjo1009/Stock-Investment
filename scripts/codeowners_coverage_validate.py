from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_PATTERNS = [
    "/src/data/",
    "/src/backtest/core/",
    "/src/backtest/engines/",
    "/src/backtest/reports/",
    "/src/execution/",
    "/src/risk/",
    "/docs/reports/",
    "/tasks/",
    "/scripts/",
]


def validate(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing CODEOWNERS: {path}"]
    text = path.read_text(encoding="utf-8")
    errors = [pattern for pattern in REQUIRED_PATTERNS if pattern not in text]
    return [f"missing CODEOWNERS pattern: {pattern}" for pattern in errors]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codeowners", type=Path, default=Path(".github/CODEOWNERS"))
    args = parser.parse_args()
    errors = validate(args.codeowners)
    if errors:
        for error in errors:
            print(f"[CODEOWNERS_ERROR] {error}")
        sys.exit(1)
    print(f"[CODEOWNERS_OK] {args.codeowners}")


if __name__ == "__main__":
    main()
