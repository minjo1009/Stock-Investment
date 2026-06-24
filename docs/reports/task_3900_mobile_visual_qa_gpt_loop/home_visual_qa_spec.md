# HOME Visual QA Revision Spec

## Scope

Mobile-first HOME cleanup based on 390x844 screenshot QA and GPT expert-agent feedback.

## Safety

- Frontend remains read-only and fixture-backed.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No DB, runtime API, broker, paper/live, or order mutation connection is allowed.

## Required UI Changes

1. HOME information order must be:
   - portfolio hero,
   - 오늘 확인할 것,
   - 수익현황 chart,
   - 보유 포트폴리오,
   - 투자 일지,
   - source/governance support.
2. The first viewport must not be dominated by governance or safety copy.
3. `UNKNOWN 원`, `Performance`, `SOURCE_NOT_ATTACHED`, `현재 상태`, and `차트 포인트` must not be primary visible HOME copy.
4. Missing account values must display as `연결 대기`, not fake numbers.
5. The performance chart title must be `수익현황`, with the subtitle `평가금 vs 원금 vs QQQ`.
6. Timeframe chips must remain locally clickable: `1D`, `1M`, `3M`, `6M`, `1Y`, `ALL`.
7. Chart placeholder height should stay compact enough that the next section can be discovered on a phone.
8. Journal month rail must continue from `22.01` through the current month, with January and current month showing `YY.MM`.

## Acceptance

- 390x844 screenshot shows portfolio hero and 오늘 확인할 것 above the chart.
- No fake chart line or fake account value appears.
- Source/gov state remains present, but only in the lower support layer.
