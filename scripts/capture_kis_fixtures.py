from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SENSITIVE_KEYWORDS = {
    "authorization",
    "appkey",
    "appsecret",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "cano",
    "acnt_prdt_cd",
    "account",
    "hashkey",
}

DEFAULT_CASE_FILES = {
    "cancel_success": "cancel_success.json",
    "cancel_rejected": "cancel_rejected.json",
    "order_status_pending": "order_status_pending.json",
    "order_status_filled": "order_status_filled.json",
    "fills_empty": "fills_empty.json",
    "fills_partial_or_full": "fills_partial_or_full.json",
    "error_transport_or_api": "error_transport_or_api.json",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()
    return any(token in normalized for token in SENSITIVE_KEYWORDS)


def sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                sanitized[str(key)] = "***REDACTED***"
            else:
                sanitized[str(key)] = sanitize_payload(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    return value


def write_fixture(output_dir: Path, case: str, response: Any, *, source: str, real_capture: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = DEFAULT_CASE_FILES.get(case, f"{case}.json")
    payload = {
        "_fixture_meta": {
            "source": source,
            "captured_at": _now_iso(),
            "sanitized": True,
            "case": case,
            "real_capture": real_capture,
        },
        "response": sanitize_payload(response),
    }
    target = output_dir / file_name
    target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return target


def _has_required_env() -> bool:
    required = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NUMBER", "KIS_PRODUCT_CODE")
    return all(bool(os.environ.get(name, "").strip()) for name in required)


def capture_read_only(symbol: str) -> dict[str, Any]:
    from integration.kis_client import KISClient

    client = KISClient.from_env()
    statuses = client.fetch_broker_order_statuses(symbol=symbol)
    return {
        "order_status_raw": statuses,
        "order_status_count": len(statuses),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture/sanitize KIS paper fixtures for contract tests.")
    parser.add_argument("--output-dir", default="tests/fixtures/kis", help="Fixture output directory.")
    parser.add_argument("--symbol", default="AAPL", help="Symbol for read-only status capture.")
    parser.add_argument("--read-only", action="store_true", help="Use read-only endpoints only.")
    parser.add_argument(
        "--allow-paper-order",
        action="store_true",
        help="Allow submitting paper order (disabled by default for safety).",
    )
    args = parser.parse_args()

    env = os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper"
    if env != "paper":
        raise RuntimeError(f"Refusing capture outside paper environment (KIS_ENVIRONMENT={env})")

    if args.allow_paper_order:
        raise RuntimeError("Order-generating capture is disabled in this script revision for safety.")

    if not args.read_only:
        print("[capture] defaulting to read-only mode; pass --read-only explicitly for clarity.")

    output_dir = Path(args.output_dir)
    if not _has_required_env():
        print("[capture] KIS credentials missing; no live capture performed.")
        write_fixture(
            output_dir,
            "error_transport_or_api",
            {"error": "KIS credentials missing in environment", "mode": "read_only"},
            source="synthetic-fallback",
            real_capture=False,
        )
        return 0

    try:
        raw = capture_read_only(symbol=args.symbol)
    except Exception as exc:
        write_fixture(
            output_dir,
            "error_transport_or_api",
            {"error": str(exc), "mode": "read_only"},
            source="KIS paper",
            real_capture=True,
        )
        print(f"[capture] read-only capture failed: {exc}")
        return 0

    write_fixture(
        output_dir,
        "order_status_pending",
        raw,
        source="KIS paper",
        real_capture=True,
    )
    print(f"[capture] saved read-only fixture to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
