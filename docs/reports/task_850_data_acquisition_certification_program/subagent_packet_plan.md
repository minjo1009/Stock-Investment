# Task850 Subagent Packet Plan

## Shared Constraints

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- GPT/Chrome and subagent outputs are review-only.
- No raw data deletion.
- No broad redownload until audit proves systemic failure.
- No symbol/date/price/time proximity fallback.
- Missing raw source is reported, not approximated.

## Packets

| packet | role | task focus | edit authority |
| --- | --- | --- | --- |
| P1 | Institutional quant/trader | Review required data families, periods, universe, split/OOS readiness | none, review-only |
| P2 | Backend data engineer | Review canonical manifest schema, storage layout, validator design | none for Task850, implementation later |
| P3 | Market microstructure reviewer | Review Alpaca SIP scope, timestamp namespaces, session filters, leakage risks | none, review-only |
| P4 | Daily data owner | Later Task854 daily certification matrix | Task854 report only |
| P5 | Intraday data owner | Later Task855 15m certification matrix | Task855 report only |
| P6 | Data acquisition engineer | Later Task857 missing-slice download plan | Task857 report only |

## Validation Authority

Task850 validation authority is governance and data-infrastructure health only. It cannot declare strategy acceptance, deployment readiness, live-source readiness, or capital permission.

