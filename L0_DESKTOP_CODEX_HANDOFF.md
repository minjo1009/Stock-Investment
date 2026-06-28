# L0 Desktop Codex Handoff

Read the full handoff when OneDrive sync catches up:

`docs/reports/task_l0_collection_host_migration_handoff/l0_collection_host_migration_handoff.md`

Notebook-side collection workers were stopped at `2026-06-28T22:59Z`.
OneDrive sync nudge from notebook was requested after desktop did not see this file.
After cleanup, no `python*` collection process remained on the notebook.

Desktop restart checklist:

1. Confirm OneDrive sync is complete.
2. Run `python scripts/report_l0_collection_status.py`.
3. Start collectors on desktop only; do not run notebook and desktop collectors at the same time.
4. Suggested restart commands:

```powershell
.\scripts\start_l0_bar_full_backfill.ps1 -Lanes 5m
.\scripts\start_l0_news_background_collector.ps1
.\scripts\start_l0_news_full_backfill.ps1
.\scripts\start_l0_public_newswire_collector.ps1
.\scripts\start_l0_public_newswire_backfill.ps1
.\scripts\start_l0_public_context_news_collector.ps1
.\scripts\start_l0_public_context_news_backfill.ps1
.\scripts\start_l0_public_market_macro_news_collector.ps1
.\scripts\start_l0_public_market_macro_news_backfill.ps1
.\scripts\start_l0_public_industry_dive_news_backfill.ps1
```

Latest notebook status before stop:

- Daily bars: `11,965/12,040`, `99.3771%`, stopped.
- 5m bars: `17,374,752` rows, `715` symbols, `5.4054%`, stopped for host migration.
- GDELT: `13,918/367,872`, `3.7834%`, cursor `20160524233000`, stopped for host migration.
- Marketaux: `94/26,499`, `0.3547%`, daily cap exhausted for `2026-06-28`.
- Newswire live: `4,750` rows.
- Newswire backfill: `1,761/4,099`, `42.9617%`, rows `15,970`.
- Context news backfill: `79/149`, `53.0201%`, rows `125,115`.
- Market/macro live: `68/68` sources, rows `17,820`, blocked `0`.
- Market/macro backfill: `760/2,611`, `29.1076%`, rows `96,246`.
- Industry Dive backfill: `11/2,338`, `0.4705%`, rows `983`.

Key weekend changes:

- Newswire collector improved to use article metadata descriptions and source-declared exchange tags without ticker-token fallback.
- Market/macro news collector expanded to `68` live RSS/HTML sources.
- Market/macro historical backfill expanded to `21` sources.
- Separate Industry/sector Dive backfill covers `22` archives.
- Chrome crawler remains fallback/verification only; primary path is RSS/API/sitemap/WordPress REST.
