from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = Path.home() / ".codex" / "skills"
TASK_ID = "task_2601_2640_docs_wiki_skill_operating_cleanup"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_text(path: Path) -> str:
    require(path.exists(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate_skill(name: str) -> None:
    skill_dir = SKILLS_ROOT / name
    require(skill_dir.exists(), f"missing skill: {name}")
    quick_validate = SKILLS_ROOT / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    result = subprocess.run(
        [sys.executable, str(quick_validate), str(skill_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    require(result.returncode == 0, f"skill validation failed for {name}: {result.stdout} {result.stderr}")
    body = read_text(skill_dir / "SKILL.md")
    require("NOT_ACCEPTED" in body, f"{name} missing NOT_ACCEPTED guardrail")
    require("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in body, f"{name} missing deployment guardrail")
    require("FORBIDDEN" in body or "real capital" in body.lower(), f"{name} missing real-capital guardrail")
    require("[TODO" not in body, f"{name} still has TODO placeholder")
    if name != "trader-brain-source-acquisition":
        require("trader-brain-source-acquisition" in body or name == "trader-brain-policy-freeze-and-compare", f"{name} missing source-acquisition routing boundary")


def main() -> None:
    vault = read_text(ROOT / "docs/obsidian/Vault Home.md")
    os_map = read_text(ROOT / "docs/obsidian/mocs/Operating System Map.md")
    quant_map = read_text(ROOT / "docs/obsidian/mocs/Quant Research Map.md")
    require("Task599" not in vault and "Task598" not in vault, "Vault Home still has stale current Task598/599 links")
    require("Obsidian is a navigation cockpit only" in vault, "Vault Home missing cockpit boundary")
    require("Project Operating State" in os_map, "Operating map missing operating state pointer")
    require("Validation success does not modify strategy acceptance status" in os_map, "Operating map missing validation boundary")
    require("Task2581-2600" in quant_map, "Quant map missing latest task pointer")

    wiki_files = [
        "README.md",
        "status_boundaries.md",
        "source_truth_map.md",
        "backtest_replay_contract.md",
        "task_artifact_index.md",
        "anti_loop_checklist.md",
        "subagent_gpt_boundaries.md",
    ]
    for file_name in wiki_files:
        text = read_text(ROOT / "docs/llm_wiki" / file_name)
        require("NOT_ACCEPTED" in text or file_name not in {"README.md", "status_boundaries.md"}, f"{file_name} missing status where expected")
    require("Do not add sources merely because performance is disappointing" in read_text(ROOT / "docs/llm_wiki/source_truth_map.md"), "source truth map missing anti-source-loop rule")
    require("If nothing changed, do not rerun the same experiment" in read_text(ROOT / "docs/llm_wiki/backtest_replay_contract.md"), "backtest contract missing anti-rerun rule")
    require("L0-L5 judgment logic belongs in backend engine code" in read_text(ROOT / "docs/llm_wiki/README.md"), "LLM wiki missing brain/skill boundary")
    require("turning skills into strategy engines" in read_text(ROOT / "docs/llm_wiki/anti_loop_checklist.md"), "anti-loop checklist missing skill-as-engine warning")

    for skill in [
        "trader-brain-docs-wiki-maintenance",
        "trader-brain-paper-run",
        "trader-brain-mdd-attribution",
        "trader-brain-policy-freeze-and-compare",
    ]:
        validate_skill(skill)

    closeout = read_csv(OUT_DIR / "task2640_closeout.csv")
    hardening = read_csv(OUT_DIR / "task2641_five_loop_hardening_audit.csv")
    decision = read_csv(REPORT_DIR / "task_2640_decision.csv")
    require(closeout == decision, "closeout and decision mismatch")
    require(closeout[0]["strategy_acceptance"] == "NOT_ACCEPTED", "strategy status changed")
    require(closeout[0]["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    require(closeout[0]["real_capital"] == "FORBIDDEN", "real capital status changed")
    require(len(hardening) == 5, "five-loop hardening audit must have five rows")
    require(hardening[-1]["focus"] == "final_regression", "five-loop audit missing final regression loop")
    require("Five-Loop Hardening" in read_text(REPORT_DIR / "task_2601_2640_docs_wiki_skill_operating_cleanup.md"), "report missing five-loop hardening section")
    require((OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    require(any(row["task_id"] == "Task2601" for row in registry), "registry missing Task2601 row")
    operating_state = read_text(ROOT / "docs/operating_system/project_operating_state.md")
    require("127. Task2601-Task2640" in operating_state, "operating state missing Task2601-2640 line")
    print("[TASK2601_2640_DOCS_WIKI_SKILL_CLEANUP_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
