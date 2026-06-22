# Task753 GPT Review Notes

GPT was given a new-engineer onboarding packet with project status, architecture, cleanup history, W2 files, imports, and forbidden claims.

Applied review points:

1. Do not promote `engine.py` or `engine_full.py` as canonical W2 core.
2. Remove or explicitly gate sample fallback from canonical data loading.
3. Treat next-open usage as requiring an explicit as-of/execution convention.
4. Keep `engine_full.py` owner-review-only because it imports risk/execution/portfolio/universe/strategy layers.
5. No strategy or deployment status changes.
