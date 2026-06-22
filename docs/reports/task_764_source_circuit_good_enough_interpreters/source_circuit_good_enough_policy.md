# Source Circuit Good-Enough Policy

## Purpose

Task764 defines pragmatic, research-only interpretation rules for source circuits used by the Trader Brain program.

The policy fills the gap between Task732 circuit contexts and Task760 pragmatic meaning. It says what is enough to interpret a source as context, a modifier, or a review-ready meaning candidate without demanding infinite external denominators.

## Standing Rule

Non-operating sources are interpreted as context or modifiers. They are not discarded, and they are not traded directly.

This includes Form 4, 13D/G, 13F, ownership filings, financing 8-Ks, generic 8-Ks before classification, and macro/policy sources. These sources may modify confidence, risk context, special-situation routing, dilution/liquidity context, ownership structure, or theme linkage. They may not create buy/sell/rank/sizing/backtest eligibility.

Direct operating sources and financial results/guidance may support operating meaning only when the source-local facts are visible and as-of safe. Even then, they remain research-only L2/L3 inputs and do not create execution permission.

## Layer Boundary

Allowed:

- Interpret retained L1 evidence using source-specific circuits.
- Extract source-local L2 facts that are visible in the source trace.
- Create L3 review meaning states with explicit uncertainty.
- Preserve context even when denominator, history, or comparator data is incomplete.
- Cap confidence or require confirmation when source trace, timing, or linkage is weak.

Forbidden:

- Source family blanket block.
- Automatic bullish or bearish state from source existence.
- Buy, sell, hold, rank, sizing, allocation, backtest eligibility, or deployment readiness.
- Inferred lifecycle matching.
- Symbol/date/price/time fallback matching.
- Missing context to negative conversion.
- Outcome, future return, price, PnL, or label fields in assignment logic.
- Code promotion from this task.

## Good-Enough Standard

Good enough means the source gives enough source-local facts to assign a bounded interpretation state and explicit uncertainty. It does not mean the investment case is complete.

Stop asking for more data when the available source has enough facts to classify the circuit state and all missing context can be carried as uncertainty, confidence cap, or confirmation need.

Ask for repair or source review only when source trace, timestamp, source family, or required source-local facts are missing.

## Circuit Policies

### Form 4

Enough inputs:

- Insider role or role language.
- Transaction type: purchase, sale, award, option/exercise, tax/admin, or other compensation.
- 10b5-1, planned, automatic, or non-plan status when visible.
- Shares, price, amount, or ownership-after when visible.

Good-enough interpretation:

- Open-market purchase may become insider positive context.
- Non-plan open-market sale by officer/director may become insider negative context.
- Planned, automatic, RSU, option exercise, tax, or compensation flows remain context or confidence cap.
- Missing full holdings denominator is uncertainty, not a negative label.

Stop rule:

- For insider sales, planned/non-plan, purchase/sale, compensation/tax, size, and role are enough unless exact holdings are already available.

### 13D/G

Enough inputs:

- 13D versus 13G state.
- Ownership percent when visible.
- Amendment state when visible.
- Control, board, proposal, activist, or passive language when visible.

Good-enough interpretation:

- Active/control language routes to structural mixed or special-situation context.
- Passive 13G routes to sponsorship, float, or crowding context.
- Missing holder history is uncertainty, not a negative label.

### 13F

Enough inputs:

- Manager, period, reported holding, position value, or position presence.

Good-enough interpretation:

- 13F is stale by design.
- It can support institutional positioning, sponsorship, or crowding context.
- It cannot create a fresh operating catalyst.

### Ownership Filing

Enough inputs:

- Holder identity or beneficial owner language.
- Ownership percent, voting/dispositive power, class, float, or change language when visible.

Good-enough interpretation:

- Ownership filings support float, holder concentration, liquidity, sponsorship, or governance context.
- They do not create revenue, order, backlog, margin, or guidance facts.

### Generic 8-K

Enough inputs:

- Item number, agreement family, event type, or classifier state.
- Operating transmission evidence if an operating claim is requested.

Good-enough interpretation:

- Agreement text alone remains classified context.
- Operating support requires classification plus company-specific operating transmission.
- Governance, compensation, severance, M&A, financing, and boilerplate remain retained context.

### Financing 8-K

Enough inputs:

- Amount or instrument when visible.
- Use of proceeds, dilution feature, liquidity language, covenant, maturity, refinance, or runway context when visible.

Good-enough interpretation:

- Growth funding can be positive review context.
- Survival funding, refinance, or liquidity language can be mixed context.
- Convertible, warrant, ATM, shelf, or offering language can be dilution overhang context.
- Missing full DCF or exact pro-forma dilution is uncertainty, not a discard reason.

### Direct Operating Source

Enough inputs:

- Source-local evidence for customer/order/backlog/demand/supply/margin/production/product/regulatory operating fact.
- Counterparty, product, geography, period, or metric when visible.
- As-of timestamp and source trace.

Good-enough interpretation:

- Direct operating source may support operating primitive facts and L3 operating meaning.
- Weak counterparty or period detail caps confidence rather than creating a negative.
- It cannot bypass L4/L5 gates or create backtest eligibility.

### Financial Results Or Guidance

Enough inputs:

- Reported result, guidance, reaffirmation, raise, cut, margin, revenue, backlog, order, cash flow, or segment fact.
- Period, company source, filing/release/call trace, and as-of timestamp when available.

Good-enough interpretation:

- Results and guidance can support operating meaning states such as reaffirmed guidance, guidance raise, guidance cut, margin pressure, demand acceleration, or demand softness.
- Prior guidance, consensus, or denominator gaps are uncertainty and confirmation needs.
- Direction hints remain review metadata only.

### Macro Or Policy

Enough inputs:

- Policy, budget, tariff, regulation, geopolitics, supply-chain, procurement, or demand theme.
- Company link, sector link, theme link, or explicit missing-link state.

Good-enough interpretation:

- Macro/policy evidence is retained as theme or modifier context.
- Company-specific operating claims require company-specific linkage.
- Weak company link is uncertainty, not a negative label.

## Allowed Downstream Effects

Allowed L2 effects:

- Source-local primitive extraction.
- Context-only fact retention.
- Explicit uncertainty flags.
- Join blocker state.
- Source trace and as-of state.

Allowed L3 effects:

- Review-only meaning state.
- Economic direction hint as metadata only.
- Confidence band or confidence cap.
- Relation readiness tier.
- Needed confirmation.
- Invalidation clue.

Forbidden downstream effects:

- Trade instruction.
- Rank or score.
- Sizing or allocation.
- Candidate assignment.
- Backtest eligibility.
- Deployment readiness.
- Real capital permission.

## Validation Authority

Task764 validation is diagnostic and research-only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
