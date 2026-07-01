# GPT Pro 검수 요약

## 결론

조건부 통과다. 방향은 맞지만 한 번에 과격하게 늘리면 중복, 누락, provider block, partial 완료 오판이 생길 수 있다.

## 바로 적용할 것

| 우선순위 | 내용 | 이유 |
|---|---|---|
| P0 | progress / partial / stale 지표 강화 | 속도를 올리기 전에 멈춤과 진행 중을 구분해야 한다. |
| P0 | dynamic lane rebalance | GlobeNewswire가 끝나면 빈 lane을 BusinessWire로 넘겨야 한다. |
| P0 | source별 budget / sleep / runtime | BW, GN, PR은 archive 크기와 처리 방식이 다르다. |
| P0-P1 | BusinessWire lane 3~4 controlled increase | 현재 병목은 BusinessWire다. 다만 4 lane까지 단계적으로 간다. |

## 아직 하지 말 것

| 항목 | 판단 |
|---|---|
| PRNewswire offset/range split | 아직 금지. row progress가 있으므로 먼저 지표를 본다. |
| request sleep 0.5 | 아직 금지. block/empty/timeout 지표 확인 전이다. |
| BusinessWire 6+ lane | 아직 금지. BW 4 lane 안정 확인 후 판단한다. |
| PRNewswire 2+ lane | 아직 금지. PR은 cap 1 유지. |
| BusinessWire daily split default | 아직 금지. 필요하면 flag 뒤에서만 검토한다. |

## 핵심 해석

전체 평균 ETA는 GlobeNewswire 속도 때문에 좋아 보일 수 있다. 실제 long-tail은 BusinessWire가 결정한다. 따라서 전체 평균보다 source별 ETA와 BusinessWire pending을 중심으로 봐야 한다.
