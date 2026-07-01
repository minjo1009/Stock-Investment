from __future__ import annotations

import argparse
import sys

from ops_common import load_yaml, print_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        profiles = load_yaml("ops/task_profiles.yaml").get("profiles", {})
        rules = load_yaml("ops/profile_validation_rules.yaml").get("rules", {})
        operating = load_yaml("ops/operating_state.yaml")
    except Exception as exc:
        return print_result("TASK PROFILE RULE VALIDATION", [], [], [str(exc)])

    profile = profiles.get(args.profile)
    rule = rules.get(args.profile)
    if not profile:
        failures.append(f"profile missing: {args.profile}")
        return print_result("TASK PROFILE RULE VALIDATION", passes, warnings, failures)
    if not rule:
        failures.append(f"profile validation rule missing: {args.profile}")
        return print_result("TASK PROFILE RULE VALIDATION", passes, warnings, failures)

    for section, expected_values in rule.get("must_include", {}).items():
        actual = profile.get(section, [])
        if isinstance(actual, str):
            actual = [actual]
        missing = sorted(set(expected_values) - set(actual))
        if missing:
            failures.append(f"{args.profile}.{section} missing: {', '.join(missing)}")
        else:
            passes.append(f"{args.profile}.{section}")

    for section, forbidden_values in rule.get("must_not_include", {}).items():
        actual = profile.get(section, [])
        if isinstance(actual, str):
            actual = [actual]
        present = sorted(set(forbidden_values) & set(actual))
        if present:
            failures.append(f"{args.profile}.{section} forbidden values present: {', '.join(present)}")

    hard = operating.get("hard_boundaries", {})
    for key, expected in rule.get("hard_boundaries", {}).items():
        if hard.get(key) != expected:
            failures.append(f"hard boundary mismatch: {key}={hard.get(key)} expected {expected}")
        else:
            passes.append(f"hard_boundary.{key}")

    return print_result("TASK PROFILE RULE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
