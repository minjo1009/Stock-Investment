# Team Routes

Use this table when generating a GPT/Chrome review packet.

| Lane | Owner Team | Reviewer Team | Default Read Scope | Highest-Value GPT/Chrome Review |
|---|---|---|---|---|
| strategy | Regime Research | Research Governance | Task599, Task604, current operating model, strategy acceptance contract | Acceptance-language overclaim and missing gate review |
| backtest | Backtest & Simulation Infra | Research Governance | T602 reports, replay diffs, Task512, cost/slippage reports | Exact lifecycle, split/OOS, leakage, replay gap review |
| frontend | Frontend/UI | Research Governance | Task594, Task597, Task603-1, frontend catalog, browser screenshot | Five-second blocker visibility and mobile overflow review |
| data | Data & Market Microstructure | Research Governance | source-health reports, Task590, Task571-575, readiness registry | Missing source and freshness ledger review |
| execution | Execution & Risk | Data & Market Microstructure | T600 reports, broker truth, STOP/TP, risk reports | Broker-truth SELL and proxy-vs-realized separation review |
| slack | Slack/EOD | Research Governance | Task589, Slack audits, EOD reports | Blocker-first wording and duplicate/noise guard review |
| chart | Chart Evidence | Intraday Continuation Research | chart packets, Task594, Task599 review packet, frontend chart code | Exact-id visual packet and fake-marker prevention review |
| governance | Research Governance | Relevant owner team | report standard, task registry, closeout protocol | Manifest, registry, and status-change discipline review |

## 필수-Led Routing

필수 / Regime Research owns the top-level strategy gate language. For any strategy or acceptance review packet, route the final interpretation back to 필수 and Research Governance before implementation.

## Write Scope

Default GPT/Chrome packets are read-only. A packet may request repo edits only after a reviewer converts the finding into a normal task with a disjoint write scope and validation command.

## Validation Authority

Every lane must apply `docs/architecture/test_validation_canonicalization_map.md` before interpreting test or validation output.

Passing tests do not change:

- strategy acceptance
- deployment readiness
- broker truth completion
- real-capital permission
