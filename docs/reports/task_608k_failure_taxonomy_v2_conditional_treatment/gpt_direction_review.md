# Task608K GPT Direction Review

Captured via Chrome ChatGPT project `1. 코딩/투자`.

## 결론

- Task608K는 실패 원인 분해에는 성공했다.
- 하지만 실패 치료법 검증은 아직 실패다.
- live rule promotion은 아직 안 된다.
- reducer retry는 계속 닫는다.
- Task608L은 rule-lock이 아니라 clean false 해부부터 해야 한다.

## GPT 판정

- Failure Discovery Stage: PASS
- Failure Treatment Stage: FAIL
- Live Rule Promotion: NOT READY
- Current strategy status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## 이유

- taxonomy coverage는 100%까지 올라왔다.
- live/wait-window actionable coverage도 80%까지 올라왔다.
- 그러나 best live candidate인 `wait15_early_adverse_abort_candidate`는 failure rate 46.15%, clean false 7개다.
- 지금 abort/reduce rule로 쓰면 실패 제거보다 winner destruction 위험이 더 크다.
- delayed 60m는 전체 정책으로 쓰기에는 +0.1659pp 수준이라 약하다.
- delayed 60m는 opening trap family subset에서만 연구해야 한다.

## Task608L Objective

Task608L의 목적은 `wait15_early_adverse_abort_candidate` 안에서 true failure 6개와 clean false 7개를 분리하는 live-detectable interaction feature를 찾고, fold-forward에서 winner destruction 없이 failure concentration을 높일 수 있는지 검증하는 것이다.

Task608L은 abort rule 개발이 아니다. Task608L은 failure classifier 검증이다.

## Task608L 필수 비교 Feature

- `symbol_mae_15m`
- `symbol_mfe_15m`
- `symbol_mae_30m`
- `symbol_mfe_30m`
- `symbol_ret_15m`
- `symbol_ret_30m`
- `symbol_ret_60m`
- `symbol_ret_120m`
- `symbol_vwap_fail_15m_flag`
- `symbol_vwap_fail_30m_flag`
- `symbol_vwap_fail_60m_flag`
- `opening_rejection_120m_flag`
- `symbol_opening_range_high_reclaim_120m_flag`
- `relative_ret_vs_qqq_15m`
- `relative_ret_vs_qqq_30m`
- `relative_ret_vs_qqq_120m`
- `symbol_volume_decay_120m`
- `theme_confirmation_fail_pre_entry_flag`
- `failure_type_v2`
- `detection_horizon`

## Interaction 후보 우선순위

1. early adverse AND no MFE recovery
2. early adverse AND persistent VWAP fail
3. early adverse AND opening range rejection
4. early adverse AND relative_ret_vs_qqq decay
5. early adverse AND volume decay
6. early adverse AND theme drag
7. early adverse AND VWAP fail AND no MFE recovery
8. early adverse AND relative strength decay AND volume decay

## Task608L PASS 기준

- trigger coverage가 무너지면 안 된다.
- failure concentration은 현재 46.15%보다 올라야 한다.
- clean false는 현재 7개보다 줄어야 한다.
- fold-forward positive evidence가 필요하다.
- winner destruction evidence가 없어야 한다.

## Task608M 진입 조건

- failure concentration 상승
- clean false 감소
- trigger coverage 유지
- fold-forward positive

위 조건이 모두 맞으면 Task608M에서 candidate rule-lock 검토가 가능하다.

## Branch 중단 조건

- interaction을 붙여도 failure concentration이 개선되지 않음
- clean false가 줄지 않음
- trigger 수가 너무 작아져 재현성이 사라짐

이 경우 early adverse branch는 중단한다.

## Late Followthrough 처리

- `late_followthrough_failure` 7개는 Task608L 대상이 아니다.
- detection이 `post_entry_eval`이라 entry qualification 문제가 아니라 exit/trailing review track에 가깝다.
- 별도 exit management track으로 보낸다.

## 운영 문구

Task608K status: `FAIL_TREATMENT_PROMOTION`.

Failure taxonomy is complete. Treatment evidence is not.

Current evidence supports failure classification research, not live rule deployment.

`wait15 early adverse` remains a diagnostic candidate only.

Reducer retry remains CLOSED.

Next objective: separate true failures from clean winners inside the early adverse bucket.

No rule-lock promotion without fold-forward evidence, reduced clean false, and no winner destruction.
