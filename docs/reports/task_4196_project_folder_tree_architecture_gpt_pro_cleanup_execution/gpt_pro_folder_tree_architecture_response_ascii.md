# GPT Pro Folder Tree Architecture ASCII Restatement

- Captured at: 2026-07-01T15:57:43.409Z
- Source URL: https://chatgpt.com/c/6a446fb0-4860-83ee-a962-afcb93e796ab
- Page title: Structure Cleanup Review
- Article count: 0
- Capture status: possibly_still_generating

---

콘텐츠로 건너뛰기
정민
채팅 기록
ChatGPT Pro
새 채팅
채팅 검색
라이브러리
일정
앱
더 보기
고정됨
4. 관리
2. 운동
1. 코딩/투자
프로젝트
여행
7. 업무
6. 영어
5. 노래
3. 경제/시사
더 보기
채팅
L1 작업 완료 여부
L1 Review Completion Request
TASK-4182 L1 문제 해결
L1 Blockers and Improvements
Backend Task Review
L0 Backfill Improvement Plan
유통기한 경과 우유 섭취 여부
Prime Harness Review Strategy
Blocker Burn-down Review
L0-L4 문제 해결 방향
Task 4167 L0-L4 Prioritization
Quant Research Shortlist
Monday Battery & EV Brief
Newswire Recall Loss Review
GlobeNewswire L0-L2 Review
Structure Cleanup Review
Task-4158 Optimization Plan
Backend newswire backfill review
L0 백필 성능 개선
Market regime update: US-Iran deal sparks Risk-On rally
식물 햇빛 요구사항
Patch Review TASK-4156
L4 Thesis Bundle Review
L4 Development Plan Review
L3 Relation Graph Review
L3 relation graph 분석
L3 Diagnostic Strategy Plan
L0 Backfill Recovery Review
정민
정우 민
Pro
공유하기
# GPT Pro Prompt: TASK-4160 L0-L4 Structure Cleanup Review

You are reviewing a local working copy that is not fully reflected in GitHub.

Do not rely on GitHub as the latest source of truth. Use the local context packet below as the latest state. You may use GitHub only for broad project context if available, but do not override the local packet with stale GitHub state.

Act as:

1. Professional Backend Engineer
2. Data Platform Architect
3. Quant Data Infrastructure Reviewer
4. Systematic PM / Trading Research Reviewer

Project hard state:

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is UNKNOWN/BLOCKER, never negative evidence
- No BUY/SELL/ranking/sizing/order/paper/live/deployment recommendation.

User goal:

The user wants Codex to do structure cleanup for Layer 0 through Layer 4 while L0 public newswire backfill continues. The cleanup should reduce project confusion and make it clear which layer owns which artifacts, validators, handoff files, and status reports.

Important: Avoid over-engineering. Do not recommend code for code's sake, guardrails for guardrails' sake, or large framework migrations. Recommend only changes with direct practical value.

## Current Local State

### L0 public newswire backfill

- TASK-4159 implemented controlled acceleration.
- Current aggregate status: RUNNING.
- Current progress: about 47.6%.
- Completed units: 1,953 / 4,101.
- Pending units: 2,148.
- Current workers: BusinessWire 2, GlobeNewswire 1, PRNewswire 1.
- Safety flags are all closed: broker/order/live/paper/real-capital/trade-authority all 0.
- BusinessWire remains the long-tail bottleneck.
- GlobeNewswire is not a one-month/two-hour bottleneck. Typical GN monthly shard takes about 1.5 minutes, but the whole remaining GN set still takes time because many monthly shards remain.
- PRNewswire unit completion is slow, but row/offset progress is observed. PRNewswire offset/range split remains prohibited for now.

### TASK-4159 implemented

Files:

