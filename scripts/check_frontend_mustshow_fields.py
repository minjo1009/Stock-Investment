# -*- coding: utf-8 -*-
import argparse
import json
from pathlib import Path

VALID_ACTION_ROUTES = {
    "home",
    "scan",
    "analysis",
    "market",
    "risk",
    "detail",
    "settings",
}

VALID_ACTION_PRIORITIES = {
    "must",
    "strong",
    "reference",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_path(root, path: str):
    cur = root
    for raw in path.split("."):
        if raw == "":
            return False, None

        if isinstance(cur, dict):
            if raw not in cur:
                return False, None
            cur = cur[raw]
            continue

        if isinstance(cur, list):
            try:
                index = int(raw)
                if index < 0 or index >= len(cur):
                    return False, None
                cur = cur[index]
                continue
            except ValueError:
                return False, None

        return False, None

    return True, cur


def validate_value(value, rule, min_len=None, required_keys=None):
    if rule == "exists":
        return value is not None
    if rule == "nonEmpty":
        if value is None:
            return False
        if isinstance(value, str):
            return value != ""
        if isinstance(value, (list, tuple, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True
        return value is not None
    if rule == "number":
        return isinstance(value, (int, float)) and value == value
    if rule == "array_min_len":
        if not isinstance(value, list):
            return False
        if min_len is None:
            min_len = 1
        return len(value) >= min_len
    if rule == "object_shape":
        if not isinstance(value, dict):
            return False
        if not required_keys:
            return True
        return all(key in value for key in required_keys)
    return True


def validate_required_actions(tab_id: str, actions):
    report = []
    if not isinstance(actions, list) or not actions:
        report.append(
            {
                "type": "required-action",
                "tabId": tab_id,
                "itemId": "requiredActions",
                "path": "requiredActions",
                "rule": "exists",
                "status": "missing",
            }
        )
        return report

    action_ids = set()
    routes = {}
    for action in actions:
        if not isinstance(action, dict):
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": "requiredActions",
                    "path": "requiredActions[n]",
                    "rule": "object",
                    "status": "invalid",
                }
            )
            continue

        action_id = action.get("actionId")
        label = action.get("label")
        route = action.get("route")
        reason = action.get("reason")
        priority = action.get("priority", "reference")

        if not isinstance(action_id, str) or not action_id:
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action.get("route", ""),
                    "path": "requiredActions.actionId",
                    "rule": "nonEmpty",
                    "status": "invalid",
                }
            )
        elif action_id in action_ids:
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action_id,
                    "path": "requiredActions.actionId",
                    "rule": "unique",
                    "status": "invalid",
                }
            )
        else:
            action_ids.add(action_id)

        if not isinstance(label, str) or not label:
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action_id or "",
                    "path": "requiredActions.label",
                    "rule": "nonEmpty",
                    "status": "invalid",
                }
            )

        if route not in VALID_ACTION_ROUTES:
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action_id or "",
                    "path": "requiredActions.route",
                    "rule": "enum",
                    "status": "invalid",
                    "route": route,
                }
            )
        else:
            if route in routes:
                report.append(
                    {
                        "type": "required-action",
                        "tabId": tab_id,
                        "itemId": action_id or "",
                        "path": "requiredActions.route",
                        "rule": "unique",
                        "status": "invalid",
                        "route": route,
                    }
                )
            else:
                routes[route] = action_id

        if reason not in ("", None) and not isinstance(reason, str):
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action_id or "",
                    "path": "requiredActions.reason",
                    "rule": "string",
                    "status": "invalid",
                }
            )

        if priority not in VALID_ACTION_PRIORITIES:
            report.append(
                {
                    "type": "required-action",
                    "tabId": tab_id,
                    "itemId": action_id or "",
                    "path": "requiredActions.priority",
                    "rule": "enum",
                    "status": "invalid",
                    "priority": priority,
                }
            )

    return report


def load_payload(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"payload not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="iOS cockpit must-show checklist validator")
    parser.add_argument("--checklist", required=True, help="path to checklist json")
    parser.add_argument("--cockpit-payload", required=True, help="path to cockpit payload json")
    parser.add_argument("--scan-payload", default=None, help="optional separate scan payload json")
    parser.add_argument("--screen", default="all", choices=["all", "home", "scan", "analysis", "market", "risk", "detail", "settings"], help="target tab")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    checklist = load_json(Path(args.checklist))
    cockpit_payload = load_payload(Path(args.cockpit_payload))
    scan_payload = load_payload(Path(args.scan_payload)) if args.scan_payload else cockpit_payload

    missing_count = 0
    report = []

    for tab in checklist.get("tabs", []):
        tab_id = tab["tabId"]
        if args.screen != "all" and args.screen != tab_id:
            continue

        payload = scan_payload if tab.get("scope") == "scan" else cockpit_payload
        for item in tab.get("mustShow", []):
            item_id = item.get("itemId")
            for check in item.get("checkFields", []):
                path = check.get("path")
                rule = check.get("rule")
                min_len = check.get("min")
                required_keys = check.get("requiredKeys", [])

                exists, value = has_path(payload, path)
                ok = exists and validate_value(value, rule, min_len=min_len, required_keys=required_keys)
                if not ok:
                    report.append(
                        {
                            "type": "must-show",
                            "tabId": tab_id,
                            "itemId": item_id,
                            "path": path,
                            "rule": rule,
                            "status": "missing" if not exists else "invalid",
                        }
                    )

        required_action_report = validate_required_actions(tab_id, tab.get("requiredActions"))
        report.extend(required_action_report)
        missing_count += len(required_action_report)

    missing_count += len([row for row in report if row.get("type") != "required-action"])

    if args.json:
        print(
            json.dumps(
                {
                    "missingCount": missing_count,
                    "mustShowCount": len([item for item in report if item.get("type") == "must-show"]),
                    "requiredActionCount": len([item for item in report if item.get("type") == "required-action"]),
                    "missing": report,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        must_show_count = len([item for item in report if item.get("type") == "must-show"])
        required_action_count = len([item for item in report if item.get("type") == "required-action"])
        if not report:
            print("[OK] front-end must-show + requiredAction checklist: no missing fields")
        else:
            print(
                f"[FAIL] checklist check: {must_show_count} must-show failures, {required_action_count} required-action failures"
            )
            for item in report:
                print(f"- {item['type']} / {item['tabId']} / {item['itemId']} / {item['path']} ({item['status']})")


if __name__ == "__main__":
    main()
