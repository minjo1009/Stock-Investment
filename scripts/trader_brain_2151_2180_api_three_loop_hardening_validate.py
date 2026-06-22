from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
REPORT = ROOT / "docs/reports/task_2151_2180_api_three_loop_hardening/task_2151_2180_api_three_loop_hardening.md"
DECISION = ROOT / "docs/reports/task_2151_2180_api_three_loop_hardening/task_2151_2180_decision.csv"
SCRIPT = ROOT / "scripts/trader_brain_2151_2180_api_three_loop_hardening.py"
AUTHORITY = "DIAGNOSTIC_API_THREE_LOOP_HARDENING_ONLY"
SECRET_PATTERNS = [
    re.compile(r"apikey\s*=", re.IGNORECASE),
    re.compile(r"token\s*=", re.IGNORECASE),
    re.compile(r"access_token\s*=", re.IGNORECASE),
    re.compile(r"authorization\s*:", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9_.-]{12,}", re.IGNORECASE),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        if len(text) == 10:
            text += "T00:00:00+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def api_secrets() -> list[str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return []
    secrets: list[str] = []
    for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() in {"FINNHUB_API_KEY", "FMP_API_KEY", "ALPHA_VANTAGE_API_KEY", "FRED_API_KEY"}:
            value = value.strip().strip('"').strip("'")
            if value:
                secrets.append(value)
    return secrets


def validate_no_secret_leak() -> None:
    secrets = api_secrets()
    roots = [OUT_DIR, REPORT, DECISION, SCRIPT]
    for root in roots:
        paths = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for secret in secrets:
                require(secret not in text, f"API secret leaked in {path}")
            if path.suffix.lower() in {".csv", ".json", ".md"}:
                for pattern in SECRET_PATTERNS:
                    require(not pattern.search(text), f"secret-like pattern persisted in {path}: {pattern.pattern}")


def validate_loop_contract(rows: list[dict[str, str]]) -> None:
    require(len(rows) == 3, "expected exactly 3 loop contract rows")
    loop_ids = {row["loop_id"] for row in rows}
    require(
        loop_ids == {
            "loop1_capture_scope_quality",
            "loop2_dataset_semantic_hardening",
            "loop3_brain_replay_validation",
        },
        f"loop id mismatch: {loop_ids}",
    )


def validate_source_packets(rows: list[dict[str, str]]) -> None:
    allowed_raw_root = ROOT / "data/raw/task_2121_2150_free_api_full_capture_proxy_replay"
    require(len(rows) > 0, "source packet rows missing")
    for row in rows:
        require(row["authority"] == AUTHORITY, "packet authority mismatch")
        require(row["strict_gate_pass"] == "0", "packet strict gate opened")
        require(row["proxy_feature_allowed"] == "1", "packet proxy feature flag mismatch")
        require(row["missing_source_is_negative"] == "0", "packet missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "packet future assignment")
        require(row["outcome_used_for_assignment"] == "0", "packet outcome assignment")
        source_ts = parse_dt(row["provider_available_ts"])
        decision_ts = parse_dt(row["decision_asof_ts"])
        require(source_ts is not None and decision_ts is not None, "packet timestamp parse failure")
        require(source_ts <= decision_ts, "packet source_ts after decision_asof")
        if row["provider_available_ts_basis"] == "provider_record_timestamp_or_capture_only":
            require(row["strict_gate_pass"] == "0", "capture-only basis opened strict gate")
        if row["raw_path"]:
            raw = ROOT / row["raw_path"]
            require(raw.exists(), f"missing raw file: {raw}")
            require(raw.resolve().is_relative_to(allowed_raw_root.resolve()), f"raw path outside allowed root: {raw}")
            require(row["raw_sha256"] == file_sha256(raw), f"raw hash mismatch: {raw}")


def validate_semantic_chain(
    coverage: list[dict[str, str]],
    semantics: list[dict[str, str]],
    edges: list[dict[str, str]],
    cards: list[dict[str, str]],
    decisions: list[dict[str, str]],
) -> None:
    require(len(coverage) == 377, f"expected 377 coverage rows, got {len(coverage)}")
    require(len(semantics) == 377, f"expected 377 semantics rows, got {len(semantics)}")
    require(len(cards) == 377, f"expected 377 score cards, got {len(cards)}")
    require(len(decisions) == 377, f"expected 377 L5 decision rows, got {len(decisions)}")
    sem_ids = {row["api_l2_semantic_id"] for row in semantics}
    spec_ids = {row["trade_spec_id"] for row in coverage}
    for row in coverage:
        require(row["strict_transcript_gate_pass"] == "0", "coverage transcript gate opened")
        require(row["strict_analyst_revision_gate_pass"] == "0", "coverage analyst gate opened")
        require(row["missing_source_is_negative"] == "0", "coverage missing negative")
        require(row["authority"] == AUTHORITY, "coverage authority mismatch")
    for row in semantics:
        require(row["trade_spec_id"] in spec_ids, "semantic outside coverage")
        require(row["l5_direct_gate_permission"] == "0", "semantic opened L5 direct gate")
        require(row["missing_source_is_negative"] == "0", "semantic missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "semantic future assignment")
        require(row["outcome_used_for_assignment"] == "0", "semantic outcome assignment")
    for row in edges:
        require(row["api_l2_semantic_id"] in sem_ids, "edge points outside semantics")
        require(row["relation_permission"] == "proxy_only_not_strict_gate", "edge overclaims permission")
        require(row["missing_source_is_negative"] == "0", "edge missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "edge future assignment")
        require(row["outcome_used_for_assignment"] == "0", "edge outcome assignment")
    for row in cards:
        require(row["strict_gate_status"] == "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED", "card strict status mismatch")
        require(row["assignment_uses_future_outcome"] == "0", "card future assignment")
        require(row["outcome_used_for_assignment"] == "0", "card outcome assignment")
    for row in decisions:
        require(row["strict_gate_status"] == "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED", "decision strict status mismatch")
        require(row["assignment_uses_future_outcome"] == "0", "decision future assignment")
        require(row["outcome_used_for_assignment"] == "0", "decision outcome assignment")


def validate_replay(trades: list[dict[str, str]], equity: list[dict[str, str]], metrics: list[dict[str, str]]) -> None:
    require(len(metrics) == 3, "expected three replay metrics rows")
    require(len(trades) > 0, "missing replay trades")
    require(len(equity) > 0, "missing replay equity")
    for row in trades:
        require(row["assignment_uses_future_outcome"] == "0", "trade future assignment")
        require(row["outcome_used_for_assignment"] == "0", "trade outcome assignment")
        require(row["outcome_used_for_audit_only"] == "1", "trade outcome audit flag")
        require(row["authority"] == AUTHORITY, "trade authority mismatch")
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")
        require(row["assignment_uses_future_outcome"] == "0", "metric future assignment")
        require(row["outcome_used_for_assignment"] == "0", "metric outcome assignment")
        require(row["outcome_used_for_audit_only"] == "1", "metric outcome audit flag")


def validate_closeout(closeout: list[dict[str, str]], decision: list[dict[str, str]]) -> None:
    require(len(closeout) == 1, "expected one closeout row")
    require(decision == closeout, "decision differs from closeout")
    row = closeout[0]
    require(row["verdict"] == "api_three_loop_hardening_complete_proxy_only_gates_still_blocked", "bad verdict")
    require(row["strict_transcript_gate_pass_rows"] == "0", "closeout transcript gate opened")
    require(row["strict_analyst_revision_gate_pass_rows"] == "0", "closeout analyst gate opened")
    require(row["strategy_acceptance"] == "NOT_ACCEPTED", "closeout acceptance changed")
    require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment changed")
    require(row["real_capital"] == "FORBIDDEN", "closeout real capital changed")
    require(row["assignment_uses_future_outcome"] == "0", "closeout future assignment")
    require(row["outcome_used_for_assignment"] == "0", "closeout outcome assignment")
    require(row["outcome_used_for_audit_only"] == "1", "closeout outcome audit")


def main() -> None:
    loop_contract = read_csv(OUT_DIR / "task2151_loop_contract.csv")
    gap = read_csv(OUT_DIR / "task2152_api_quality_gap_audit.csv")
    scope = read_csv(OUT_DIR / "task2153_capture_scope_matrix.csv")
    secret = read_csv(OUT_DIR / "task2154_secret_and_blocker_audit.csv")
    packets = read_csv(OUT_DIR / "task2161_api_source_packets.csv")
    coverage = read_csv(OUT_DIR / "task2162_decision_asof_coverage.csv")
    semantics = read_csv(OUT_DIR / "task2163_l2_api_semantics_hardened.csv")
    edges = read_csv(OUT_DIR / "task2164_l3_api_relation_edges_hardened.csv")
    cards = read_csv(OUT_DIR / "task2171_l4_api_score_cards_hardened.csv")
    decisions = read_csv(OUT_DIR / "task2172_l5_api_decisions_hardened.csv")
    trades = read_csv(OUT_DIR / "task2173_api_three_loop_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2174_api_three_loop_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2175_api_three_loop_replay_metrics.csv")
    audit = read_csv(OUT_DIR / "task2176_expert_audit_matrix.csv")
    closeout = read_csv(OUT_DIR / "task2180_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(gap) == 8, "expected 8 provider endpoint gap rows")
    require(len(scope) >= 73, "scope matrix too small")
    require(secret[0]["secret_hit_count"] == "0", "secret audit hit count nonzero")
    require(len(audit) >= 3, "expert audit rows missing")
    require(len(manifest) >= 15, "manifest missing artifacts")
    validate_no_secret_leak()
    validate_loop_contract(loop_contract)
    validate_source_packets(packets)
    validate_semantic_chain(coverage, semantics, edges, cards, decisions)
    validate_replay(trades, equity, metrics)
    validate_closeout(closeout, decision)

    print("[TASK2151_2180_VALIDATE_OK] data_health=pass governance_health=pass replay_diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
