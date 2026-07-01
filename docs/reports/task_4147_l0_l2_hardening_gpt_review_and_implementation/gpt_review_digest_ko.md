# TASK-4147 GPT Pro Review Digest

GPT Pro 검수 요지:
- 먼저 L1을 기사/행 단위 packet으로 넓힌다.
- L2는 L1 packet만 먹게 하고, L0 raw 직접 우회는 막는다.
- 뉴스와이어 매핑은 deterministic rule + review queue가 맞다. 모르는 것을 억지 ticker로 만들면 안 된다.
- L0 실시간 config는 기존 보수 config와 분리한다.
- 15분 loop는 무한 루프 하나 더 만들기보다 Windows Task Scheduler에 one-shot job을 15분 반복으로 등록하는 쪽이 안정적이다.
- feature schema에는 올리되, signal/order/broker로는 절대 연결하지 않는다.

Codex cut:
- 대형 DAG/orchestrator 재작성은 하지 않는다.
- LLM sentiment/NER는 넣지 않는다.
- feature store 전체 재구축은 하지 않는다.
- backfill 완료를 과장하지 않고, 완료/미완료/UNKNOWN을 proof로 남긴다.
