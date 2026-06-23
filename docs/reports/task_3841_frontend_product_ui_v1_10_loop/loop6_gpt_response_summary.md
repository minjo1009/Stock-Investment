# Loop 6 GPT Response Summary

Loop 6 added a dedicated detail v1 route validator.

Codex action:

- Added `validate:detail-v1`.
- Added the validator to `npm test`.
- The validator checks Candidate, Chain, Position, and Order detail routes for v1 labels, read-only boundary text, and forbidden score/order-submit terms.