- scripts/run_l0_public_newswire_sharded_backfill.py
- scripts/aggregate_l0_public_newswire_shards.py
- scripts/validate_l0_public_newswire_sharded_backfill.py
- scripts/control_l0_public_newswire_acceleration.ps1
- scripts/run_l0_public_newswire_sharded_progress_monitor.ps1
- tests/test_l0_public_newswire_sharded_backfill.py
- docs/reports/task_4159_l0_public_newswire_controlled_acceleration/*

Capabilities:

- source base lanes and caps.
- dynamic lane rebalance.
- source-specific budgets/runtime.
- progress-aware stale detection using completed unit, active offset, row count, raw bytes, last successful fetch.
- dead RUNNING lock recovery.
- live lock skip defense.
- source-level ETA and active/partial/stale worker aggregate fields.
- validator for dead PID, active offset completed misclassification, aggregate fields, safety flags.
- hourly monitor writes controlled_acceleration_decision.json.

Current controller decision:


text
decision: BW4_BLOCKED
reason: globenewswire_not_complete,stable_minutes_below_threshold
validator_passed: true
safety_closed: true


### L1

Known L1 direction from recent tasks:

- L1 should be row/article-level packetization, not only batch-level.
- News, macro, public newswire must remain swing/daily trading feature candidates, not "not feature forever".
- L1 must preserve source lineage, raw path/hash, source time, available-to-brain time, mapping status, blocker status.
- Data missing because L0 is still backfilling is UNKNOWN/BLOCKER, not negative evidence.
- L1 validation should keep running and should not block just because L0 coverage is incomplete.

Important local summary:


json
{
  "task_id": "TASK-4138",
  "source_family_policy_rows": 5,
  "validation_runs": 3,
  "validation_failures": [],
  "trading_authority_opened": false,
  "paper_live_broker_order_opened": false,
  "feature_allowed_now_rows": []
}


### L2

Known L2 direction:

- L2 is not final signal/scoring/order logic.
- L2 should convert L1 packets into safe swing event primitive/admission/read views.
- News, macro, public newswire are feature candidates, but materialization remains diagnostic and gated.
- L2 must separate existing legacy news code from the new L2 event/primitive pipeline.
- L2 must dedup repeated source events, map entity/ticker/source family, keep stale/effect-window metadata, and pass to L3.

Important local TASK-4147 summary:


json
{
  "task_id": "TASK-4147",
  "l1_article_packets": 1093,
  "l1_article_ready_packets": 1093,
  "raw_article_packet_blockers": 0,
  "newswire_mapping_queue_rows": 407,
  "newswire_l0_mapped_rows": 8253,
  "l2_diagnostic_feature_rows": 1842,
  "critical_incomplete_dead_backfill_lanes": [],
  "separated_realtime_config": "configs/l0_realtime_operational_safe_config_4147.json",
  "scheduler_task_name": "TraderBrainL0L2Hardening4147",
  "trading_eligible_rows": 0,
  "signal_order_export_allowed_rows": 0,
  "broker_mutation_permitted_rows": 0
}


### L3

Known L3 direction:

- L3 should build relation graphs, event clusters, coverage gaps, relation quality, and diagnostic strategy view.
- L3 must not treat graph count as evidence quality.
- L3 must not convert diagnostic relations into trading signals.
- L3 v2 increased relation graph coverage materially, but still has quality/coverage caveats.

Known artifacts/scripts:

- scripts/build_l3_diagnostic_strategy_view_4150.py
- scripts/build_l3_relation_graph_v2_4152.py
- scripts/build_l3_relation_graph_quality_guard_4154.py
- corresponding validators.

### L4

Known L4 direction:

- L4 is diagnostic thesis bundle assembly, not final institutional thesis acceptance.
- L4 should connect L0-L3 evidence, lineage, relation graph, coverage gap, contradiction status, and blocker status into reviewable thesis bundles.
- L4 must not produce buy/sell/hold/ranking/sizing/order/paper/live/deployment readiness.

Known scripts:

- scripts/build_l4_thesis_bundles.py
- scripts/validate_l4_thesis_bundle_package.py

### Current problem to solve

The project now has many task-specific scripts and reports:

- L0 task scripts and validators.
- L1 packet scripts and validators.
- L2 admission/materialization scripts and validators.
- L3 relation graph scripts and validators.
- L4 thesis bundle scripts and validators.
- Many old/dirty files in the worktree.

This makes it easy for future Codex runs to read the wrong file, treat superseded reports as active, or confuse legacy L2/news code with current L2 event primitive/admission pipeline.

## What Codex wants from GPT

Please review and propose a concrete, low-overhead structure cleanup plan.

Focus on:

1. Which small set of current L0-L4 files should be treated as active entrypoints.
2. Which files should be indexed in a single handoff manifest or README so future Codex reads the right files first.
3. Whether we need a layer ownership matrix such as:
   - L0: collectors/backfill/scheduler/raw integrity
   - L1: source packets/lineage/mapping/blockers
   - L2: event primitive/admission/materialization candidates
   - L3: relation graph/event clusters/quality/coverage gaps
   - L4: thesis bundle/review blockers
4. Whether to create one docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_handoff.md and one machine-readable active_layer_manifest.json.
5. How to avoid touching huge amounts of dirty/unrelated files.
6. What validators should be run after the cleanup.
7. What should explicitly NOT be done now.

Expected output:

1. Verdict: PASS / CONDITIONAL PASS / FAIL.
2. Prioritized structure cleanup plan.
3. Exact files Codex should create or edit.
4. Exact files Codex should avoid.
5. Validator checklist.
6. Korean plain-language summary suitable for the user.
더 보기

구조 정리는 파일 이동이 아니라 활성 진입점·계층 소유권·읽기 순서를 최소 문서와 manifest로 고정하는 방향입니다. 실행 중인 L0 백필과 dirty/legacy 파일은 건드리지 않는 전제로 보겠습니다.

5m 9s 동안 생각함
핵심 3줄 요약

Verdict: CONDITIONAL PASS. 지금 필요한 것은 파일 이동/삭제가 아니라, “현재 정본 파일 목록”을 고정하는 얇은 인덱스 작업입니다.

Codex는 코드 리팩터링 없이 active_layer_handoff.md와 active_layer_manifest.json만 만들고, L0 백필/컨트롤러/기존 validator는 건드리지 않는 것이 맞습니다.

L1/L2의 정확한 활성 스크립트명은 제공 패킷에 없으므로, Codex가 로컬 파일명만 확인해 manifest에 채우되, 의미상 ownership은 명확히 고정해야 합니다.

1. Verdict
항목	판정
구조 정리 필요성	PASS
대규모 정리/파일 이동 필요성	FAIL
권장 방식	CONDITIONAL PASS
조건	새 정본 인덱스 2개 생성, 기존 코드 수정/이동/삭제 금지, validator만 실행

결론:
TASK-4160은 “구조 리팩터링”이 아니라 “활성 정본 인덱스 생성” 작업으로 해야 합니다.
현재 L0 public newswire backfill이 RUNNING이고, TASK-4159 controller/monitor가 정상 동작 중이므로, 파일 이동·삭제·대량 rename은 리스크 대비 효용이 낮습니다.

2. 우선순위 구조 정리 계획
우선순위	작업	목적	복잡도	리스크	판정
P0	docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_handoff.md 생성	사람이 먼저 읽을 정본 문서	낮음	낮음	필수
P0	docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_manifest.json 생성	Codex/스크립트가 읽을 machine-readable 정본	낮음	낮음	필수
P0	L0~L4 ownership matrix 고정	“어느 레이어가 무엇을 소유하는지” 명확화	낮음	낮음	필수
P1	active entrypoint / validator / output / report를 레이어별로 명시	future Codex가 잘못된 파일을 먼저 읽는 문제 방지	낮음	낮음	필수
P1	superseded / legacy / read-only / do-not-edit 상태 태그 추가	오래된 task report와 legacy L2/news code 혼동 방지	낮음	낮음	필수
P2	root README 또는 기존 docs index 수정	프로젝트 전체 진입점 개선	낮음	중간	지금은 보류
P2	파일 이동, 폴더 재배치, rename	물리 구조 정리	중간~높음	높음	금지
P2	legacy L2/news 코드 정리	장기적으로 필요 가능	중간~높음	높음	지금은 금지
3. Active Layer Ownership Matrix

Codex가 가장 먼저 고정해야 하는 구조는 아래입니다.

Layer	소유 범위	입력	산출물	금지 사항
L0	collector, backfill, scheduler, raw integrity, shard state, source-specific progress	외부 원천 데이터, archive, API/RSS/web source	raw rows, shard state, aggregate status, L0 validation report	signal, scoring, ranking, trading decision
L1	row/article-level packetization, lineage, raw hash/path, source time, available-to-brain time, mapping/blocker status	L0 raw data	source packet, article packet, mapping queue, blocker status	L0 incomplete을 negative evidence로 해석
L2	safe swing event primitive, admission/read views, diagnostic materialization candidates	L1 packets	event primitive, admission view, stale/effect-window metadata, entity/ticker mapping	final signal, score, order intent, ranking, trading eligibility
L3	relation graph, event clusters, relation quality, coverage gaps, diagnostic strategy view	L2 primitives/views	graph, cluster, relation quality, coverage gap report	graph count를 evidence quality로 오해, trading signal 생성
L4	diagnostic thesis bundle assembly, evidence stitching, contradiction/blocker status	L0~L3 evidence and lineage	reviewable thesis bundle, blocker/coverage/contradiction status	buy/sell/hold, sizing, ranking, paper/live/deployment readiness
4. Active Entrypoints — 현재 정본으로 취급할 파일
4.1 L0 — exact active files
역할	Active file
Backfill runner	scripts/run_l0_public_newswire_sharded_backfill.py
Shard aggregator	scripts/aggregate_l0_public_newswire_shards.py
Backfill validator	scripts/validate_l0_public_newswire_sharded_backfill.py
Acceleration controller	scripts/control_l0_public_newswire_acceleration.ps1
Progress monitor	scripts/run_l0_public_newswire_sharded_progress_monitor.ps1
Test	tests/test_l0_public_newswire_sharded_backfill.py
Report directory	docs/reports/task_4159_l0_public_newswire_controlled_acceleration/*
Current decision file	controlled_acceleration_decision.json under TASK-4159 report path

주의:
L0 active files는 수정 대상이 아니라 읽기/검증 대상입니다. TASK-4160에서 L0 코드를 바꾸면 안 됩니다.

4.2 L1 — ownership은 확정, exact script는 Codex가 로컬에서 채워야 함

제공된 패킷에서 L1의 정확한 script filename은 주어지지 않았습니다. 따라서 GPT가 임의 파일명을 만들면 안 됩니다.

항목	TASK-4160에서 해야 할 일
L1 role	row/article-level packetization, lineage, mapping, blocker status
Known task	TASK-4138
Known status	validation_failures: [], trading_authority_opened: false
Manifest 처리	active_entrypoints에 Codex가 로컬에서 확인한 실제 L1 script/validator 경로만 기입
금지	L0 coverage incomplete을 L1 validation failure로 처리하지 말 것

Manifest에는 임시로 아래처럼 넣는 것이 안전합니다.

JSON
{
  "layer": "L1",
  "status": "active_direction_confirmed_exact_files_require_local_resolution",
  "known_task": "TASK-4138",
  "owner_scope": [
    "row_article_packetization",
    "source_lineage",
    "raw_path_hash",
    "source_time",
    "available_to_brain_time",
    "mapping_status",
    "blocker_status"
  ],
  "active_entrypoints": [],
  "active_validators": [],
  "codex_action": "Fill exact local L1 script and validator paths after local file inspection. Do not invent filenames."
}
4.3 L2 — legacy/news code와 current event primitive pipeline 분리

제공된 패킷상 L2의 정확한 active script filename도 주어지지 않았습니다. 다만 TASK-4147의 상태와 역할은 명확합니다.

항목	내용
Known task	TASK-4147
Current role	L1 packet → safe swing event primitive/admission/read view
Known output facts	l2_diagnostic_feature_rows: 1842, trading_eligible_rows: 0, signal_order_export_allowed_rows: 0
Known config	configs/l0_realtime_operational_safe_config_4147.json
Scheduler	TraderBrainL0L2Hardening4147
금지	legacy news code를 current L2 event primitive pipeline으로 오인하지 말 것

Manifest 처리:

JSON
{
  "layer": "L2",
  "status": "active_direction_confirmed_exact_files_require_local_resolution",
  "known_task": "TASK-4147",
  "owner_scope": [
    "event_primitive",
    "admission_view",
    "diagnostic_materialization_candidate",
    "entity_ticker_mapping",
    "dedup",
    "stale_metadata",
    "effect_window_metadata"
  ],
  "known_configs": [
    "configs/l0_realtime_operational_safe_config_4147.json"
  ],
  "active_entrypoints": [],
  "active_validators": [],
  "legacy_warning": "Do not treat legacy news code as current L2 primitive/admission pipeline unless explicitly marked active."
}
4.4 L3 — exact active files
역할	Active file
Diagnostic strategy view	scripts/build_l3_diagnostic_strategy_view_4150.py
Relation graph v2	scripts/build_l3_relation_graph_v2_4152.py
Relation graph quality guard	scripts/build_l3_relation_graph_quality_guard_4154.py
Validators	Corresponding L3 validators in local tree

L3 manifest에는 반드시 아래 caveat를 넣어야 합니다.

Relation count is not evidence quality.
L3 output is diagnostic relation infrastructure only.
No trading signal, ranking, sizing, order intent, or eligibility may be derived from L3.
4.5 L4 — exact active files
역할	Active file
Thesis bundle builder	scripts/build_l4_thesis_bundles.py
Thesis bundle validator	scripts/validate_l4_thesis_bundle_package.py

L4 manifest에는 반드시 아래 caveat를 넣어야 합니다.

L4 is diagnostic thesis bundle assembly only.
L4 does not produce institutional thesis acceptance.
L4 must not emit buy/sell/hold, final_score, recommendation, policy_action, target_weight, position_size, order intent, paper/live eligibility, or deployment readiness.
5. Codex가 생성/수정해야 할 정확한 파일
5.1 Create
파일	목적
docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_handoff.md	사람이 읽는 현재 L0~L4 정본 handoff
docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_manifest.json	Codex/자동화가 읽는 machine-readable active file index
5.2 Optional create
파일	판정	이유
docs/reports/task_4160_l0_l4_structure_cleanup/validation_log.md	선택	validator 실행 결과를 남기고 싶을 때만 생성
root README.md 수정	보류	dirty/unrelated 파일 충돌 가능성 있음
기존 docs index 수정	보류	지금은 새 task folder만으로 충분

권장:
이번 TASK-4160에서는 정확히 2개 파일만 생성하는 것이 가장 안전합니다.
검증 로그가 꼭 필요하면 validation_log.md까지 3개로 제한합니다.

6. active_layer_handoff.md에 들어가야 할 내용

권장 목차:

Markdown
# TASK-4160 Active L0-L4 Layer Handoff

## 1. Hard State
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data: UNKNOWN/BLOCKER, never negative evidence
- No BUY/SELL/ranking/sizing/order/paper/live/deployment recommendation

## 2. Current Running State
- L0 public newswire backfill: RUNNING
- Progress: 1,953 / 4,101, about 47.6%
- Workers: BW 2, GN 1, PR 1
- Current controller decision: BW4_BLOCKED
- Safety flags: all closed

## 3. Layer Ownership Matrix

## 4. Active Entrypoints by Layer

## 5. Active Validators by Layer

## 6. Active Reports / Handoff Outputs

## 7. Legacy / Superseded / Read-only Rules

## 8. Explicit Do-Not-Do List

## 9. Open Local Resolution Items
- Exact L1 active scripts/validators need local path confirmation.
- Exact L2 active scripts/validators need local path confirmation.
7. active_layer_manifest.json 권장 스키마

복잡한 schema validator는 지금 만들 필요 없습니다.
python -m json.tool로 JSON 문법만 확인하면 충분합니다.

JSON
{
  "task_id": "TASK-4160",
  "purpose": "Active L0-L4 layer handoff index for future Codex runs",
  "hard_state": {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation": false,
    "live_order": false,
    "paper_promotion": false,
    "missing_stale_incomplete_data_policy": "UNKNOWN_OR_BLOCKER_NEVER_NEGATIVE_EVIDENCE",
    "forbidden_outputs": [
      "BUY",
      "SELL",
      "ranking",
      "sizing",
      "order_intent",
      "paper_eligibility",
      "live_eligibility",
      "deployment_readiness"
    ]
  },
  "layers": {
    "L0": {
      "owner_scope": [
        "collectors",
        "backfill",
        "scheduler",
        "raw_integrity",
        "shard_state",
        "source_progress"
      ],
      "active_entrypoints": [
        "scripts/run_l0_public_newswire_sharded_backfill.py",
        "scripts/aggregate_l0_public_newswire_shards.py",
        "scripts/control_l0_public_newswire_acceleration.ps1",
        "scripts/run_l0_public_newswire_sharded_progress_monitor.ps1"
      ],
      "active_validators": [
        "scripts/validate_l0_public_newswire_sharded_backfill.py",
        "tests/test_l0_public_newswire_sharded_backfill.py"
      ],
      "active_reports": [
        "docs/reports/task_4159_l0_public_newswire_controlled_acceleration/"
      ],
      "current_status": {
        "public_newswire_backfill": "RUNNING",
        "completed_units": 1953,
        "total_units": 4101,
        "pending_units": 2148,
        "progress_pct_approx": 47.6,
        "workers": {
          "BusinessWire": 2,
          "GlobeNewswire": 1,
          "PRNewswire": 1
        },
        "controller_decision": "BW4_BLOCKED"
      }
    },
    "L1": {
      "owner_scope": [
        "row_article_packetization",
        "source_lineage",
        "raw_path_hash",
        "source_time",
        "available_to_brain_time",
        "mapping_status",
        "blocker_status"
      ],
      "known_task": "TASK-4138",
      "active_entrypoints": [],
      "active_validators": [],
      "local_resolution_required": true,
      "notes": [
        "Exact L1 script and validator filenames were not provided in the TASK-4160 packet.",
        "Codex must fill exact local paths after local inspection.",
        "Do not treat incomplete L0 backfill coverage as negative evidence."
      ]
    },
    "L2": {
      "owner_scope": [
        "event_primitive",
        "admission_view",
        "diagnostic_materialization_candidate",
        "dedup",
        "entity_ticker_mapping",
        "stale_metadata",
        "effect_window_metadata"
      ],
      "known_task": "TASK-4147",
      "known_configs": [
        "configs/l0_realtime_operational_safe_config_4147.json"
      ],
      "active_entrypoints": [],
      "active_validators": [],
      "local_resolution_required": true,
      "notes": [
        "Exact L2 script and validator filenames were not provided in the TASK-4160 packet.",
        "Codex must separate legacy news code from current L2 event primitive/admission pipeline.",
        "L2 must not emit final signal, score, ranking, order intent, or trading eligibility."
      ]
    },
    "L3": {
      "owner_scope": [
        "relation_graph",
        "event_clusters",
        "relation_quality",
        "coverage_gaps",
        "diagnostic_strategy_view"
      ],
      "active_entrypoints": [
        "scripts/build_l3_diagnostic_strategy_view_4150.py",
        "scripts/build_l3_relation_graph_v2_4152.py",
        "scripts/build_l3_relation_graph_quality_guard_4154.py"
      ],
      "active_validators": [
        "LOCAL_CORRESPONDING_L3_VALIDATORS_TO_BE_CONFIRMED"
      ],
      "notes": [
        "Graph count is not evidence quality.",
        "L3 output is diagnostic only.",
        "No trading signal, ranking, sizing, order intent, or eligibility."
      ]
    },
    "L4": {
      "owner_scope": [
        "diagnostic_thesis_bundle",
        "evidence_stitching",
        "lineage_review",
        "coverage_gap_review",
        "contradiction_status",
        "blocker_status"
      ],
      "active_entrypoints": [
        "scripts/build_l4_thesis_bundles.py"
      ],
      "active_validators": [
        "scripts/validate_l4_thesis_bundle_package.py"
      ],
      "notes": [
        "L4 is diagnostic thesis bundle assembly only.",
        "No buy/sell/hold, ranking, sizing, order intent, paper/live eligibility, or deployment readiness."
      ]
    }
  },
  "do_not_edit_now": [
    "running L0 backfill scripts",
    "TASK-4159 controller and monitor scripts",
    "L0 shard state, lock, pid, or progress files",
    "legacy L2/news code",
    "old task reports except to read them",
    "large dirty or unrelated files",
    "database migrations",
    "scheduler framework",
    "broker, order, paper, live, or deployment code"
  ]
}
8. Codex가 피해야 할 파일/영역
8.1 읽기는 가능하지만 수정 금지
파일/영역	이유
scripts/run_l0_public_newswire_sharded_backfill.py	L0 backfill RUNNING 상태에서 수정 리스크 큼
scripts/aggregate_l0_public_newswire_shards.py	TASK-4159 산출 안정화 영역
scripts/validate_l0_public_newswire_sharded_backfill.py	현재 validator passed 상태 유지 필요
scripts/control_l0_public_newswire_acceleration.ps1	controller decision 생성 중
scripts/run_l0_public_newswire_sharded_progress_monitor.ps1	monitor가 ongoing status 작성 중
tests/test_l0_public_newswire_sharded_backfill.py	TASK-4160 목적은 테스트 변경이 아님
docs/reports/task_4159_l0_public_newswire_controlled_acceleration/*	실행 중인 L0 상태/결정 기록. 수정 금지, 읽기만
configs/l0_realtime_operational_safe_config_4147.json	L0/L2 operational safe config. 구조 정리에서 건드릴 이유 없음
scripts/build_l3_diagnostic_strategy_view_4150.py	active L3 entrypoint
scripts/build_l3_relation_graph_v2_4152.py	active L3 entrypoint
scripts/build_l3_relation_graph_quality_guard_4154.py	active L3 quality guard
scripts/build_l4_thesis_bundles.py	active L4 builder
scripts/validate_l4_thesis_bundle_package.py	active L4 validator
8.2 이번 작업에서 명시적으로 금지
금지 작업	이유
old reports 삭제	어떤 report가 아직 audit trail인지 확실하지 않음
task-specific scripts rename	future reference와 validator가 깨질 수 있음
L0 shard/lock/progress 파일 편집	RUNNING backfill 방해 가능
PRNewswire offset/range split	현재 명시적으로 prohibited
BW concurrency 추가 변경	TASK-4160은 구조 정리 작업이지 가속 작업이 아님
legacy L2/news code 정리	범위 초과. 잘못 건드리면 L2 current pipeline과 혼동 심화
Airflow/Celery/K8s/DB migration	과도한 구조 변경
신규 validator framework	지금은 manifest 문법 확인 + 기존 validator 실행이면 충분
BUY/SELL/ranking/sizing/order 관련 필드 추가	hard state 위반 가능성
9. Validator Checklist
9.1 Manifest 자체 검증
체크	명령/방법	기대 결과
JSON syntax	python -m json.tool docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_manifest.json	parse success
hard state 포함 여부	manifest 수동 확인	NOT_ACCEPTED / FORBIDDEN / diagnostic-only 포함
forbidden outputs 포함 여부	manifest 수동 확인	BUY/SELL/ranking/sizing/order/paper/live/deployment 금지 명시
L1/L2 unknown 파일명 처리	manifest 수동 확인	없는 파일명을 임의로 만들지 않았는지 확인
9.2 L0 검증
Validator	기대 결과
python scripts/validate_l0_public_newswire_sharded_backfill.py	pass
python -m pytest tests/test_l0_public_newswire_sharded_backfill.py	pass
TASK-4159 controlled_acceleration_decision.json 확인	validator_passed: true, safety_closed: true 유지
PID/dead lock check	dead RUNNING lock 없음
active offset misclassification check	active offset을 completed로 잘못 분류하지 않음
9.3 L1 검증

제공 패킷상 exact validator path는 없습니다. Codex는 로컬에서 기존 TASK-4138 검증 스크립트를 확인해 실행해야 합니다.

체크	기대 결과
TASK-4138 L1 validation 재실행	validation_failures: []
source family policy rows	source_family_policy_rows: 5 유지
trading authority	trading_authority_opened: false
feature allowed now	feature_allowed_now_rows: []
L0 incomplete 처리	UNKNOWN/BLOCKER, negative evidence 아님
9.4 L2 검증

제공 패킷상 exact L2 validator path는 없습니다. Codex는 TASK-4147 계열 L2 validator를 로컬에서 확인해야 합니다.

체크	기대 결과
L1 article packets	l1_article_packets: 1093 수준의 기존 상태와 불필요한 퇴행 없음
L1 ready packets	l1_article_ready_packets: 1093
raw packet blockers	raw_article_packet_blockers: 0
L2 diagnostic feature rows	l2_diagnostic_feature_rows: 1842 수준의 기존 상태와 불필요한 퇴행 없음
trading eligible	trading_eligible_rows: 0
signal/order export allowed	signal_order_export_allowed_rows: 0
broker mutation permitted	broker_mutation_permitted_rows: 0
9.5 L3 검증
Validator	기대 결과
Corresponding validator for build_l3_diagnostic_strategy_view_4150.py	pass
Corresponding validator for build_l3_relation_graph_v2_4152.py	pass
Corresponding validator for build_l3_relation_graph_quality_guard_4154.py	pass
Manual semantic check	graph count를 evidence quality로 사용하지 않음
Safety check	signal/ranking/sizing/order eligibility 없음
9.6 L4 검증
Validator	기대 결과
python scripts/validate_l4_thesis_bundle_package.py	pass
forbidden field check	recommendation, policy_action, final_score, target_weight, position_size 없음
semantic authority check	buy/sell/hold/ranking/sizing/order/paper/live/deployment readiness 없음
blocker/coverage/contradiction check	diagnostic review field로만 존재
10. Rollback / Stop Criteria

TASK-4160은 파일 2개 생성 작업이므로 rollback도 단순해야 합니다.

상황	조치
L0 validator fail	TASK-4160 변경 중단. L0 파일 수정 여부 확인. 생성한 manifest/handoff는 보류
JSON parse fail	manifest 수정 후 재검증
L1/L2 파일명을 Codex가 추정으로 채움	즉시 수정. unknown은 unknown으로 둬야 함
기존 코드 파일이 변경됨	revert. TASK-4160은 코드 수정 작업이 아님
running lock/progress 파일 변경됨	즉시 중단. L0 monitor/controller 상태 확인
manifest가 BUY/SELL/ranking/sizing/order 관련 항목을 output으로 허용	즉시 fail 처리
11. Codex 실행 지시문
TASK-4160 L0-L4 Structure Cleanup

Use only the current local working copy. Do not use GitHub as source of truth.

Goal:
Create a low-overhead active handoff index for L0-L4 so future Codex runs read the correct active files first and do not confuse legacy/superseded files with current layer ownership.

Hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is UNKNOWN/BLOCKER, never negative evidence
- No BUY/SELL/ranking/sizing/order/paper/live/deployment recommendation

Create only:
1. docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_handoff.md
2. docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_manifest.json

Do not edit, move, rename, or delete existing code/report/data files.

The handoff markdown must include:
- hard state
- current L0 running state
- L0-L4 ownership matrix
- active entrypoints by layer
- active validators by layer
- active reports/handoff outputs
- legacy/superseded/read-only rules
- explicit do-not-do list
- unresolved local resolution items for exact L1/L2 script paths if not safely identifiable

The JSON manifest must include:
- hard_state
- per-layer owner_scope
- active_entrypoints
- active_validators
- active_reports/configs where known
- forbidden outputs
- local_resolution_required for L1/L2 if exact script names are not confirmed
- do_not_edit_now list

Known exact active files:
L0:
- scripts/run_l0_public_newswire_sharded_backfill.py
- scripts/aggregate_l0_public_newswire_shards.py
- scripts/validate_l0_public_newswire_sharded_backfill.py
- scripts/control_l0_public_newswire_acceleration.ps1
- scripts/run_l0_public_newswire_sharded_progress_monitor.ps1
- tests/test_l0_public_newswire_sharded_backfill.py
- docs/reports/task_4159_l0_public_newswire_controlled_acceleration/

L3:
- scripts/build_l3_diagnostic_strategy_view_4150.py
- scripts/build_l3_relation_graph_v2_4152.py
- scripts/build_l3_relation_graph_quality_guard_4154.py
- corresponding local L3 validators

L4:
- scripts/build_l4_thesis_bundles.py
- scripts/validate_l4_thesis_bundle_package.py

Known L2 config:
- configs/l0_realtime_operational_safe_config_4147.json

Important:
Do not invent exact L1/L2 script names. If exact files are not safely identifiable, mark local_resolution_required=true and explain that future Codex must fill exact local paths after local inspection.

Validation:
- python -m json.tool docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_manifest.json
- python scripts/validate_l0_public_newswire_sharded_backfill.py
- python -m pytest tests/test_l0_public_newswire_sharded_backfill.py
- run existing local L1 TASK-4138 validator if identifiable
- run existing local L2 TASK-4147 validator if identifiable
- run corresponding local L3 validators if identifiable
- python scripts/validate_l4_thesis_bundle_package.py

Success criteria:
- Only the two TASK-4160 files are created/edited.
- JSON manifest parses.
- No running L0 backfill/controller/monitor code or state is modified.
- No trading authority is opened.
- Future Codex can identify active L0-L4 entrypoints, validators, reports, and forbidden legacy areas from the handoff files.
12. 사용자용 쉬운 요약
질문	답
지금 구조 정리가 필요한가?	필요함. 파일이 많아져서 Codex가 잘못된 파일을 읽을 위험이 있음
어떻게 정리해야 하나?	파일을 옮기지 말고, 현재 정본 파일 목록을 문서와 JSON으로 고정
몇 개 파일을 만들면 되나?	우선 2개: active_layer_handoff.md, active_layer_manifest.json
코드도 고쳐야 하나?	아니오. 이번 작업은 코드 수정이 아니라 active index 생성
L0 백필에는 영향 있나?	없어야 함. L0 runner/controller/monitor/state 파일은 수정 금지
L1/L2 파일명은 어떻게 하나?	GPT가 임의로 만들면 안 됨. Codex가 로컬에서 실제 파일명만 확인해서 채워야 함
지금 하지 말아야 할 것	파일 이동, 삭제, rename, legacy L2 정리, PR split, BW 추가 가속, 신규 framework 도입
최종 판정	CONDITIONAL PASS — 얇은 handoff/manifest 방식으로 하면 안전하고 실용적임
# GPT Pro Consult Prompt - TASK-4189 Project Structure Cleanup

You are an expert panel for the minjo1009/Stock-Investment project.

Required expert roles:
- Principal Project Architect
- Technical Program Manager for complex research systems
- Repository Governance Engineer
- Data/ML Platform Architect
- Trading-system Safety Reviewer

Required GPT mode:
- Agent Mode with GitHub enabled for minjo1009/Stock-Investment
- Inspect the repository before answering.
- Do not use Deep Research unless you need current external best practices; this is primarily repo-architecture work.

User goal:
The user says the project root and repository structure are disorganized. They want a durable system for file/folder management so Codex does not keep creating scattered scripts, skills, harnesses, reports, wiki notes, Graphify outputs, Obsidian notes, task logs, and duplicate root folders. They want safe deletion or trash/archive movement where appropriate, no duplicate root axes, clear layer/function separation, and persistent governance so this stays clean without repeated manual intervention.

Current local evidence from Codex TASK-4188/TASK-4189:
- ops/project_hygiene_policy.yaml classifies root entries and makes new unclassified root clutter fail validation.
- scripts/ops/validate_project_hygiene.py is wired into scripts/ops/validate_codex_closeout.py.
- TASK-4189 deleted only .pytest_cache as safe transient cache.
- Current duplicate axes needing expert review:
  - config vs configs: keep configs canonical until imports prove otherwise.
  - apps vs frontend: likely keep apps canonical for app surfaces; review frontend.
  - .obsidian vs docs/obsidian: .obsidian is local app state; docs/obsidian is repo cockpit.
  - tasks vs ops/task_registry.yaml: registry is canonical; legacy tasks needs archive or migration.
- Current docs surfaces marked REVIEW:
  - docs/acceptance
  - docs/active
  - docs/audits
  - docs/candidate_funnel
  - docs/context
  - docs/contracts
  - docs/db
  - docs/execution
  - docs/frontend_ios
  - docs/frontend_web
  - docs/graphify
  - docs/harness
  - docs/logs
  - docs/specs
- Canonical or keep surfaces:
  - AGENTS.md
  - ops/**
  - docs/operating_system/**
  - docs/architecture/**
  - docs/ownership/**
  - docs/generated_context/**
  - docs/reports/task_*/**
  - docs/llm_wiki/** as routing memory only
  - docs/obsidian/** as human cockpit only
  - docs/frontend_app_ssot/** for frontend SSOT

Hard project state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence
- GPT is advisory only; repo SSOT and validators remain source of truth.

What I need from you:
1. Propose a durable target repository tree for this project, grouped by layer and function.
2. Decide which root-level axes should be canonical and which should become archived, local-only, or deleted.
3. Give a concrete cleanup decision matrix for the duplicate axes and REVIEW docs surfaces above.
4. Define a safe trash/archive policy. Include when to delete, when to move to docs/archive, when to move to a local ignored folder, and when to block.
5. Define closeout validators or registry checks Codex should add so future tasks cannot recreate clutter.
6. Identify P0/P1 risks in deleting or moving the listed surfaces.
7. Give Codex a small next patch plan that is safe to implement now without touching broker, live trading, strategy logic, raw data, DB schema, or secrets.

Output format:
1. Architecture Diagnosis
2. Target Repository Tree
3. Canonical vs Archive/Delete Decisions
4. Cleanup Decision Matrix
5. Persistent Governance / Validators
6. P0/P1 Risks
7. Codex Patch Plan
8. Validation Checklist
더 보기

먼저 GitHub의 실제 루트·문서·ops 구조와 hygiene/closeout 파일을 확인한 뒤, 로컬 TASK-4188/4189 증거를 우선해 안전한 정리안을 제시하겠습니다. 삭제·이동보다 canonical axis, archive 정책, clutter 차단 validator, 즉시 가능한 작은 패치 범위를 분리하겠습니다.

GitHub main에는 기존 거버넌스 문서가 있으나 새 hygiene policy는 아직 없으므로, 로컬 최신 증거와 stale GitHub 상태를 분리해 판단하겠습니다. 과거 task registry 축과 새 ops registry 축의 공존은 별도 위험으로 보겠습니다.

사용 가능한 도구 찾는 중
8m 57s 동안 생각함
핵심 3줄 요약

판정: CONDITIONAL PASS. 지금은 대량 이동/삭제가 아니라, ops/project_hygiene_policy.yaml 중심의 root/docs/scripts governance를 강화하는 작은 패치가 맞습니다.

**canonical root 축은 ops, configs, src, scripts, tests, tools, apps, docs, data, skills**로 고정하고, config, frontend, .obsidian, tasks는 각각 legacy/local/archive/migration 대상으로 분리해야 합니다.

삭제는 cache/transient만, 나머지는 dependency check 후 docs/archive/** 또는 local ignored folder로 보내야 합니다. 특히 tasks, frontend, docs/acceptance, docs/db, docs/contracts는 바로 삭제하면 P0 리스크가 있습니다.

1. Architecture Diagnosis
판정
항목	판정
구조 정리 필요성	PASS
대량 이동/삭제	FAIL
root clutter validator	PASS
docs surface registry 추가	PASS
지금 가능한 안전 패치	P0/P1 governance-only patch
전략/배포/실거래 상태 변경	금지

GitHub main을 확인한 결과, 저장소는 이미 “작은 변경, 검증 가능한 결과, 저토큰 read order, task report/manifest/registry closeout”를 강하게 요구하고 있습니다. AGENTS.md는 비자명 작업 전 최소 read order를 project_operating_state.md와 관련 task report로 제한하고, broad governance 작업에서만 architecture/ownership/task registry를 열도록 규정합니다. 또한 small change, surgical change, artifact discipline, closeout discipline을 명시합니다.

문제의 본질은 “파일이 많다”가 아니라 current/canonical/legacy/local/generated의 구분이 root와 docs 1-depth에서 강제되지 않는 것입니다. GitHub의 Task745 inventory도 docs, src, tests, tasks, scripts, frontend, skills 표면이 이미 크고, needs_owner_review가 1,066개라고 보고합니다. 동시에 cleanup 단계에서는 “delete/move 금지, classification first”가 명시되어 있습니다.

따라서 TASK-4189의 올바른 방향은 repository reorganization이 아니라 repository governance hardening입니다. 즉, 먼저 “어느 root/docs surface가 canonical인지”를 정책 파일과 validator로 고정하고, 이동/삭제는 별도 migration task에서 dependency evidence가 있을 때만 해야 합니다.

2. Target Repository Tree

아래는 durable target tree입니다. 즉시 모두 이동하라는 뜻이 아니라, 신규 파일 생성·이동·archive 판단의 기준축입니다.

Stock-Investment/
├── AGENTS.md
├── README.md
├── pyproject.toml / package manager files / lock files
│
├── ops/
│   ├── project_hygiene_policy.yaml
│   ├── task_registry.yaml
│   ├── registries/
│   ├── validators/
│   ├── closeout/
│   └── archive_policy.yaml
│
├── configs/
│   ├── runtime/
│   ├── sources/
│   ├── scheduler/
│   ├── frontend/
│   └── local/                  # ignored env/local overrides only
│
├── src/
│   ├── brain/                  # L3-L6 contracts/adapters/read-model bridge
│   ├── data/                   # normalized data interfaces, source evidence helpers
│   ├── infra/                  # accelerators, external tool wrappers
│   ├── backtest/               # diagnostic replay/backtest engines and historical builders
│   ├── app/                    # runtime app entrypoints
│   ├── execution/              # broker/execution interfaces, no real-capital permission
│   ├── integration/            # KIS/Slack/provider clients
│   ├── market/
│   ├── reporting/
│   ├── risk/
│   ├── state/
│   └── strategy/               # interfaces only; not strategy acceptance
│
├── scripts/
│   ├── ops/                    # governance, closeout, hygiene, registry validators
│   ├── l0/                     # collectors/backfill/raw integrity runners
│   ├── l1/                     # packetization/lineage/mapping/blocker builders
│   ├── l2/                     # primitive/admission/materialization-candidate builders
│   ├── l3/                     # relation graph/cluster/quality/coverage validators
│   ├── l4/                     # diagnostic thesis bundle builders/validators
│   ├── db/                     # DB tooling wrappers when not under tools/db
│   ├── frontend/               # read-model/catalog/screenshot/storybook helpers
│   └── task_scoped/            # future task scripts only if registered
│
├── tools/
│   └── db/                     # DB authority/health/snapshot/restore/source tooling
│
├── tests/
│   ├── package/                # PACKAGE_HEALTH
│   ├── governance/             # GOVERNANCE_HEALTH
│   ├── data/                   # DATA_HEALTH
│   ├── research/               # RESEARCH_ONLY
│   ├── execution/              # EXECUTION_HEALTH, owner-specific
│   ├── reporting/              # REPORTING_HEALTH
│   └── historical/             # EVIDENCE_ONLY; not fast gate
│
├── apps/
│   └── ios-trader-brain/       # active frontend app root
│
├── docs/
│   ├── operating_system/       # current operating rules/runbooks
│   ├── architecture/           # canonical maps and layer boundaries
│   ├── ownership/              # readiness, owners, operating model
│   ├── contracts/              # typed/behavioral contracts
│   ├── acceptance/             # acceptance/deployment contracts; authority-sensitive
│   ├── db/                     # DB topology/scheduler/retention/authority docs
│   ├── frontend_app_ssot/      # active frontend SSOT
│   ├── generated_context/      # generated context, routing only unless promoted
│   ├── llm_wiki/               # short routing memory only
│   ├── obsidian/               # human cockpit only
│   ├── reports/
│   │   └── task_*/             # task reports, small manifests, decision files
│   └── archive/
│       └── task_4189_project_structure_cleanup/
│
├── data/
│   ├── samples/                # tiny tracked fixtures only
│   ├── raw/                    # ignored raw source data
│   ├── artifacts/              # ignored large derived outputs
│   ├── cache/                  # ignored
│   ├── panels/                 # ignored
│   └── snapshots/              # ignored
│
├── skills/
│   └── ...                     # operating procedures, never hidden strategy engine
│
└── local-only ignored surfaces:
    .obsidian/
    .pytest_cache/
    .mypy_cache/
    .ruff_cache/
    .cache/
    .codex/
    .venv/
    logs/
    runs/
    outputs/
    downloads/
    graphify-out/
    artifacts/
    frontend_data/

