---
name: project-reporting-rule
description: Mandatory project-owner briefing format for every response in the Stock-Investment project. Use for all assistant responses, including status updates, final answers, confirmations, blocked reports, implementation summaries, loop reports, UI/image-heavy work, and GPT-assisted work, so the user can understand current work, completed value, next step, blockers, and token-cost discipline within five seconds.
---

# Project Reporting Rule

## Purpose

Start every response with a short project-owner briefing. This is not a developer log. It must explain user-visible value in business Korean within five seconds.

The opening report must answer:

- What is being worked on now?
- What became possible?
- What comes next?
- What is blocked?

## Mandatory Opening

Every response must start with exactly this shape and stay within 8 lines before the main answer starts:

```text
# 3줄 요약
🛠️ 현재: [지금 무엇을 만들고 있는가]
✅ 완료: [무엇이 가능해졌는가]
🎯 다음: [다음 단계 후 무엇이 가능해지는가]
🚧 차단사항: 없음
```

If blocked, replace the blocker line with:

```text
🚧 차단사항: [문제]
👉 결정 필요: [사용자가 결정해야 할 것]
```

## Opening Block Rules

- This block is mandatory even for short answers.
- Do not replace it with `done / failed / next`.
- Do not add a table or technical report before it.
- Do not mention that the report format is being applied unless the task is about reporting.
- If nothing meaningful changed, say that plainly in user language.
- If the task only answers a question, describe the current work as answering that decision question.
- Keep the opening block in short Korean business language.

Before sending, inspect the opening block. It fails if it contains:

- file names or paths
- function, class, component, or screen names
- task IDs, commit hashes, branch names, or PR numbers
- typecheck, lint, test, build, or validation status
- percentages or estimated completion rates
- internal architecture terms
- fake progress or low-value status wording

If the opening block fails, rewrite it in user language before sending.

## Multi-Loop Reporting

When work was done in multiple loops, repeated passes, review rounds, or user-requested N-step iterations, add a loop summary immediately after the mandatory opening block and before implementation detail.

Use this shape:

```text
🔁 루프별 진행
1. 루프 1: [사용자 관점에서 무엇이 바뀌었는가]
2. 루프 2: [사용자 관점에서 무엇이 바뀌었는가]
```

Rules:

- Keep the mandatory opening block unchanged and within 8 lines.
- Report every loop when the user requested an exact loop count.
- Each loop line must be one short sentence in user language.
- Do not put file names, command names, validation status, commit hashes, task IDs, or internal architecture terms in loop lines.
- If a loop did not create meaningful progress, say `의미 있는 변화 없음` and state why plainly.
- Put technical detail after the loop summary only when useful.

## Token Cost Reporting

For UI, image, screenshot, browser, GPT relay, deep review, large-document, or multi-loop work, include a compact token-cost section after the main result or loop summary.

Use this shape when meaningful:

```text
🧾 토큰/비용 메모
- 소모량: [낮음/보통/높음/매우 높음 또는 가능한 경우 대략치]
- 과소비 원인: [큰 문서, 이미지/스크린샷, GPT 왕복, 브라우저 자동화, 긴 로그 등]
- 절감 조치: [다음부터 줄일 방법]
- 계속 필요했던 이유: [품질/증거/정렬을 위해 필요했는지]
```

Rules:

- Do not invent exact token counts when the runtime did not provide them.
- Prefer calibrated labels: `낮음`, `보통`, `높음`, `매우 높음`.
- If a concrete count is available from a goal/budget tool or runtime metadata, report it as evidence-backed.
- Explain excessive usage honestly, especially for image-heavy UI work, screenshots, GPT loops, broad document reads, or repeated browser retries.
- When usage was higher than necessary, say what will change next time.
- Keep this section short; it is cost governance, not an engineering diary.
- Do not include the token-cost section for trivial replies unless the user asks.

## Style

- Report like a project-owner briefing, not an engineering log.
- Use short Korean unless the user asks otherwise.
- Explain user-visible capability before implementation detail.
- Keep expert detail in repo reports when the work produced one.
- Preserve project hard state: strategy not accepted, deployment not ready, real capital forbidden, no broker mutation, no live order, no paper promotion.

## Examples

Bad:

- Current: Candidate Detail
- Completed: Summary Section
- Next: Evidence Section

Bad:

- Current: Response format migration
- Completed: Skill integration
- Next: Validation automation

Good:

- Current: 투자 후보를 검토하는 화면을 다듬고 있습니다
- Completed: 사용자가 후보가 왜 선택됐는지 볼 수 있습니다
- Next: 사용자가 근거 자료까지 확인할 수 있습니다

Good:

- Current: 자동매매 시스템 상태 확인을 개선하고 있습니다
- Completed: 이상 상태를 더 빨리 발견할 수 있습니다
- Next: 원인까지 추적할 수 있습니다
