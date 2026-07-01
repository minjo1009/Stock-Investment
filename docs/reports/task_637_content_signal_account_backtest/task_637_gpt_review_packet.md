# Task637 GPT Review Packet

## Scope

Use this packet only for external-model review. GPT output is not source truth and must not change trading acceptance without repo-native artifacts and validation.

## Supplied Facts

- Full refreshed entry period: 2024-01-02 to 2026-06-03.
- Entry count: 5,265.
- Linked official events: 3,319.
- Certified source texts: 3,319 of 3,319.
- Entries with certified content prediction: 2,406.
- Information presence and density fields are forbidden for assignment.
- Form 4 boilerplate is blocked from supply/demand interpretation.
- Stable validation/recent OOS content features:
  - `content_negative_score_flag`
  - `content_guidance_margin_flag`
  - `content_supply_demand_flag`
- $1000 full-period 50bp best content candidate:
  - `content_negative_score`, max5, final capital $5,148.31.
  - QQQ buy-and-hold final capital $1,751.31.
  - Task617 original max5 final capital $3,248.89.
- Validation-only 50bp best:
  - `content_guidance_supply_combo`, max5, final capital $1,236.73.
  - same-period QQQ $1,020.64.
- Recent OOS-only 50bp best:
  - `content_any_stable_feature`, max10, final capital $1,470.57.
  - same-period QQQ $1,140.89.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Real capital remains `FORBIDDEN`.

## Review Questions

1. Does `content_negative_score` look like a valid long-entry signal, or should it be reframed as an event-intensity or post-shock reversal signal?
2. Which exact live-readable rule should be locked first: negative-score reversal, guidance/margin, supply/demand, or guidance+supply combo?
3. What additional leakage, boilerplate, or survivorship risks should block promotion?
4. What should be the next validation before runtime use: Task617 overlay, exact delayed-entry replay, stricter event-to-symbol relevance, or source latency audit?
5. What evidence would make this candidate firm-grade enough for paper-only runtime gating?

## Required GPT Output

Return Korean review notes with each item labeled as one of:

- `interpretation`
- `inference`
- `source_gap`
- `promotion_blocker`

Do not invent facts, prices, dates, filings, URLs, analyst claims, or source text. Use only the supplied facts above.
