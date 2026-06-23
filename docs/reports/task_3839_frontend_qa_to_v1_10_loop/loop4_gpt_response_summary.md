# Loop 4 GPT Response Summary

GPT verdict: modify `StatusRow` only.

Required behavior:

- use `numberOfLines={1}`
- use `ellipsizeMode="middle"`
- apply to `value` and `sourceRef`
- preserve source/path visibility at the beginning and end

GPT explicitly prohibited new generic components, interaction handlers, modal/tooltip/bottom-sheet expansion, fixture changes, read-model changes, route changes, and authority/boundary hiding.
