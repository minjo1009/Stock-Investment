You are the expert closeout reviewer for Task3836.

Task summary:
- User requested 5 GPT-Codex expert loops for frontend next work.
- GPT Loop 1 selected screenshot capture as the evidence-first task.
- Codex captured 18 before screenshots under `data/artifacts/task_3836_frontend_actual_screenshot_capture/`.
- GPT reviewed the capture evidence summary and classified right-edge clipped governance/status badges as P1.
- Codex repaired only `Badge` and `StatusRow`.
- Codex recaptured 18 final after2 screenshots under `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/`.
- GPT reviewed after2 and returned PASS, recommending no further UI patch in this task.
- Codex wrote Task3836 closeout docs and artifact manifest.

Changed code files:
- `apps/ios-trader-brain/src/components/foundation/badge.tsx`
- `apps/ios-trader-brain/src/components/generic/status-row.tsx`

New evidence/report files:
- `docs/reports/task_3836_frontend_screenshot_capture_loop/`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/`

Hard boundaries:
- Strategy remains NOT_ACCEPTED.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Real capital remains FORBIDDEN.
- Frontend remains read-only and NOT_AUTHORITY.
- No DB/runtime/KIS/Alpaca/broker connection.
- No broker mutation.
- No order handler.
- No paper/live/deployment/real-capital permission.

Review request:
1. Decide whether Task3836 should stop now.
2. List required validation before commit.
3. List any remaining blocker.
4. State the next recommended frontend task after this closeout.

Output:
1. PASS / FAIL / BLOCKED
2. Stop / Continue
3. Required validation
4. Residual risks
5. Next task
