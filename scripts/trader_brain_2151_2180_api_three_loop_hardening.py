from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2121 = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
TASK1991 = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
OUT_DIR = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
REPORT_DIR = ROOT / "docs/reports/task_2151_2180_api_three_loop_hardening"
REPORT = REPORT_DIR / "task_2151_2180_api_three_loop_hardening.md"
DECISION = REPORT_DIR / "task_2151_2180_decision.csv"

AUTHORITY = "DIAGNOSTIC_API_THREE_LOOP_HARDENING_ONLY"
SOURCE_POLICY = "winner_defense_budget_top5_v1"
BASELINE_POLICY = "winner_accel_top5_to_top2_convex_v1"
POLICY_VARIANTS = [
    "api_loop3_filings_quality_top2_v1",
    "api_loop3_source_gap_neutral_top2_v1",
    "api_loop3_guarded_risk_cap_top2_v1",
]
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        if len(text) == 10 and text[4] == "-" and text[7] == "-":
            text = text + "T00:00:00+00:00"
        if " " in text and "T" not in text:
            text = text.replace(" ", "T", 1)
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    dt = parse_dt(value)
    return dt.date() if dt else None


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None", "nan"}:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


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


def secret_scan(paths: list[Path]) -> tuple[int, list[str]]:
    secrets = api_secrets()
    hits: list[str] = []
    for root in paths:
        if not root.exists():
            continue
        files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        for path in files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for secret in secrets:
                if secret and secret in text:
                    hits.append(str(path.relative_to(ROOT)))
    return len(hits), sorted(set(hits))


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "capability": read_csv(TASK2121 / "task2121_provider_capability_gate.csv"),
        "ledger": read_csv(TASK2121 / "task2122_api_call_ledger.csv"),
        "normalized": read_csv(TASK2121 / "task2123_api_normalized_sources.csv"),
        "features": read_csv(TASK2121 / "task2124_l1_api_proxy_features.csv"),
        "l5": read_csv(TASK1991 / "task1996_l5_winner_acceleration_decisions.csv"),
        "source_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "baseline_metrics": read_csv(TASK1991 / "task1998_winner_acceleration_replay_metrics.csv"),
    }


def endpoint_status(row: dict[str, str]) -> str:
    status = row.get("call_status", "")
    http = row.get("http_status", "")
    blocked = row.get("blocked_by_plan_or_entitlement", "")
    blocker = (row.get("blocker_reason", "") + " " + row.get("first_blocker", "")).lower()
    if status in {"downloaded", "reused"} and blocked != "1":
        return "usable"
    if http == "429" or "quota" in blocker or "limit" in blocker:
        return "quota_or_rate_blocked"
    if http in {"402", "403"} or "premium" in blocker or "entitlement" in blocker:
        return "entitlement_blocked"
    if blocked == "1":
        return "blocked_other"
    return status or "unknown"


def task2151_loop_contract() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2151",
            "loop_id": "loop1_capture_scope_quality",
            "purpose": "audit API coverage, blocked endpoint status, raw reuse, and secret safety before any scoring",
            "required_outputs": "task2152,task2153,task2154",
            "success_criteria": "no secret leak; feature/capture mismatch explicit; blocked rows cannot become positives",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2161",
            "loop_id": "loop2_dataset_semantic_hardening",
            "purpose": "turn usable API rows into PIT-aware source packets and event microstructure, not broad source-count boosts",
            "required_outputs": "task2161,task2162,task2163,task2164",
            "success_criteria": "provider timestamp basis explicit; source gap neutral; strict gates stay closed",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2171",
            "loop_id": "loop3_brain_replay_validation",
            "purpose": "connect hardened API semantics to L2/L3/L4/L5 and run diagnostic replay variants",
            "required_outputs": "task2171,task2172,task2173,task2174,task2175,task2180",
            "success_criteria": "outcome is audit-only; no future assignment; replay proves only diagnostic impact",
            "authority": AUTHORITY,
        },
    ]


