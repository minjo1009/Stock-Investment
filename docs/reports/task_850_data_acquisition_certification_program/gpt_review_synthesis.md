# Task850 GPT / Subagent Review Synthesis

## Conclusion

The review panel agrees that Task850-Task859 must be a data certification program, not a broad data redownload and not a backtest execution program.

## Institutional Quant Review

- Require point-in-time universe data before any universe-level claim.
- Do not treat current top500 files as survivorship-safe.
- Freeze split/OOS/final holdout before seeing any result.
- Keep cost and slippage assumptions separate from Alpaca AFRM/AMD microstructure coverage.

## Backend Data Engineering Review

- Add schema fingerprint, content hash, source path, as-of cutoff, data availability timestamp, and validator version to the manifest.
- File-by-file certification is required.
- Mixed schema must be normalized only through an explicit schema map.
- Redownload should be gap-driven, not global.

## Microstructure / Leakage Review

- First controlled replay should use certified daily plus 15m bars only.
- Alpaca SIP quotes/trades stay research-only because current observed coverage is narrow and historical flags are not live-ready.
- Tradable-after timestamps require a certified regular-session calendar.
- Daily and 15m adjustment policies must be reconciled before adjusted replay.

## Final Program Upgrade

Task859 closeout should default to `MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY` unless every market data, calendar, corporate-action, PIT universe, schema, and hash gate passes.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
