# Task671 GPT Review Packet

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: GPT output is review input only.

## Correction

Task671 must use currently available entry-time data only.

Historical quote/trade/NBBO/microstructure data is still being collected and must not be used in current state decomposition. It can only be recorded as `SOURCE_PENDING_NOT_USED`.

## Available Data Categories

1. macro/market
2. rates/dollar/credit/liquidity
3. theme leadership and rotation
4. company catalyst/content
5. price/chart acceptance
6. relation/transmission
7. portfolio/capacity computed from candidate set
8. source integrity/as-of flags

## Review Questions

1. What are final implementable axes now?
2. Which axes are explicitly deferred?
3. Which axes are diagnostic-only?
4. What artifacts should Task671 produce?
5. What is forbidden?
6. Should factor/crowding remain proxy-only or be excluded?

