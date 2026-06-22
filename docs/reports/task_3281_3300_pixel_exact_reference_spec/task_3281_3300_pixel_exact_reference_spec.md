# Task3281-3300 Pixel-Exact Reference Spec

## Decision Summary

- Verdict: the next UI implementation must target the supplied images as pixel references, not broad inspiration. The canonical target canvas is `853x1844` raw pixels, equivalent to about `426.5x922` CSS pixels at `deviceScaleFactor=2`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 3 reference images measured, 3 annotated overlay images produced, raw-to-CSS scale fixed at `0.5`, Reference 2 Scanner remains the primary target.
- What changed: no app code, replay, selector, paper order, live order, source acquisition, deployment readiness, or real-capital status changed. This is a pixel-level UI spec for the next implementation.
- Next action: implement the Scanner screen first using this spec, capture at `426.5x922` CSS with `deviceScaleFactor=2`, and compare against Reference 2 side by side.

## Quant Expert Report

### Data Source And Source Readiness

- Reference 1 Analysis image: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-ff378cc6-9b75-4070-9acd-a9b5ed0c73bd.png`
- Reference 2 Scanner image: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`
- Reference 3 Home image: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7861d17d-2f17-4482-93fd-00f81457e599.png`
- All three images are `853x1844` raw pixels.
- Required QA viewport: `426.5x922` CSS pixels with `deviceScaleFactor=2`, or `427x922` CSS if the renderer requires integer viewport width.
- Raw-to-CSS conversion: `css_px = raw_px / 2`.

### Pixel Scale Rule

Previous UI specs that mixed raw pixels and CSS pixels are superseded for layout measurement. Use this rule:

```text
reference raw image: 853 x 1844
target CSS viewport: 426.5 x 922
device scale factor: 2
raw section height 68px = CSS section height 34px
raw margin 22px = CSS margin 11px
raw card radius 18px = CSS radius 9px
```

This matters most for Reference 2. Its scanner rows are about `68-69` raw px, which means about `34-34.5` CSS px. The screen feels dense because it is genuinely dense.

### Reference 2 Scanner Layout Contract

Reference 2 is the primary target.

| Section | Raw Box `(x,y,w,h)` | CSS Box `(x,y,w,h)` | Implementation Notes |
|---|---:|---:|---|
| Screen | `0,0,853,1844` | `0,0,426.5,922` | Fixed mobile shell, no desktop max-width hero. |
| iOS status + title controls | `0,0,853,132` | `0,0,426.5,66` | Status row, title `?ㅼ틪`, mode pill, star button, update time, green dot, menu badge. |
| Filter chips | `16,143,761,45` | `8,71.5,380.5,22.5` | Horizontal chip row, 6-7 compact chips, selected chip red. |
| Theme strip | `16,207,821,89` | `8,103.5,410.5,44.5` | Four sector cells with icon, label, count, change, tiny sparkline. |
| Scanner header | `10,319,832,37` | `5,159.5,416,18.5` | Column labels, small text, no table chrome. |
| Candidate rows | `10,358,832,412` | `5,179,416,206` | 6 dense rows, about `34.3` CSS px each. |
| Scanner footer | `10,770,832,42` | `5,385,416,21` | Data key, count, sort, filter icon. |
| Selected chart card | `6,829,841,703` | `3,414.5,420.5,351.5` | Main chart module starts inside first long viewport, not after large KPI cards. |
| Status cards | `13,1548,826,80` | `6.5,774,413,40` | Five compact summary tiles. |
| Event/data strip | `10,1650,833,43` | `5,825,416.5,21.5` | Event overlays and data health row. |
| Bottom tabs | `0,1697,853,147` | `0,848.5,426.5,73.5` | Five tabs with large icons, active blue. |

### Reference 2 Color Tokens

Measured average samples:

| Token | Hex | Usage |
|---|---:|---|
| `scan.bg` | `#090a0c` | Root app background. |
| `scan.panel` | `#11161d` | Main panels and chart card. |
| `scan.filter` | `#1b1f24` | Filter chip fill. |
| `scan.row.selected` | `#151b29` | Selected ticker row fill. |
| `scan.blue.border` | `#142d5a` | Selected row/chart border base. |
| `scan.nav` | `#12161b` | Bottom nav surface. |
| `scan.text.primary` | `#f4f7fb` | Major labels and prices. |
| `scan.text.secondary` | `#a3abb8` | Header labels and metadata. |
| `scan.text.muted` | `#6f7885` | Source keys, low-emphasis labels. |
| `scan.blue` | `#2f8cff` | Active tab, active controls, chart interaction. |
| `scan.green` | `#22c96b` | Positive price/action/freshness. |
| `scan.red` | `#ff4d5a` | Risk, negative price action, danger status. |
| `scan.amber` | `#f0b84a` | Watch/medium-risk/rank. |

