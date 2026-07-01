# L0 Source Acquisition Project Management Plan

## Decision

L0/L1 source acquisition is managed as a staged data product. The active
implementation baseline is the TASK-4116 recovered source-acquisition code plus
the TASK-4117 project-management integration layer.

This plan is the active roadmap for collection code, scheduler posture, task
records, and validation. Historical task reports are evidence, not the current
operating plan.

## Active Files

| Area | Active file |
|---|---|
| Scheduler baseline | `configs/db_source_acquisition_scheduler.json` |
| Local operator override template | `configs/local_templates/db_source_acquisition_scheduler.override.example.json` |
| Status report | `scripts/report_l0_collection_status.py` |
| Status builder | `tools/db/source_acquisition/l0_collection_status.py` |
| Project-management validator | `scripts/validate_l0_source_acquisition_project_management.py` |
| Recovery report | `docs/reports/task_4116_l0_l1_source_acquisition_stash_recovery/report.md` |
| Integration report | `docs/reports/task_4117_l0_source_acquisition_project_management_integration/report.md` |

## Six-Stage Roadmap

| Stage | Name | Entry condition | Exit condition |
|---:|---|---|---|
| 1 | Official/core API smoke stabilization | TASK-4116 files present and validators pass | Official, GDELT, Marketaux, and microstructure smoke commands prove credentials, rate limits, raw ledgers, and closed permissions |
| 2 | Real-time source budget optimization | Stage 1 validated | Per-provider cadence stays below quota with request ledgers, cooldowns, backoff, and no secret leakage |
| 3 | Real-time scheduler setup and execution | Stage 2 validated | Local override enables only diagnostic jobs, scheduler recurrence is proven, and status snapshots show current cycles |
| 4 | Historical backfill optimization | Stage 3 validated | Backfill chunk sizes, checkpoints, resumes, retry classes, and coverage audits are tuned per source |
| 5 | Background historical backfill from 2016 | Stage 4 validated | Long-running collectors operate from 2016 baselines with STOP/resume controls and manifestable raw/cache ledgers |
| 6 | L1 quality/coverage audit and L2 handoff | Stage 5 validated | Ticker/entity/news mapping, publication time, raw hash, coverage, and blocker ledgers are sufficient for an explicit L2 handoff decision |

## Source Implementation Modes

## Stage 1 Current State

TASK-4118 added the Stage 1 no-network smoke preflight. Current status is
`COMPLETE_NETWORK_SMOKE_PASS`: TASK-4118 proved config, source registry bounds,
materialization, L1 normalization contracts, credential-presence checks, and
closed safety gates without API calls; TASK-4119 then executed bounded network
smoke for official public releases, GDELT, Marketaux, and Alpaca
microstructure.

TASK-4120 completed Stage 2 real-time budget optimization. Marketaux now uses a
16-minute budgeted cadence, which yields 90 requests/day against the 95/day
guard. This is near the cap without crossing it.

TASK-4121 completed the Stage 3 scheduler setup/execution proof. A task-local
operator override enabled only `official_news_sources_15m`,
`gdelt_news_discovery_15m`, and `marketaux_news_free_30m`; the PowerShell DB
source scheduler ran two forced-due cycles and produced 6/6 guarded execution
artifacts. This proof used `AUDIT_ONLY_NO_PROVIDER_EXECUTION`, made no provider
network calls, made no DB mutation, and did not install a persistent OS
scheduled task.

TASK-4122 completed Stage 4 historical backfill optimization without starting
background collection. The optimized Stage 5 backfill candidates are
`public_context_news_backfill`, `public_market_macro_news_backfill`, and
`microstructure_backfill_batch`, all disabled with `allow_network=false` and
`scheduler_activation_permitted=0`. Public market/macro backfill is explicitly
blocked until the OneDrive-materialized collector file is available locally.

TASK-4123 resolved the Stage 5 materialization blocker by restoring the readable
public market/macro, newswire, and public source-registry files from local
desktop conflict copies, then removing the conflict suffix copies. It executed a
bounded Stage 5 background historical backfill proof from the 2016 baseline:
`federal_register_documents` exported 2 rows for January 2016,
`wikimedia_current_events` recorded an empty provider response for January 2016,
and `microstructure_backfill_batch` produced a dry-run coverage/checkpoint
proof for AAPL 2016-01-04 without credentials or network market-data calls.
The full 2016-to-present run remains disclosed as not complete. Stage 6
L1 quality/coverage audit and L2 handoff decision is now the next active L0
step.