이 tree는 GitHub의 현재 architecture와도 맞습니다. README.md는 저장소를 raw source → economic meaning → relation graph → thesis → validation → paper/shadow review → deployment gate로 설명하고, src, tools/db, scripts, docs/reports, docs/llm_wiki, docs/obsidian, docs/db, data/artifacts, data/raw, tasks/task_registry.csv를 repository map으로 둡니다.

또한 brain_layer_map.md는 L0-L7 operating stack을 이미 정의하고, L0-L2/L3/L4/L5/L6/L7의 권한 경계를 구분합니다. 특히 L0-L2는 buy/sell/rank/size/exit 금지, L4는 thesis/blocker/invalidation까지만 허용, L6만 runtime/paper/shadow/broker-truth gate를 다룰 수 있습니다.

3. Canonical vs Archive/Delete Decisions
3.1 Root-level axes
Root axis	Decision	Canonical target	Action
ops/	KEEP CANONICAL	ops/**	governance policy, registry, closeout validators의 canonical home
configs/	KEEP CANONICAL	configs/**	config/보다 우선. env/local override는 ignored
config/	LEGACY / MIGRATE / THEN ARCHIVE	configs/** or local ignored	import/reference check 전 삭제 금지
src/	KEEP CANONICAL	src/**	backend/package/research code home
scripts/	KEEP, BUT GOVERN	scripts/{ops,l0,l1,l2,l3,l4,db,frontend,task_scoped}	신규 root-level scripts/*.py는 validator로 제한
tests/	KEEP, BUT GOVERN	authority-tagged tests	fast gate와 owner-specific gate 분리
tools/	KEEP CANONICAL	tools/db/**	DB tooling canonical
apps/	KEEP CANONICAL	apps/ios-trader-brain/**	frontend app root canonical
frontend/	LEGACY READ-ONLY / MIGRATE OR ARCHIVE	apps/** or docs/archive/**	신규 app work 금지. reference check 후 archive
.obsidian/	LOCAL-ONLY	local ignored	repo truth 금지. 의미 있는 노트는 docs/obsidian/**
docs/obsidian/	KEEP HUMAN COCKPIT	docs/obsidian/**	navigation only, SSOT 아님
tasks/	LEGACY / MIGRATION REQUIRED	ops/task_registry.yaml	GitHub docs still reference tasks/task_registry.csv; 즉시 삭제 금지
docs/	KEEP CANONICAL WITH SUB-SURFACE REGISTRY	see matrix below	1-depth docs surface를 policy로 분류
data/	KEEP MIXED: samples tracked, rest ignored	data/samples, data/raw, data/artifacts	raw/artifacts/cache는 Git 제외
skills/	KEEP OPERATING PROCEDURES	skills/**	skill은 전략 엔진이 아님
root artifacts/, outputs/, runs/, downloads/, logs/, graphify-out/	LOCAL-ONLY / DELETE IF TRANSIENT	ignored local	Git tracked이면 review 필요

GitHub의 .gitignore도 이 방향과 일치합니다. .pytest_cache, .coverage, htmlcov, .obsidian workspace/cache/plugins, logs, env, raw/artifact/cache/panel/snapshot data, root artifacts/outputs/runs/downloads/graphify-out/frontend_data 등이 ignored 대상입니다.

3.2 Important correction: tasks/ migration

로컬 TASK-4188/4189 기준으로 ops/task_registry.yaml이 canonical이라면, 새 기준은 ops/task_registry.yaml이 맞습니다. 다만 GitHub main의 AGENTS.md, README.md, current_operating_model.md, work_closeout_protocol.md, llm_wiki는 아직 tasks/task_registry.csv를 참조합니다.

따라서 tasks/는 바로 삭제 금지입니다. 순서는 아래가 안전합니다.

ops/task_registry.yaml canonical 확정.

scripts/ops/validate_codex_closeout.py가 YAML registry를 읽는지 확인.

기존 docs의 tasks/task_registry.csv 참조를 ops/task_registry.yaml로 바꾸는 별도 migration task.

tasks/README.md에 “legacy registry mirror / no new task logs” 선언.

dependency validator 통과 후 tasks/를 docs/archive/...로 이동하거나, registry mirror만 남김.

4. Cleanup Decision Matrix
4.1 Duplicate axes
Surface	Current issue	Decision	Immediate action	Later action	Risk
config vs configs	duplicate config axis	configs canonical	validator에 config/ 신규 생성/성장 금지 추가	grep/import check 후 config/ 파일을 configs/ 또는 local ignored로 이동	P0 if imported
apps vs frontend	app root duplicate	apps canonical	frontend/는 legacy read-only로 mark	no refs 확인 후 docs/archive/.../frontend_legacy/	P1/P0 if scripts rely on it
.obsidian vs docs/obsidian	app state vs repo cockpit 혼동	.obsidian local-only, docs/obsidian cockpit	.obsidian/** tracked 파일 차단. workspace/cache/plugins 삭제 가능	의미 있는 노트만 docs/obsidian으로 수동 이동	P1 human workflow
tasks vs ops/task_registry.yaml	old registry path vs new canonical registry	ops/task_registry.yaml canonical, tasks legacy	tasks/ 신규 task log 금지. docs 참조 migration 계획 작성	validator/docs/scripts가 모두 YAML 기준이면 archive	P0 if deleted now
docs/llm_wiki vs docs/generated_context	routing memory vs generated context	둘 다 keep, authority 분리	llm_wiki는 routing only, generated_context는 generated only	stale generated context는 archive/local ignored	P1 stale context
docs/graphify vs graphify-out	repo note vs generated output	graphify-out local-only, docs/graphify read-only/archive	Graphify를 current state로 쓰지 못하게 validator 문구	stale docs/graphify archive	P1 stale evidence

docs/frontend_app_ssot와 apps/ios-trader-brain은 이미 GitHub에서 active frontend axis로 정리되어 있습니다. Frontend SSOT는 app root를 apps/ios-trader-brain으로 고정하고, 임의 app root 생성을 막는 목적이라고 설명합니다. 또 implementation architecture는 preferred path를 apps/ios-trader-brain으로 명시합니다.

4.2 REVIEW docs surfaces
Docs surface	Decision	Rationale	Immediate policy
docs/acceptance	KEEP CANONICAL / AUTHORITY-SENSITIVE	strategy/deployment contracts are referenced as canonical in operating model	이동/삭제 금지
docs/active	ARCHIVE CANDIDATE	이름이 모호하고 SSOT 축과 중복 가능	no new writes; migrate active content to operating_system/architecture/reports
docs/audits	KEEP IF CROSS-TASK AUDIT; ELSE REPORT/ARCHIVE	audit trail은 가치 있음. task-specific이면 reports로	README/manifest 요구
docs/candidate_funnel	ARCHIVE CANDIDATE	likely old domain-specific lane	registry refs 없으면 archive
docs/context	MIGRATE/ARCHIVE	llm_wiki/generated_context와 중복	no new writes
docs/contracts	KEEP CANONICAL	typed/behavioral contracts canonical	유지
docs/db	KEEP CANONICAL	README가 DB topology/scheduler/retention/authority docs로 지정	유지
docs/execution	KEEP WITH AUTHORITY BOUNDARY	execution/risk docs may be safety-critical	live/broker permission wording validator 필요
docs/frontend_ios	ARCHIVE/MIGRATE TO frontend_app_ssot	active frontend SSOT already exists	no new writes
docs/frontend_web	ARCHIVE / DESIGN EVIDENCE ONLY	prior web pack retained as design/migration evidence only	no new implementation work
docs/graphify	READ-ONLY / ARCHIVE CANDIDATE	stale Graphify must not be current state	no current-state refs
docs/harness	MIGRATE SELECTIVELY	active harness discipline belongs in operating_system/contracts/reports	no new writes unless README defines scope
docs/logs	LOCAL/ARCHIVE, NOT CANONICAL DOCS	raw logs should be ignored logs/; summaries go reports	block new docs/logs
docs/specs	MIGRATE/ARCHIVE UNLESS ACTIVE SPEC INDEX EXISTS	specs duplicate architecture/contracts/frontend SSOT	no new specs without registry row

current_operating_model.md already says Graphify output must not be used as current state unless regenerated after the relevant task family, and stale Graphify is not current truth.

5. Persistent Governance / Validators
5.1 Extend ops/project_hygiene_policy.yaml

Add these sections if not already present:

YAML
root_policy:
  canonical_dirs:
    - ops
    - configs
    - src
    - scripts
    - tests
    - tools
    - apps
    - docs
    - data
    - skills

  canonical_files:
    - AGENTS.md
    - README.md
    - .gitignore
    - pyproject.toml
    - package.json
    - package-lock.json
    - pnpm-lock.yaml
    - yarn.lock
    - tsconfig.json

  legacy_root_dirs:
    config:
      decision: migrate_to_configs_or_local_ignored
      new_files_allowed: false
    frontend:
      decision: legacy_read_only_migrate_to_apps_or_archive
      new_files_allowed: false
    tasks:
      decision: legacy_registry_migration_to_ops_task_registry_yaml
      new_files_allowed: false

  local_only_dirs:
    - .obsidian
    - .pytest_cache
    - .mypy_cache
    - .ruff_cache
    - .cache
    - .codex
    - .venv
    - logs
    - runs
    - outputs
    - downloads
    - graphify-out
    - artifacts
    - frontend_data
5.2 Add docs surface policy
YAML
docs_surface_policy:
  canonical:
    operating_system: current_operating_rules
    architecture: canonical_maps
    ownership: owners_readiness_registry
    contracts: contracts
    acceptance: authority_sensitive_acceptance_contracts
    db: db_authority_docs
    frontend_app_ssot: frontend_single_source_of_truth
    reports: task_reports
    generated_context: generated_context
    llm_wiki: routing_memory_only
    obsidian: human_cockpit_only
    archive: archived_superseded_material

  review_no_new_writes:
    - active
    - candidate_funnel
    - context
    - frontend_ios
    - frontend_web
    - graphify
    - harness
    - logs
    - specs

  conditional_keep:
    audits:
      rule: keep_only_if_cross_task_audit_or_has_manifest
    execution:
      rule: keep_with_no_live_no_broker_no_acceptance_boundary
5.3 Validator checks Codex should add
Validator/check	Rule	Failure condition
root classification	every root child must be canonical, legacy, local-only, or blocked	unclassified root entry
duplicate root axis guard	config, frontend, tasks cannot grow	new files under legacy axis
docs surface registry	every docs/* first-level folder classified	unclassified docs surface
archive manifest	every docs/archive/** move requires manifest	archived file without source/reason/task/dependency check
report discipline	new task reports under docs/reports/task_*	scattered task docs
generated artifact guard	large CSV/JSONL/parquet under docs blocked except allowed manifests/decision/pass_fail	generated panel committed
scripts placement guard	new scripts must be under approved subdir or explicitly task-scoped in registry	new random scripts/foo.py
task registry authority	use ops/task_registry.yaml canonical after migration	new tasks/* task log
Graphify boundary	docs/graphify cannot be current state	current-state reference to stale Graphify
frontend root guard	app code must be under apps/ios-trader-brain	new root frontend app work
local-only guard	.obsidian, caches, logs, DBs, raw data not staged	tracked local state
safety wording guard	cleanup cannot modify strategy/deployment/real-capital	missing hard-state footer

This aligns with existing test authority separation. GitHub’s test map says only PACKAGE_HEALTH and GOVERNANCE_HEALTH are fast local quality-gate candidates; RESEARCH_ONLY, DATA_HEALTH, EXECUTION_HEALTH, REPORTING_HEALTH, and acceptance evidence require owner-specific validation.

6. P0/P1 Risks
P0 risks — do not touch without dependency proof
Risk	Why it is P0	Required mitigation
Delete/move tasks/ now	GitHub docs and validators still reference tasks/task_registry.csv	migrate docs/scripts to ops/task_registry.yaml first
Delete/move docs/acceptance	strategy/deployment contracts are authority-sensitive	keep; only edit with acceptance governance task
Delete/move docs/db	DB topology/scheduler/authority docs may govern runtime safety	keep; owner review required
Delete/move docs/contracts	package/runtime/frontend contracts may be imported by validators/docs	keep
Delete/move config/ blindly	code may import/read config/...	grep/import/config path check
Delete/move frontend/ blindly	legacy scripts, screenshots, package refs may still point there	dependency check + archive manifest
Delete docs/reports/** bulk	task reports are audit trail and registry evidence	never bulk delete; archive only with manifest
Move broker/execution docs/code	may alter safety boundaries or validation paths	out of scope
Touch raw data/DB/schema/secrets	can corrupt evidence or leak secrets	out of scope
P1 risks — manageable, but still require review
Risk	Why it matters	Mitigation
.obsidian local-only enforcement breaks human cockpit	user may rely on vault app state	keep docs/obsidian; only local app state ignored
docs/frontend_ios archive loses design history	may contain useful UX decisions	archive, not delete
docs/frontend_web archive breaks old references	old web pack is migration evidence	keep read-only until refs are updated
docs/graphify archive loses stale but useful context	stale context can still be useful as historical evidence	archive with “not current state” manifest
docs/specs migration breaks links	specs may be linked in reports	use link/reference check
stricter script placement blocks urgent task scripts	Codex may need task-scoped helper	allow scripts/task_scoped/<task_id>/ with registry row
7. Codex Patch Plan
Safe next patch: small, governance-only

Do not move/delete existing code/docs except transient cache. TASK-4189 already deleted .pytest_cache, which is correct.

Patch A — extend hygiene policy

Edit:

ops/project_hygiene_policy.yaml

Add or confirm:

root_policy.canonical_dirs

root_policy.legacy_root_dirs

root_policy.local_only_dirs

docs_surface_policy

archive_policy

new_file_placement_policy

blocked_write_policy

Patch B — extend hygiene validator

Edit:

scripts/ops/validate_project_hygiene.py

Add checks:

- fail unclassified root entries
- fail unclassified docs first-level entries
- fail new files under legacy root dirs unless allowlisted
- fail tracked local-only dirs/files
- fail docs/archive files without archive manifest
- fail new scattered task docs outside docs/reports/task_*/
- fail root config/frontend/tasks growth unless explicitly grandfathered
Patch C — keep closeout wiring

