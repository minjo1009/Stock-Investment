Task3841 Loop 10 final GPT review prompt.

You are the expert panel for minjo1009/Stock-Investment in Agent Mode with GitHub enabled.

Original user goal:
- Prioritize the next 10 frontend tasks using GPT Agent Mode with GitHub repo reading.
- Then run a safe 10-loop frontend work pass.

Codex result:
- Loop 1: GPT prioritized the next frontend tasks.
- Loop 2: Codex reconciled GPT's plan with local repo and avoided duplicate existing detail routes.
- Loop 3: Chain Detail v1 hierarchy.
- Loop 4: Position Detail v1 hierarchy.
- Loop 5: Order Detail v1 hierarchy.
- Loop 6: Added detail v1 route validator.
- Loop 7: Expanded Storybook coverage validator.
- Loop 8: Hardened screenshot target evidence checks.
- Loop 9: Recaptured Chrome-headless web-preflight screenshots.
- Loop 10: Closeout/report/registry review.

Changed areas:
- Existing detail route display files only.
- Existing QA validators plus one new detail-v1 validator.
- Package scripts.
- Task report artifacts.
- Screenshot artifacts.

Validation:
- npm run typecheck: PASS.
- npm run lint: PASS.
- npm test: PASS.
- npm run validate:detail-v1: PASS.
- npm run validate:story-coverage: PASS.
- python scripts/task_registry_validate.py: PASS.
- git diff --check: PASS.

Hard state:
- Strategy remains NOT_ACCEPTED.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Real Capital remains FORBIDDEN.
- No DB/runtime/API/broker connection.
- No paper/live permission.
- No broker mutation.
- Screenshots remain NOT_AUTHORITY.

Review criteria:
1. Is this safe to close as scaffold-only frontend QA/product-polish work?
2. Any P0/P1 issue before commit?
3. What should be the next frontend phase?

Return:
1. PASS / FAIL / BLOCKED
2. P0/P1/P2 findings
3. Required patch if any
4. Next recommended task
