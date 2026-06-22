from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3301_3320_mobile_scanner_pixel_build"
REPORT_DIR = ROOT / "docs" / "reports" / "task_3301_3320_mobile_scanner_pixel_build"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"not a png: {path}")
    return struct.unpack(">II", header[16:24])


def main() -> None:
    required = [
        ROOT / "apps" / "trader-brain-web" / "src" / "components" / "MobileScannerApp.tsx",
        ROOT / "apps" / "trader-brain-web" / "src" / "app" / "page.tsx",
        ROOT / "apps" / "trader-brain-web" / "src" / "app" / "globals.css",
        ARTIFACT_DIR / "scan_impl_3053_427x922_dsf2.png",
        ARTIFACT_DIR / "scan_impl_3053_chart_card_crop.png",
        ARTIFACT_DIR / "scan_impl_3053_bottom_readability_crop.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_side_by_side.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_header_filters_theme.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_candidate_list.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_chart_card.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_bottom_nav.png",
        ARTIFACT_DIR / "scan_ref2_vs_impl_3053_visual_audit.csv",
        REPORT_DIR / "task_3301_3320_mobile_scanner_pixel_build.md",
        REPORT_DIR / "task_3320_decision.csv",
        REPORT_DIR / "artifact_manifest.csv",
        ROOT / "design-qa.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise AssertionError(f"missing required files: {missing}")

    impl_size = png_size(ARTIFACT_DIR / "scan_impl_3053_427x922_dsf2.png")
    if impl_size != (854, 1844):
        raise AssertionError(f"unexpected implementation screenshot size: {impl_size}")

    comparison_size = png_size(ARTIFACT_DIR / "scan_ref2_vs_impl_3053_side_by_side.png")
    if comparison_size != (1730, 1886):
        raise AssertionError(f"unexpected side-by-side size: {comparison_size}")

    component = (ROOT / "apps" / "trader-brain-web" / "src" / "components" / "MobileScannerApp.tsx").read_text(
        encoding="utf-8"
    )
    if "createChart" not in component or "Lightweight Charts" in component:
        raise AssertionError("scanner component must use lightweight chart runtime")
    if 'className="chart-readout"' not in component:
        raise AssertionError("chart metrics must render in the reserved readout bar")
    if "chart-tooltip" in component:
        raise AssertionError("chart metrics must not use plot-overlapping tooltip markup")
    styles = (ROOT / "apps" / "trader-brain-web" / "src" / "app" / "globals.css").read_text(encoding="utf-8")
    for token in ["--scan-readout-font", "--scan-micro-font", "--scan-compact-font", ".chart-readout"]:
        if token not in styles:
            raise AssertionError(f"missing scanner readability baseline token: {token}")
    forbidden = ["placeOrder", "sendOrder", "live order", "real capital"]
    found = [token for token in forbidden if token in component]
    if found:
        raise AssertionError(f"forbidden execution wording in read-only UI: {found}")

    report = (REPORT_DIR / "task_3301_3320_mobile_scanner_pixel_build.md").read_text(encoding="utf-8")
    if "Exact-match verdict: FAILED" not in report:
        raise AssertionError("report must explicitly mark exact-match status")

    print("Task3301-3320 mobile scanner pixel build validation passed")


if __name__ == "__main__":
    main()
