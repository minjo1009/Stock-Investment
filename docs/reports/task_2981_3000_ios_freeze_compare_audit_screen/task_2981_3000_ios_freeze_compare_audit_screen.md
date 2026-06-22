# Task2981-3000 iOS Freeze Compare Audit Screen

## Decision Summary

- Verdict: `frozen_policy_l4_challenger_compare_plan_completed_no_replay`.
- iOS audit screen exposed: `1`.
- Runtime catalog policy compare audit: `1`.
- Governed replay decision: `NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED`.
- Strict as-of status: `BLOCKED`.
- Performance compare allowed now: `0`.
- Replay performed: `0`.
- Paper order intents created: `0`.
- Live orders created: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Task2961-2980 froze the baseline and L4 challenger identities but explicitly blocked performance comparison. This task exposes that governance state in the read-only Expo iOS risk audit screen and adds a runtime catalog `policy_compare_audit` payload.

The app now shows baseline/challenger ids, strict as-of blocker state, replay status, freeze rows, same-experiment gate rows, split/OOS plan rows, and replay blockers. It does not run replay, does not create paper order intents, and does not create live orders.

Strict raw/as-of status remains `BLOCKED`. Therefore L4 challenger replay remains blocked until a separate governed replay task states how strict as-of blockers are handled.

## No-Background Decision-Maker Report

Conclusion first: iPhone cockpit can now show the L4 challenger freeze/compare plan.

But it still says replay is blocked. Reason: strict as-of source completeness is not solved. So the app is an audit screen, not a signal to trade.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2981_3000_ios_freeze_compare_audit_screen/`.
- Report: `docs/reports/task_2981_3000_ios_freeze_compare_audit_screen/`.
- iOS app files touched:
  - `apps/ios-trader-brain/src/types/cockpit.ts`
  - `apps/ios-trader-brain/src/lib/cockpit-data.ts`
  - `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
  - `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- Catalog builder touched:
  - `scripts/build_trader_terminal_catalog.py`
- Validator: `python scripts/trader_brain_2981_3000_ios_freeze_compare_audit_screen_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
