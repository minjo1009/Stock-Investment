# TASK-4141 GPT Pro Prompt

You are an expert review panel for a US equity swing-trading research platform.

Required expert roles:
- Quant Data Infrastructure Reviewer
- Institutional Quant Researcher
- Data Platform Architect
- News/Macro Feature Engineering Reviewer
- Trading Safety / Leakage Reviewer

User goal:
Review the current local Layer 1 and Layer 2 design state, then advise what Layer 2 view should be, why it should be developed that way, what should be built first, and how to validate it. The user explicitly wants practical development, not overengineering.

Important context:
- The latest local work has NOT been pushed to GitHub.
- Do NOT rely on GitHub as current state for L0/L1/L2.
- Use the local state packet below as the current source of truth.
- You may mention repo-file types to inspect later, but do not assume GitHub contains the newest TASK-4138 to TASK-4140 work.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence
- GPT advice is review-only. It does not approve trading.

Strategy context:
- US equity swing strategy.
- Average holding period is roughly one month.
- Therefore minute/second publication timestamps are not the main bottleneck for news/macro/newswire features.
- For this strategy, daily/as-of availability, mapping, deduplication, stale policy, and 1D/5D/20D/60D effect windows are more important than intraday timestamp precision.

Current local Layer 0 / Layer 1 state:
- L0 source acquisition has collectors, scheduler evidence, backfill evidence, and status reporting from recent TASK-4116 through TASK-4132.
- L1 now has normalized source packets and gates:
  - source-time gate
  - raw-integrity gate
  - mapping gate
  - authority gate
  - gap ledger
  - diagnostic L1-to-L2 handoff samples
- L1 is not supposed to create features.
- L1 should preserve evidence and say whether a row can move downstream.
- Missing/stale data remains UNKNOWN/BLOCKER.

TASK-4138 local outcome:
- Added explicit L1 source-time precision policy.
- Wikimedia day-level dates may be represented as noon UTC only as imputed nominal time.
- Wikimedia noon is NOT actual source/publication time.
- Month/year-only Wikimedia dates remain context-only or blocked for feature timing.
- L1 now records source-family block reasons.
- L1 repeated validation ledger ran 3 validators and passed.
- No trading/paper/live/broker/order gate opened.

TASK-4139 local outcome:
- Dirty worktree was classified, not cleaned.
- 645 dirty rows were classified.
- 207 P0 owner-review rows.
- 39 DVC pointer deletion rows.
- 76 L2/L3 code/report deletion rows.
- 72 L0 source code/config change rows.
- No automatic delete/restore/cleanup was performed.
- This means future work should avoid broad cleanup and keep new artifacts narrowly scoped.

TASK-4140 local outcome:
- Corrected news/macro/newswire posture for swing strategy.
- `public_context_news_feeds`, `public_market_macro_news_feeds`, and `public_newswire_feeds` are now active swing/daily feature candidates.
- All three have:
  - `swing_feature_candidate_now = 1`
  - `blocked_by_intraday_timestamp = 0`
  - `minute_second_timestamp_required = 0`
  - `daily_publication_date_can_be_sufficient = 1`
  - activation policy: `NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION`
  - primary effect window: `20D`
  - secondary effect windows: `1D`, `5D`, `60D`
  - feature materialization still closed now
- Mapping scopes:
  - TICKER allowed
  - ENTITY allowed
  - SECTOR allowed
  - MACRO allowed
  - UNKNOWN blocks feature admission
- Required checks:
  - mapping scope
  - dedup
  - stale policy
  - effect window
  - no future outcome / no leakage

Current L2 state before next development:
- Existing TASK-4136 created a thin L2 intake contract.
- Legacy L2 news builder is quarantined.
- Direct legacy L0-to-L2 news path is separated.
- L2 currently has intake/admission artifacts, but not a fully developed primitive builder for swing news/macro/newswire.
- The next likely task is TASK-4142 or similar: build L2 swing primitive/admission view for news, macro, and newswire.

What we need from you:
1. Define what Layer 2 should mean in this system.
2. Explain the right “view” of Layer 2:
   - Is it an event primitive layer?
   - A feature-admission queue?
   - A normalized economic meaning layer?
   - A read/view layer for L3?
   - Which of these should come first?
3. Say what Layer 2 should NOT do yet.
4. Propose the first 3-5 concrete development tasks for L2.
5. For news/macro/newswire specifically, propose the minimum useful primitive schema.
6. Propose mapping/dedup/stale/effect-window logic appropriate for a one-month swing strategy.
7. Identify P0/P1 risks and how to validate them.
8. Give Codex a practical implementation plan that avoids code-for-code overengineering.

Please answer in Korean, using simple and direct wording.

Output format:
1. 결론
2. L2의 역할
3. L2에서 먼저 만들 view
4. 뉴스/매크로/뉴스와이어 primitive 최소 스키마
5. mapping / dedup / stale / effect window 기준
6. 하지 말아야 할 것
7. P0/P1 리스크
8. Codex가 다음에 구현할 작업 순서
9. 검증 체크리스트
