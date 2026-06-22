# Task3301-3320 Mobile Scanner Pixel Build

## Decision Summary

- Verdict: Reference 2 Scanner has been rebuilt and deeply refined as a mobile-first Next.js screen. The approved lower typography and chart readout baselines are now encoded in the app, but pixel-exact match is not achieved yet.
- Exact-match verdict: FAILED.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: `apps/trader-brain-web` now renders a dedicated `MobileScannerApp` at the root route, using compact scanner rows, theme strip, selected chart card, status cards, event strip, bottom tabs, and TradingView Lightweight Charts. Latest loop promoted the approved baseline into app code: chart metrics render through `.chart-readout` instead of plot-overlapping tooltip markup, and lower status/event/nav typography uses shared compact CSS tokens.
- What did not change: no replay, selector, sizing, source acquisition, paper order, live order, deployment readiness, or real-capital status changed.
- Next action: keep the next loop Scanner-only and resolve the remaining visual-system gaps before expanding to Reference 3 Home or Reference 1 Analysis/Risk.

## Quant Expert Report

### Visual QA

- Reference image: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`.
- Implementation capture: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_427x922_dsf2.png`.
- Capture viewport: `427x922` CSS pixels.
- Device scale factor: `2`.
- Implementation raw capture size: `854x1844`.
- Reference comparison crop: `853x1844`.
- Side-by-side artifact: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_side_by_side.png`.
- Focused chart-card crop: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_chart_card_crop.png`.
- Focused bottom readability crop: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_impl_3053_bottom_readability_crop.png`.
- Focused header/filter/theme artifact: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_header_filters_theme.png`.
- Focused candidate-list artifact: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_candidate_list.png`.
- Focused chart-card artifact: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_chart_card.png`.
- Focused bottom-nav artifact: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_bottom_nav.png`.
- Section visual audit CSV: `data/artifacts/task_3301_3320_mobile_scanner_pixel_build/scan_ref2_vs_impl_3053_visual_audit.csv`.

### Remaining Exact-Match Gaps

1. Header/filter/theme remains brighter than Reference 2, but improved: mean RGB `20.05,22.78,27.56` vs reference `14.74,16.28,19.05`.
2. Candidate-list density is much closer after the 70%-scale typography pass; remaining mean RGB is `19.01,21.77,26.58` vs reference `13.84,15.44,18.36`.
3. Theme strip no longer clips core labels with ellipses in the latest capture; the strip now uses fixed icon/text/spark slots.
4. Scanner header labels are no longer hidden behind the first row; the header and candidate rows now use separate fixed grids.
5. Chart-card overdraw was reduced by hiding the custom current-price label, moving the OHLC table into `.chart-readout` below the plot, disabling default last-value labels, increasing candle density from 56 to 78 bars, and lowering grid/volume opacity. Remaining mean RGB is `21.57,26.31,31.65` vs reference `16.97,19.56,23.69`.
6. Bottom status/event/nav typography now uses the same reduction rule as the main surface; bottom mean RGB improved to `23.48,27.51,32.53` vs reference `21.89,25.44,30.51`.
7. Layout slots now broadly match the Reference 2 section map, but exact optical fidelity still fails because the rendered Windows/Chrome Korean font, icon set, and chart renderer differ from the iOS-style source.

### Validation

- `cd apps/trader-brain-web; npm run build`
- `cd apps/trader-brain-web; npx tsc --noEmit`
- `python scripts/trader_brain_3301_3320_mobile_scanner_pixel_build_validate.py`
- `python scripts/task_registry_validate.py`

## No-Background Decision-Maker Report

The old desktop-like cockpit was replaced with a true mobile Scanner surface. The screen now follows the Reference 2 map: dark header, compact filters, sector strip, six ticker rows, selected chart, summary cards, event strip, and bottom tabs.

The latest pass promoted the accepted fixes into app-level baselines: lower status/event/nav typography uses shared compact tokens, and the chart OHLC table is semantically a lower readout instead of an overlay tooltip. It is still not exact-match enough to proceed to Home and Analysis/Risk without another Scanner-only QA decision.

## Artifact Manifest

See `docs/reports/task_3301_3320_mobile_scanner_pixel_build/artifact_manifest.csv`.
