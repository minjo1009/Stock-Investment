# Task753 Subagent Review Notes

Three read-only subagents reviewed distinct scopes:

1. Backtest Core: `models.py`, `data_loader.py`, and `analysis.py` are the only near-term reusable candidates. `engine.py` needs repair. `engine_full.py` remains owner-review-only.
2. Data/As-of: sample fallback violates missing-source rules; next-open and full-period portfolio ranking require leakage/as-of gates.
3. Test/Governance: W2 has weak direct test coverage. Historical/EVIDENCE_ONLY tests cannot promote W2.