Confirm only:

scripts/ops/validate_codex_closeout.py

It should call:

scripts/ops/validate_project_hygiene.py

No broker, live trading, strategy, DB schema, raw data, or secrets touched.

Patch D — add structure cleanup report

Create:

docs/reports/task_4189_project_structure_cleanup/task_4189_project_structure_cleanup.md
docs/reports/task_4189_project_structure_cleanup/artifact_manifest.csv

Report should include:

- root canonical decisions
- docs surface decisions
- duplicate axis decisions
- no-delete policy
- validator command/results
- hard-state footer
Patch E — optional, low-risk registry note

If local canonical registry is now YAML:

ops/task_registry.yaml

Add TASK-4189 row only if existing closeout convention requires it.

Do not update every old tasks/task_registry.csv reference in this patch unless Codex has already migrated the registry authority. That should be a separate P1 migration task because GitHub main still contains many old references.

8. Validation Checklist
Required
PowerShell
python scripts/ops/validate_project_hygiene.py
python scripts/ops/validate_codex_closeout.py
If local registry is YAML-canonical
PowerShell
python scripts/ops/validate_task_registry.py

or whatever existing local validator is canonical for:

ops/task_registry.yaml
If legacy CSV still participates
PowerShell
python scripts/task_registry_validate.py

