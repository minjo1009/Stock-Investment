You are an expert panel for the minjo1009/Stock-Investment project.

Required expert roles:
- Principal Expo/React Native Frontend Architect
- Mobile UI QA Reviewer
- Screenshot/Visual QA Engineer
- Trading Governance Reviewer
- Repository Governance Auditor

User goal:
Run 5 GPT-Codex expert loops for the next frontend work. GPT must read Git/repo context and, where relevant, screenshot evidence before planning and reviewing. If screenshots are missing, GPT should say that and make screenshot capture the first evidence-gathering step.

Required GPT mode:
Agent Mode with GitHub enabled for minjo1009/Stock-Investment.

Repository context to inspect first:
- README.md
- AGENTS.md
- docs/operating_system/project_operating_state.md
- docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md
- docs/frontend_app_ssot/11_IMPLEMENTATION_PRECONDITIONS.md
- docs/frontend_app_ssot/22_SCREENSHOT_QA_BASELINE_TARGETS.md
- docs/reports/task_3834_frontend_screenshot_qa_baseline/task_3834_frontend_screenshot_qa_baseline.md
- apps/ios-trader-brain/package.json
- apps/ios-trader-brain/src/qa/screenshot-targets.json
- apps/ios-trader-brain/src/qa/screenshot-qa-validator.mjs

Current repo facts from Codex:
- Latest committed frontend task is Task3834: screenshot target validation, route validation, and screen-boundary validation are runnable.
- `qa:screenshot` currently validates targets only; it does not capture screenshots.
- Screenshot artifacts and visual approval have not occurred.
- Worktree has unrelated dirty operational/paper changes; Codex must not stage or modify them.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence
- Frontend is read-only and NOT_AUTHORITY unless future operating docs explicitly change it.

Task request:
1. Rank the next 5 frontend loops from current repo state.
2. Prefer evidence-first work: actual screenshot capture path, screenshot artifact manifest, visual QA review, then only bounded P0 scaffold repair if evidence supports it.
3. Do not authorize product readiness, backend/source integration, DB access, broker mutation, paper/live, deployment, or real capital.
4. For each loop, define:
   - loop goal
   - files Codex should read
   - allowed write scope
   - forbidden actions
   - validation commands
   - expected artifact/report evidence
5. Decide what Codex should implement in Loop 1 now.
6. Include whether GPT needs screenshots before giving visual feedback. If screenshots are absent, say exactly what screenshots should be captured.

Output format:
1. Task Diagnosis
2. GitHub Files Inspected
3. Screenshot Evidence Status
4. Ranked 5-Loop Plan
5. Loop 1 Codex Implementation Prompt
6. Validation Checklist
7. Safety Boundary Confirmation
