from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = Path.home() / ".codex" / "skills" / "trader-brain-ios-cockpit-frontend"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, term: str, name: str) -> None:
    if term not in text:
        fail(f"{name} missing {term}")


def main() -> None:
    llm_readme = read(ROOT / "docs" / "llm_wiki" / "README.md")
    llm_frontend = read(ROOT / "docs" / "llm_wiki" / "frontend_ios_cockpit.md")
    vault_home = read(ROOT / "docs" / "obsidian" / "Vault Home.md")
    mobile_map = read(ROOT / "docs" / "obsidian" / "mocs" / "Mobile Cockpit Map.md")
    skill_md = read(SKILL / "SKILL.md")
    skill_ref = read(SKILL / "references" / "ios_cockpit_frontend_contract.md")
    registry = read(ROOT / "tasks" / "task_registry.csv")
    operating = read(ROOT / "docs" / "operating_system" / "project_operating_state.md")

    status_checked = {
        "llm_readme": llm_readme,
        "llm_frontend": llm_frontend,
        "vault_home": vault_home,
        "mobile_map": mobile_map,
        "skill_md": skill_md,
        "skill_ref": skill_ref,
        "operating": operating,
    }
    for name, text in status_checked.items():
        require(text, "NOT_ACCEPTED", name)
        require(text, "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", name)
        require(text, "FORBIDDEN", name)

    require(registry, "NOT_ACCEPTED", "registry")
    require(llm_readme, "frontend_ios_cockpit.md", "llm_readme")
    require(vault_home, "Mobile Cockpit Map.md", "vault_home")
    require(llm_frontend, "trader-brain-ios-cockpit-frontend", "llm_frontend")
    require(mobile_map, "Task2831-2840", "mobile_map")
    require(skill_md, "apps/ios-trader-brain", "skill_md")
    require(skill_md, "Do not add live order buttons", "skill_md")
    require(skill_ref, "realOrdersAllowed: false", "skill_ref")
    require(skill_ref, "bottom time/date x-axis", "skill_ref")
    require(registry, "Task2841", "registry")
    require(operating, "Task2841-Task2850", "operating")

    forbidden = ["realOrdersAllowed: true", "liveOrderButtonsAllowed: true", "Strategy: ACCEPTED"]
    combined = "\n".join([llm_readme, llm_frontend, vault_home, mobile_map, skill_md, skill_ref])
    for term in forbidden:
        if term in combined:
            fail(f"forbidden claim detected: {term}")

    print("PASS: Task2841-2850 frontend wiki and skillization is valid")


if __name__ == "__main__":
    main()