GitHub scripts/task_registry_validate.py currently validates tasks/task_registry.csv, requires columns such as task_id, owner_team, canonical_state, strategy_acceptance, key_report, key_artifacts, and fails if no canonical rows exist.

Existing closeout/gov checks, if present locally
PowerShell
python scripts/codeowners_coverage_validate.py
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py

These are the minimum closeout commands listed in the GitHub closeout protocol, but if local TASK-4189 has replaced them with scripts/ops/validate_codex_closeout.py, use the local closeout validator as the umbrella and record any skipped legacy commands with reason.

Manual safety checks
git status --short --branch

Confirm:

- no broker/execution/live/paper/order code changed
- no raw data changed
- no DB/schema changed
- no secrets/env files staged
- no docs/acceptance contract moved
- no docs/db contract moved
- no docs/contracts moved
- no tasks/ deleted
- no frontend/ deleted
- only intended hygiene/report files changed
Required closeout footer
This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.

Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN

GitHub’s authority matrix explicitly says skill/MD cleanup, inventory completion, source-code classification, test classification, governance health, and GPT review do not change strategy acceptance, deployment readiness, or real-capital permission. It also requires cleanup tasks to state that they do not change strategy acceptance, deployment readiness, or real capital.

출처
# GPT Pro Prompt - Project Folder Tree Architecture And Cleanup Execution