TASK-4124 completed Stage 6 L1 quality/coverage audit. The bounded Stage 5
sample passed raw hash, secret, mapping, and source-time checks for the rows
present: Federal Register rows are macro context with ticker mapping not
required and certified publication timestamps; Wikimedia returned an empty
provider response. L2 handoff is `BLOCKED` because the full 2016-to-present
coverage requirement is not met and strict/proxy feature gates remain closed.

TASK-4125 completed the full 2016-to-present continuation with task-scoped
resumable collector state rather than replacing TASK-4123 evidence. The frozen
window is 2016-01-01 to 2026-06-29 for `federal_register_documents`,
`federal_reserve_press_all`, `cftc_press_releases`, `guardian_open_platform`,
and `wikimedia_current_events`. Final accumulated evidence records 115 provider
events, 6,103 raw files, and 498,382 headline/context rows, with 5/5 source
coverage complete.

TASK-4126 reran Stage 6 against the full TASK-4125 evidence. Raw integrity
failures are 0, mapping blocker rows are 0, and source coverage is 5/5, but
19,492 source-time rows remain uncertified and strict/proxy feature admission
gates remain closed. L2 handoff remains `BLOCKED_SOURCE_TIME_AND_FEATURE_ADMISSION`
until those rows and gates are explicitly resolved.

TASK-4127 resolved that handoff classification without changing trading
authority. It keeps `wikimedia_current_events` historical rows blocked because
the collector contract marks those rows as diagnostic context only with
`source_time_certified_flag=0`. It admits the remaining 478,890
source-time-certified macro/context rows as L2 context-only handoff candidates.
Strict trading gates, trade feature rows, feature builder enablement, order
intent, broker mutation, strategy acceptance, deployment readiness, and
real-capital permission remain closed.

TASK-4128 completed the final current-state end-to-end audit for this six-stage
roadmap. It verifies 6/6 stage statuses in `configs/db_source_acquisition_scheduler.json`,
Stage 5 full coverage complete, and Stage 6 partial L2 context-only handoff
ready. This is not strategy acceptance, deployment readiness, or trading
permission.

TASK-4129 completes the first risk burn-down pass for the six known L0/L1
follow-ups. Wikimedia Current Events rows with only year/month/day evidence are
interpreted as noon UTC for L2 macro context, bringing context rows to the full
498,382 TASK-4125 rows. This does not make those rows trading features. Trading
feature use still requires stricter row-level source timing, mapping precision,
raw-hash integrity, leakage checks, market-data as-of gates, and owner approval.
The scheduler remains proof-validated but not activated. Chrome crawling is
registered only as a disabled, no-network smoke lane for public page snapshots
and selector drift checks. Ticker/news mapping hardening rules are defined for
future audits before any trading-feature admission.

TASK-4130 applies only the public-page hardening work with direct collection
value. Public newswire collection now records a visible fallback order from
RSS/feed to sitemap to robots sitemap to static HTML probe/base pages, classifies
fetch and parse failures into human-readable reasons, and emits non-authority
ticker/entity candidate hints for L2 review. This is deliberately not a broad
crawler framework. Chrome remains a disabled, no-network smoke path for selector
drift and public page availability diagnostics only.

TASK-4131 turns the remaining L0 collection work into a background operation.
The priority order is daily bars remaining, public context news backfill,
public newswire backfill, public market/macro news backfill, and long-running
5-minute bar backfill. The started processes write status under
`data/artifacts/l0_backfill_orchestration/`, and an hourly reporter writes
snapshots plus local alert rows without requiring Codex to stay attached.
Codex is the setup/review operator only; the runtime collectors are Python and
PowerShell processes. This does not activate trading, broker mutation, order
generation, strategy acceptance, deployment readiness, or real capital.

TASK-4132 hardens TASK-4131 from "started" into "operable." The hourly status
path now includes a fast reliability layer with lane health, progress deltas,
last-event age, stall flags, source failure summaries, 5-minute checkpoint
visibility, bounded raw/cache/source-time audit rows, and human-readable current
alerts. A supervisor script may restart only stopped, incomplete lanes when no
STOP file is present; it does not kill running stalled lanes, open trading gates,
or promote data into L2/L3.

