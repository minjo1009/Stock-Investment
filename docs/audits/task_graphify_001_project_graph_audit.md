# Task GRAPHIFY-001 - Project Graph Audit

## 1. Summary
- install result: `PASS` (`graphifyy` installed successfully)
- graph generated: `YES`
- graph output path:
  - `graphify-out/graph.html`
  - `graphify-out/graph.json`
  - `graphify-out/GRAPH_REPORT.md`
- note:
  - This environment's CLI does not support `graphify .` directly (`unknown command '.'`).
  - Graph generation succeeded with `graphify update .` (same output artifacts produced).

## 2. Graphify Configuration
- package/version:
  - `graphifyy==0.5.0` (installed via pip)
- install commands used:
  - `python -m pip install graphifyy`
  - `graphify install --platform codex`
  - `graphify codex install`
- Codex install status: `PASS`
  - skill installed under `C:\Users\minjo\.agents\skills\graphify\SKILL.md`
  - `AGENTS.md` updated by Graphify installer
  - `.codex/hooks.json` pre-tool hook registered
- Codex multi-agent support:
  - `C:\Users\minjo\.codex\config.toml` updated with:
    - `[features]`
    - `multi_agent = true`
- `.graphifyignore` summary:
  - created at project root
  - excludes env/secret/token/key patterns
  - excludes runtime DB/cache/noisy generated directories
  - excludes raw/unsanitized KIS fixture patterns
  - retains source/docs/tests (no logic or report exclusions)

## 3. Generated Outputs
- `graphify-out/graph.html`: found
- `graphify-out/graph.json`: found
- `graphify-out/GRAPH_REPORT.md`: found

## 4. Cluster Review

### 4.1 Backtest / Strategy Cluster
- status: `partial`
- expected nodes:
  - `engine_full.py`: found
  - `strategy/conditions.py`: found
  - `entry_gates`: found
  - `task_083`: missing (task label not directly indexed as node name)
  - `task_084`: missing (task label not directly indexed as node name)
  - `task_093`: missing (task label not directly indexed as node name)
  - `task_093_review`: missing (task label not directly indexed as node name)
  - `task_094`: missing (task label not directly indexed as node name)
- interpretation:
  - code nodes are captured well
  - task-id style report nodes are not consistently represented as graph nodes

### 4.2 Runtime / Paper Ops Cluster
- status: `found`
- key nodes found:
  - `task_089_market_signal_refresh.py`
  - `run_trade_once.py`
  - `task_087_pilot_evidence.py`
  - `task_088_evidence_decision.py`
  - `run_phase5_paper_loop.ps1`
- interpretation:
  - runtime evidence loop is graph-visible and traceable

### 4.3 Broker Lifecycle Cluster
- status: `partial`
- key nodes found:
  - `task_091a_controlled_broker_lifecycle.py`
  - `kis_client.py`
  - `cancel_loop.py`
  - `reconciliation.py`
  - `store.py`
- missing:
  - `fixtures/kis` as cluster keyword node
- interpretation:
  - lifecycle code path is visible
  - fixture directories are not represented as strong semantic nodes

### 4.4 Contracts / Safety Cluster
- status: `partial`
- found:
  - `unknown` concept appears
- missing:
  - `execution_state_contract.md`
  - `cancel_reconcile_loop_contract.md`
  - `task_086` docs cluster
  - explicit `kill switch` concept node
  - explicit `reconciliation critical` concept node
- interpretation:
  - markdown contract docs were not strongly ingested into conceptual graph nodes
  - safety semantics exist in code/tests but weakly connected as named contract entities

### 4.5 UI / Reporting Cluster
- status: `partial`
- found:
  - `src/ui/app.py`
- missing:
  - `docs/reports` as concept node
  - `docs/audits` as concept node
  - `docs/INDEX.md` node
- interpretation:
  - UI code is captured
  - report/document topology is underrepresented

## 5. God Nodes / Over-Coupling
Top over-connected nodes from graph output:
1. `HybridAdaptiveStrategy` (161 edges) - external reference corpus dominates centrality
2. `TestRepositoryFoundationStructure` (122 edges) - test mega-hub; expected but high coupling
3. `HybridAdaptiveStrategyV2` (81 edges) - external reference corpus
4. `EnsembleStrategy` (73 edges) - external reference corpus
5. `app.py` (41 edges) - core UI over-aggregation risk
6. `initialize_store()` (36 edges) - persistent state choke point
7. `run_controlled_lifecycle()` (30 edges) - broker lifecycle concentration
8. `engine_full.py` (30 edges) - backtest orchestration concentration

Assessment:
- acceptable:
  - `store.py`, `cancel_loop.py`, `engine_full.py` being central is expected for core system flows.
- refactor attention needed:
  - `src/ui/app.py` and large test hub concentration suggest boundary and decomposition opportunities.
  - external reference sources inflate graph centrality and can hide project-local critical coupling.

## 6. Architecture Insights

### Strengths
- runtime evidence loop (`089 -> 087 -> 088`) is structurally visible.
- broker lifecycle safety flow (submit/cancel/reconcile/store) appears as coherent cluster.
- backtest engine and analytics/report scripts are linked sufficiently for root-cause workflows.

### Hidden Coupling
- `app.py` still acts as a broad integration hub across reporting and runtime contexts.
- state store and reconciliation logic remain high-centrality choke points.
- orchestration/testing dependencies are tightly connected to foundational structures.

### Duplicated Logic Risks
- risk/control semantics appear across analysis scripts and runtime controls with weak conceptual normalization in graph labels.
- task/report naming is not canonicalized into shared graph entities, reducing lineage clarity.

### Stale Docs Risk
- contract/report markdown nodes are weakly represented in graph topology.
- this increases risk of task drift (code evolves while doc graph remains thin).

## 7. Recommended Follow-Up Tasks
1. **Graph scope normalization**
   - add/maintain a Graphify profile that prioritizes project-local `src/`, `docs/`, `tests/` and down-weights large external reference corpora.
2. **Contract indexing task**
   - add graph-friendly metadata headers to `docs/contracts/*.md` and key `docs/reports/*` to improve contract node discoverability.
3. **UI decomposition audit**
   - split `src/ui/app.py` into report loader, chart builder, and runtime monitor modules.
4. **Safety flow simplification**
   - define a single canonical safety-state map document and ensure code references that shared taxonomy.
5. **Task/report lineage registry**
   - generate machine-readable task lineage manifest (`task -> script -> report`) to improve graph cluster fidelity.
6. **Reference corpus separation**
   - move exploratory external repos to optional graph scope or separate graph runs.
7. **Graph CI check**
   - add a non-blocking CI check that validates required critical nodes/edges are present after major changes.

## 8. Final Verdict
Is graphify useful for this project? **YES**

Reason:
- it surfaces real over-coupling hotspots and runtime/broker safety topology quickly,
- and provides a practical structure map for architecture audits and handoff,
- though doc/task lineage visibility needs follow-up normalization.