### Reference 2 Typography Contract

Use this font stack first:

```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "SF Pro Display",
  "SF Pro Text",
  "Apple SD Gothic Neo",
  "Pretendard",
  "Inter",
  "Noto Sans KR",
  sans-serif;
```

Approximate CSS type scale:

| Role | CSS Size | Weight | Line Height | Notes |
|---|---:|---:|---:|---|
| iOS status | `14px` | `700` | `18px` | Only if simulating phone status bar. |
| Screen title | `28px` | `800` | `34px` | `?ㅼ틪`; do not use 40px hero text. |
| Mode pill | `16px` | `700` | `22px` | Icon + text + chevron. |
| Filter chip | `14px` | `600` | `20px` | 22.5 CSS px tall. |
| Theme label | `15px` | `700` | `18px` | Two-line sector cell. |
| Theme count | `13px` | `600` | `16px` | Count below label. |
| Scanner header | `12px` | `600` | `18px` | Column labels. |
| Row ticker | `20px` | `800` | `20px` | Very tight. |
| Row company | `12px` | `500` | `14px` | One-line truncated. |
| Row price | `17px` | `500` | `20px` | Numeric. |
| Row change | `16px` | `700` | `20px` | Green/red. |
| Row reason | `13px` | `500` | `16px` | Two Korean lines max. |
| Chart symbol | `24px` | `800` | `28px` | In selected card. |
| Chart price | `32px` | `800` | `36px` | Large but not hero-scale. |
| Bottom tab label | `12px` | `600` | `14px` | Active blue. |

### Reference 2 Component Rules

1. Root shell:
   - Width: `426.5px`.
   - Min-height: `922px`.
   - Background: `scan.bg`.
   - Content x-padding: `5-8px` in dense Scanner.
   - Bottom nav fixed or visually fixed at `y=848.5 CSS`.

2. Header:
   - No marketing copy.
   - No product subtitle.
   - No implementation stack text.
   - Top region total height: `66px`.
   - Title left x: about `16px CSS`.
   - Update/status group right aligned.

3. Filter chips:
   - Height: `22-23px CSS`.
   - Border radius: `6px CSS`.
   - Gap: `6px CSS`.
   - Selected risk chip: red border and red text.
   - Dropdown chips include chevron.

4. Theme strip:
   - Outer radius: `5-6px CSS`.
   - Height: `44.5px CSS`.
   - Four equal cells.
   - Each cell contains icon, label/count, change, sparkline.
   - Vertical separators at 25%, 50%, 75%.

5. Candidate row:
   - Height: `34-35px CSS`.
   - Selected row border: `1px CSS` blue.
   - Selected row fill: `#151b29`.
   - Row uses a dense grid, not table element layout.
   - Required cells: star, ticker/company, sparkline, price/value, change, RelVol, rank badge, freshness dot/time, reason, chevron.
   - Sparkline size target: `45x16 CSS`.
   - Rank badge: `14-16px CSS` square/rounded, one digit.

