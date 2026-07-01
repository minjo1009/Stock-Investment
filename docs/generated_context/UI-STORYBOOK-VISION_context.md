# Codex Context Bundle

Task: UI_STORYBOOK_VISION
Profile: UI_STORYBOOK_VISION
Generated At: 2026-06-29T02:28:51+00:00
Token Count: 11068
Token Count Mode: approximate
Max Tokens: 24000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/frontend_app_ssot/00_PROJECT_SSOT.md | 1604 | 401 | must_include |
| docs/frontend_app_ssot/01_ACTIVE_FRONTEND_TARGET_AND_STACK_DECISION.md | 1121 | 280 | must_include |
| docs/frontend_app_ssot/02_INFORMATION_ARCHITECTURE.md | 966 | 241 | must_include |
| docs/frontend_app_ssot/05_ROUTE_MAP_AND_SCREEN_REGISTRY.md | 1217 | 304 | must_include |
| docs/frontend_app_ssot/06_DESIGN_SYSTEM.md | 1024 | 256 | must_include |
| docs/frontend_app_ssot/07_COMPONENT_CATALOG.md | 986 | 246 | must_include |
| docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md | 14688 | 3670 | must_include |
| docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md | 788 | 197 | must_include |
| docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md | 5160 | 1290 | must_include |
| docs/frontend_app_ssot/21_SCAFFOLD_ONLY_SCREEN_ASSEMBLY_BOUNDARY.md | 8927 | 2231 | must_include |
| ops/profile_validation_rules.yaml | 2054 | 513 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| docs/reports/** | configured exclude |
| node_modules/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |

---

## File: AGENTS.md

```md
# AGENTS.md

## Project Identity

This repository is a Trading Operating System for observing, verifying, monitoring, and controlling an automated US equity trading engine.

It is not a retail brokerage UI, stock recommendation app, or chart-first app.

## Mandatory Operating Rules

1. Do not start work without a task id.
2. Do not scan the whole repository by default.
3. Read generated context bundles first when they exist.
4. Follow `ops/task_profiles.yaml`.
5. Respect `ops/doc_registry.yaml`.
6. Never treat archived/superseded docs as active SSOT.
7. Do not create new markdown reports outside the relevant task report folder.
8. All task outputs must update `ops/task_registry.yaml`.
9. All new docs must update `ops/doc_registry.yaml`.
10. Run required validators before closeout.

## Trading Safety

- No real capital.
- No live order.
- No broker mutation.
- No paper promotion unless explicitly accepted.
- Missing or stale data is UNKNOWN/BLOCKER, not negative evidence.

## UI Safety

- No one-off components.
- No business logic in UI.
- No IA redesign without approval.
- Storybook before P0 screens.
- Screenshot/Vision QA required for UI screens.

## Completion Definition

A task is complete only when:

- task registry updated
- doc registry updated
- required validators pass
- artifact manifest exists
- no forbidden files touched
- closeout report exists

```

---

## File: docs/frontend_app_ssot/00_PROJECT_SSOT.md

```md
# Frontend App SSOT

## Authority

This pack is the current frontend/app planning authority for future implementation work.
It does not grant strategy acceptance, paper permission, deployment readiness, broker mutation, live order permission, or real-capital permission.

Standing project status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Frontend mode: read-only L7 observation surface

## Active Target

The active frontend target is an Expo Development Build, iOS-first mobile app.

The near-term operator preview target is mobile-web-first phone preview because
the project currently has no paid Apple Developer Program and no Mac operator
path. This does not replace the later native iOS app path; it only defines the
current phone-visible implementation route.

The app must preserve:

- `decision -> reason/thesis -> evidence -> source`
- explicit source freshness
- blockers and missing evidence
- provenance for decision-support content
- read-only controls unless a future operating-state document changes permission

## Supersession

The prior React plus TypeScript web architecture pack is retained as design input only.
It is not the active implementation stack.

The prior Expo Go 3052 DOM cockpit is retained as historical UI evidence and migration reference only.
It is not the final route authority.

The mobile web preview path is governed by `23_MOBILE_WEB_PWA_BOUNDARY.md`.

Backtest, paper, and live are lifecycle states. They are not top-level navigation tabs.

```

---

## File: docs/frontend_app_ssot/01_ACTIVE_FRONTEND_TARGET_AND_STACK_DECISION.md

```md
# Active Frontend Target And Stack Decision

## Decision

Active target: Expo Development Build, iOS-first mobile app.

## Stack

| Layer | Current decision |
| --- | --- |
| Runtime | Expo Development Build |
| Platform priority | iOS first |
| Navigation | Expo Router |
| UI language | React Native plus TypeScript |
| Styling | NativeWind |
| Component base | React Native Reusables where practical |
| Micro charts | Skia |
| Main charts | TradingView Lightweight Charts through WebView when required |
| Component isolation | Storybook |
| Visual QA | screenshot checklist plus device/emulator captures |

## Backend Boundary

The frontend reads backend-generated read models, catalogs, and API responses.
It must not write to the active DB directly.
It must not call broker APIs.
It must not create or submit orders.
It must not infer permissions from paper-looking, live-looking, or successful-test states.

## Non-Active Inputs

React web, Next.js, Kubernetes, AWS, Cypress, Playwright, and the 3052 DOM cockpit are not active stack requirements unless a future operating document explicitly reauthorizes them.


```

---

## File: docs/frontend_app_ssot/02_INFORMATION_ARCHITECTURE.md

```md
# Information Architecture

## Top-Level Tabs

The fixed top-level IA is:

1. `HOME`
2. `BRAIN`
3. `PORTFOLIO`
4. `ORDERS`
5. `SYSTEM`

No other top-level trading lifecycle tab is authoritative.

## Lifecycle States

Backtest, shadow, paper, live, blocked, stale, and unknown are lifecycle or evidence states.
They appear inside screens as status, filter, evidence, or blocker fields.
They do not become top-level navigation tabs.

## Legacy Route Mapping

| Historical surface | New IA location |
| --- | --- |
| Scan | `BRAIN` candidate scanner |
| Detail | Detail route under `BRAIN`, `PORTFOLIO`, or `ORDERS` |
| Analysis | `BRAIN` thesis and validation sections |
| Market | `HOME` market context or `SYSTEM` source health |
| Risk | `SYSTEM` risk controls plus detail `Risk` section |
| Settings | `SYSTEM` |

## Required Surface Contract

Every screen that displays a decision must also display reason/thesis, evidence, source, freshness, and blocker state.


```

---

## File: docs/frontend_app_ssot/05_ROUTE_MAP_AND_SCREEN_REGISTRY.md

```md
# Route Map And Screen Registry

## Canonical Routes

| Route | Tab | Purpose |
| --- | --- | --- |
| `/` | `HOME` | Portfolio-level overview, DB/source status, current blockers |
| `/brain` | `BRAIN` | Candidate scanner, thesis bundles, runtime decision summaries |
| `/brain/candidates/[id]` | `BRAIN` | Candidate detail frame V2 |
| `/brain/chains/[id]` | `BRAIN` | Source-to-decision chain detail frame V2 |
| `/portfolio` | `PORTFOLIO` | Read-only positions, account summary, holdings evidence |
| `/portfolio/positions/[id]` | `PORTFOLIO` | Position detail frame V2 |
| `/orders` | `ORDERS` | Read-only order-intent, local order, broker-truth, and reconciliation views |
| `/orders/[id]` | `ORDERS` | Order detail frame V2 |
| `/system` | `SYSTEM` | Governance, source freshness, control state, validators, runtime health |
| `/system/sources` | `SYSTEM` | Source freshness and provenance |
| `/system/risk` | `SYSTEM` | Kill switch, blocker, and risk-control evidence |

## Registry Rule

Every new screen must declare:

- owning tab
- source read model
- required freshness fields
- required blocker fields
- disabled action controls, if any
- screenshot QA target
- Storybook story target, if componentized


```

---

## File: docs/frontend_app_ssot/06_DESIGN_SYSTEM.md

```md
# Design System

## Principles

The app is an operational quant cockpit, not a marketing surface.
It should be dense, calm, scannable, and evidence-forward.

## Token Groups

| Token group | Required use |
| --- | --- |
| Color | status, source freshness, risk severity, disabled controls |
| Type | numeric scan rows, section titles, compact evidence labels |
| Spacing | 4 px rhythm, stable list rows, compact mobile cards |
| Radius | 8 px or less unless native platform conventions require otherwise |
| Elevation | minimal; avoid nested card stacks |
| Motion | optional and non-authoritative |

## Status Color Semantics

Status colors must never imply strategy acceptance, paper permission, deployment readiness, or real-capital permission.

`STALE`, `UNKNOWN`, `BLOCKED`, `SOURCE_NOT_ATTACHED`, and `CHART_MISSING` must be visible states, not hidden fallbacks.

## Chart Rule

Charts must show source attachment or explicit absence.
Synthetic OHLC/VWAP fallback charts are not allowed for decision-support display.


```

---

## File: docs/frontend_app_ssot/07_COMPONENT_CATALOG.md

```md
# Component Catalog

## Required Component Families

| Component | Purpose |
| --- | --- |
| `DecisionHeader` | decision state, authority, timestamp, gate status |
| `SourceFreshnessBadge` | fresh/stale/missing/source-not-attached display |
| `BlockerList` | blockers and unknown states |
| `EvidenceList` | source-backed observations with provenance |
| `ValidationReadinessPanel` | split/OOS, leakage, cost/slippage, source gate state |
| `RiskPanel` | exposure, stale source, kill-switch, control-state evidence |
| `DisabledActionBar` | disabled approve/reject/cancel/execute affordances with governance reason |
| `ProvenanceLink` | source or artifact pointer |
| `ChartWithSourceState` | chart plus source attachment/freshness status |
| `LifecycleStatePill` | candidate/paper/live/shadow lifecycle display only |

## Storybook Minimum

Each component must have stories for:

- fresh source
- stale source
- missing source
- blocked state
- unknown state
- disabled action state


```

---

## File: docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md

```md
# Frontend Read Model Contract

## Contract Goal

Frontend implementation must start from screen-ready read models, not from invented UI props.

The frontend is a read-only L7 query surface. It displays backend/runtime state, source freshness, blockers, provenance, and disabled action reasons. It must not compute trading authority, broker truth, strategy acceptance, paper permission, live permission, deployment readiness, or real-capital permission.

## Read Path Authority

One implementation task must select exactly one primary read path before app code expands:

| Read path | Status before selection | Rule |
| --- | --- | --- |
| Generated JSON catalog | allowed | Must include fingerprint, generated timestamp, source refs, and stale/missing states. |
| Runtime API endpoint | allowed | Must be read-only and backed by the same contract fields. |
| Read-only SQLite export | allowed for diagnostics | Must not open active DB write handles from the app. |
| Direct active `trading.db` write/read from app | forbidden | The frontend must not become DB authority. |
| Broker API | forbidden | No KIS/Alpaca/broker mutation or account action from the frontend. |

## Common Types

`` `ts
type GovernanceStatus = {
  strategyAcceptance: "NOT_ACCEPTED";
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
  realCapital: "FORBIDDEN";
  brokerMutationPermitted: false;
  paperPermission: false;
  livePermission: false;
  killSwitchActive: boolean;
  controlStateSource: string;
  authorityReportPath?: string;
};

type FreshnessStatus = "FRESH" | "STALE" | "MISSING" | "UNKNOWN" | "NOT_APPLICABLE";

type SourceState = {
  sourceId: string;
  sourceLabel: string;
  freshnessStatus: FreshnessStatus;
  observedAt: string | null;
  generatedAt: string | null;
  sourceCount: number | null;
  strictGateAllowed: boolean;
  proxyAllowed: boolean;
  provenanceRefs: string[];
  blockerReason: string | null;
};

type BlockerState = {
  blockerId: string;
  severity: "P0" | "P1" | "P2" | "P3";
  label: string;
  reason: string;
  sourceRefs: string[];
  detectedAt: string | null;
};

type DisabledAction = {
  actionId:
    | "approve"
    | "reject"
    | "cancel"
    | "execute"
    | "submit"
    | "paper_promote"
    | "live_promote"
    | "broker_sync";
  label: string;
  actionState: "disabled";
  disabledReason: string;
  requiredGovernanceChange: string[];
};

type EvidenceItem = {
  evidenceId: string;
  label: string;
  value: string | number | boolean | null;
  unit?: string;
  sourceId: string;
  provenanceRefs: string[];
  freshnessStatus: FreshnessStatus;
};

type ChartSourceState = {
  chartId: string;
  status: "READY" | "CHART_MISSING" | "SOURCE_NOT_ATTACHED" | "STALE" | "UNKNOWN";
  sourceIds: string[];
  blockerReason: string | null;
};

type ChartResolution = "1D" | "1H" | "30M" | "15M" | "5M";

type RelativeReturnChartPoint = {
  timestamp: string;
  portfolioReturnPct: number | null;
  qqqReturnPct: number | null;
  relativeReturnPct: number | null;
  maxDrawdownPct: number | null;
};

type HomeRelativeReturnChart = {
  chartId: "home-relative-return-vs-qqq";
  title: "수익현황";
  benchmarkSymbol: "QQQ";
  selectedResolution: ChartResolution;
  allowedResolutions: ChartResolution[];
  chartState: ChartSourceState;
  sourceState: SourceState;
  points: RelativeReturnChartPoint[];
};
`` `

## Global App Shell Read Model

Every top-level tab receives this shell object:

`` `ts
type AppShellReadModel = {
  generatedAt: string;
  contractVersion: "frontend-read-model-v1";
  readPath: "json_catalog" | "runtime_api" | "readonly_sqlite_export";
  governance: GovernanceStatus;
  sourceSummary: {
    freshCount: number;
    staleCount: number;
    missingCount: number;
    unknownCount: number;
    strictGateOpenCount: number;
  };
  blockers: BlockerState[];
  disabledActions: DisabledAction[];
};
`` `

Shell rules:

- If any required source is stale or missing, the screen must show it.
- `strictGateOpenCount` does not grant permission by itself.
- A fresh source does not grant strategy acceptance.
- Disabled actions stay disabled even when data is fresh.

## Screen Inventory

| Screen | Required read model | Primary purpose |
| --- | --- | --- |
| `HOME` | `HomeReadModel` | Portfolio/brain/system snapshot and attention queue. |
| `BRAIN` | `BrainReadModel` | Candidate scanner, thesis bundles, review-only runtime decisions. |
| `Candidate Detail` | `CandidateDetailReadModel` | Six-section detail frame V2 for one candidate. |
| `Chain Detail` | `ChainDetailReadModel` | Source-to-decision provenance chain. |
| `PORTFOLIO` | `PortfolioReadModel` | Read-only positions and broker/local reconciliation summary. |
| `Position Detail` | `PositionDetailReadModel` | Holding thesis, risk, evidence, and reconciliation. |
| `ORDERS` | `OrdersReadModel` | Read-only intents, local records, broker-truth reconciliation. |
| `Order Detail` | `OrderDetailReadModel` | Order purpose, state, evidence, and disabled action context. |
| `SYSTEM` | `SystemReadModel` | Governance, source freshness, control state, validator status. |

## HOME Read Model

`` `ts
type HomeReadModel = AppShellReadModel & {
  relativeReturnChart: HomeRelativeReturnChart;
  portfolioSnapshot: {
    accountValue: number | null;
    cash: number | null;
    investedCash: number | null;
    openPnl: number | null;
    realizedPnl: number | null;
    totalReturnPct: number | null;
    winRatePct: number | null;
    maxDrawdownPct: number | null;
    sourceState: SourceState;
  };
  brainSnapshot: {
    candidateCount: number;
    blockedCount: number;
    reviewOnlyCount: number;
    latestRuntimeDecisionAt: string | null;
    sourceState: SourceState;
  };
  attentionQueue: Array<{
    itemId: string;
    kind: "candidate" | "position" | "order" | "source" | "system";
    label: string;
    reason: string;
    severity: "P0" | "P1" | "P2" | "P3";
    route: string;
    sourceRefs: string[];
  }>;
  freshnessSummary: SourceState[];
  blockerSummary: BlockerState[];
};
`` `

HOME first-screen priority is product/account comprehension: invested cash, account state, win-rate state, and the QQQ-relative return/MDD chart area must appear before governance/source detail. The return/MDD chart must use `relativeReturnChart`; it must render `SOURCE_NOT_ATTACHED`, `CHART_MISSING`, `STALE`, or `UNKNOWN` when authoritative portfolio equity curve and QQQ benchmark series are absent. HOME must not draw fake or synthetic chart series. HOME must not show duplicate account snapshot, operating restriction, or disabled-action sections as primary first-level sections; source freshness and disabled permissions remain visible as secondary context or in SYSTEM.

## BRAIN Read Model

`` `ts
type BrainReadModel = AppShellReadModel & {
  scannerSummary: {
    candidateCount: number | null;
    reviewOnlyCount: number | null;
    blockedCount: number | null;
    weakEvidenceCount: number | null;
    latestReviewAt: string | null;
  };
  candidates: Array<{
    candidateId: string;
    symbol: string;
    displayName: string;
    lifecycleState: "REVIEW_ONLY" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
    decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
    thesisSummary: string | null;
    reasonSummary: string | null;
    validationState: "NOT_VALIDATED" | "BLOCKED" | "PARTIAL" | "UNKNOWN";
    evidenceStrength: "NONE" | "WEAK" | "PARTIAL" | "SOURCE_BACKED";
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
  filters: {
    allowedFilterKeys: string[];
    forbiddenFilterKeys: ["future_outcome", "realized_label", "post_event_return"];
  };
};
`` `

Forbidden rule: no `candidate_score`, `candidate_rank`, or `confidence_score` may be invented unless a backend authority explicitly provides and documents the field. BRAIN first-screen priority is candidate review comprehension: candidate count, review-only count, blocked count, and weak-evidence count must appear before governance/source detail.

## Candidate Detail Read Model

`` `ts
type CandidateDetailReadModel = AppShellReadModel & {
  candidateId: string;
  symbol: string;
  sections: {
    decisionSummary: {
      decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
      authority: string;
      generatedAt: string;
      disabledActions: DisabledAction[];
    };
    thesisLogic: {
      thesis: string | null;
      reason: string | null;
      economicMeaningRefs: string[];
      relationRefs: string[];
    };
    validationReadiness: {
      splitOosStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      leakageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      costSlippageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      sourceGateStatus: "OPEN" | "CLOSED" | "BLOCKED" | "UNKNOWN";
      readinessSummary: string;
    };
    evidence: EvidenceItem[];
    risk: {
      blockers: BlockerState[];
      sourceStates: SourceState[];
      chartStates: ChartSourceState[];
    };
    nextAction: {
      allowedReadOnlyActions: string[];
      disabledTradingActions: DisabledAction[];
      nextEngineeringAction: string | null;
    };
  };
};
`` `

Candidate detail must render all six sections from `03_UNIVERSAL_DETAIL_FRAME_V2.md`.

## Chain Detail Read Model

`` `ts
type ChainDetailReadModel = AppShellReadModel & {
  chainId: string;
  layers: Array<{
    layer: "L0_RAW" | "L1_FACT" | "L2_MEANING" | "L3_RELATION" | "L4_THESIS" | "L5_POLICY" | "L6_RUNTIME" | "L7_FRONTEND";
    status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN";
    artifactRefs: string[];
    provenanceRefs: string[];
    blockerReason: string | null;
  }>;
};
`` `

Missing layers must be shown as blockers or unknowns. They must not be silently skipped.

## PORTFOLIO Read Model

`` `ts
type PortfolioReadModel = AppShellReadModel & {
  portfolioSummary: {
    investedCash: number | null;
    cash: number | null;
    totalMarketValue: number | null;
    unrealizedPnl: number | null;
    realizedPnl: number | null;
    positionCount: number | null;
    exposurePct: number | null;
    winRatePct: number | null;
    maxDrawdownPct: number | null;
  };
  positions: Array<{
    positionId: string;
    symbol: string;
    quantity: number | null;
    marketValue: number | null;
    unrealizedPnl: number | null;
    thesisState: "VALID" | "INVALIDATED" | "UNKNOWN" | "BLOCKED" | "NOT_APPLICABLE";
    brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED";
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
};
`` `

PORTFOLIO first-screen priority is account/position comprehension: invested cash, cash, market value, unrealized PnL, realized PnL, exposure, MDD, and win-rate state must appear before governance/source detail. Broker truth and local runtime records must be visibly separated.

## Position Detail Read Model

`` `ts
type PositionDetailReadModel = AppShellReadModel & {
  positionId: string;
  symbol: string;
  sections: CandidateDetailReadModel["sections"] & {
    reconciliation: {
      localRecordState: "PRESENT" | "MISSING" | "UNKNOWN";
      brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED";
      latestReconciliationAt: string | null;
      blockerReason: string | null;
    };
  };
};
`` `

Position detail must never imply that local records are broker truth.

## ORDERS Read Model

`` `ts
type OrdersReadModel = AppShellReadModel & {
  orderRows: Array<{
    orderId: string;
    symbol: string | null;
    side: "BUY" | "SELL" | "NONE" | "UNKNOWN";
    quantity: number | null;
    localState: "NONE" | "CREATED" | "SUBMITTING" | "SUBMITTED_LOCAL_RECORDED" | "UNKNOWN" | "RECONCILED" | "BLOCKED";
    brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED" | "NOT_APPLICABLE";
    mutationPermitted: false;
    disabledActions: DisabledAction[];
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
};
`` `

Order rows are observation rows. They are not broker mutation controls.

## Order Detail Read Model

`` `ts
type OrderDetailReadModel = AppShellReadModel & {
  orderId: string;
  sections: {
    decisionSummary: CandidateDetailReadModel["sections"]["decisionSummary"];
    thesisLogic: CandidateDetailReadModel["sections"]["thesisLogic"];
    validationReadiness: CandidateDetailReadModel["sections"]["validationReadiness"];
    evidence: EvidenceItem[];
    risk: CandidateDetailReadModel["sections"]["risk"];
    nextAction: CandidateDetailReadModel["sections"]["nextAction"];
    orderState: {
      localState: OrdersReadModel["orderRows"][number]["localState"];
      brokerTruthState: OrdersReadModel["orderRows"][number]["brokerTruthState"];
      submittedAt: string | null;
      reconciledAt: string | null;
      unknownAgeSeconds: number | null;
    };
  };
};
`` `

Cancel, amend, execute, submit, approve, reject, paper-promote, and live-promote controls must be disabled under current governance.

## SYSTEM Read Model

`` `ts
type SystemReadModel = AppShellReadModel & {
  controlState: {
    runMode: "DIAGNOSTIC_ONLY";
    killSwitchActive: boolean;
    emergencyCancelAllowed: false;
    sourcePath: string;
    observedAt: string | null;
  };
  sourceFreshness: SourceState[];
  validatorStatus: Array<{
    validatorId: string;
    command: string;
    latestStatus: "PASS" | "FAIL" | "UNKNOWN" | "NOT_RUN";
    latestRunAt: string | null;
    reportPath?: string;
  }>;
  artifactHealth: Array<{
    artifactId: string;
    path: string;
    status: "PRESENT" | "MISSING" | "STALE" | "UNKNOWN";
  }>;
};
`` `

SYSTEM is the canonical UI location for source freshness, control state, disabled-action reasons, and validator visibility.

## Empty And Error State Rules

| State | UI meaning | Forbidden interpretation |
| --- | --- | --- |
| `UNKNOWN` | source or state cannot be proven | negative trading evidence |
| `MISSING` | required input is absent | zero value or failed thesis |
| `STALE` | input exists but is not current enough | fresh permission |
| `BLOCKED` | governance or source gate prevents action | optional warning |
| `NOT_APPLICABLE` | field does not apply to this screen | hidden failure |

## Mapping Rules

Missing or stale data is `UNKNOWN` or `BLOCKER`.
It is never negative evidence.

Labels and outcomes must not enter assignment logic.

The frontend may filter and sort visible rows, but it must not infer lifecycle matching or source readiness from symbol/date/price/time proximity.

Storybook fixtures, screenshot QA states, and safety validators must be generated from this contract, not from ad hoc mock fields.

```

---

## File: docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md

```md
# Storybook And QA Plan

## Storybook Coverage

Storybook must cover:

- five top-level IA tabs
- universal detail frame V2
- source freshness badges
- blocker states
- disabled action controls
- chart missing/source not attached states
- governance status panels

## Screenshot QA

Screenshot QA must capture:

- `HOME`
- `BRAIN`
- candidate detail
- `PORTFOLIO`
- position detail
- `ORDERS`
- order detail
- `SYSTEM`
- stale source state
- disabled action state

## Validator Targets

Frontend validation should include:

- no live order text or handlers that imply permission
- no broker mutation controls with active handlers
- no synthetic chart fallback for source-required charts
- required freshness and provenance fields visible
- backtest/paper/live not used as top-level tabs


```

---

## File: docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md

```md
# Screenshot QA Preflight Plan

## Purpose

Define the future visual QA evidence contract before product screens are implemented.

This is a preflight plan only. It does not install screenshot tooling, run captures, implement screens, or prove UI quality.

## Current Status

- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Current frontend fixtures are scaffold-only and `NOT_AUTHORITY`.
- No product screen, Candidate Detail screen, DB connection, runtime API connection, broker connection, paper/live path, deployment readiness, or real-capital path is authorized by this document.

## Non-Authorization Rule

Screenshot QA evidence can show what is visible. It must not be treated as strategy acceptance, deployment readiness, paper readiness, live readiness, broker readiness, source truth, backend truth, broker truth, order execution permission, or real-capital permission.

## Target Surfaces

| Surface ID | Surface | Current Status | Required State Coverage |
| --- | --- | --- | --- |
| SS-001 | Home | future required | normal, stale source, blocked |
| SS-002 | Brain Overview | future required | normal, missing source, unknown |
| SS-003 | Candidate Detail | future required | decision summary, evidence, disabled action |
| SS-004 | Portfolio Overview | future required | normal, stale or missing source |
| SS-005 | Position Detail | future required | position verdict, risk, source state |
| SS-006 | Orders Overview | future required | read-only order states |
| SS-007 | Order Detail | future required | disabled approve/reject/cancel |
| SS-008 | System Overview | future required | system health, blockers |
| SS-009 | Stale Source State | required special state | stale visible above fold |
| SS-010 | Disabled Action State | required special state | disabled reason plus governance change visible |

## Device / Browser Matrix

Required baseline:

| Axis | Required Value |
| --- | --- |
| Device | iPhone 15 Pro |
| Theme | Light |
| Scale | 100% |
| Orientation | Portrait |

Future optional matrix:

| Tier | Target |
| --- | --- |
| P0 | iPhone 15 Pro, Light, Portrait |
| P1 | iPhone SE width stress, Light, Portrait |
| P1 | iPhone 15 Pro Max, Light, Portrait |
| P2 | Dark theme, only after theme support is explicitly selected |
| P2 | Android, only after iOS-first baseline is stable |

## State Matrix

| State | Required Visual Evidence |
| --- | --- |
| `fresh` | source freshness visible |
| `stale` | stale badge/warning visible |
| `missing` | missing source visible, not hidden |
| `unknown` | unknown state visible as blocker/unknown |
| `blocked` | blocker reason visible |
| `disabled_action` | disabled action plus reason and required governance change visible |
| `chart_missing` | chart unavailable state visible |
| `source_not_attached` | source-not-attached visible |
| `read_only` | no active trading action affordance |
| `safety_boundary` | `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN` visible where relevant |

## Artifact Naming Policy

Future screenshot files must use deterministic names:

`` `text
<surface_id>__<surface_slug>__<state>__<device>__<theme>__<orientation>__<yyyymmdd>.png
`` `

Example:

`` `text
SS-003__candidate-detail__disabled-action__iphone-15-pro__light__portrait__20260622.png
`` `

## Storage Locations

| Artifact Type | Path |
| --- | --- |
| Preflight plan | `docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md` |
| Future screenshot outputs | `docs/reports/task_<id>_screenshot_qa_run/screenshots/` |
| Screenshot manifest | `docs/reports/task_<id>_screenshot_qa_run/screenshot_manifest.csv` |
| Vision review notes | `docs/reports/task_<id>_screenshot_qa_run/vision_review.md` |

## Future Run Manifest Fields

`screenshot_id,surface_id,surface_name,route_or_story,state,fixture_or_source_artifact,device,theme,orientation,scale,captured_at,capture_command,pass_fail,failure_reason,reviewer,notes`

## Acceptance Criteria

Future screenshot QA can pass only if:

1. Required surfaces are captured or explicitly blocked with reason.
2. Device preset matches iPhone 15 Pro / Light / 100% / Portrait.
3. Stale/missing/unknown/source-not-attached states are visible.
4. Disabled actions show `actionState = disabled`, `disabledReason`, `requiredGovernanceChange`, and current hard boundary.
5. No active BUY/SELL/EXECUTE/LIVE/PLACE ORDER affordance appears.
6. Charts do not silently use synthetic source-free fallback.
7. Every image maps to surface, state, fixture/source, device, date, and pass/fail.
8. Missing/stale remains `UNKNOWN/BLOCKER`.

## Failure Criteria

Screenshot QA must fail or block if required surfaces are unavailable without explicit blocker evidence, forbidden active trading affordances appear, source-free charts are treated as evidence, stale/missing/unknown states are hidden, or screenshots are used to imply trading/deployment readiness.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, DB/runtime connection, or product screen implementation is authorized.

```

---

## File: docs/frontend_app_ssot/21_SCAFFOLD_ONLY_SCREEN_ASSEMBLY_BOUNDARY.md

```md
# Scaffold-only Screen Assembly Boundary

## Purpose

This document defines the limited frontend implementation class that may start before product screen implementation is authorized.

It exists because the user asked to begin frontend real implementation, while `11_IMPLEMENTATION_PRECONDITIONS.md` still blocks product screen implementation until an authoritative read source and screenshot QA evidence are selected.

## Current Problem

`apps/ios-trader-brain` has an Expo Router scaffold, read-only placeholder tabs, P0 foundation/generic/domain components, and scaffold-only JSON fixtures.

The current fixtures are useful for screen assembly and Storybook smoke work, but they remain `NOT_AUTHORITY`. They do not prove backend truth, source truth, broker truth, product readiness, paper permission, live permission, deployment readiness, or real-capital permission.

## Non-Authorization Rule

Scaffold-only screen assembly is not strategy acceptance.

Scaffold-only screen assembly is not deployment readiness.

Scaffold-only screen assembly is not paper or live trading permission.

Scaffold-only screen assembly is not broker mutation permission.

Scaffold-only screen assembly is not real-capital permission.

The hard project state remains:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Definitions

### Scaffold-only Screen Assembly

Scaffold-only screen assembly means:

- screen UI may be assembled from existing read-model JSON fixtures
- fixtures remain `NOT_AUTHORITY`
- no source truth is inferred
- no backend truth is inferred
- no broker truth is inferred
- no production read path is inferred
- no trading permission is inferred
- no deployment readiness is inferred
- no paper/live permission is inferred
- no real-capital permission is inferred
- the screen visibly surfaces read-only, scaffold-only, and `NOT_AUTHORITY` boundaries

### Product Screen Implementation

Product screen implementation means a screen is being prepared as a product-quality operating surface that can rely on an authoritative read path, screenshot QA evidence, device-flow evidence, and production data-source governance.

Product screen implementation remains blocked.

## Allowed Scaffold-only Screen Assembly

After this boundary exists, a future selected loop may assemble scaffold-only screens from existing fixtures and existing read-only components.

Allowed future loop candidates:

- `HOME v0` scaffold-only fixture-backed assembly
- `Candidate Detail v0` scaffold-only fixture-backed assembly

Both candidates must remain read-only, fixture-backed, and `NOT_AUTHORITY`.

## Still-blocked Product Screen Implementation

The following remain blocked until future authoritative operating documents explicitly change them:

- authoritative backend read-source integration
- runtime API integration
- active DB integration
- broker API integration
- KIS or Alpaca integration
- paper/live operating promotion
- production screenshot QA claims
- iOS development build readiness claims
- deployment readiness claims
- real-capital readiness claims

## Allowed Data Sources

For future scaffold-only screen assembly, the only allowed initial data sources are existing scaffold fixtures:

- `apps/ios-trader-brain/src/mocks/fixtures/home.json`
- `apps/ios-trader-brain/src/mocks/fixtures/candidate-detail.json`
- other existing `apps/ios-trader-brain/src/mocks/fixtures/*.json` files only if explicitly selected by a future loop

These sources remain fixture evidence only and are not authority.

## Forbidden Data Sources

Scaffold-only screen assembly must not read from or connect to:

- active `trading.db`
- runtime API
- broker API
- KIS
- Alpaca
- paper/live execution services
- real-capital account sources
- any mutation-capable account, order, or broker surface

## Required Visual Boundaries

Each scaffold-only screen must visibly surface, directly or through existing components:

- read-only state
- fixture-backed state
- `NOT_AUTHORITY` status
- source freshness state when present
- blockers when present
- disabled trading action state when present
- current hard state when applicable: `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, `FORBIDDEN`

Stale, missing, unknown, and blocked states must be visible. They must not be hidden behind healthy-looking portfolio, candidate, order, or system summaries.

## Required Component Sources

Scaffold-only screens should use existing P0 components first:

- `ScreenContainer`
- `SectionContainer`
- `AppText`
- `Badge`
- `CardContainer`
- `MetricCard`
- `StatusRow`
- `SourceFreshnessBadge`
- `BlockerList`
- `DecisionHeader`
- `EvidenceList`
- `ValidationReadinessPanel`
- `RiskGate`
- `DisabledActionBar`
- `ChartWithSourceState`
- `SystemHealth`
- `OrderStateSummary`

New components are allowed only when a future selected loop proves they are reusable, props-only, read-only, and not screen-specific business logic.

## Required Fixture Boundaries

Fixture-backed screens must state or encode that:

- fixture payloads are `NOT_AUTHORITY`
- fixture payloads are not live source evidence
- fixture payloads are not broker truth
- fixture payloads are not runtime permission
- fixture payloads are not strategy validation
- fixture payloads are not deployment evidence

No code may infer missing source fields as negative evidence. Missing, stale, unknown, and blocked remain explicit states.

## Required Safety Copy

Scaffold-only screens must avoid language that implies execution permission.

Allowed intent language:

- Review
- Inspect
- Validate
- Open Evidence
- Open Source
- View Risk
- View Order Detail
- Disabled
- Blocked
- Requires Governance Change

Any future disabled action affordance must expose:

- disabled state
- disabled reason
- required governance change
- no hidden mutation handler

## Allowed Loop 2 Candidate: HOME v0

`HOME v0` may be implemented in a future selected loop as a scaffold-only fixture-backed screen.

Required boundaries:

- read from `home.json` or an explicit typed wrapper around that fixture only
- show portfolio, brain, attention, freshness, and blocker summaries as fixture-backed
- show stale/missing/unknown/blocker states if present
- preserve fixed top-level IA: `HOME / BRAIN / PORTFOLIO / ORDERS / SYSTEM`
- add no DB, runtime, broker, paper/live, or real-capital connection

## Allowed Loop 3 Candidate: Candidate Detail v0

`Candidate Detail v0` may be implemented in a future selected loop as a scaffold-only fixture-backed screen.

Required boundaries:

- read from `candidate-detail.json` or an explicit typed wrapper around that fixture only
- render the six-section detail frame: Decision Summary, Thesis-Logic, Validation-Readiness, Evidence, Risk, Next Action
- show disabled action state and governance reason
- preserve evidence and source freshness visibility
- add no DB, runtime, broker, paper/live, or real-capital connection

## Acceptance Criteria

A scaffold-only screen assembly loop passes only if:

- the loop is explicitly selected in the loop ledger or task report
- source fixtures remain `NOT_AUTHORITY`
- read-only and fixture-backed boundaries are visible
- stale/missing/unknown/blocked states remain visible
- no mutation-capable handler or import is added
- no app code claims operational readiness
- `npm run typecheck`, `npm run lint`, `npm test`, `npm run validate:safety`, and `npm run validate:fixtures` pass when app code changes
- `python scripts/task_registry_validate.py` and `git diff --check` pass

## Failure Criteria

The loop fails if it:

- treats fixtures as authoritative
- hides stale/missing/unknown/blocker states
- connects to active DB, runtime API, broker API, KIS, Alpaca, paper/live services, or real-capital sources
- adds a mutation handler
- claims paper/live/deployment/real-capital readiness
- claims strategy acceptance
- removes the product screen implementation blocker
- bypasses screenshot QA or authoritative read-source requirements for product readiness

## Validation Checklist

Before closing any scaffold-only screen assembly loop:

1. Confirm changed files are limited to the selected loop scope.
2. Confirm fixture use is visible as `NOT_AUTHORITY`.
3. Confirm read-only state is visible.
4. Confirm disabled or blocked action states have governance reasons.
5. Confirm no DB/runtime/broker/KIS/Alpaca imports were added.
6. Confirm no package/config/tooling change occurred unless explicitly selected.
7. Run the required validators for the files changed.
8. Update the task report, artifact manifest, task registry, and loop ledger.

## Safety Boundaries

This document authorizes only narrow scaffold-only screen assembly in future selected loops.

It does not authorize product screen implementation, source authority, runtime integration, broker mutation, paper/live operation, deployment readiness, or real-capital use.

```

---

## File: ops/profile_validation_rules.yaml

```yaml
version: 1
updated_at: "2026-06-29"

rules:
  L4_THESIS_BUNDLE:
    must_include:
      required_principles:
        - thesis_specificity
        - evidence_linkage
        - source_traceability
        - contradiction_handling
        - blocked_context_mixed_rate_visibility
      forbidden_intents:
        - final_policy_action
        - broker_mutation
        - live_order
        - paper_promotion
      required_checks:
        - thesis_quality_review
        - evidence_coverage
        - source_access
        - institutional_quality_score
    hard_boundaries:
      strategy_status: NOT_ACCEPTED
      deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
      real_capital: FORBIDDEN
      live_order: FORBIDDEN

  L5_POLICY_ACTION:
    must_include:
      required_principles:
        - review_only_boundary
        - sizing_intent_separation
        - order_intent_separation
        - hold_reduce_exit_rerisk_support
      forbidden_intents:
        - broker_mutation
        - live_order
        - auto_approval
        - real_capital
      required_checks:
        - policy_action_schema
        - no_broker_mutation
        - no_live_order
    hard_boundaries:
      strategy_status: NOT_ACCEPTED
      deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
      real_capital: FORBIDDEN
      broker_mutation: FORBIDDEN
      live_order: FORBIDDEN

  UI_STORYBOOK_VISION:
    must_include:
      required_principles:
        - component_first
        - storybook_before_p0_screens
        - screenshot_qa_required
        - ui_is_pure_rendering
        - no_business_logic_in_ui
        - no_chart_first_screens
      forbidden_intents:
        - ia_redesign_without_approval
        - one_off_component
        - promotion_calculation_in_ui
        - risk_calculation_in_ui
        - order_mutation
      required_checks:
        - typecheck
        - lint
        - storybook_story_exists
        - screenshot_exists
        - vision_review_report
    hard_boundaries:
      live_order: FORBIDDEN
      broker_mutation: FORBIDDEN

```

---

## File: ops/task_profiles.yaml

```yaml
version: 1
updated_at: "2026-06-29"

profiles:
  DOCS_GOVERNANCE:
    purpose: Maintain task/document registry, context bundles, governance tooling.
    allowed_intents:
      - create_or_update_registries
      - create_validators
      - render_read_only_dashboard
      - create_context_bundles
    forbidden_intents:
      - trading_logic_change
      - broker_mutation
      - live_order
      - db_schema_change
      - scheduler_registration_change
      - strategy_acceptance_change
    required_outputs:
      - task_registry_update
      - doc_registry_update
      - report
      - artifact_manifest
      - validation_results

  L0_L1_DATA_PIPELINE:
    purpose: Raw source acquisition, storage, normalization, source-time integrity.
    required_principles:
      - source_time_must_be_preserved
      - raw_data_integrity_first
      - no_strategy_logic
      - missing_or_stale_data_is_unknown_or_blocker
    forbidden_intents:
      - candidate_promotion
      - policy_action
      - order_intent
      - broker_mutation
      - live_order
    required_checks:
      - storage_contract
      - source_time_audit
      - freshness_status
      - artifact_manifest

  L2_INTERPRETATION:
    purpose: Convert raw/source data into economic meaning without promotion or execution.
    required_principles:
      - actual_vs_inference_separation
      - missing_data_explicit
      - no_unverified_source_claims
    forbidden_intents:
      - portfolio_sizing
      - order_intent
      - broker_mutation
      - live_order

  L3_RELATIONSHIP:
    purpose: Validate economic relationships and chains.
    required_principles:
      - relationship_evidence_required
      - chain_break_conditions_required
      - contradictory_evidence_must_be_visible
    forbidden_intents:
      - order_intent
      - broker_mutation
      - live_order

  L4_THESIS_BUNDLE:
    purpose: Construct and validate thesis bundles at institutional quality.
    required_principles:
      - thesis_specificity
      - evidence_linkage
      - source_traceability
      - contradiction_handling
      - blocked_context_mixed_rate_visibility
    forbidden_intents:
      - final_policy_action
      - broker_mutation
      - live_order
      - paper_promotion
    required_checks:
      - thesis_quality_review
      - evidence_coverage
      - source_access
      - institutional_quality_score

  L5_POLICY_ACTION:
    purpose: Translate thesis state into review-only policy actions.
    required_principles:
      - review_only_boundary
      - sizing_intent_separation
      - order_intent_separation
      - hold_reduce_exit_rerisk_support
    forbidden_intents:
      - broker_mutation
      - live_order
      - auto_approval
      - real_capital
    required_checks:
      - policy_action_schema
      - no_broker_mutation
      - no_live_order

  L6_EXECUTION_SAFETY:
    purpose: Execution safety, order lifecycle visibility, broker truth checks.
    required_principles:
      - user_control_required
      - no_real_capital
      - no_live_order_without_explicit_acceptance
      - broker_truth_separation
      - kill_switch_visibility
    forbidden_intents:
      - hidden_order_mutation
      - bypass_approval
      - live_order_enablement
      - real_capital_enablement
    required_checks:
      - broker_mutation_absent
      - order_control_audit
      - kill_switch_audit
      - execution_permission_audit

  UI_STORYBOOK_VISION:
    purpose: Expo/React Native UI implementation using component-first, Storybook, screenshot QA.
    required_principles:
      - component_first
      - storybook_before_p0_screens
      - screenshot_qa_required
      - ui_is_pure_rendering
      - no_business_logic_in_ui
      - no_chart_first_screens
    forbidden_intents:
      - ia_redesign_without_approval
      - one_off_component
      - promotion_calculation_in_ui
      - risk_calculation_in_ui
      - order_mutation
    required_checks:
      - typecheck
      - lint
      - storybook_story_exists
      - screenshot_exists
      - vision_review_report

  TASK_CLOSEOUT:
    purpose: Close tasks only after registries, artifacts, validators, and reports are complete.
    required_principles:
      - no_done_without_validator_pass
      - artifact_manifest_required
      - doc_registry_update_required
      - task_registry_update_required
      - forbidden_paths_clean

```
