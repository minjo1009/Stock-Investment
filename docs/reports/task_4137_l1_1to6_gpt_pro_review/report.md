# TASK-4137 L1 1~6 GPT Pro 검토

## 목적

L1 관련 현재 상태와 1~6 보완 과제를 GPT Pro에게 전달하고, 과도한 코드 없이 실효성 있는 보완 방향을 검토받는다.

## 검토 대상

1. Wikimedia 날짜 정책
2. 뉴스/매크로 매매 feature 기준과 검증
3. 스케줄러 실행/검수
4. Validator 분리
5. Chrome crawling 추가 기준
6. 티커/뉴스 매핑 고도화

## 현재 상태

- prompt: `docs/reports/task_4137_l1_1to6_gpt_pro_review/gpt_prompt.md`
- response: `docs/reports/task_4137_l1_1to6_gpt_pro_review/gpt_response.md`
- capture_status: CAPTURED

## GPT 핵심 결론

- L1은 feature를 만드는 곳이 아니라, 넘겨도 되는 후보인지와 왜 막혔는지를 계속 남기는 검문소로 강화해야 한다.
- L2는 뉴스, 매크로, Wikimedia, Chrome 데이터를 매매 feature로 쓰기 전에 source time, 매핑, 중복, stale, effect window 입학시험을 담당해야 한다.
- 아직 하지 말아야 할 것은 L3 scoring, 실제 feature materialization, paper/live promotion, 광범위 Chrome crawling이다.

## 다음 후보

GPT는 TASK-4138을 작은 실행 단위로 제안했다. 핵심은 L1 source-time precision과 Wikimedia 정오 정책, 뉴스/매크로 feature 입학시험 기준, ticker/news mapping 기준을 먼저 명확히 하는 것이다.