You are an expert project architecture and repository operations panel for the minjo1009/Stock-Investment project.

Required expert roles:
- Principal Repository Architect
- Senior Engineering Manager for Trading/Data Systems
- Documentation/Governance Systems Architect
- Python/TypeScript Monorepo Maintainer
- Safe Cleanup/Refactor Reviewer

Required GPT mode:
- Agent Mode with GitHub enabled for minjo1009/Stock-Investment
- Inspect repository files before answering.
- Do not answer as generic best practices. Give repo-specific folder-tree decisions and an execution plan Codex can apply.

User goal:
The user is angry because prior Codex runs kept saying "prepared" or "installed validators" instead of fully cleaning the project. The goal is to define a clear, durable folder-tree architecture, then execute remaining safe folder/file cleanup: renaming, moving, deleting, archiving, and registry updates where appropriate. The user explicitly permits file moves/deletes/renames, but trading safety and source-data safety must remain intact.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence
- DB/source data/secrets/broker/order/live/paper artifacts must not be deleted or moved unless owner-reviewed and task-scoped.

Current local root snapshot as of 2026-07-02:

| Root entry | Current classification / issue |
|---|---|
| .codex/ | local Codex state; contains 10 project skills under .codex/skills/*/SKILL.md; keep flat for Codex discovery unless all references migrate |
| .dvc/, .dvcignore | data versioning metadata/config |
| .obsidian/ | local Obsidian state |
| .env, .kis_token_cache.json, kis_paper.env | local secret/token/env files; do not read/delete |
| AGENTS.md, README.md | root entry docs |
| apps/ | canonical app surface, but very large: about 35,116 files / 6,129 dirs, likely includes dependencies/build output that may need review |
| configs/ | canonical non-secret config |
| data/ | protected data/runtime artifacts; no cleanup without owner review |
| docs/ | docs, reports, architecture, generated context, Obsidian, LLM wiki; about 913 files / 232 dirs |
| frontend/ | legacy-active frontend web surface; about 8,785 files / 492 dirs; still referenced; migrate/archive decision needed |
| logs/ | local logs |
| ops/ | governance registry/policy/context/prompts; current canonical governance |
| schemas/ | contracts |
| scripts/ | automation and validators; about 196 files; many run/validate task scripts and layer wrappers |
| src/ | reusable source code; about 70 files / 32 dirs |
| tasks/ | legacy-active task registry surface; 46 files; code/docs still reference tasks/task_registry.csv / tasks/active_task_registry.csv; migrate/archive decision needed |
| tests/ | tests |
| tools/ | currently tools/db L0/L1 source acquisition package; 21 files |
| trading.db | root local runtime DB known debt; 21.6GB; review before move/delete |
| trading-DESKTOP-2R00TB4.db | root machine-conflict DB known debt; 788MB; review before move/delete |

Recent cleanup already executed:
- TASK-4191: classified frontend/ and tasks/ as legacy-active migration-required, not immediate delete targets; root DB files remain known debt.
- TASK-4192: removed root prompts/; moved readable governance prompts to ops/prompts/; created ops/project_knowledge_surfaces.yaml; registered 10 .codex/skills by layer/profile; added knowledge-surface validator.
- TASK-4194: deleted 36 __pycache__ directories; archived 8 active DESKTOP-2R00TB4 markdown conflict docs under docs/archive/task_4194_desktop_conflict_docs/; added scripts/ops/validate_internal_cleanliness.py.

Current policy files Codex has locally:
- ops/project_structure_policy.yaml
- ops/project_hygiene_policy.yaml
- ops/project_knowledge_surfaces.yaml
- docs/architecture/project_knowledge_surface_map.md
- docs/architecture/skill_md_subagent_canonicalization_map.md
- ops/task_profiles.yaml
- ops/task_registry.yaml
- ops/doc_registry.yaml

Current known validators:
- python scripts/ops/validate_project_hygiene.py
- python scripts/ops/validate_project_structure_policy.py
- python scripts/ops/validate_knowledge_surfaces.py
- python scripts/ops/validate_internal_cleanliness.py
- python scripts/ops/validate_codex_closeout.py --task <TASK_ID>

Observed top file clusters:

| Cluster | Count / meaning |
|---|---:|
| docs/reports | 698 files; task reports dominate docs |
| apps | 35k+ files, 6k+ dirs; inspect for node_modules, build artifacts, generated caches, or app duplication |
| frontend | 8.7k files; legacy-active web frontend/catalog surface, likely candidate for archive/migration |
| scripts/ops | 26 files; governance harness |
| docs/generated_context | 21 files; generated context bundles |
| tools/db | 21 files; L0/L1 source tools with active imports |
| .codex/skills | 10 skills; flat runtime discovery |
| tasks | 46 legacy files; active references remain |

The user wants:
1. A clear folder-tree architecture with levels, not vague "best practices".
2. A decision on each root folder: canonical / local-only / legacy-active-migrate / archive / delete / blocked.
3. A concrete execution sequence for remaining cleanup.
4. Guidance on what Codex can safely move/delete now versus what needs owner review.
5. No "prepared" ending. Codex should apply safe changes after the consult.

Your required output:

1. Recommended final folder tree
   - Level 0 root folders
   - Level 1 per domain
   - Where skills, prompts, harnesses, validators, scripts, source code, data artifacts, docs, reports, generated context, frontend apps, and legacy task records belong

2. Root folder decision table
   - root path
   - desired status
   - action now
   - action later
   - risk if moved/deleted

3. Naming and placement rules
   - scripts/run_*
   - scripts/validate_*
   - task-specific scripts
   - docs/reports/task_*
   - docs/archive
   - .codex/skills
   - ops/prompts
   - tools/db
   - frontend vs apps
   - tasks vs ops/task_registry.yaml

4. Safe immediate cleanup plan Codex should execute now
   - concrete file/folder moves/deletes/archives
   - skip anything unsafe
   - include validators after each phase

5. Migration plan for blocked legacy surfaces
   - frontend/
   - tasks/
   - root DB files
   - giant app folders / possible dependency folders

6. Validator rules Codex should add or harden
   - prevent root alias folders
   - prevent unmanaged __pycache__
   - prevent active DESKTOP conflict docs
   - prevent unmanaged new scripts/prompts/skills/tools
   - enforce docs archive registration

7. A Codex execution prompt
   - Bounded, concrete, and safe
   - Must end with real cleanup and validation, not "prepare for cleanup"

Please be direct. If a folder should not be renamed because import paths are active, say so. If a folder should be archived now, say so. If a move requires a shim, specify exact shims.
더 보기

사장님, 먼저 GitHub에 보이는 현재 구조와 로컬 스냅샷을 대조해서 판단하겠습니다. 로컬 TASK-4191~4194가 GitHub보다 앞서 있을 수 있으니, 최종 결정은 “로컬 증거 우선 + GitHub로 참조 위험 확인” 방식으로 잡겠습니다.

확인 결과, frontend/와 tasks/는 즉시 전체 이동 대상이 아니라 active 참조가 남은 legacy 축입니다. 대신 cache·build 산출물 삭제와 shim/manifest/validator 기반 단계 migration으로 나누겠습니다.

Please restate the final repository architecture decision in ASCII English only. Keep it concise and actionable. Include: final root tree, root decision table, safe immediate cleanup actions, blocked migrations for frontend/tasks/root DBs, validator hardening, and a bounded Codex execution prompt. Do not use Korean or non-ASCII characters because the capture pipeline corrupts Korean text.
Pro 생각 중

Pro 확장
답변 중지
⏎
ChatGPT는 실수를 할 수 있습니다. 중요한 정보는 재차 확인하세요.