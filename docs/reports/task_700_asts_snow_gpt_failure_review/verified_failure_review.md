# Task700 ASTS/SNOW GPT Failure Review

## Decision Summary

- GPT review completed through the `1. 코딩/투자` ChatGPT tab.
- GPT response is saved in `gpt_response_raw.md`.
- Data packet sent to GPT is saved in `asts_snow_gpt_data_packet.md`.
- GPT output was useful but not source-complete. SEC and external-source checks were added separately.
- Status: research-only. No strategy promotion and no trading approval.

## Quant Expert Report

### Supplied Project Facts

- ASTS source-direct row lost `-13.78%` after 50 bps cost and underperformed QQQ by `-3.99%`.
- SNOW source-direct rows lost `-25.52%` and `-23.66%` after 50 bps cost.
- ASTS had `company_contract_customer_order` and `cleaner_company_multi_signal`, yet failed.
- SNOW had `company_revenue_guidance`, `high_noise_thin_signal`, and noise ratio near `0.96`.

### GPT Review Takeaway

- ASTS was not simply a good contract/customer/order event. The same packet had financing/convertible-note overhang that our positive signal did not penalize enough.
- SNOW was not a true guidance raise signal. It was closer to guidance reaffirmation after unauthorized executive comments. The model treated guidance presence as positive, but did not score guidance novelty or expectation surprise.
- Both cases show the same modeling gap: `economic signal exists` is not the same as `market has new underpriced information`.

### Verified External Source Notes

- ASTS official SEC 8-K dated January 27, 2025 says AST SpaceMobile completed a private offering of `$460 million` aggregate principal amount of `4.25% Convertible Senior Notes due 2032`, with initial conversion price around `$26.99`, and capped call arrangements intended to reduce potential dilution subject to a cap.
- Snowflake official SEC 8-K dated October 27, 2025 says an unauthorized Instagram interview contained statements about future results, investors should not rely on those statements, and Snowflake reaffirmed Q3 and FY26 revenue guidance originally issued on August 27, 2025.
- Reuters/Investing.com reported on December 3-4, 2025 that Snowflake shares fell because Q4 product revenue growth guidance disappointed lofty investor expectations despite headline results, with slower growth and discounts on large long-term deals cited.
- External sources on ASTS convertible offerings support the trader inference that convertible-note offerings can create dilution/hedging/financing overhang and short-term stock pressure.

### Feature Logic Fix

- Add `financing_overhang_axis`: private offering, notes, convertible, capped call, dilution, use of proceeds.
- Add `guidance_quality_axis`: raise, reaffirm, soft, unauthorized-comment cleanup, consensus surprise.
- Add `information_novelty_axis`: new contract/order/guidance versus already announced/reaffirmed.
- Add `noise_dominance_axis`: high-noise thin signal should require extra confirmation.
- Add `price_absorption_required_for_conflict`: when positive catalyst and financing/noise conflict coexist, require price confirmation before eligibility.

## No-Background Decision-Maker Report

- ASTS failed because our model saw the good parts but did not punish the convertible-note financing overhang enough.
- SNOW failed because our model saw guidance, but missed that it was mostly reaffirmation/cleanup, not a strong new raise.
- The next rule should not say `source-direct = buy`.
- It should say `source-direct + new information + no financing overhang + clean guidance quality + price confirmation`.

## Artifact Manifest

- `asts_snow_gpt_data_packet.md`: sanitized internal packet sent to GPT.
- `gpt_response_raw.md`: copied ChatGPT response.
- `verified_failure_review.md`: source-checked project summary.

