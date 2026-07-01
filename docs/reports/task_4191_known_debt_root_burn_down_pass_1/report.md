# TASK-4191 Known Debt Root Burn Down Pass 1

## Goal

Answer the practical cleanup question: which remaining root known-debt entries can actually be deleted or moved now?

## Results

No physical move/delete was performed in this pass. The useful result is a corrected decision:

- `config/` is absent now. It remains an optional legacy alias in hygiene policy so a future re-created `config/` is flagged for review instead of silently accepted.
- `kis_paper.env` is the actual sensitive local root file and must not be read or deleted.
- `frontend` is not dead clutter. `frontend/trader-terminal` and `frontend/frontend_data` are still referenced by docs/catalog surfaces.
- `tasks` is not safely removable. Code and docs still reference `tasks/task_registry.csv` and `tasks/active_task_registry.csv`.

`frontend` and `tasks` were reclassified out of active root cleanup debt. `config/` was corrected to absent optional legacy alias debt.

Remaining actual root known debt:

- `trading.db`
- `trading-DESKTOP-2R00TB4.db`

Those DB files still require runtime-owner review before move/delete.

## User-Facing Bottom Line

The next thing is not "read reports." The next real cleanup target is the two root DB files. Everything else that looked messy is either active legacy surface or sensitive local config and needs migration first.

## Safety

No broker mutation, live order, paper promotion, strategy acceptance, deployment readiness, source data mutation, or DB mutation occurred.