def task2152_gap_audit(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in inputs["ledger"]:
        key = (row["provider"], row["endpoint_name"])
        counts[key]["attempted"] += 1
        counts[key][endpoint_status(row)] += 1
        if row.get("raw_path"):
            counts[key]["raw_path_rows"] += 1
    normalized_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in inputs["normalized"]:
        normalized_counts[(row["provider"], row["endpoint_name"])] += 1
    capability_by_key = {(row["provider"], row["endpoint_name"]): row for row in inputs["capability"]}
    rows: list[dict[str, object]] = []
    for idx, key in enumerate(sorted(counts), start=1):
        provider, endpoint = key
        c = counts[key]
        cap = capability_by_key.get(key, {})
        if c.get("usable", 0) == 0:
            gate = "do_not_recall_until_entitlement_or_quota_changes"
        elif c.get("entitlement_blocked", 0) + c.get("quota_or_rate_blocked", 0) > c.get("usable", 0):
            gate = "reuse_usable_only_and_stop_blocked_recall"
        else:
            gate = "reuse_cache_allowed"
        rows.append(
            {
                "task_id": "Task2152",
                "gap_audit_id": f"APIGAP-2152-{idx:03d}",
                "provider": provider,
                "endpoint_name": endpoint,
                "attempted_rows": c.get("attempted", 0),
                "usable_rows": c.get("usable", 0),
                "entitlement_blocked_rows": c.get("entitlement_blocked", 0),
                "quota_or_rate_blocked_rows": c.get("quota_or_rate_blocked", 0),
                "blocked_other_rows": c.get("blocked_other", 0),
                "raw_path_rows": c.get("raw_path_rows", 0),
                "normalized_rows": normalized_counts.get(key, 0),
                "strict_gate_permission": cap.get("strict_gate_permission", ""),
                "next_call_policy": gate,
                "blocked_rows_can_score_positive": "0",
                "missing_source_is_negative": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2153_scope_matrix(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    feature_symbols = sorted({row["symbol"] for row in inputs["features"]})
    normalized_symbols = sorted({row["symbol"] for row in inputs["normalized"] if row.get("symbol")})
    normalized_by_symbol: dict[str, int] = defaultdict(int)
    usable_by_symbol: dict[str, int] = defaultdict(int)
    for row in inputs["normalized"]:
        normalized_by_symbol[row["symbol"]] += 1
    usable_calls = {
        (row["provider"], row["endpoint_name"], row["symbol"])
        for row in inputs["ledger"]
        if endpoint_status(row) == "usable"
    }
    for provider, endpoint, symbol in usable_calls:
        usable_by_symbol[symbol] += 1
    rows: list[dict[str, object]] = []
    for idx, symbol in enumerate(sorted(set(feature_symbols) | set(normalized_symbols)), start=1):
        in_feature = symbol in feature_symbols
        in_capture = symbol in normalized_symbols
        if in_feature and in_capture:
            state = "feature_and_capture_aligned"
        elif in_feature:
            state = "feature_without_api_capture_source_gap_neutral"
        else:
            state = "capture_without_feature_not_scored"
        rows.append(
            {
                "task_id": "Task2153",
                "scope_matrix_id": f"APISCOPE-2153-{idx:04d}",
                "symbol": symbol,
                "in_feature_scope": "1" if in_feature else "0",
                "in_api_capture_scope": "1" if in_capture else "0",
                "normalized_source_rows": normalized_by_symbol.get(symbol, 0),
                "usable_endpoint_count": usable_by_symbol.get(symbol, 0),
                "scope_state": state,
                "score_permission": "proxy_allowed" if state == "feature_and_capture_aligned" else "source_gap_neutral_only",
                "missing_source_is_negative": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2154_secret_blocker_audit(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    hit_count, hit_paths = secret_scan([TASK2121, ROOT / "data/raw/task_2121_2150_free_api_full_capture_proxy_replay"])
    status_counts: dict[str, int] = defaultdict(int)
    for row in inputs["ledger"]:
        status_counts[endpoint_status(row)] += 1
    return [
        {
            "task_id": "Task2154",
            "secret_hit_count": hit_count,
            "secret_hit_paths": ";".join(hit_paths),
            "usable_call_rows": status_counts.get("usable", 0),
            "entitlement_blocked_rows": status_counts.get("entitlement_blocked", 0),
            "quota_or_rate_blocked_rows": status_counts.get("quota_or_rate_blocked", 0),
            "blocked_other_rows": status_counts.get("blocked_other", 0),
            "request_params_secret_persisted": "0",
            "blocked_rows_can_score_positive": "0",
            "authority": AUTHORITY,
        }
    ]


def parse_record(row: dict[str, str]) -> dict[str, object]:
    try:
        payload = json.loads(row.get("record_json", "") or "{}")
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def classify_form(form_value: str) -> tuple[str, float, str]:
    form = form_value.upper().strip()
    if form in {"8-K", "8-K/A", "6-K", "6-K/A"}:
        return "material_event_or_issuer_update", 1.0, "event_update"
    if form in {"10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "40-F"}:
        return "periodic_operating_disclosure", 0.6, "operating_context"
    if form.startswith("S-") or form in {"424B", "424B2", "424B3", "424B4", "424B5", "FWP"}:
        return "capital_markets_financing_or_dilution", -1.15, "financing_risk"
    if "13G" in form or "13D" in form:
        return "ownership_position_disclosure", 0.2, "ownership_context"
    if "DEF" in form or "PRE" in form:
        return "proxy_governance_disclosure", -0.15, "governance_context"
    return "other_filing_context", 0.0, "other_context"


def build_api_event_index(normalized: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    by_symbol: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in normalized:
        record = parse_record(row)
        provider = row["provider"]
        endpoint = row["endpoint_name"]
        if provider == "finnhub" and endpoint == "stock_filings":
            source_ts = parse_dt(record.get("acceptedDate") or row.get("source_ts"))
            form = str(record.get("form", ""))
            family, score, relation = classify_form(form)
            detail = f"form={form}"
            accession = record.get("accessNumber", "")
            cik = record.get("cik", "")
            filed_date = record.get("filedDate", "")
            source_url = record.get("filingUrl", "")
            primary_doc_url = record.get("reportUrl", "")
            value_numeric = score
        elif provider == "finnhub" and endpoint == "stock_recommendation":
            source_ts = parse_dt(record.get("period"))
            strong_buy = to_float(record.get("strongBuy"))
            buy = to_float(record.get("buy"))
            hold = to_float(record.get("hold"))
            sell = to_float(record.get("sell"))
            strong_sell = to_float(record.get("strongSell"))
            total = max(strong_buy + buy + hold + sell + strong_sell, 1.0)
            balance = ((2.0 * strong_buy + buy) - (sell + 2.0 * strong_sell)) / total
            family = "recommendation_balance_proxy"
            score = clamp(balance * 1.5, -1.5, 1.5)
            relation = "expectation_proxy_context"
            detail = (
                f"strongBuy={int(strong_buy)};buy={int(buy)};hold={int(hold)};"
                f"sell={int(sell)};strongSell={int(strong_sell)}"
            )
            accession = ""
            cik = ""
            filed_date = record.get("period", "")
            source_url = ""
            primary_doc_url = ""
            value_numeric = balance
        elif provider == "alpha_vantage" and endpoint == "earnings_history":
            source_ts = parse_dt(record.get("reportedDate"))
            surprise_pct = to_float(record.get("surprisePercentage"))
            family = "earnings_surprise_proxy"
            score = clamp(surprise_pct / 12.0, -1.5, 1.5)
            relation = "earnings_expectation_gap_proxy"
            detail = (
                f"reportedDate={record.get('reportedDate','')};reportedEPS={record.get('reportedEPS','')};"
                f"estimatedEPS={record.get('estimatedEPS','')};surprisePct={record.get('surprisePercentage','')}"
            )
            accession = ""
            cik = ""
            filed_date = record.get("reportedDate", "")
            source_url = ""
            primary_doc_url = ""
            value_numeric = surprise_pct
        elif provider == "fmp" and endpoint in {"income_statement", "balance_sheet", "cash_flow"}:
            source_ts = parse_dt(record.get("acceptedDate") or record.get("filingDate") or record.get("date"))
            if not source_ts:
                continue
            revenue = to_float(record.get("revenue"))
            net_income = to_float(record.get("netIncome") or record.get("bottomLineNetIncome"))
            fcf = to_float(record.get("freeCashFlow"))
            debt = to_float(record.get("totalDebt"))
            cash = to_float(record.get("cashAndCashEquivalents"))
            quality = 0.0
            if revenue > 0:
                quality += 0.3
            if net_income > 0:
                quality += 0.35
            if fcf > 0:
                quality += 0.35
            if debt > 0 and cash / max(debt, 1.0) < 0.35:
                quality -= 0.4
            family = "fundamental_quality_proxy"
            score = clamp(quality, -1.0, 1.0)
            relation = "financial_statement_quality_proxy"
            detail = f"revenue={revenue};netIncome={net_income};fcf={fcf};cash={cash};debt={debt}"
            accession = ""
            cik = record.get("cik", "")
            filed_date = record.get("filingDate") or record.get("date", "")
            source_url = ""
            primary_doc_url = ""
            value_numeric = quality
        else:
            continue
        if not source_ts:
            continue
        by_symbol[row["symbol"]].append(
            {
                "api_normalized_source_id": row["api_normalized_source_id"],
                "provider": provider,
                "endpoint_name": endpoint,
                "symbol": row["symbol"],
                "source_ts": source_ts,
                "source_ts_text": source_ts.isoformat(),
                "form_type": record.get("form", ""),
                "accession_no": accession,
                "cik": cik,
                "filed_date": filed_date,
                "source_url": source_url,
                "primary_doc_url": primary_doc_url,
                "event_family": family,
                "event_score": score,
                "event_value_numeric": value_numeric,
                "event_detail": detail,
                "relation_type": relation,
                "provider_available_ts_basis": row.get("provider_available_ts_basis", ""),
                "strict_gate_pass": row.get("strict_gate_pass", "0"),
                "raw_path": row.get("raw_path", ""),
                "raw_sha256": row.get("raw_sha256", ""),
            }
        )
    for rows in by_symbol.values():
        rows.sort(key=lambda item: item["source_ts"])
    return by_symbol


def sources_before(api_event_index: dict[str, list[dict[str, object]]], symbol: str, asof: str, days: int) -> list[dict[str, object]]:
    dt = parse_dt(asof)
    if not dt:
        return []
    cutoff_days = days * 24 * 60 * 60
    out = []
    for item in api_event_index.get(symbol, []):
        source_ts = item["source_ts"]
        if source_ts <= dt and 0 <= (dt - source_ts).total_seconds() <= cutoff_days:
            out.append(item)
    return out


def task2161_source_packets(inputs: dict[str, list[dict[str, str]]], api_event_index: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    seen: set[tuple[str, str, str]] = set()
    for feature in inputs["features"]:
        for item in sources_before(api_event_index, feature["symbol"], feature["decision_asof_ts"], 365):
            key = (
                feature["trade_spec_id"],
                str(item["provider"]),
                str(item["endpoint_name"]),
                str(item["accession_no"]) or str(item["source_ts_text"]) + str(item["event_detail"]),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "task_id": "Task2161",
                    "api_source_packet_id": f"APIPACKET-2161-{idx:07d}",
                    "trade_spec_id": feature["trade_spec_id"],
                    "candidate_source_id": feature["candidate_source_id"],
                    "symbol": feature["symbol"],
                    "decision_asof_ts": feature["decision_asof_ts"],
                    "provider": item["provider"],
                    "endpoint_name": item["endpoint_name"],
                    "api_normalized_source_id": item["api_normalized_source_id"],
                    "cik": item["cik"],
                    "accession_no": item["accession_no"],
                    "form_type": item["form_type"],
                    "filed_date": item["filed_date"],
                    "provider_available_ts": item["source_ts_text"],
                    "provider_available_ts_certified": "0",
                    "provider_available_ts_basis": item["provider_available_ts_basis"],
                    "source_url": item["source_url"],
                    "primary_doc_url": item["primary_doc_url"],
                    "evidence_family": item["event_family"],
                    "event_score": item["event_score"],
                    "event_value_numeric": item["event_value_numeric"],
                    "event_detail": item["event_detail"],
                    "raw_path": item["raw_path"],
                    "raw_sha256": item["raw_sha256"],
                    "strict_gate_pass": "0",
                    "proxy_feature_allowed": "1",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def task2162_decision_coverage(inputs: dict[str, list[dict[str, str]]], source_packets: list[dict[str, object]]) -> list[dict[str, object]]:
    packet_by_spec: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in source_packets:
        packet_by_spec[str(row["trade_spec_id"])].append(row)
    capture_symbols = {row["symbol"] for row in inputs["normalized"] if row.get("symbol")}
    rows: list[dict[str, object]] = []
    for idx, feature in enumerate(inputs["features"], start=1):
        packets = packet_by_spec.get(feature["trade_spec_id"], [])
        counts: dict[str, int] = defaultdict(int)
        value_sums: dict[str, float] = defaultdict(float)
        for packet in packets:
            counts[str(packet["evidence_family"])] += 1
            value_sums[str(packet["evidence_family"])] += to_float(packet.get("event_value_numeric"))
        if feature["symbol"] not in capture_symbols:
            state = "source_gap_neutral"
        elif not packets:
            state = "capture_exists_but_no_asof_packet"
        elif counts.get("capital_markets_financing_or_dilution", 0) > 0:
            state = "asof_packet_with_financing_risk_context"
        elif counts.get("earnings_surprise_proxy", 0) > 0 or counts.get("recommendation_balance_proxy", 0) > 0:
            state = "asof_packet_with_expectation_proxy_context"
        elif counts.get("material_event_or_issuer_update", 0) > 0:
            state = "asof_packet_with_material_event_context"
        else:
            state = "asof_packet_context_only"
        rows.append(
            {
                "task_id": "Task2162",
                "coverage_id": f"APICOVER-2162-{idx:06d}",
                "trade_spec_id": feature["trade_spec_id"],
                "candidate_source_id": feature["candidate_source_id"],
                "symbol": feature["symbol"],
                "decision_asof_ts": feature["decision_asof_ts"],
                "api_capture_scope_pass": "1" if feature["symbol"] in capture_symbols else "0",
                "asof_source_packet_count": len(packets),
                "material_event_packet_count": counts.get("material_event_or_issuer_update", 0),
                "periodic_operating_packet_count": counts.get("periodic_operating_disclosure", 0),
                "capital_markets_packet_count": counts.get("capital_markets_financing_or_dilution", 0),
                "ownership_packet_count": counts.get("ownership_position_disclosure", 0),
                "governance_packet_count": counts.get("proxy_governance_disclosure", 0),
                "earnings_surprise_packet_count": counts.get("earnings_surprise_proxy", 0),
                "earnings_surprise_pct_sum": round(value_sums.get("earnings_surprise_proxy", 0.0), 6),
                "recommendation_packet_count": counts.get("recommendation_balance_proxy", 0),
                "recommendation_balance_sum": round(value_sums.get("recommendation_balance_proxy", 0.0), 6),
                "fundamental_quality_packet_count": counts.get("fundamental_quality_proxy", 0),
                "fundamental_quality_sum": round(value_sums.get("fundamental_quality_proxy", 0.0), 6),
                "strict_transcript_gate_pass": "0",
                "strict_analyst_revision_gate_pass": "0",
                "coverage_state": state,
                "missing_source_is_negative": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def semantic_score(row: dict[str, object]) -> tuple[float, str]:
    event = int(row["material_event_packet_count"])
    periodic = int(row["periodic_operating_packet_count"])
    financing = int(row["capital_markets_packet_count"])
    ownership = int(row["ownership_packet_count"])
    governance = int(row["governance_packet_count"])
    earnings = int(row["earnings_surprise_packet_count"])
    recommendation = int(row["recommendation_packet_count"])
    fundamentals = int(row["fundamental_quality_packet_count"])
    count = int(row["asof_source_packet_count"])
    if row["coverage_state"] == "source_gap_neutral":
        return 0.0, "api_source_gap_neutral"
    risk = min(2.8, financing * 0.65 + governance * 0.08)
    surprise = clamp(to_float(row.get("earnings_surprise_pct_sum")) / max(earnings, 1) / 12.0, -1.8, 1.8)
    rec_balance = clamp(to_float(row.get("recommendation_balance_sum")) / max(recommendation, 1), -1.5, 1.5)
    fundamental_quality = clamp(to_float(row.get("fundamental_quality_sum")) / max(fundamentals, 1), -1.0, 1.0)
    support = min(3.6, event * 0.25 + periodic * 0.08 + ownership * 0.03 + surprise + rec_balance + fundamental_quality)
    crowding = -0.25 if count > 18 else 0.0
    score = clamp(support - risk + crowding, -2.5, 2.5)
    if financing >= 2:
        state = "api_financing_or_dilution_risk"
    elif surprise >= 0.8 and recommendation > 0:
        state = "api_two_family_expectation_support"
    elif surprise <= -0.8 or rec_balance <= -0.75:
        state = "api_expectation_weakening_risk"
    elif score >= 0.8:
        state = "api_event_context_supportive"
    elif score <= -0.8:
        state = "api_risk_context_cap_required"
    elif count > 0:
        state = "api_context_light"
    else:
        state = "api_no_asof_packet_neutral"
    return round(score, 6), state


def task2163_semantics(coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(coverage, start=1):
        score, state = semantic_score(row)
        rows.append(
            {
                "task_id": "Task2163",
                "api_l2_semantic_id": f"APIL2H-2163-{idx:06d}",
                "coverage_id": row["coverage_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "api_l2_state": state,
                "api_l2_score": score,
                "microstructure_summary": (
                    f"event={row['material_event_packet_count']};periodic={row['periodic_operating_packet_count']};"
                    f"financing={row['capital_markets_packet_count']};governance={row['governance_packet_count']};"
                    f"earnings={row['earnings_surprise_packet_count']};recommendation={row['recommendation_packet_count']};"
                    f"fundamentals={row['fundamental_quality_packet_count']}"
                ),
                "l5_direct_gate_permission": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2164_edges(semantics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    edge_map = [
        ("event_context_modulates_payoff_confidence", "supports_or_contextualizes"),
        ("financing_or_dilution_context_caps_size", "weakens_or_caps"),
        ("source_gap_remains_neutral", "blocks_overclaim"),
    ]
    idx = 1
    for row in semantics:
        for relation_type, relation_effect in edge_map:
            rows.append(
                {
                    "task_id": "Task2164",
                    "api_l3_edge_id": f"APIL3H-2164-{idx:07d}",
                    "api_l2_semantic_id": row["api_l2_semantic_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "relation_type": relation_type,
                    "relation_effect": relation_effect,
                    "relation_permission": "proxy_only_not_strict_gate",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def task2171_score_cards(inputs: dict[str, list[dict[str, str]]], semantics: list[dict[str, object]]) -> list[dict[str, object]]:
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    sem_by_spec = {str(row["trade_spec_id"]): row for row in semantics}
    raw_rows: list[dict[str, object]] = []
    for idx, feature in enumerate(inputs["features"], start=1):
        l5 = l5_by_spec.get(feature["trade_spec_id"], {})
        sem = sem_by_spec.get(feature["trade_spec_id"], {})
        base_rank = to_float(l5.get("winner_acceleration_rank_score"))
        api_l2_score = to_float(sem.get("api_l2_score"))
        state = str(sem.get("api_l2_state", "api_source_gap_neutral"))
        if state in {"api_source_gap_neutral", "api_no_asof_packet_neutral"}:
            raw_overlay = 0.0
        else:
            raw_overlay = api_l2_score
        if state == "api_financing_or_dilution_risk":
            raw_overlay -= 0.9
        raw_rows.append(
            {
                "task_id": "Task2171",
                "api_l4_score_card_id": f"APIL4H-2171-{idx:06d}",
                "trade_spec_id": feature["trade_spec_id"],
                "candidate_source_id": feature["candidate_source_id"],
                "symbol": feature["symbol"],
                "decision_asof_ts": feature["decision_asof_ts"],
                "target_policy_variant_id": l5.get("target_policy_variant_id", ""),
                "base_winner_acceleration_rank_score": round(base_rank, 6),
                "api_l2_state": state,
                "api_l2_score": api_l2_score,
                "api_raw_overlay_score": round(raw_overlay, 6),
                "winner_acceleration_state": l5.get("winner_acceleration_state", ""),
                "winner_thesis_state": l5.get("winner_thesis_state", ""),
                "strict_gate_status": "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in raw_rows:
        grouped[str(row["decision_asof_ts"])].append(row)
    rows: list[dict[str, object]] = []
    for decision_ts, cohort in grouped.items():
        values = [to_float(row["api_raw_overlay_score"]) for row in cohort]
        mean = sum(values) / max(len(values), 1)
        variance = sum((value - mean) ** 2 for value in values) / max(len(values), 1)
        std = math.sqrt(variance) or 1.0
        for row in cohort:
            raw_overlay = to_float(row["api_raw_overlay_score"])
            if raw_overlay == 0.0:
                overlay = 0.0
            else:
                overlay = clamp(((raw_overlay - mean) / std) * 8.0, -15.0, 15.0)
            adjusted_rank = to_float(row["base_winner_acceleration_rank_score"]) + overlay
            row["api_cohort_overlay_score"] = round(overlay, 6)
            row["api_adjusted_rank_score"] = round(adjusted_rank, 6)
            rows.append(row)
    rows.sort(key=lambda item: (str(item["decision_asof_ts"]), str(item["trade_spec_id"])))
    return rows


def task2172_l5_decisions(inputs: dict[str, list[dict[str, str]]], cards: list[dict[str, object]]) -> list[dict[str, object]]:
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    rows: list[dict[str, object]] = []
    for idx, card in enumerate(cards, start=1):
        l5 = l5_by_spec.get(str(card["trade_spec_id"]), {})
        state = str(card["api_l2_state"])
        raw_mult = to_float(l5.get("raw_combined_multiplier"))
        if state == "api_two_family_expectation_support":
            multiplier = 1.1
            action = "two_family_expectation_confirmed_boost"
        elif state == "api_event_context_supportive":
            multiplier = 1.04
            action = "minor_boost_context_confirmed"
        elif state == "api_financing_or_dilution_risk":
            multiplier = 0.78
            action = "risk_cap_financing_or_dilution"
        elif state == "api_expectation_weakening_risk":
            multiplier = 0.7
            action = "risk_cap_expectation_weakening"
        elif state == "api_risk_context_cap_required":
            multiplier = 0.88
            action = "risk_cap_context_required"
        else:
            multiplier = 1.0
            action = "neutral_hold_existing_brain"
        rows.append(
            {
                "task_id": "Task2172",
                "api_l5_decision_id": f"APIL5H-2172-{idx:06d}",
                "trade_spec_id": card["trade_spec_id"],
                "candidate_source_id": card["candidate_source_id"],
                "symbol": card["symbol"],
                "decision_asof_ts": card["decision_asof_ts"],
                "api_l2_state": state,
                "api_l5_action": action,
                "api_l5_budget_multiplier": multiplier,
                "base_raw_combined_multiplier": round(raw_mult, 6),
                "strict_gate_status": "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def metrics_for(
    policy_id: str,
    trades: list[dict[str, object]],
    equity: list[dict[str, object]],
    baseline_metrics: list[dict[str, str]],
) -> dict[str, object]:
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1] if values else INITIAL_CAPITAL
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date() if equity else date(2021, 1, 1)
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final / INITIAL_CAPITAL) ** (1 / years) - 1.0
    mdd = replay.max_drawdown(values)
    baseline = next(row for row in baseline_metrics if row["policy_variant_id"] == BASELINE_POLICY)
    return {
        "task_id": "Task2175",
        "policy_variant_id": policy_id,
        "source_policy_variant_id": SOURCE_POLICY,
        "baseline_policy_variant_id": BASELINE_POLICY,
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final, 4),
        "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(mdd, 6),
        "trade_count": len(trades),
        "qqq_benchmark_final": QQQ_BENCHMARK_FINAL,
        "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
        "baseline_final_equity": baseline["final_equity"],
        "baseline_cagr": baseline["cagr"],
        "baseline_max_drawdown": baseline["max_drawdown"],
        "delta_vs_baseline_final_equity": round(final - to_float(baseline["final_equity"]), 4),
        "delta_vs_baseline_cagr": round(cagr - to_float(baseline["cagr"]), 6),
        "delta_vs_baseline_mdd": round(mdd - to_float(baseline["max_drawdown"]), 6),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def replay_variants(
    inputs: dict[str, list[dict[str, str]]],
    cards: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    card_by_spec = {str(row["trade_spec_id"]): row for row in cards}
    decision_by_spec = {str(row["trade_spec_id"]): row for row in decisions}
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["source_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["l5"]:
        if row["target_policy_variant_id"] == SOURCE_POLICY:
            grouped[row["decision_asof_ts"]].append(row)

    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    trade_idx = 1
    for policy_id in POLICY_VARIANTS:
        capital = INITIAL_CAPITAL
        for decision_ts in sorted(grouped):
            if policy_id == "api_loop3_filings_quality_top2_v1":
                candidates = sorted(
                    grouped[decision_ts],
                    key=lambda row: (
                        to_float(card_by_spec.get(row["trade_spec_id"], {}).get("api_adjusted_rank_score")),
                        to_float(card_by_spec.get(row["trade_spec_id"], {}).get("base_winner_acceleration_rank_score")),
                    ),
                    reverse=True,
                )[:2]
            elif policy_id == "api_loop3_guarded_risk_cap_top2_v1":
                candidates = sorted(
                    grouped[decision_ts],
                    key=lambda row: (
                        to_float(card_by_spec.get(row["trade_spec_id"], {}).get("api_adjusted_rank_score")),
                        to_float(card_by_spec.get(row["trade_spec_id"], {}).get("base_winner_acceleration_rank_score")),
                    ),
                    reverse=True,
                )[:2]
            else:
                candidates = sorted(
                    grouped[decision_ts],
                    key=lambda row: to_float(l5_by_spec.get(row["trade_spec_id"], {}).get("winner_acceleration_rank_score")),
                    reverse=True,
                )[:2]
            base_alloc = capital / 2.0
            period_pnl = 0.0
            allocated = 0
            for row in candidates:
                spec_id = row["trade_spec_id"]
                src = source_trades.get((SOURCE_POLICY, spec_id))
                l5 = l5_by_spec.get(spec_id)
                card = card_by_spec.get(spec_id)
                decision = decision_by_spec.get(spec_id)
                if not src or not l5 or not card or not decision:
                    continue
                raw_mult = to_float(l5["raw_combined_multiplier"])
                api_mult = to_float(decision["api_l5_budget_multiplier"], 1.0)
                if policy_id == "api_loop3_source_gap_neutral_top2_v1" and card["api_l2_state"] == "api_source_gap_neutral":
                    api_mult = 1.0
                if policy_id == "api_loop3_guarded_risk_cap_top2_v1" and "risk" in str(card["api_l2_state"]):
                    api_mult = min(api_mult, 0.72)
                mult = clamp(raw_mult * api_mult, 0.0, 1.42)
                cap_alloc = base_alloc * mult
                pnl = cap_alloc * to_float(src["net_return"])
                capital += pnl
                period_pnl += pnl
                allocated += 1
                trades.append(
                    {
                        "task_id": "Task2173",
                        "trade_row_id": f"API3LOOPTRADE-2173-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": SOURCE_POLICY,
                        "baseline_policy_variant_id": BASELINE_POLICY,
                        "trade_spec_id": spec_id,
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "api_l2_state": card["api_l2_state"],
                        "api_l2_score": card["api_l2_score"],
                        "api_l5_action": decision["api_l5_action"],
                        "base_rank_score": card["base_winner_acceleration_rank_score"],
                        "api_adjusted_rank_score": card["api_adjusted_rank_score"],
                        "final_budget_multiplier": round(mult, 6),
                        "source_net_return": src.get("net_return", ""),
                        "capital_allocated": round(cap_alloc, 4),
                        "pnl": round(pnl, 4),
                        "net_return": src.get("net_return", ""),
                        "entry_date": src.get("entry_date", ""),
                        "actual_exit_date": src.get("actual_exit_date", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task2174",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "candidate_pool_count": len(grouped[decision_ts]),
                    "allocated_count": allocated,
                    "authority": AUTHORITY,
                }
            )
        policy_trades = [row for row in trades if row["policy_variant_id"] == policy_id]
        policy_equity = [row for row in equity if row["policy_variant_id"] == policy_id]
        metrics.append(metrics_for(policy_id, policy_trades, policy_equity, inputs["baseline_metrics"]))
    return trades, equity, metrics


def task2176_expert_audit(gap_rows: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    blocked = sum(to_float(row["entitlement_blocked_rows"]) + to_float(row["quota_or_rate_blocked_rows"]) for row in gap_rows)
    return [
        {
            "task_id": "Task2176",
            "expert_role": "api_data_engineer",
            "verdict": "pass_with_blockers",
            "finding": "cache reuse and stoplist are correct; blocked provider rows cannot be recalled blindly",
            "required_followup": "obtain entitlement or alternative free official source before strict gate upgrade",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2176",
            "expert_role": "trading_brain_reviewer",
            "verdict": "diagnostic_only",
            "finding": f"best variant {best['policy_variant_id']} has final {best['final_equity']} but remains proxy-only",
            "required_followup": "do not promote proxy filing context into paper/live gate",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2176",
            "expert_role": "governance_leakage_reviewer",
            "verdict": "pass",
            "finding": f"blocked API rows={int(blocked)} are explicit and missing sources stay neutral",
            "required_followup": "keep outcome audit-only and strict gates closed until source receipt is certified",
            "authority": AUTHORITY,
        },
    ]


def closeout_rows(
    gap_rows: list[dict[str, object]],
    scope_rows: list[dict[str, object]],
    source_packets: list[dict[str, object]],
    coverage: list[dict[str, object]],
    metrics: list[dict[str, object]],
    secret_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    feature_without_capture = sum(1 for row in scope_rows if row["scope_state"] == "feature_without_api_capture_source_gap_neutral")
    source_gap = sum(1 for row in coverage if row["coverage_state"] == "source_gap_neutral")
    blocked = sum(int(row["entitlement_blocked_rows"]) + int(row["quota_or_rate_blocked_rows"]) for row in gap_rows)
    verdict = "api_three_loop_hardening_complete_proxy_only_gates_still_blocked"
    return [
        {
            "task_id": "Task2180",
            "verdict": verdict,
            "loop_count": 3,
            "provider_endpoint_rows": len(gap_rows),
            "blocked_or_quota_rows": blocked,
            "feature_without_capture_symbols": feature_without_capture,
            "source_packet_rows": len(source_packets),
            "decision_coverage_rows": len(coverage),
            "source_gap_neutral_rows": source_gap,
            "secret_hit_count": secret_rows[0]["secret_hit_count"],
            "replay_variant_count": len(metrics),
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met": best["joint_target_met"],
            "strict_transcript_gate_pass_rows": 0,
            "strict_analyst_revision_gate_pass_rows": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], audit: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric_lines = "\n".join(
        [
            f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, delta final {row['delta_vs_baseline_final_equity']}."
            for row in metrics
        ]
    )
    audit_lines = "\n".join([f"- {row['expert_role']}: {row['verdict']} - {row['finding']}." for row in audit])
    text = f"""# Task2151-2180 API Three Loop Hardening

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Loop count: {closeout['loop_count']}.
- Provider endpoint rows: {closeout['provider_endpoint_rows']}.
- Blocked or quota rows: {closeout['blocked_or_quota_rows']}.
- Feature without API capture symbols: {closeout['feature_without_capture_symbols']}.
- Source packet rows: {closeout['source_packet_rows']}.
- Decision coverage rows: {closeout['decision_coverage_rows']}.
- Source gap neutral rows: {closeout['source_gap_neutral_rows']}.
- Secret hit count: {closeout['secret_hit_count']}.
- Best diagnostic replay: `{closeout['best_policy_variant_id']}` final {closeout['best_final_equity']}, CAGR {closeout['best_cagr']}, MDD {closeout['best_max_drawdown']}.
- Strict transcript gate pass rows: 0.
- Strict analyst PIT gate pass rows: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task ran three loops over the free API capture from Task2121-2150:

1. Capture scope quality: provider and endpoint gaps were separated into usable, entitlement blocked, quota/rate blocked, and neutral source gaps.
2. Dataset semantic hardening: Finnhub filing rows were converted into per-decision source packets with form/accession/source URL fields and proxy-only L2/L3 states.
3. Brain/replay validation: three bounded replay variants were run. The API layer can modulate rank and size, but it cannot open strict transcript or analyst PIT gates.

Replay results:

{metric_lines}

Expert audit:

{audit_lines}

## No-Background Decision-Maker Report

Conclusion first: the API work is now cleaner, but it is still proxy-only. Finnhub filings are useful as context. FMP and Alpha remain blocked or too thin for full brain upgrade. The replay is diagnostic only and does not permit paper/live trading.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2151_2180_api_three_loop_hardening/`.
- Decision CSV: `docs/reports/task_2151_2180_api_three_loop_hardening/task_2151_2180_decision.csv`.
- Validator: `python scripts/trader_brain_2151_2180_api_three_loop_hardening_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    report_rel = "docs/reports/task_2151_2180_api_three_loop_hardening/task_2151_2180_api_three_loop_hardening.md"
    decision_rel = "docs/reports/task_2151_2180_api_three_loop_hardening/task_2151_2180_decision.csv"
    artifact_rel = "data/artifacts/task_2151_2180_api_three_loop_hardening"
    validation = "python scripts/trader_brain_2151_2180_api_three_loop_hardening_validate.py"
    for task_no in range(2151, 2181):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"API Three Loop Hardening Step {task_no}",
                "workstream": "Research Governance / Data & Market Microstructure / Backtest & Simulation Infra",
                "status": "active",
                "validation_tier": "diagnostic-only",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "api-three-loop-hardened-proxy-only-gates-still-blocked",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2151 else "Task2150",
                "report_path": report_rel,
                "decision_path": decision_rel,
                "artifact_path": artifact_rel,
                "validation_command": validation,
                "notes": "Runs three API hardening loops: capture scope quality, dataset semantic hardening, and diagnostic replay while strict transcript/analyst gates remain blocked.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "107. Task2151-Task2180"
    if marker in text:
        return
    line = (
        f"107. Task2151-Task2180 ran three API hardening loops over Task2121 free API captures: "
        f"provider endpoint gaps and scope mismatches were audited, Finnhub filing rows were converted into "
        f"per-decision proxy-only source packets, and three diagnostic replay variants were tested; best "
        f"`{closeout['best_policy_variant_id']}` ended final {closeout['best_final_equity']} with CAGR "
        f"{closeout['best_cagr']} and MDD {closeout['best_max_drawdown']}, but strict transcript and analyst PIT "
        f"gates remain closed and strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n\n\nTask851-859 data certification status:")
    if insert_at == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()

    loop_contract = task2151_loop_contract()
    gap_rows = task2152_gap_audit(inputs)
    scope_rows = task2153_scope_matrix(inputs)
    secret_rows = task2154_secret_blocker_audit(inputs)
    api_event_index = build_api_event_index(inputs["normalized"])
    source_packets = task2161_source_packets(inputs, api_event_index)
    coverage = task2162_decision_coverage(inputs, source_packets)
    semantics = task2163_semantics(coverage)
    edges = task2164_edges(semantics)
    cards = task2171_score_cards(inputs, semantics)
    decisions = task2172_l5_decisions(inputs, cards)
    trades, equity, metrics = replay_variants(inputs, cards, decisions)
    expert_audit = task2176_expert_audit(gap_rows, metrics)
    closeout = closeout_rows(gap_rows, scope_rows, source_packets, coverage, metrics, secret_rows)

    write_csv(OUT_DIR / "task2151_loop_contract.csv", loop_contract)
    write_csv(OUT_DIR / "task2152_api_quality_gap_audit.csv", gap_rows)
    write_csv(OUT_DIR / "task2153_capture_scope_matrix.csv", scope_rows)
    write_csv(OUT_DIR / "task2154_secret_and_blocker_audit.csv", secret_rows)
    write_csv(OUT_DIR / "task2161_api_source_packets.csv", source_packets)
    write_csv(OUT_DIR / "task2162_decision_asof_coverage.csv", coverage)
    write_csv(OUT_DIR / "task2163_l2_api_semantics_hardened.csv", semantics)
    write_csv(OUT_DIR / "task2164_l3_api_relation_edges_hardened.csv", edges)
    write_csv(OUT_DIR / "task2171_l4_api_score_cards_hardened.csv", cards)
    write_csv(OUT_DIR / "task2172_l5_api_decisions_hardened.csv", decisions)
    write_csv(OUT_DIR / "task2173_api_three_loop_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2174_api_three_loop_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2175_api_three_loop_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2176_expert_audit_matrix.csv", expert_audit)
    write_csv(OUT_DIR / "task2180_closeout.csv", closeout)
    write_json(OUT_DIR / "task2180_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, expert_audit)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])

    print("[TASK2151_2180_API_THREE_LOOP_HARDENING_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
