from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/reports/task_3211_3230_mobile_reference_deep_dive/task_3211_3230_mobile_reference_deep_dive.md"
DECISION = ROOT / "docs/reports/task_3211_3230_mobile_reference_deep_dive/task_3230_decision.csv"
MANIFEST = ROOT / "data/artifacts/task_3211_3230_mobile_reference_deep_dive/artifact_manifest.csv"
REGISTRY = ROOT / "tasks/task_registry.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    for path in [REPORT, DECISION, MANIFEST, REGISTRY]:
        require(path.exists(), f"missing required file: {path}")
        require(path.stat().st_size > 0, f"empty required file: {path}")

    report = REPORT.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    for section in [
        "## Decision Summary",
        "## Quant Expert Report",
        "## No-Background Decision-Maker Report",
        "## Artifact Manifest",
    ]:
        require(section in report, f"missing report section: {section}")

    for phrase in [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "TradingView-style Scanner/Chart 70%",
        "CockpitReadModelV2",
        "No inferred lifecycle matching was used.",
        "No unavailable raw source was approximated.",
    ]:
        require(phrase in report, f"missing report phrase: {phrase}")

    for phrase in [
        "Task3230",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
    ]:
        require(phrase in decision, f"missing decision phrase: {phrase}")

    for phrase in [
        "Task3230",
        "Mobile Reference Deep Dive",
        "Diagnostic Only",
        "NOT_ACCEPTED",
        "mobile-reference-deep-dive-no-trading-logic-change",
    ]:
        require(phrase in registry, f"missing registry phrase: {phrase}")

    for path_fragment in [
        "task_3211_3230_mobile_reference_deep_dive.md",
        "task_3230_decision.csv",
        "artifact_manifest.csv",
        "trader_brain_3211_3230_mobile_reference_deep_dive_validate.py",
    ]:
        require(path_fragment in manifest, f"missing manifest artifact: {path_fragment}")

    print("Task3211-3230 mobile reference deep dive validation passed.")


if __name__ == "__main__":
    main()
