# Design QA

- Source visual truth: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`
- Implementation screenshot: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_427x922_dsf2.png`
- Viewport: `427x922` CSS pixels
- Device scale factor: `2`
- Raw implementation size: `854x1844`
- Full-view comparison evidence: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_side_by_side.png`
- Focused region evidence:
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_chart_card_crop.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_bottom_readability_crop.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_header_filters_theme.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_candidate_list.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_chart_card.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_bottom_nav.png`
  - `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_visual_audit.csv`

## Findings

- [P2] Header/filter/theme surface is still brighter than the source, but no longer has the user-reported theme-label ellipsis defect.
  Location: `scan-top`, `scan-filters`, `theme-strip`.
  Evidence: reference mean RGB `14.74,16.28,19.05`; implementation `20.05,22.78,27.56`.
  Fix: reduce remaining chip/text foreground brightness and align source-device font rendering.

- [P2] Candidate rows remain optically heavier than the source, but scanner-header occlusion is fixed.
  Location: `.candidate-row`, `.candidate-symbol`, `.candidate-price`, `.candidate-reason`.
  Evidence: latest pass reduced most row/header text roles toward 70% of the prior pass; candidate-list mean RGB is now `19.01,21.77,26.58` vs reference `13.84,15.44,18.36`.
  Fix: move closer to source-device typography by either bundling a matching SF/Pretendard-like webfont or further lowering foreground contrast and badge stroke intensity.

- [P2] Chart card is much improved but not exact.
  Location: `MobileTradingChart`, `.chart-tooltip`, `.chart-controls`.
  Evidence: removed custom current-price label, moved the OHLC table below the plot into `.chart-readout`, removed old `.chart-tooltip` markup, removed default last-value labels, increased candles from 56 to 78, and reduced grid/volume opacity; chart mean RGB is now `21.57,26.31,31.65` vs reference `16.97,19.56,23.69`.
  Fix: align selected chart data shape and tooltip timing behavior more closely with the reference.

- [P2] Bottom status/event/nav typography is now reduced, but source-device optical match is still not exact.
  Location: `.mini-status-row`, `.event-strip`, `.scan-bottom-nav`.
  Evidence: lower crop `scan_impl_3052_bottom_readability_crop.png` shows the previously missed rows now use reduced text, badges, and icon sizes. Bottom mean RGB is `23.48,27.51,32.53` vs reference `21.89,25.44,30.51`.
  Fix: align the iOS source font/icon system before widening to Home.

## Patches Made Since Previous QA

- Reordered font stack to prioritize installed `Noto Sans KR`.
- Reduced header/filter/theme typography weights.
- Reduced candidate-row role fonts, weights, badge sizes, freshness, and reason copy density.
- Disabled Lightweight Charts default last-value labels and price-line labels.
- Increased chart candle density from 56 to 78 bars.
- Reduced chart grid and volume opacity.
- Reduced bottom-nav icon size.
- Reduced major text roles again toward 70% of the previous pass.
- Fixed theme-strip layout so labels no longer collapse into ellipses.
- Fixed scanner-header and candidate-row grid separation so labels are not hidden.
- Hid the custom chart current-price label and reduced tooltip/table collision.
- Moved the chart OHLC table out of the candle plot into a reserved lower readout bar.
- Reduced the previously missed bottom status/event/nav typography, badges, and icons.
- Promoted the accepted sizes into shared CSS tokens: `--scan-readout-font`, `--scan-micro-font`, `--scan-mini-font`, `--scan-compact-font`, and `--scan-status-value-font`.
- Renamed plot-overlap-prone `.chart-tooltip` to `.chart-readout`.
- Added focused visual audit crop generator and section RGB CSV.

## Result

Final result: blocked for pixel-exact match; pass for the latest user-reported P1 readability defects.

The implementation is materially closer to Reference 2 than the previous dashboard and previous 3044/3045/3049/3050/3052 passes, but it is not a pixel-exact match. Remaining blockers are section brightness, exact source-device typography, and chart optical density.
