# TASK-4158 L0 Public Newswire Scheduler Repair

## 결론

TASK-4157의 표현은 과했다. 세 소스를 shard로 나눌 수 있게 만든 것은 맞지만, 실제 worker 배정은 inventory 순서라 BusinessWire가 worker를 독점했다.

TASK-4158에서 아래를 고쳤다.

- source별 round-robin queue
- source lane 제한: BusinessWire `2`, GlobeNewswire `1`, PRNewswire `1`
- worker 무응답 recycle: 15분 동안 진행 흔적이 없으면 재시작
- worker 최대 실행 시간: 30분
- 재시작 시 기존 shard별 완료 state도 inventory에 반영
- TASK-4158 진행률 모니터로 교체

현재 실행 상태:

- 런처 PID: `33036`
- 모니터 PID: `24952`
- schedule strategy: `source_round_robin`
- lanes: `businesswire=2, globenewswire=1, prnewswire=1`
- status: `RUNNING`
- progress: `45.4036%`
- completed units: `1,862 / 4,101`
- pending units: `2,239`
- row count: `80,591`

## 실제 확인한 worker 분포

현재 RUNNING worker는 아래처럼 분산되어 있다.

- BusinessWire: `businesswire:2020-11`, `businesswire:2020-12`
- GlobeNewswire: `globenewswire:2016-03`
- PRNewswire: `prnewswire:2016-01`

즉 BusinessWire가 느려도 GlobeNewswire/PRNewswire가 별도 lane에서 계속 진행된다.

## 왜 다시 고쳤나

TASK-4157의 문제는 코드 구조와 운영 효과를 혼동한 것이다.

구조적으로는 shard 병렬 처리가 가능했지만, queue가 source별 공정성을 보장하지 않았다. 그래서 worker 4개가 BusinessWire에 몰렸고, 사용자가 기대한 "세 소스가 동시에 넓게 수집되는 상태"가 아니었다.

TASK-4158은 이 차이를 없애는 보정 작업이다.

## 안전 경계

이 작업은 L0 수집/진단 전용이다.

- strategy: `NOT_ACCEPTED`
- deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real capital: `FORBIDDEN`
- broker mutation: forbidden
- live order: forbidden
- trade authority: none

