# Frontend Visual Evidence Contract

- React Trader Terminal continues to read only `trader_terminal_catalog.json`.
- No event/news/execution marker may be shown unless the source artifact exists.
- Every visual KPI must remain under Task/Artifact/PNL/Status/Hash provenance.
- Heavy chart windows should migrate to lazy chart artifacts or an API boundary before deployment-style usage.