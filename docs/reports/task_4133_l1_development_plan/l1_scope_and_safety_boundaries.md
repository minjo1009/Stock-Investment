# TASK-4133 L1 Scope And Safety Boundaries

L1 is an evidence and gate layer. It is not a strategy, trading feature factory, or order path.

Required boundaries:

- Missing or stale source evidence is UNKNOWN/BLOCKER, not negative evidence.
- Public newswire rows are discovery-only candidate hints unless a later task proves authority and mapping quality.
- Macro/context rows may bypass ticker mapping only when explicitly non-symbol-specific.
- 5-minute DB resident rows must carry a DB partition hash rather than relying on a raw file path alone.
- Daily bars may use `data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv` as the raw CSV source when that L0 backfill output exists.
- TASK-4133 does not mutate L2 tables, broker state, paper/live orders, strategy acceptance, deployment readiness, or real-capital state.