6. Chart card:
   - Outer x: `3px CSS`, y starts around `414.5px CSS`.
   - Width: `420.5px CSS`.
   - Height through chart status: about `351.5px CSS`.
   - Border: `1px CSS` blue-slate.
   - Radius: `7px CSS`.
   - Header and chart controls must be inside the card, not separate cards.
   - Toggle controls must be functional visually: 1D/5D/1M/All, VWAP, volume, marker, settings, expand.
   - Chart needs candles, VWAP line, volume bars, entry/block markers, crosshair tooltip, right price labels, bottom time labels, mini range scrubber.

7. Bottom tabs:
   - Height: `73.5px CSS`.
   - Five equal columns.
   - Active tab: blue icon and label.
   - Icons should use a real icon library, not text symbols.

### Reference 3 Home Layout Contract

Reference 3 is the 20% support target. It must influence only the Home tab.

| Section | Raw Box `(x,y,w,h)` | CSS Box `(x,y,w,h)` | Implementation Notes |
|---|---:|---:|---|
| Title/generated time | `0,36,853,96` | `0,18,426.5,48` | Large `??, subtitle, generated time + refresh. |
| Account card | `22,136,809,374` | `11,68,404.5,187` | Main account summary + 7D chart. |
| Market status card | `22,534,809,257` | `11,267,404.5,128.5` | Six small metric chips + green summary row. |
| Candidate list card | `22,814,809,406` | `11,407,404.5,203` | Three symbol rows, status stripe, logo/avatar, status chip, reason. |
| Quick actions | `23,1244,808,114` | `11.5,622,404,57` | Three equal action cards. |
| Data status card | `22,1378,809,202` | `11,689,404.5,101` | Five compact health tiles. |
| Safety strip | `23,1598,808,97` | `11.5,799,404,48.5` | Three safety/status columns. |
| Bottom tabs | `0,1697,853,147` | `0,848.5,426.5,73.5` | Same global nav. |

Reference 3 colors:

| Token | Hex | Usage |
|---|---:|---|
| `home.bg` | `#fafafb` | Root background. |
| `home.card` | `#f5f6f7` | Large cards. |
| `home.border` | `#e6e9ee` | Card border. |
| `home.text.primary` | `#111827` | Headline values. |
| `home.text.secondary` | `#667085` | Labels. |
| `home.blue` | `#2563eb` | Active nav and line chart. |
| `home.green.soft` | `#ddeee4` | Positive chip background. |
| `home.red.soft` | `#fae6e8` | Risk chip background. |

Home typography:

- Title `??: `32px`, weight `800`, line-height `38px`.
- Subtitle: `15px`, weight `500`, muted.
- Account value: `42px`, weight `500-600`, numeric tracking normal.
- Card title: `22px`, weight `750`.
- Candidate ticker: `19px`, weight `700`.
- Candidate secondary: `14px`, weight `500`.

### Reference 1 Analysis/Risk Layout Contract

Reference 1 is the 10% analysis/risk target. It must influence Analysis and Risk tabs, not the Scanner first screen.

| Section | Raw Box `(x,y,w,h)` | CSS Box `(x,y,w,h)` | Implementation Notes |
|---|---:|---:|---|
| Header/status | `0,0,853,160` | `0,0,426.5,80` | Dark navy header with status chips and data-source row. |
| Decision summary | `21,162,811,198` | `10.5,81,405.5,99` | Three status columns: ?좎?/愿李?李⑤떒. |
| Market regime | `21,373,811,212` | `10.5,186.5,405.5,106` | White card with six market metrics. |
| Symbol analysis + chart | `21,598,811,553` | `10.5,299,405.5,276.5` | Selected symbol facts + chart + stats side panel. |
| Lower audit cards | `21,1163,811,546` | `10.5,581.5,405.5,273` | Winner/Loser, cost drag, MDD, blockers, events, next checks. |
| Safety strip | `21,1710,811,68` | `10.5,855,405.5,34` | Three governance status columns. |
| Bottom tabs | `0,1779,853,65` | `0,889.5,426.5,32.5` | Dark compact nav in this reference. |

Reference 1 colors:

| Token | Hex | Usage |
|---|---:|---|
| `analysis.header` | `#19212e` | Top header. |
| `analysis.bg` | `#e6e8e9` | Body background. |
| `analysis.card` | `#f1f1f0` | White card sampled with subtle shadow. |
| `analysis.border` | `#a5adb6` | Card border/divider sample. |
| `analysis.green.soft` | `#d2ecdc` | Maintain icon badge background. |
| `analysis.amber.soft` | `#fbe9cd` | Watch icon badge background. |
| `analysis.red.soft` | `#f3ced0` | Block icon badge background. |
| `analysis.nav` | `#142030` | Bottom nav. |

