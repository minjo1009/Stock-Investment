from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_APP_MARKERS = [
    "_render_selected_task_provenance",
    "_render_investor_performance_dashboard",
    "_render_portfolio_source_warning",
    "NOT_TASK_ARTIFACT",
    "Source Files / Version Hashes",
    "Performance source task/artifact",
    "두 기준을 혼동하지 마십시오",
]


REQUIRED_CONTRACT_MARKERS = [
    "Legacy portfolio source",
    "Research task artifact",
    "Paper/shadow capture",
    "React Trader Terminal",
    "Required UI Provenance",
    "Update Discipline",
    "Prohibited",
]


REQUIRED_TRADER_TERMINAL_FILES = [
    Path("scripts/build_trader_terminal_catalog.py"),
    Path("frontend/trader-terminal/package.json"),
    Path("frontend/trader-terminal/src/App.jsx"),
    Path("frontend/trader-terminal/public/catalog/trader_terminal_catalog.json"),
]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    app_path = root / "src" / "ui" / "app.py"
    contract_path = root / "docs" / "frontend_data_contract.md"

    if not app_path.exists():
        return [f"missing UI app: {app_path}"]
    if not contract_path.exists():
        errors.append(f"missing frontend data contract: {contract_path}")
        contract_text = ""
    else:
        contract_text = contract_path.read_text(encoding="utf-8")

    app_text = app_path.read_text(encoding="utf-8")
    for marker in REQUIRED_APP_MARKERS:
        if marker not in app_text:
            errors.append(f"missing frontend provenance marker in app.py: {marker}")
    for marker in REQUIRED_CONTRACT_MARKERS:
        if marker not in contract_text:
            errors.append(f"missing frontend contract marker: {marker}")
    for path in REQUIRED_TRADER_TERMINAL_FILES:
        if not (root / path).exists():
            errors.append(f"missing trader terminal file: {path}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"[FRONTEND_CONTINUITY_ERROR] {error}")
        sys.exit(1)
    print("[FRONTEND_CONTINUITY_OK]")


if __name__ == "__main__":
    main()
