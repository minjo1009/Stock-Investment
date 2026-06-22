from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
RAW_OUT = ROOT / "data/raw/task_2121_2150_free_api_full_capture_proxy_replay"
REPORT = ROOT / "docs/reports/task_2121_2150_free_api_full_capture_proxy_replay/task_2121_2150_free_api_full_capture_proxy_replay.md"
DECISION = ROOT / "docs/reports/task_2121_2150_free_api_full_capture_proxy_replay/task_2121_2150_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_API_FULL_CAPTURE_PROXY_REPLAY_ONLY"


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def api_secrets() -> list[str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return []
    secrets = []
    for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() in {"FINNHUB_API_KEY", "FMP_API_KEY", "ALPHA_VANTAGE_API_KEY"}:
            value = value.strip().strip('"').strip("'")
            if value:
                secrets.append(value)
    return secrets


def validate_no_secret_leak() -> None:
    secrets = api_secrets()
    roots = [OUT_DIR, RAW_OUT, REPORT, ROOT / "scripts/trader_brain_2121_2150_free_api_full_capture_proxy_replay.py"]
    for root in roots:
        paths = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for secret in secrets:
                require(secret not in text, f"API secret leaked in {path}")


def validate_ledger(ledger: list[dict[str, str]]) -> None:
    require(len(ledger) == 384, f"expected 384 api call rows, got {len(ledger)}")
    providers = {row["provider"] for row in ledger}
    require(providers == {"finnhub", "fmp", "alpha_vantage"}, f"provider mismatch: {providers}")
    for row in ledger:
        require(row["authority"] == AUTHORITY, "ledger authority mismatch")
        require(row["request_url_contains_secret"] == "0", "ledger URL secret flag")
        require("apikey" not in row["params_json_without_key"].lower(), "apikey persisted in params")
        require("token" not in row["params_json_without_key"].lower(), "token persisted in params")
        require(row["missing_source_is_negative"] == "0", "missing source treated negative")
        require(row["assignment_uses_future_outcome"] == "0", "future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag")
        if row["raw_path"]:
            raw = ROOT / row["raw_path"]
            require(raw.exists(), f"raw path missing: {raw}")
            require(row["raw_sha256"] == file_sha256(raw), f"raw hash mismatch: {raw}")
        if row["http_status"] in {"402", "403", "429"}:
            require(row["blocked_by_plan_or_entitlement"] == "1", "blocked HTTP status not marked blocked")
        if row["blocked_by_plan_or_entitlement"] == "1":
            require(row["strict_gate_permission"] != "strict_gate", "blocked row has strict gate permission")


def validate_features(features: list[dict[str, str]], semantics: list[dict[str, str]], edges: list[dict[str, str]], cards: list[dict[str, str]]) -> None:
    require(len(features) == 377, f"expected 377 feature rows, got {len(features)}")
    require(len(semantics) == 377, f"expected 377 semantic rows, got {len(semantics)}")
    require(len(edges) == 1131, f"expected 1131 edges, got {len(edges)}")
    require(len(cards) == 377, f"expected 377 cards, got {len(cards)}")
    feature_ids = {row["api_feature_id"] for row in features}
    for row in features:
        require(row["strict_transcript_gate_pass"] == "0", "strict transcript gate opened")
        require(row["strict_analyst_revision_gate_pass"] == "0", "strict analyst gate opened")
        require(row["missing_source_is_negative"] == "0", "feature missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "feature future assignment")
        require(row["outcome_used_for_assignment"] == "0", "feature outcome assignment")
        require(row["authority"] == AUTHORITY, "feature authority mismatch")
    for row in semantics:
        require(row["api_feature_id"] in feature_ids, "semantic points outside feature rows")
        require(row["l5_direct_gate_permission"] == "0", "semantic opened L5 direct gate")
    for row in edges:
        require(row["from_api_feature_id"] in feature_ids, "edge points outside feature rows")
        require(row["relation_permission"] == "proxy_only_not_strict_gate", "edge overclaims relation permission")
    for row in cards:
        require(row["api_feature_id"] in feature_ids, "card points outside feature rows")
        require(row["strict_gate_status"] == "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED", "card strict gate status mismatch")
        require(row["assignment_uses_future_outcome"] == "0", "card future assignment")
        require(row["outcome_used_for_assignment"] == "0", "card outcome assignment")


def validate_replay(trades: list[dict[str, str]], equity: list[dict[str, str]], metrics: list[dict[str, str]]) -> None:
    require(len(trades) == 116, f"expected 116 replay trades, got {len(trades)}")
    require(len(equity) > 0, "missing equity rows")
    require(len(metrics) == 1, "expected one metrics row")
    metric = metrics[0]
    require(metric["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(metric["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    require(metric["real_capital"] == "FORBIDDEN", "real capital changed")
    require(metric["assignment_uses_future_outcome"] == "0", "metric future assignment")
    require(metric["outcome_used_for_assignment"] == "0", "metric outcome assignment")
    require(metric["outcome_used_for_audit_only"] == "1", "metric should mark outcome audit only")
    for row in trades:
        require(row["assignment_uses_future_outcome"] == "0", "trade future assignment")
        require(row["outcome_used_for_assignment"] == "0", "trade outcome assignment")
        require(row["outcome_used_for_audit_only"] == "1", "trade should mark outcome audit only")
        require(row["authority"] == AUTHORITY, "trade authority mismatch")


def validate_closeout(closeout: list[dict[str, str]], decision: list[dict[str, str]], metrics: list[dict[str, str]]) -> None:
    require(len(closeout) == 1, "expected one closeout row")
    require(decision == closeout, "decision differs from closeout")
    row = closeout[0]
    metric = metrics[0]
    require(row["verdict"] == "free_api_capture_proxy_replay_complete_diagnostic_only", "bad verdict")
    require(row["best_final_equity"] == metric["final_equity"], "closeout final mismatch")
    require(row["best_cagr"] == metric["cagr"], "closeout cagr mismatch")
    require(row["best_max_drawdown"] == metric["max_drawdown"], "closeout mdd mismatch")
    require(row["strict_transcript_gate_pass_rows"] == "0", "closeout transcript gate opened")
    require(row["strict_analyst_revision_gate_pass_rows"] == "0", "closeout analyst gate opened")
    require(row["strategy_acceptance"] == "NOT_ACCEPTED", "closeout acceptance changed")
    require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment changed")
    require(row["real_capital"] == "FORBIDDEN", "closeout real capital changed")


def main() -> None:
    capability = read_csv(OUT_DIR / "task2121_provider_capability_gate.csv")
    ledger = read_csv(OUT_DIR / "task2122_api_call_ledger.csv")
    normalized = read_csv(OUT_DIR / "task2123_api_normalized_sources.csv")
    features = read_csv(OUT_DIR / "task2124_l1_api_proxy_features.csv")
    semantics = read_csv(OUT_DIR / "task2125_l2_api_proxy_semantics.csv")
    edges = read_csv(OUT_DIR / "task2126_l3_api_proxy_edges.csv")
    cards = read_csv(OUT_DIR / "task2127_l4_api_proxy_score_cards.csv")
    trades = read_csv(OUT_DIR / "task2128_api_proxy_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2129_api_proxy_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2130_api_proxy_replay_metrics.csv")
    closeout = read_csv(OUT_DIR / "task2150_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(capability) == 8, "expected 8 provider capability rows")
    require(len(normalized) > 0, "normalized source rows missing")
    require(len(manifest) >= 11, "manifest missing artifacts")
    validate_no_secret_leak()
    validate_ledger(ledger)
    validate_features(features, semantics, edges, cards)
    validate_replay(trades, equity, metrics)
    validate_closeout(closeout, decision, metrics)

    print("[TASK2121_2150_VALIDATE_OK] source_health=pass governance_health=pass replay_diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