TASK-4133 starts the L1 rebuild on top of the new L0 outputs. L1 is now defined
as the evidence checkpoint: normalized source packets must pass source-time,
raw-integrity, mapping, and authority gates before any downstream L2 consumption
is treated as project state. TASK-4133 writes bounded diagnostic samples and
handoff-candidate rows only; it does not mutate L2 tables. Existing direct
L0-to-L2 news ingest surfaces are legacy/non-authoritative until this normalized
L1 gate is used.

TASK-4134 burns down data-present L1 risks without waiting for incomplete
backfills. The daily bar contract now recognizes
`data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv`, the bounded L1 sample
includes daily bars when those CSVs exist, and the legacy direct L0-to-L2 news
ingest CLI fails closed unless explicitly overridden for diagnostic repair.
Missing-data/backfill-incomplete items remain blockers rather than negatives.

TASK-4135 is the L1-to-L2 transition checkpoint. It freezes a practical
handoff contract, records data-present coverage, and captures a local-only GPT
consult response for L2 development guidance. GitHub is explicitly excluded
from that consult because the latest L0/L1 work is not committed/pushed. The
task remains diagnostic-only and does not materialize L2.

TASK-4136 starts the L2 intake layer without producing trading features. It
keeps news and macro on a future trading-feature path, but requires source-time,
ticker/entity/macro-scope mapping, deduplication, stale-data policy, and
effect-window validation before admission. The legacy L2 news builder is
quarantined so new L2 work enters through the intake contract instead of the
old direct news path.

TASK-4138 applies the practical L1 hardening recommended by the TASK-4137 GPT
Pro review. It does not add broad crawling or feature generation. Instead, it
records the source-time kind, precision, usable-after policy, authority status,
and block reason for each L1 source family. Wikimedia day precision may be
represented as noon UTC only as imputed nominal time, not as actual market
source time. News, macro, and newswire rows remain future feature candidates
only after L2 mapping, deduplication, stale-data, and effect-window checks.

| Source family | Implementation mode | Notes |
|---|---|---|
| `official_public_releases` | Python HTTP/RSS/API collector | Official-primary diagnostic rows only. |
| `gdelt_news_events` | Python API collector | Discovery-only. Broad high-frequency queries remain out of scope. |
| `marketaux_news_free` | Python API collector | Metadata proxy; quota ledger and token redaction required. |
| `public_newswire_feeds` | Python HTTP/RSS/page collector | PRNewswire, GlobeNewswire, and BusinessWire discovery/context collection. |
| `public_context_news_feeds` | Python HTTP/RSS/API collector | Fed, BLS, BEA, CFTC, Federal Register, White House, Nasdaq Trader, and similar macro context. |
| `public_market_macro_news_feeds` | Python HTTP/RSS/page collector | Market and macro context feeds. Some restored OneDrive files may need local materialization before execution. |
| `microstructure_quotes` / `microstructure_trades` | Python Alpaca historical collector | Diagnostic raw quote/trade infrastructure only; feature builder remains blocked. |
| `public_headline_browser_watch` | Chrome/Node smoke only | Browser-based smoke is not the default runtime collector. |
| Codex/GPT | Planning, recovery, review only | Codex/GPT is not a runtime collection engine or source of truth. |

## Mapping Status

Ticker/entity/news mapping exists as an initial L0/L1 gate, not as a final
institutional quality resolver.

Current implemented checks include:

- `tools/db/news_l0_l1.py` checks symbols, tickers, entities, and entity maps.
- Rows missing required mapping remain blocked with mapping-related status.
- Macro/context rows may bypass ticker mapping only when explicitly marked as
  macro context and not as symbol-specific evidence.
- Public newswire mapping has a versioned mapper label, but Stage 6 must audit
  precision, ambiguity, ticker collisions, and false-positive source links
  before L2 handoff.

## Scheduler Governance

The committed scheduler baseline remains conservative:

- all jobs disabled by default
- `allow_network=false` by default
- strategy remains `NOT_ACCEPTED`
- deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real capital remains `FORBIDDEN`
- broker mutation, paper promotion, live order, replay permission, and
  buy/sell signal generation remain closed

The local operator override may enable bounded diagnostic collection only. Any
runtime activation must be recorded through task reports, status snapshots, and
validators before being treated as project state.

## Project Management Rule

Future L0/L1 source-acquisition changes must update all affected layers together:

1. source code or collector scripts
2. scheduler baseline or local override template when cadence/posture changes
3. source registry when source inventory changes
4. active policy or roadmap documentation when scope/stage changes
5. task registry and doc registry
6. task report, artifact manifest, and validation results
7. the project-management validator when a new invariant is introduced

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