### Implementation Sequence Required For Exact Match

1. Create `mobile-shell` first.
   - Fixed target width: `426.5px`.
   - QA device scale factor: `2`.
   - The app must not use desktop `max-w-[1720px]`, `grid-cols-12`, or hero titles for the mobile reference route.

2. Implement Reference 2 Scanner as the first route/state.
   - Do not implement Home first.
   - Do not implement Analysis first.
   - Do not improve the current dashboard; replace the mobile route.

3. Implement layout with hard measured slots.
   - Header `66px CSS`.
   - Filter row `22.5px CSS`.
   - Theme strip `44.5px CSS`.
   - Scanner rows `34-35px CSS`.
   - Chart card starts near `414.5px CSS`.
   - Bottom nav begins near `848.5px CSS`.

4. Implement data with fixture-first exact visual state.
   - Pixel matching requires stable text, symbol order, prices, and reason copy.
   - After the fixture state matches, connect `CockpitReadModelV2`.
   - DB-connected state must keep the same layout contract even when text changes.

5. Implement visual QA as a side-by-side artifact.
   - Reference image and rendered app screenshot must be placed in one comparison image.
   - Use same raw output dimensions: about `853x1844`.
   - Report section mismatch by section, not as a general screenshot.

### Pixel-Match Non-Negotiables

- No visible tech-stack copy.
- No marketing headline.
- No desktop table.
- No horizontal scroll table.
- No large KPI stack before scanner rows.
- No one-note slate dashboard palette.
- No CSS-only fake icons where a real icon is available.
- No VWAP fallback-to-close shown as real VWAP.
- No layout acceptance without a same-viewport reference comparison.

## No-Background Decision-Maker Report

- What happened: the three reference screenshots were converted into a pixel-level implementation spec.
- Why it matters: the next build now has exact section sizes, colors, typography, and component rules instead of broad UI inspiration.
- Whether this changes capital/deployment readiness: no. This is frontend design specification only.
- Plain-language next step: rebuild Scanner exactly against Reference 2 first, then apply Home and Analysis/Risk after Scanner passes visual comparison.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-ff378cc6-9b75-4070-9acd-a9b5ed0c73bd.png`
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7861d17d-2f17-4482-93fd-00f81457e599.png`
  - `docs/reports/task_3211_3230_mobile_reference_deep_dive/task_3211_3230_mobile_reference_deep_dive.md`
- Outputs:
  - `docs/reports/task_3281_3300_pixel_exact_reference_spec/task_3281_3300_pixel_exact_reference_spec.md`
  - `docs/reports/task_3281_3300_pixel_exact_reference_spec/task_3300_decision.csv`
  - `data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref1_analysis_section_overlay.png`
  - `data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref2_scanner_section_overlay.png`
  - `data/artifacts/task_3281_3300_pixel_exact_reference_spec/ref3_home_section_overlay.png`
  - `data/artifacts/task_3281_3300_pixel_exact_reference_spec/artifact_manifest.csv`
  - `scripts/trader_brain_3281_3300_pixel_exact_reference_spec_validate.py`
- Row counts:
  - Reference images measured: 3.
  - Overlay images produced: 3.
  - Layout sections measured: 25.
- Validation commands:
  - `python scripts/trader_brain_3281_3300_pixel_exact_reference_spec_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No new raw source acquisition was performed.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`

