from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TASK1171 = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
TASK1181 = ROOT / "data/artifacts/task_1181_1190_l0_l3_strengthening_plan"
RAW_PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
SEC_ZIP = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip"
OUT_DIR = ROOT / "data/artifacts/task_1191_1200_l0_l3_candidate_compression"
REPORT_DIR = ROOT / "docs/reports/task_1191_1200_l0_l3_candidate_compression"

AUTHORITY = "DIAGNOSTIC_L0_L3_CANDIDATE_COMPRESSION_ONLY"
FORBIDDEN_ASSIGNMENT_INPUTS = "forward_return forward_hit pnl realized_return next_period_return exit_price future_price"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: object, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(var)
    if std == 0:
        return [0.0 for _ in values]
    return [(value - mean) / std for value in values]


def load_pool() -> dict[str, dict[str, str]]:
    rows = read_csv(TASK1171 / "task1171_price_download_pool.csv")
    return {row["symbol"].upper(): row for row in rows}


def load_sec_metadata(pool: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    ciks = {row["cik"].zfill(10) for row in pool.values() if row.get("cik")}
    metadata_by_cik: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(SEC_ZIP) as zf:
        names = {Path(name).stem.replace("CIK", "").zfill(10): name for name in zf.namelist() if name.lower().endswith(".json")}
        for cik in sorted(ciks):
            member = names.get(cik)
            if not member:
                continue
            payload = json.loads(zf.read(member))
            metadata_by_cik[cik] = {
                "sic": str(payload.get("sic", "") or ""),
                "sic_description": str(payload.get("sicDescription", "") or ""),
                "entity_type": str(payload.get("entityType", "") or ""),
                "category": str(payload.get("category", "") or ""),
                "state_of_incorporation": str(payload.get("stateOfIncorporation", "") or ""),
            }
    return metadata_by_cik


def likely_bad_security(symbol: str, entity_name: str, category: str, entity_type: str) -> tuple[bool, str]:
    upper_name = entity_name.upper()
    upper_symbol = symbol.upper()
    category_l = category.lower()
    entity_l = entity_type.lower()
    if upper_symbol.endswith(("W", "WS", "WT", "R", "U")):
        return True, "warrant_right_unit_suffix"
    if any(token in upper_name for token in ["ACQUISITION", "SPAC", "BLANK CHECK", "HOLDINGS II", "HOLDINGS III"]):
        return True, "spac_or_blank_check_name"
    if "shell" in category_l or "shell" in entity_l:
        return True, "shell_company_metadata"
    if upper_symbol.endswith(("F", "Y")) and ("ADR" in upper_name or "PLC" in upper_name or "S A" in upper_name):
        return True, "adr_or_foreign_ordinary_proxy"
    return False, ""


def industry_and_theme(entity_name: str, sic: str, sic_desc: str) -> tuple[str, str, str]:
    text = f"{entity_name} {sic_desc}".upper()
    sic_int = to_int(sic, -1)
    industry = "other"
    theme = "unclassified"
    relation_hint = "generic_public_filer"
    if any(k in text for k in ["SEMICONDUCTOR", "CHIP", "INTEGRATED CIRCUIT", "ELECTRONIC COMPONENT"]):
        industry, theme, relation_hint = "semiconductors", "ai_semiconductors", "compute_supply_chain"
    elif any(k in text for k in ["SOFTWARE", "CLOUD", "DATA", "INFORMATION SERVICES", "COMPUTER PROGRAMMING"]):
        industry, theme, relation_hint = "software_services", "cloud_ai_platforms", "software_monetization"
    elif any(k in text for k in ["CYBER", "SECURITY"]):
        industry, theme, relation_hint = "cybersecurity", "cybersecurity", "security_spend"
    elif any(k in text for k in ["ELECTRIC", "POWER", "UTILITY", "ENERGY", "GRID"]):
        industry, theme, relation_hint = "power_energy", "power_grid_electrification", "load_growth"
    elif any(k in text for k in ["AEROSPACE", "DEFENSE", "MISSILE", "SPACE", "AIRCRAFT"]):
        industry, theme, relation_hint = "aerospace_defense", "aerospace_defense_space", "defense_procurement"
    elif any(k in text for k in ["PHARM", "BIOTECH", "BIOLOG", "MEDICAL", "THERAPEUTIC", "HEALTH"]):
        industry, theme, relation_hint = "healthcare_biotech", "biotech_glp1_healthcare", "clinical_regulatory"
    elif any(k in text for k in ["BANK", "FINANCIAL", "PAYMENT", "CREDIT", "INSURANCE", "BROKER"]):
        industry, theme, relation_hint = "financials", "crypto_fintech", "financial_cycle"
    elif any(k in text for k in ["AUTO", "VEHICLE", "MOTOR", "TRUCK", "BATTERY"]):
        industry, theme, relation_hint = "autos_mobility", "ev_autonomy_mobility", "mobility_cycle"
    elif any(k in text for k in ["MACHINERY", "INDUSTRIAL", "ROBOT", "AUTOMATION", "EQUIPMENT"]):
        industry, theme, relation_hint = "industrial_automation", "industrial_automation_robotics", "capex_cycle"
    elif 3570 <= sic_int <= 3579 or 7370 <= sic_int <= 7379:
        industry, theme, relation_hint = "technology", "cloud_ai_platforms", "digital_capex"
    elif 3600 <= sic_int <= 3679:
        industry, theme, relation_hint = "electronics", "ai_semiconductors", "hardware_supply_chain"
    elif 2800 <= sic_int <= 2899 or 8000 <= sic_int <= 8099:
        industry, theme, relation_hint = "healthcare_biotech", "biotech_glp1_healthcare", "healthcare_demand"
    elif 4900 <= sic_int <= 4999:
        industry, theme, relation_hint = "utilities_energy", "power_grid_electrification", "load_growth"
    elif 3700 <= sic_int <= 3799:
        industry, theme, relation_hint = "industrial_transport", "ev_autonomy_mobility", "mobility_cycle"
    return industry, theme, relation_hint


def l0_filter_rows(features: list[dict[str, str]], pool: dict[str, dict[str, str]], metadata: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, object]] = []
    for row in features:
        symbol = row["symbol"].upper()
        key = (row["decision_asof_ts"], symbol)
        if key in seen:
            continue
        seen.add(key)
        pool_row = pool.get(symbol, {})
        meta = metadata.get(str(pool_row.get("cik", "")).zfill(10), {})
        bad_security, bad_reason = likely_bad_security(symbol, pool_row.get("entity_name", ""), meta.get("category", ""), meta.get("entity_type", ""))
        price = to_float(row["decision_close"])
        adv = to_float(row["avg_dollar_volume_60d"])
        vol = to_float(row["realized_vol_90d"])
        mom126 = to_float(row["momentum_126d"])
        reasons: list[str] = []
        if bad_security:
            reasons.append(bad_reason)
        if price < 5:
            reasons.append("price_below_5")
        if adv < 20_000_000:
            reasons.append("adv_below_20m")
        if vol > 1.10:
            reasons.append("volatility_above_110pct")
        if mom126 < -0.55:
            reasons.append("severe_recent_drawdown")
        if not pool_row.get("cik"):
            reasons.append("missing_cik")
        pass_flag = "1" if not reasons else "0"
        rows.append(
            {
                "task_id": "Task1191",
                "l0_filter_id": f"L0FILTER1191-{len(rows)+1:09d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": symbol,
                "cik": pool_row.get("cik", ""),
                "entity_name": pool_row.get("entity_name", ""),
                "sic": meta.get("sic", ""),
                "sic_description": meta.get("sic_description", ""),
                "entity_type": meta.get("entity_type", ""),
                "category": meta.get("category", ""),
                "decision_close": round(price, 6),
                "avg_dollar_volume_60d": round(adv, 2),
                "realized_vol_90d": round(vol, 6),
                "momentum_126d": round(mom126, 6),
                "l0_tradable_pass": pass_flag,
                "block_reasons": ";".join(reasons),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def industry_map_rows(l0_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in l0_rows:
        industry, theme, relation_hint = industry_and_theme(str(row["entity_name"]), str(row["sic"]), str(row["sic_description"]))
        rows.append(
            {
                "task_id": "Task1192",
                "industry_map_id": f"INDMAP1192-{len(rows)+1:09d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "entity_name": row["entity_name"],
                "sic": row["sic"],
                "sic_description": row["sic_description"],
                "derived_industry_group": industry,
                "derived_theme": theme,
                "relation_hint": relation_hint,
                "theme_label_source": "sic_description_and_entity_name_rule",
                "theme_label_for_selection_basis": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_packets(features: list[dict[str, str]], l0_rows: list[dict[str, object]], industry_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    source_catalog = read_csv(TASK1181 / "task1181_download_ledger.csv")
    source_by_domain = defaultdict(list)
    for row in source_catalog:
        if row["download_status"] in {"downloaded", "already_downloaded"}:
            source_by_domain[row["domain"]].append(row["source_id"])
    feature_by_key = {(row["decision_asof_ts"], row["symbol"].upper()): row for row in features}
    industry_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in industry_rows}
    rows = []
    for l0 in l0_rows:
        key = (str(l0["decision_asof_ts"]), str(l0["symbol"]))
        feature = feature_by_key.get(key, {})
        industry = industry_by_key.get(key, {})
        theme = str(industry.get("derived_theme", "unclassified"))
        theme_sources: list[str] = []
        if theme == "ai_semiconductors":
            theme_sources = source_by_domain["semiconductor/policy"] + source_by_domain["semiconductor/geopolitics"] + source_by_domain["semiconductor"]
        elif theme == "power_grid_electrification":
            theme_sources = source_by_domain["power_grid/ai"] + source_by_domain["power_grid"]
        elif theme == "aerospace_defense_space":
            theme_sources = source_by_domain["defense/aerospace"]
        elif theme == "cybersecurity":
            theme_sources = source_by_domain["cybersecurity/defense"]
        theme_sources = sorted(set(theme_sources))
        rows.append(
            {
                "task_id": "Task1193",
                "source_packet_id": f"L1PACKET1193-{len(rows)+1:09d}",
                "decision_asof_ts": l0["decision_asof_ts"],
                "symbol": l0["symbol"],
                "cik": l0["cik"],
                "source_families": "sec_submissions;yfinance_price;expert_context_sources",
                "sec_latest_filing_ts": feature.get("latest_filing_ts", ""),
                "price_context_asof_date": feature.get("decision_close_date", ""),
                "context_source_ids": ";".join(theme_sources),
                "source_packet_complete": "1" if feature and l0["l0_tradable_pass"] == "1" else "0",
                "source_packet_limitations": "theme_context_is_rule_based_not_company_specific;sec_public_filer_proxy_not_true_listing_pit",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def meaning_rows(features: list[dict[str, str]], l0_rows: list[dict[str, object]], industry_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    feature_by_key = {(row["decision_asof_ts"], row["symbol"].upper()): row for row in features}
    industry_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in industry_rows}
    rows = []
    for l0 in l0_rows:
        key = (str(l0["decision_asof_ts"]), str(l0["symbol"]))
        feature = feature_by_key.get(key, {})
        industry = industry_by_key.get(key, {})
        mom126 = to_float(feature.get("momentum_126d"))
        mom252 = to_float(feature.get("momentum_252d"))
        vol = to_float(feature.get("realized_vol_90d"))
        adv = to_float(feature.get("avg_dollar_volume_60d"))
        filing90 = to_int(feature.get("filing_count_90d"))
        diversity = to_int(feature.get("form_diversity_365d"))
        momentum_state = "positive_acceleration" if mom126 > 0.15 and mom252 > 0 else "weak_or_negative"
        liquidity_state = "institutional_tradeable" if adv >= 100_000_000 else ("tradeable" if adv >= 20_000_000 else "thin")
        volatility_state = "controlled" if vol <= 0.55 else ("elevated" if vol <= 1.10 else "extreme")
        filing_state = "active_disclosure" if filing90 >= 10 and diversity >= 6 else "low_context"
        theme = str(industry.get("derived_theme", "unclassified"))
        thematic_state = "theme_mapped" if theme != "unclassified" else "theme_unknown"
        rows.append(
            {
                "task_id": "Task1194",
                "meaning_id": f"L2MEANING1194-{len(rows)+1:09d}",
                "decision_asof_ts": l0["decision_asof_ts"],
                "symbol": l0["symbol"],
                "cik": l0["cik"],
                "momentum_state": momentum_state,
                "liquidity_state": liquidity_state,
                "volatility_state": volatility_state,
                "filing_activity_state": filing_state,
                "thematic_state": thematic_state,
                "economic_meaning_count": sum(
                    1
                    for state in [momentum_state, liquidity_state, volatility_state, filing_state, thematic_state]
                    if state not in {"weak_or_negative", "thin", "extreme", "low_context", "theme_unknown"}
                ),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def macro_policy_bridge(industry_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    bridge = {
        "ai_semiconductors": ("CHIPS_BIS_export_controls", "compute_supply_chain_policy"),
        "power_grid_electrification": ("DOE_data_center_power", "ai_power_load_growth"),
        "aerospace_defense_space": ("DoD_NDIS_defense_industrial_base", "defense_capacity_cycle"),
        "cybersecurity": ("DoD_DIB_cybersecurity", "cyber_resilience_spend"),
        "cloud_ai_platforms": ("FRED_BEA_productivity_and_capex", "ai_software_capex_cycle"),
        "biotech_glp1_healthcare": ("FDA_healthcare_policy_context_needed", "clinical_regulatory_cycle"),
        "crypto_fintech": ("Federal_Register_financial_policy_context", "regulatory_liquidity_cycle"),
    }
    for row in industry_rows:
        theme = str(row["derived_theme"])
        driver, mechanism = bridge.get(theme, ("generic_macro_context", "no_specific_policy_driver"))
        rows.append(
            {
                "task_id": "Task1195",
                "macro_policy_bridge_id": f"MACPOL1195-{len(rows)+1:09d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "derived_theme": theme,
                "policy_driver": driver,
                "macro_policy_mechanism": mechanism,
                "source_time_state": "context_source_downloaded_not_symbol_specific_asof",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def relation_edges(industry_rows: list[dict[str, object]], meaning: list[dict[str, object]], macro: list[dict[str, object]]) -> list[dict[str, object]]:
    meaning_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in meaning}
    macro_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in macro}
    rows = []
    for ind in industry_rows:
        key = (str(ind["decision_asof_ts"]), str(ind["symbol"]))
        mean = meaning_by_key.get(key, {})
        mac = macro_by_key.get(key, {})
        edge_templates = [
            ("company_to_industry", ind["derived_industry_group"], "industry_membership"),
            ("company_to_theme", ind["derived_theme"], str(ind["relation_hint"])),
            ("theme_to_policy_driver", mac.get("policy_driver", "generic_macro_context"), mac.get("macro_policy_mechanism", "")),
            ("company_to_risk_invalidator", "fragility_filter", "fails_if_l0_blocked_or_liquidity_thin_or_vol_extreme"),
        ]
        for edge_type, target, mechanism in edge_templates:
            rows.append(
                {
                    "task_id": "Task1196",
                    "relation_edge_id": f"L3EDGE1196-{len(rows)+1:010d}",
                    "decision_asof_ts": ind["decision_asof_ts"],
                    "symbol": ind["symbol"],
                    "edge_type": edge_type,
                    "source_node": ind["symbol"],
                    "target_node": target,
                    "mechanism": mechanism,
                    "confidence": "0.75" if mean.get("thematic_state") == "theme_mapped" else "0.35",
                    "source_time_state": "diagnostic_context_asof_not_company_specific",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def compression(features: list[dict[str, str]], l0: list[dict[str, object]], industry: list[dict[str, object]], meaning: list[dict[str, object]]) -> list[dict[str, object]]:
    feature_by_key = {(row["decision_asof_ts"], row["symbol"].upper()): row for row in features}
    ind_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in industry}
    meaning_by_key = {(str(row["decision_asof_ts"]), str(row["symbol"])): row for row in meaning}
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in l0:
        if row["l0_tradable_pass"] != "1":
            continue
        key = (str(row["decision_asof_ts"]), str(row["symbol"]))
        feat = feature_by_key.get(key)
        ind = ind_by_key.get(key, {})
        mean = meaning_by_key.get(key, {})
        if not feat:
            continue
        grouped[str(row["decision_asof_ts"])].append(
            {
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "derived_theme": ind.get("derived_theme", "unclassified"),
                "derived_industry_group": ind.get("derived_industry_group", "other"),
                "momentum_126d": to_float(feat["momentum_126d"]),
                "momentum_252d": to_float(feat["momentum_252d"]),
                "realized_vol_90d": to_float(feat["realized_vol_90d"]),
                "avg_dollar_volume_60d": to_float(feat["avg_dollar_volume_60d"]),
                "filing_count_90d": to_int(feat["filing_count_90d"]),
                "form_diversity_365d": to_int(feat["form_diversity_365d"]),
                "economic_meaning_count": to_int(mean.get("economic_meaning_count")),
            }
        )
    rows = []
    for decision_ts, items in sorted(grouped.items()):
        if not items:
            continue
        z_m126 = zscore([item["momentum_126d"] for item in items])
        z_m252 = zscore([item["momentum_252d"] for item in items])
        z_vol = zscore([item["realized_vol_90d"] for item in items])
        z_adv = zscore([math.log(max(item["avg_dollar_volume_60d"], 1.0)) for item in items])
        z_filing = zscore([float(item["filing_count_90d"]) for item in items])
        z_meaning = zscore([float(item["economic_meaning_count"]) for item in items])
        scored = []
        for idx, item in enumerate(items):
            theme_bonus = 0.20 if item["derived_theme"] != "unclassified" else -0.15
            score = (
                0.30 * z_m126[idx]
                + 0.20 * z_m252[idx]
                - 0.25 * z_vol[idx]
                + 0.20 * z_adv[idx]
                + 0.10 * z_filing[idx]
                + 0.20 * z_meaning[idx]
                + theme_bonus
            )
            scored.append((score, item))
        ranked = sorted(scored, key=lambda pair: (-pair[0], str(pair[1]["symbol"])))
        for rank, (score, item) in enumerate(ranked[:150], start=1):
            bucket = "top50" if rank <= 50 else ("top100" if rank <= 100 else "top150")
            rows.append(
                {
                    "task_id": "Task1197",
                    "compressed_candidate_id": f"COMP1197-{len(rows)+1:09d}",
                    "decision_asof_ts": decision_ts,
                    "candidate_rank": rank,
                    "candidate_bucket": bucket,
                    "symbol": item["symbol"],
                    "cik": item["cik"],
                    "derived_theme": item["derived_theme"],
                    "derived_industry_group": item["derived_industry_group"],
                    "l0_l3_compression_score": round(score, 8),
                    "economic_meaning_count": item["economic_meaning_count"],
                    "assignment_uses_future_outcome": "0",
                    "forbidden_assignment_inputs": FORBIDDEN_ASSIGNMENT_INPUTS,
                    "authority": AUTHORITY,
                }
            )
    return rows


def negative_fixtures(l0_rows: list[dict[str, object]], candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    blocked = [row for row in l0_rows if row["l0_tradable_pass"] == "0"][:20]
    candidate_symbols = {(row["decision_asof_ts"], row["symbol"]) for row in candidates}
    rows = []
    for row in blocked:
        rows.append(
            {
                "task_id": "Task1198",
                "fixture_id": f"NEG1198-{len(rows)+1:04d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "block_reasons": row["block_reasons"],
                "appears_in_compressed_candidates": "1" if (row["decision_asof_ts"], row["symbol"]) in candidate_symbols else "0",
                "expected_result": "must_not_enter_candidate_compression",
                "authority": AUTHORITY,
            }
        )
    return rows


def load_price(symbol: str) -> pd.DataFrame | None:
    path = RAW_PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if "Date" not in frame.columns or "Close" not in frame.columns:
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    return frame.sort_values("Date")


def price_on_or_after(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["Date"] >= d]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["Date"], float(row["Close"])


def price_on_or_before(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["Date"] <= d]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    return row["Date"], float(row["Close"])


def quality_diagnostic(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in candidates:
        grouped[(str(row["decision_asof_ts"]), str(row["candidate_bucket"]))].append(row)
    rows = []
    price_cache: dict[str, pd.DataFrame | None] = {}
    for (decision_ts, bucket), items in sorted(grouped.items()):
        decision_date = date.fromisoformat(decision_ts[:10])
        returns: list[float] = []
        for item in items:
            symbol = str(item["symbol"])
            if symbol not in price_cache:
                price_cache[symbol] = load_price(symbol)
            frame = price_cache[symbol]
            if frame is None:
                continue
            entry = price_on_or_after(frame, decision_date + timedelta(days=1))
            exit_ = price_on_or_before(frame, decision_date + timedelta(days=31))
            if not entry or not exit_ or entry[1] <= 0:
                continue
            returns.append(exit_[1] / entry[1] - 1.0)
        if returns:
            hit_rate = sum(1 for value in returns if value > 0) / len(returns)
            avg_return = sum(returns) / len(returns)
            median_return = sorted(returns)[len(returns) // 2]
        else:
            hit_rate = 0.0
            avg_return = 0.0
            median_return = 0.0
        rows.append(
            {
                "task_id": "Task1199",
                "quality_diag_id": f"QUAL1199-{len(rows)+1:05d}",
                "decision_asof_ts": decision_ts,
                "candidate_bucket": bucket,
                "candidate_count": len(items),
                "evaluation_rows": len(returns),
                "forward_hit_rate_1m_eval_only": round(hit_rate, 6),
                "avg_forward_return_1m_eval_only": round(avg_return, 6),
                "median_forward_return_1m_eval_only": round(median_return, 6),
                "outcome_used_for_assignment": "0",
                "selection_promoted": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def preregistration(candidates: list[dict[str, object]], quality: list[dict[str, object]]) -> list[dict[str, object]]:
    top50 = [row for row in candidates if row["candidate_bucket"] == "top50"]
    top50_quality = [row for row in quality if row["candidate_bucket"] == "top50"]
    avg_hit = sum(to_float(row["forward_hit_rate_1m_eval_only"]) for row in top50_quality) / len(top50_quality) if top50_quality else 0.0
    ready = len(top50) > 0 and avg_hit >= 0.52
    return [
        {
            "task_id": "Task1200",
            "preregistration_id": "PREREG1200-001",
            "candidate_policy_id": "l0_l3_public_filer_candidate_compression_v1",
            "top50_candidate_rows": len(top50),
            "top50_avg_hit_rate_eval_only": round(avg_hit, 6),
            "policy_preregistration_allowed": "1" if ready else "0",
            "replay_executed": "0",
            "selection_promoted": "0",
            "block_reason": "" if ready else "candidate_quality_threshold_not_met_or_requires_human_review",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1191_1200_l0_l3_candidate_compression.md"
    lines = [
        "# Task1191-1200 L0-L3 Candidate Compression",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- L0 rows: {closeout['l0_rows']}.",
        f"- L0 pass rows: {closeout['l0_pass_rows']}.",
        f"- L1 packets: {closeout['l1_packets']}.",
        f"- L2 meaning rows: {closeout['l2_meaning_rows']}.",
        f"- L3 relation edges: {closeout['l3_relation_edges']}.",
        f"- Compressed candidates: {closeout['compressed_candidate_rows']}.",
        f"- Top50 avg hit rate, eval only: {closeout['top50_avg_hit_rate_eval_only']}.",
        f"- Policy preregistration allowed: `{closeout['policy_preregistration_allowed']}`.",
        "- Replay executed: 0.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This task implements the L0-L3 front-brain strengthening plan without running a new PnL replay.",
        "",
        "Implemented layers:",
        "",
        "1. L0 filters remove bad tradable objects before ranking.",
        "2. L0 industry/theme mapper creates diagnostic industry and theme labels.",
        "3. L1 source packets bind SEC submissions, price context, and expert context sources.",
        "4. L2 meaning rows translate raw fields into momentum, liquidity, volatility, filing, and thematic states.",
        "5. L3 edges connect company, industry, theme, policy driver, and risk invalidator.",
        "6. Candidate compression produces top 50/100/150 lists before any L4/L5 replay.",
        "",
        "Outcome data is used only in Task1199 evaluation rows and is explicitly blocked from assignment logic.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The code now has a front brain.",
        "",
        "It first throws out obviously bad objects, then maps industry and theme, then builds source and meaning packets, then creates relation edges, then compresses the universe into candidates.",
        "",
        "No new backtest was run. This is the gate before another replay.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1191_l0_security_filter.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1192_industry_theme_map.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1193_l1_source_packets.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1194_l2_meaning_panel.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1195_macro_policy_bridge.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1196_l3_relation_edges.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1197_compressed_candidates.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1198_negative_fixtures.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1199_candidate_quality_diagnostic.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_replay_preregistration_gate.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_l0_l3_candidate_compression_closeout.csv`",
        "- `data/artifacts/task_1191_1200_l0_l3_candidate_compression/task1200_l0_l3_candidate_compression_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1191_1200_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    features = read_csv(TASK1171 / "task1174_public_filer_proxy_feature_panel.csv")
    pool = load_pool()
    metadata = load_sec_metadata(pool)
    l0 = l0_filter_rows(features, pool, metadata)
    industry = industry_map_rows(l0)
    packets = source_packets(features, l0, industry)
    meaning = meaning_rows(features, l0, industry)
    macro = macro_policy_bridge(industry)
    edges = relation_edges(industry, meaning, macro)
    candidates = compression(features, l0, industry, meaning)
    negatives = negative_fixtures(l0, candidates)
    quality = quality_diagnostic(candidates)
    prereg = preregistration(candidates, quality)
    top50_quality = [row for row in quality if row["candidate_bucket"] == "top50"]
    avg_hit = sum(to_float(row["forward_hit_rate_1m_eval_only"]) for row in top50_quality) / len(top50_quality) if top50_quality else 0.0
    closeout = {
        "task_id": "Task1191-1200",
        "verdict": "l0_l3_candidate_compression_implemented_replay_not_executed",
        "l0_rows": len(l0),
        "l0_pass_rows": sum(1 for row in l0 if row["l0_tradable_pass"] == "1"),
        "l1_packets": len(packets),
        "l2_meaning_rows": len(meaning),
        "l3_relation_edges": len(edges),
        "compressed_candidate_rows": len(candidates),
        "negative_fixture_rows": len(negatives),
        "quality_diagnostic_rows": len(quality),
        "top50_avg_hit_rate_eval_only": round(avg_hit, 6),
        "policy_preregistration_allowed": prereg[0]["policy_preregistration_allowed"],
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "review_candidate_quality_and_only_then_run_one_controlled_replay_if_preregistration_is_allowed",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1191_l0_security_filter.csv", l0)
    write_csv(OUT_DIR / "task1192_industry_theme_map.csv", industry)
    write_csv(OUT_DIR / "task1193_l1_source_packets.csv", packets)
    write_csv(OUT_DIR / "task1194_l2_meaning_panel.csv", meaning)
    write_csv(OUT_DIR / "task1195_macro_policy_bridge.csv", macro)
    write_csv(OUT_DIR / "task1196_l3_relation_edges.csv", edges)
    write_csv(OUT_DIR / "task1197_compressed_candidates.csv", candidates)
    write_csv(OUT_DIR / "task1198_negative_fixtures.csv", negatives)
    write_csv(OUT_DIR / "task1199_candidate_quality_diagnostic.csv", quality)
    write_csv(OUT_DIR / "task1200_replay_preregistration_gate.csv", prereg)
    write_csv(OUT_DIR / "task1200_l0_l3_candidate_compression_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1200_l0_l3_candidate_compression_closeout.json", closeout)
    write_report(closeout)
    print(
        "[TRADER_BRAIN_1191_1200_L0_L3_CANDIDATE_COMPRESSION_OK] "
        f"l0_pass={closeout['l0_pass_rows']}/{closeout['l0_rows']} "
        f"candidates={closeout['compressed_candidate_rows']} "
        f"top50_hit={closeout['top50_avg_hit_rate_eval_only']} "
        f"prereg={closeout['policy_preregistration_allowed']} "
        "replay=0"
    )


if __name__ == "__main__":
    main()
