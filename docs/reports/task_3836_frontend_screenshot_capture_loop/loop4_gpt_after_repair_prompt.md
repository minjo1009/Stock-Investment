You are the expert review panel for Task3836 Loop 4 after bounded P1 scaffold visual repair.

Repo/screenshot evidence:
- Before captures: `data/artifacts/task_3836_frontend_actual_screenshot_capture/`
- Before contact sheet: `data/artifacts/task_3836_frontend_actual_screenshot_capture/contact_sheet_iphone15_width.png`
- After2 captures: `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/`
- After2 contact sheet: `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/contact_sheet_iphone15_width_after2.png`

Codex changes:
- `apps/ios-trader-brain/src/components/foundation/badge.tsx`
  - Added max-width/flex-shrink safety.
- `apps/ios-trader-brain/src/components/generic/status-row.tsx`
  - Changed status header from horizontal space-between to vertical stack.
  - Added invisible break opportunities for long source/value tokens.

Codex visual finding after repair:
- The repeated right-edge clipped red status badges are no longer visible in the after2 contact sheet.
- Status badges remain visible.
- Long source refs wrap better but still consume vertical space.
- This remains scaffold-only, NOT_AUTHORITY, read-only, not product approval.

Validation already passed before after2 recapture:
- `npm run typecheck`
- `npm run lint`
- `npm run validate:screen-boundary`

Hard boundaries:
- Strategy remains NOT_ACCEPTED.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Real capital remains FORBIDDEN.
- No DB/runtime/KIS/Alpaca/broker connection.
- No broker mutation.
- No order handler.
- No paper/live/deployment/real-capital permission.

Review request:
1. Judge whether the P1 repair is acceptable for scaffold-only visual QA closeout.
2. Identify any P0/P1 remaining issues visible from the described after2 evidence.
3. Decide whether Codex should continue patching UI in this task or stop at closeout.
4. Provide final validation/report requirements.

Output:
1. PASS / FAIL / BLOCKED
2. Remaining P0/P1/P2 findings
3. Continue / Stop decision
4. Required closeout notes
5. Next loop recommendation
