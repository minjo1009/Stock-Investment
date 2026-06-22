from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SURFACE_ROOTS = [
    "AGENTS.md",
    "skills",
    "docs/ownership",
    "docs/operating_system",
    "docs/architecture",
    "docs/contracts",
]

REQUIRED_REFERENCES = [
    "docs/architecture/src_canonicalization_map.md",
    "docs/architecture/test_validation_canonicalization_map.md",
    "docs/ownership/subagent_roster_and_routing.md",
    "docs/ownership/subagent_packet_standard.md",
    "skills/gpt-chrome-review-subagent/SKILL.md",
]

OVERCLAIM_PHRASES = [
    "All tests passed",
    "Validation complete",
    "System healthy",
    "Production ready",
    "Brain validated",
    "Canonical package certified",
]


@dataclass(frozen=True)
class SkillMdRow:
    path: str
    surface: str
    role: str
    owner_team: str
    authority_level: str
    mentions_gpt: int
    mentions_test_authority: int
    mentions_src_map: int
    overclaim_phrase_count: int
    has_mojibake_hint: int
    required_next_action: str


def iter_surface_files() -> list[Path]:
    files: list[Path] = []
    for root_text in SURFACE_ROOTS:
        root = ROOT / root_text
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".py"})
    return sorted(set(files))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def classify_surface(path: str) -> str:
    if path == "AGENTS.md":
        return "root_agent_rules"
    if path.startswith("skills/"):
        return "skill"
    if path.startswith("docs/ownership/"):
        return "ownership"
    if path.startswith("docs/operating_system/"):
        return "operating_system"
    if path.startswith("docs/architecture/"):
        return "architecture"
    if path.startswith("docs/contracts/"):
        return "contract"
    return "other"


def classify_role(path: str) -> str:
    name = Path(path).name.lower()
    if name == "skill.md" or path.endswith("/SKILL.md"):
        return "skill_entrypoint"
    if "subagent" in path:
        return "subagent_contract_or_route"
    if "gpt" in path.lower() or "chrome" in path.lower():
        return "gpt_review_contract"
    if "canonical" in path.lower() or "map" in path.lower():
        return "canonical_map"
    if "registry" in path.lower() or "readiness" in path.lower():
        return "governance_registry"
    return "governance_doc"


def owner_team(surface: str, role: str) -> str:
    if "gpt" in role or "subagent" in role:
        return "Research Governance"
    if surface == "architecture":
        return "Research Governance"
    if surface == "skill":
        return "Research Governance"
    if surface == "ownership":
        return "Research Governance"
    return "Research Governance"


def authority_level(path: str, role: str) -> str:
    if role in {"skill_entrypoint", "subagent_contract_or_route", "gpt_review_contract"}:
        return "OPERATING_RULE"
    if role in {"canonical_map", "governance_registry"}:
        return "CANONICAL_REFERENCE"
    if path.endswith(".py"):
        return "HELPER_SCRIPT"
    return "SUPPORTING_DOC"


def count_overclaims(text: str) -> int:
    return sum(text.count(phrase) for phrase in OVERCLAIM_PHRASES)


def has_mojibake_hint(text: str) -> int:
    hints = ["�", "?꾩", "肄붾", "吏", "蹂", "媛", "濡"]
    return int(any(hint in text for hint in hints))


def next_action(row: SkillMdRow) -> str:
    if row.has_mojibake_hint:
        return "repair_readability_before_reuse"
    if row.overclaim_phrase_count and row.path not in {
        "docs/architecture/test_validation_canonicalization_map.md",
        "docs/architecture/project_status_authority_matrix.md",
    }:
        return "review_overclaim_context"
    if row.role in {"skill_entrypoint", "subagent_contract_or_route", "gpt_review_contract"} and not row.mentions_test_authority:
        return "add_test_authority_reference"
    if row.role == "skill_entrypoint" and not row.mentions_src_map:
        return "add_src_map_reference"
    return "no_immediate_action"


def build_rows() -> list[SkillMdRow]:
    rows: list[SkillMdRow] = []
    for path in iter_surface_files():
        path_text = rel(path)
        text = read_text(path)
        surface = classify_surface(path_text)
        role = classify_role(path_text)
        draft = SkillMdRow(
            path=path_text,
            surface=surface,
            role=role,
            owner_team=owner_team(surface, role),
            authority_level=authority_level(path_text, role),
            mentions_gpt=int("GPT" in text or "ChatGPT" in text or "Chrome" in text),
            mentions_test_authority=int("test_validation_canonicalization_map.md" in text or "Validation Authority" in text),
            mentions_src_map=int("src_canonicalization_map.md" in text),
            overclaim_phrase_count=count_overclaims(text),
            has_mojibake_hint=has_mojibake_hint(text),
            required_next_action="",
        )
        rows.append(
            SkillMdRow(
                **{**asdict(draft), "required_next_action": next_action(draft)}
            )
        )
    return rows


def write_csv(path: Path, rows: list[SkillMdRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SkillMdRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_summary(path: Path, rows: list[SkillMdRow]) -> None:
    counters = {
        "surface": Counter(row.surface for row in rows),
        "role": Counter(row.role for row in rows),
        "authority_level": Counter(row.authority_level for row in rows),
        "required_next_action": Counter(row.required_next_action for row in rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Task748 Skill MD Subagent Inventory Summary\n\n")
        handle.write("Task748 classifies skills, operating markdown, subagent routing, and GPT review contracts.\n\n")
        handle.write(f"Total rows: {len(rows)}\n\n")
        for section, counter in counters.items():
            handle.write(f"## {section}\n\n")
            handle.write("| value | count |\n| --- | ---: |\n")
            for value, count in counter.most_common():
                handle.write(f"| {value or 'missing'} | {count} |\n")
            handle.write("\n")
        handle.write("## Required References\n\n")
        for reference in REQUIRED_REFERENCES:
            handle.write(f"- `{reference}`\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("docs/reports/task_748_skills_md_subagent_canonicalization"))
    args = parser.parse_args()
    rows = build_rows()
    write_csv(args.out_dir / "task748_skill_md_subagent_inventory.csv", rows)
    write_summary(args.out_dir / "task748_skill_md_subagent_summary.md", rows)
    print(f"[Task748] rows={len(rows)} out={args.out_dir}")


if __name__ == "__main__":
    main()
