# Workstream Map

| Workstream | Owner team | Reviewer team | Active source | Forbidden actions |
|---|---|---|---|---|
| Active operating layer | Research Governance | Governance Reviewer | `docs/active/` | Do not use active docs to change strategy acceptance without registry/readiness evidence. |
| Product / Frontend App | Frontend/UI | Research Governance | `frontend/trader-terminal`, frontend reports | Do not present UI polish as deployment readiness. |
| Trader Brain Backend | Regime Research, Intraday Continuation Research | Backtest & Simulation Infra | current strategy reports and module files | Do not infer lifecycle joins or use future labels for assignment logic. |
| Data / DB / Scheduler | Data & Market Microstructure | Research Governance | readiness registry, source reports, DB/source contracts | Do not approximate missing raw sources. |
| Backtest / Validation | Backtest & Simulation Infra | Research Governance | replay/backtest reports and validators | Do not claim acceptance without split/OOS, leakage, cost/slippage, and artifact audit. |
| Execution / Broker / Risk | Execution & Risk | Data & Market Microstructure | execution reports and broker truth contracts | Do not touch broker mutation or order generation in cleanup tasks. |
| Governance / Archive | Research Governance | Relevant owner team | task registry, manifests, archive/delete candidates | Do not move or delete artifacts without an approved manifest. |

