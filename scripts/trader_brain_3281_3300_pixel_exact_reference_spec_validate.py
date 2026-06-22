from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/reports/task_3281_3300_pixel_exact_reference_spec/task_3281_3300_pixel_exact_reference_spec.md"
DECISION = ROOT / "docs/reports/task_3281_3300_pixel_exact_reference_spec/task_3300_decision.csv"
MANIFEST = ROOT / "data/artifacts/task_3281_3300_pixel_exact_reference_spec/artifact_manifest.csv"
REGISTRY = ROOT / "tasks/task_registry.csv"
OVERLAYS = [
    ROOT / "data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref1_analysis_section_overlay.png",
    ROOT / "data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref2_scanner_section_overlay.png",
    ROOT / "data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref3_home_section_overlay.png",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    for path in [REPORT, DECISION, MANIFEST, REGISTRY, *OVERLAYS]:
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
        "853x1844",
        "426.5x922",
        "deviceScaleFactor=2",
        "Reference 2 Scanner Layout Contract",
        "scan.bg",
        "Reference 3 Home Layout Contract",
        "Reference 1 Analysis/Risk Layout Contract",
        "No desktop table.",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
    ]:
        require(phrase in report, f"missing report phrase: {phrase}")

    for phrase in ["Task3300", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        require(phrase in decision, f"missing decision phrase: {phrase}")

    for phrase in [
        "Task3300",
        "Pixel Exact Reference Spec",
        "Diagnostic Only",
        "NOT_ACCEPTED",
        "pixel-exact-reference-spec-no-trading-logic-change",
    ]:
        require(phrase in registry, f"missing registry phrase: {phrase}")

    for path_fragment in [
        "ref1_analysis_section_overlay.png",
        "ref2_scanner_section_overlay.png",
        "ref3_home_section_overlay.png",
        "task_3281_3300_pixel_exact_reference_spec.md",
    ]:
        require(path_fragment in manifest, f"missing manifest artifact: {path_fragment}")

    print("Task3281-3300 pixel-exact reference spec validation passed.")


if __name__ == "__main__":
    main()

