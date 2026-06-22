from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parents[1]
REF = Path("C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png")
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3301_3320_mobile_scanner_pixel_build"
IMPL = ARTIFACT_DIR / "scan_impl_3053_427x922_dsf2.png"

SECTIONS = [
    ("header_filters_theme", (0, 0, 853, 320)),
    ("candidate_list", (0, 319, 853, 790)),
    ("chart_card", (0, 829, 853, 1532)),
    ("bottom_nav", (0, 1697, 853, 1844)),
]


def mean_rgb(image: Image.Image) -> str:
    stat = ImageStat.Stat(image.convert("RGB"))
    values = [round(v, 2) for v in stat.mean]
    return f"{values[0]},{values[1]},{values[2]}"


def font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", 18)
    except OSError:
        return ImageFont.load_default()


def side_by_side(ref: Image.Image, impl: Image.Image, out: Path, title: str) -> None:
    width = ref.width
    height = max(ref.height, impl.height)
    gap = 24
    label_h = 42
    canvas = Image.new("RGB", (width * 2 + gap, height + label_h), (8, 10, 12))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 8), f"REFERENCE {title}", fill=(255, 255, 255), font=font())
    draw.text((width + gap + 12, 8), f"IMPLEMENTATION {title}", fill=(255, 255, 255), font=font())
    canvas.paste(ref, (0, label_h))
    canvas.paste(impl, (width + gap, label_h))
    canvas.save(out)


def main() -> None:
    if not REF.exists():
        raise AssertionError(f"missing reference image: {REF}")
    if not IMPL.exists():
        raise AssertionError(f"missing implementation screenshot: {IMPL}")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    ref = Image.open(REF).convert("RGB")
    impl_full = Image.open(IMPL).convert("RGB")
    impl = impl_full.crop((0, 0, 853, 1844))

    side_by_side(ref, impl, ARTIFACT_DIR / "scan_ref2_vs_impl_3053_side_by_side.png", "#2 FULL")

    rows = []
    for name, box in SECTIONS:
        ref_crop = ref.crop(box)
        impl_crop = impl.crop(box)
        out = ARTIFACT_DIR / f"scan_ref2_vs_impl_3053_{name}.png"
        side_by_side(ref_crop, impl_crop, out, name)
        rows.append(
            {
                "section": name,
                "box_raw": ",".join(str(v) for v in box),
                "ref_mean_rgb": mean_rgb(ref_crop),
                "impl_mean_rgb": mean_rgb(impl_crop),
                "comparison": str(out.relative_to(ROOT)),
            }
        )

    with (ARTIFACT_DIR / "scan_ref2_vs_impl_3053_visual_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "box_raw", "ref_mean_rgb", "impl_mean_rgb", "comparison"])
        writer.writeheader()
        writer.writerows(rows)

    print("mobile scanner visual audit artifacts written")


if __name__ == "__main__":
    main()
