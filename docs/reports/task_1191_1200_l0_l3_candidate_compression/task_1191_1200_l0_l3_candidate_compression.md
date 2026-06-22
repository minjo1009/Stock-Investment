# Task1191-1200 L0-L3 Candidate Compression

## Decision Summary

- Verdict: `l0_l3_candidate_compression_implemented_replay_not_executed`.
- L0 rows: 29397.
- L0 pass rows: 16065.
- L1 packets: 29397.
- L2 meaning rows: 29397.
- L3 relation edges: 117588.
- Compressed candidates: 9450.
- Top50 avg hit rate, eval only: 0.531746.
- Policy preregistration allowed: `1`.
- Replay executed: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task implements the L0-L3 front-brain strengthening plan without running a new PnL replay.

Implemented layers:

1. L0 filters remove bad tradable objects before ranking.
2. L0 industry/theme mapper creates diagnostic industry and theme labels.
3. L1 source packets bind SEC submissions, price context, and expert context sources.
4. L2 meaning rows translate raw fields into momentum, liquidity, volatility, filing, and thematic states.
5. L3 edges connect company, industry, theme, policy driver, and risk invalidator.
6. Candidate compression produces top 50/100/150 lists before any L4/L5 replay.

Outcome data is used only in Task1199 evaluation rows and is explicitly blocked from assignment logic.

## No-Background Decision-Maker Report

The code now has a front brain.

It first throws out obviously bad objects, then maps industry and theme, then builds source and meaning packets, then creates relation edges, then compresses the universe into candidates.

No new backtest was run. This is the gate before another replay.

## Artifact Manifest

- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1191_l0_security_filter.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1192_industry_theme_map.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1193_l1_source_packets.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1194_l2_meaning_panel.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1195_macro_policy_bridge.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1196_l3_relation_edges.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1197_compressed_candidates.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1198_negative_fixtures.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1199_candidate_quality_diagnostic.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_replay_preregistration_gate.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_l0_l3_candidate_compression_closeout.csv`
- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_l0_l3_candidate_compression_closeout.json`
