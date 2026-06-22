You are the expert review panel for minjo1009/Stock-Investment frontend Task3836.

Required expert roles:
- Principal Expo/React Native Frontend Architect
- Mobile UI QA Reviewer
- Screenshot/Visual QA Engineer
- Trading Governance Reviewer

Original user goal:
Run 5 GPT-Codex expert loops. GPT must read Git/repo context and screenshot evidence before planning and feedback.

Repo context:
- Task3834 installed screenshot target validation only.
- Task3836 Loop 2 captured actual screenshot evidence under:
  - `data/artifacts/task_3836_frontend_actual_screenshot_capture/`
  - `data/artifacts/task_3836_frontend_actual_screenshot_capture/screenshot_capture_manifest.json`
  - `data/artifacts/task_3836_frontend_actual_screenshot_capture/contact_sheet_iphone15_width.png`
- 18 PNG captures exist for 9 routes x 2 mobile viewport presets.
- Screenshots are NOT_AUTHORITY and not visual approval.

Codex visual observations from contact sheet:
1. Repeated right-edge clipped red outline status badges appear inside Governance/Scaffold Boundary rows across HOME, BRAIN, PORTFOLIO, ORDERS, SYSTEM and detail screens.
2. Long source/evidence path text appears cramped in the same rows.
3. Bottom tab labels look very small in contact sheet but require per-image confirmation before repair.

Hard boundaries:
- Strategy remains NOT_ACCEPTED.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Real capital remains FORBIDDEN.
- No DB/runtime/KIS/Alpaca/broker connection.
- No broker mutation.
- No order submit/cancel/approve/reject handler.
- No paper/live/deployment/real-capital permission.
- Frontend remains read-only and NOT_AUTHORITY.

Review request:
1. Read the repo context and screenshot artifact paths.
2. Treat the screenshot evidence as actual visual evidence, not source authority.
3. Decide whether the clipped right-edge badges are P0/P1/P2.
4. Decide whether Codex should perform a bounded P0/P1 scaffold repair now in Loop 4.
5. If yes, provide the smallest patch scope and validation commands.
6. If no, recommend report-only closeout and next capture requirements.

Output:
1. PASS / FAIL / BLOCKED
2. Screenshot evidence status
3. P0/P1/P2 findings
4. Files to patch
5. Patch prompt for Codex
6. Continue / Stop decision
