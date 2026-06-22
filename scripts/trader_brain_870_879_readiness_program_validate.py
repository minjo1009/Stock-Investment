from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASK_DIRS = {
    "Task870": ROOT / "docs/reports/task_870_controlled_replay_readiness_program",
    "Task871": ROOT / "docs/reports/task_871_adapter_trade_spec_authority_contract",
    "Task872": ROOT / "docs/reports/task_872_explicit_harness_universe_contract",
    "Task873": ROOT / "docs/reports/task_873_exchange_calendar_certification",
    "Task874": ROOT / "docs/reports/task_874_corporate_action_adjustment_proof",
    "Task875": ROOT / "docs/reports/task_875_daily_canonical_normalization_plan",
    "Task876": ROOT / "docs/reports/task_876_intraday_15m_canonical_normalization_plan",
    "Task877": ROOT / "docs/reports/task_877_market_data_gate_promotion_validator",
    "Task878": ROOT / "docs/reports/task_878_controlled_trade_spec_builder_plan",
    "Task879": ROOT / "docs/reports/task_879_first_controlled_replay_retry_plan",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for task_id, directory in TASK_DIRS.items():
        if not directory.exists():
            errors.append(f"{task_id}: missing directory")
            continue
        if not list(directory.glob("*.md")):
            errors.append(f"{task_id}: missing report")
        if not list(directory.glob("*decision.csv")):
            errors.append(f"{task_id}: missing decision csv")
        manifest = directory / "artifact_manifest.csv"
        if not manifest.exists():
            errors.append(f"{task_id}: missing artifact_manifest.csv")

    authority = TASK_DIRS["Task871"] / "trade_spec_authority_contract.csv"
    if authority.exists():
        rows = read_csv(authority)
        required_fields = {"symbol", "side", "tradable_after_ts", "entry_policy_id", "exit_policy_id", "position_policy_id", "initial_capital", "benchmark_id"}
        present = {row.get("field") for row in rows}
        missing = required_fields - present
        if missing:
            errors.append(f"Task871: missing trade-spec fields {sorted(missing)}")
    else:
        errors.append("Task871: missing trade_spec_authority_contract.csv")

    universe = TASK_DIRS["Task872"] / "explicit_harness_universe_contract.csv"
    if universe.exists():
        text = universe.read_text(encoding="utf-8", errors="replace")
        for symbol in ["QQQ", "NVDA", "AMD", "SMH"]:
            if symbol not in text:
                errors.append(f"Task872: missing symbol {symbol}")
    else:
        errors.append("Task872: missing explicit_harness_universe_contract.csv")

    rules = TASK_DIRS["Task877"] / "market_data_gate_promotion_rules.csv"
    if rules.exists():
        text = rules.read_text(encoding="utf-8", errors="replace")
        for gate in ["calendar", "corporate_actions", "daily_bars", "intraday_15m", "universe", "hashes"]:
            if gate not in text:
                errors.append(f"Task877: missing gate {gate}")
    else:
        errors.append("Task877: missing market_data_gate_promotion_rules.csv")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for directory in TASK_DIRS.values()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    )
    for phrase in ["NOT_ACCEPTED", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in combined:
            errors.append(f"missing status phrase {phrase}")
    for forbidden in ["strategy_acceptance,accepted", "deployment_ready,true", "real_capital,allowed"]:
        if forbidden in combined:
            errors.append(f"forbidden phrase found: {forbidden}")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    ids = {row.get("task_id") for row in registry}
    for idx in range(870, 880):
        if f"Task{idx}" not in ids:
            errors.append(f"registry missing Task{idx}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_870_879_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_870_879_OK] controlled replay readiness program is designed")


if __name__ == "__main__":
    main()
