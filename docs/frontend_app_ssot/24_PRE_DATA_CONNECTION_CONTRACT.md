# Pre-Data Connection Contract

## Purpose

This document defines the contract that must be satisfied before HOME, PORTFOLIO, and BRAIN move from fixture-backed UI to real read-only data.

It does not authorize strategy acceptance, deployment readiness, paper/live permission, broker mutation, broker sync, order submission, active DB access from the frontend, or real-capital use.

## Current State

| Area | Current state | Rule |
| --- | --- | --- |
| UI implementation | Fixture-backed | May be visually refined without backend authority. |
| Read path | `json_catalog` fixture snapshot | `NOT_AUTHORITY`; not backend truth. |
| Runtime API | Not connected | Must be read-only if introduced. |
| Active DB | Not connected from frontend | Direct active `trading.db` access remains forbidden. |
| Broker/account API | Not connected | Broker mutation and broker submit remain forbidden. |
| Chart data | Source-not-attached where authority is absent | Do not draw fake lines. |
| News/IR source | Source-not-attached where authority is absent | Missing source is blocker/unknown, not negative evidence. |

## Required Read Path Decision

Before replacing fixture payloads, one task must select exactly one primary read path:

1. Backend-generated JSON catalog.
2. Read-only runtime API snapshot.
3. Read-only SQLite export transformed outside the app.

The app must not directly read or write the active trading DB. The frontend must display payload metadata and source state for every screen.

## Shared Payload Envelope

Every real payload must include:

```ts
type FrontendPayloadEnvelope<T> = {
  contractVersion: "frontend-read-model-v1";
  payloadId: string;
  generatedAt: string;
  asOf: string | null;
  readPath: "json_catalog" | "runtime_api" | "readonly_sqlite_export";
  authority: "NOT_AUTHORITY" | "READ_ONLY_RUNTIME_DERIVED";
  sourceRefs: string[];
  sourceSummary: {
    freshCount: number;
    staleCount: number;
    missingCount: number;
    unknownCount: number;
    strictGateOpenCount: number;
  };
  governance: {
    strategyAcceptance: "NOT_ACCEPTED";
    deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
    realCapital: "FORBIDDEN";
    brokerMutationPermitted: false;
    paperPermission: false;
    livePermission: false;
    killSwitchActive: boolean;
    controlStateSource: string;
  };
  blockers: BlockerState[];
  data: T;
};
```

Rules:

- `authority` is display authority only; it never grants trading permission.
- `asOf: null` is allowed only when the screen clearly shows `UNKNOWN`.
- `strictGateOpenCount` is health context, not permission.
- Any missing, stale, or unknown required source must remain visible.

## HOME Data Contract

HOME requires:

| Field group | Required data | Missing behavior |
| --- | --- | --- |
| Portfolio hero | evaluation amount, principal, total P/L, return rate, win rate, MDD | Show skeleton/unknown state without fake numbers. |
| Performance chart | evaluation series, principal series, QQQ series, MDD series, timeframe metadata | Show `SOURCE_NOT_ATTACHED` or `CHART_MISSING`; do not draw synthetic lines. |
| Journal month rail | available month keys from 2022-01 through current month | Generate display rail from dates; no fake trade rows. |
| Holdings preview | top holdings if present | Empty state if absent. |
| Source metadata | source states for portfolio and chart | Secondary layer; not above the fold. |

## PORTFOLIO Data Contract

PORTFOLIO requires:

| Field group | Required data | Missing behavior |
| --- | --- | --- |
| Holdings table | position id, name, ticker, quantity, sellable quantity, evaluation amount, purchase amount, P/L, yield, holding period, MDD | Row remains selectable but values show `UNKNOWN`; no action buttons become active. |
| Selected holding detail | selected position id, price, daily change, chart state, metric strip, buy reasoning, news summary | Detail card shows source-not-attached placeholders. |
| Chart data | OHLC/time series, volume, optional VWAP/MA overlays, slider range | Do not draw fake candles or lines. |
| Reasoning/news | source-backed reason items and article summaries | Show "근거 연결 대기" / "관련 뉴스 없음" with source state. |
| Reconciliation | broker truth status and local record status | Display only; no sync or mutation. |

## BRAIN Data Contract

BRAIN requires:

| Field group | Required data | Missing behavior |
| --- | --- | --- |
| Today's issue | theme, one-line interpretation, confidence/conviction display value, state badge, source refs | Show issue placeholder with `UNKNOWN`, not invented confidence. |
| News & interpretation | title, source, published time, summary, interpretation, evidence route | Show source-not-attached card; do not invent source authority. |
| Relation map | cause, effect, related theme/symbol, evidence refs | Display only; missing relations are blockers. |
| Candidate slider | candidate id, symbol, display name, status, confidence/conviction, risk, next response | No score/rank/outcome fields; no future outcome leakage. |
| Candidate detail | L2 interpretation, L3 evidence, L4 risk, L5 response | Responses stay disabled/read-only until separate write authority exists. |
| Evidence detail | metadata, summary, key points, Brain interpretation, original text/source link | Original text requires source authority; otherwise placeholder. |

## Forbidden Fields And Logic

The frontend must not introduce:

- `candidate_score`
- `candidate_rank`
- `confidence_score` as a ranking/assignment field
- realized outcome labels in assignment or filtering logic
- future return labels
- inferred lifecycle matching
- symbol/date/price/time proximity fallback
- broker submit, paper promote, live promote, or real-capital action handlers

User-facing "확신 수준" may exist only as a display field from the read model and must not become assignment logic.

## Connection Readiness Checklist

Before any real data connection:

1. Select one read path and document it.
2. Define payload envelope producer.
3. Add payload fingerprint/hash.
4. Add source refs for every chart/news/reason field.
5. Add stale/missing/unknown states for every required source.
6. Add validator proving frontend has no active DB import.
7. Add validator proving no broker/API mutation import.
8. Add screenshot QA with source-attached and source-not-attached states.
9. Add fixture-to-real parity sample.
10. Update task report, artifact manifest, and task registry.

## Acceptance Condition

The next implementation task may visually refine HOME, PORTFOLIO, and BRAIN using fixtures. It may not connect real data until this contract is satisfied by a selected read path and a validator-backed payload sample.
