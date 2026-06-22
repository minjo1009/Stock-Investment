# Loop 3 GPT Prompt Summary

Codex asked GPT to confirm whether `Candidate Detail v0` scaffold-only fixture-backed assembly should proceed after Task3826 and Task3827.

The prompt supplied current local facts:

- Candidate Detail fixture had all six detail sections
- risk states included `STALE`, `MISSING`, `CHART_MISSING`, and `SOURCE_NOT_ATTACHED`
- domain components already matched the fixture sections
- no Candidate Detail route existed
- existing brain fixture route hints used `/brain/candidate/<candidateId>`

Codex asked GPT to choose a route path, fixture loading approach, exact patch scope, validations, and failure criteria.
