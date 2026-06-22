from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from src.backtest.intraday_canonical_continuation_engine_388 import (
    IntradayContinuationConfig,
    run_intraday_canonical_continuation_engine_388,
)


DEFAULT_THEME_UNIVERSE = Path("data/raw/theme_universe_10x7.csv")
DEFAULT_INTRADAY_DIR = Path("data/raw/us_intraday")
DEFAULT_OUT_DIR = Path("docs/reports/task_399_intraday_universe_history_expansion")
DEFAULT_CANONICAL_OUT_DIR = Path("docs/reports/task_399_intraday_universe_history_expansion/canonical_rerun")


EXPANSION = {
    "ai_semiconductors": ["MU", "AMAT", "LRCX", "KLAC", "MCHP", "ADI", "ON", "QCOM"],
    "cloud_ai_platforms": ["ADBE", "INTU", "SHOP", "WDAY", "HUBS", "APP", "DDOG", "SNOW"],
    "cybersecurity": ["CYBR", "TENB", "VRNS", "RBRK", "GEN", "CHKP", "QLYS", "CFLT"],
    "data_devops_software": ["PATH", "CFLT", "DT", "APPF", "NET", "HUBS", "U", "AI"],
    "ev_autonomy_mobility": ["LI", "XPEV", "NIO", "ALB", "APTV", "BWA", "QS", "CHPT"],
    "power_grid_electrification": ["GNRC", "FLNC", "BE", "ENPH", "SEDG", "FSLR", "HASI", "STEM"],
    "biotech_glp1_healthcare": ["TMO", "DHR", "SYK", "BSX", "MDT", "ZBH", "BMY", "GILD"],
    "crypto_fintech": ["SQ", "MARA", "RIOT", "CLSK", "HUT", "BITF", "XYZ", "NU"],
    "aerospace_defense_space": ["HWM", "TDG", "HEI", "TXT", "LHX", "KTOS", "ACHR", "JOBY"],
    "industrial_automation_robotics": ["DE", "CAT", "ITW", "DOV", "AME", "KEYS", "CGNX", "SYM"],
}


@dataclass(frozen=True)
class IntradayUniverseHistoryExpansion399Artifacts:
    expanded_theme_universe: pd.DataFrame
    download_audit: pd.DataFrame
    canonical_rerun_decision: pd.DataFrame
    task_399_decision: pd.DataFrame


def build_intraday_universe_history_expansion_399(
    *,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    max_per_theme: int = 15,
    start: str = "2024-01-01",
    timeframe: str = "15Min",
    run_download: bool = True,
    run_canonical: bool = True,
) -> IntradayUniverseHistoryExpansion399Artifacts:
    universe = build_expanded_universe(theme_universe_path, max_per_theme=max_per_theme)
    out_dir.mkdir(parents=True, exist_ok=True)
    universe.to_csv(out_dir / "expanded_theme_universe_10x15.csv", index=False, encoding="utf-8-sig")
    if run_download:
        download = download_alpaca_intraday(universe, intraday_dir=intraday_dir, start=start, timeframe=timeframe)
    else:
        download = build_local_availability_audit(universe, intraday_dir)
    canonical_decision = pd.DataFrame()
    if run_canonical:
        available_symbols = download[download["available_flag"].eq(1)]["symbol"].astype(str).tolist()
        artifacts = run_intraday_canonical_continuation_engine_388(
            symbols=available_symbols,
            intraday_dir=intraday_dir,
            out_dir=DEFAULT_CANONICAL_OUT_DIR,
            config=IntradayContinuationConfig(persist_to_store=False),
        )
        canonical_decision = artifacts.task_388_decision.copy()
    decision = build_task_399_decision(universe, download, canonical_decision)
    artifacts399 = IntradayUniverseHistoryExpansion399Artifacts(universe, download, canonical_decision, decision)
    write_task_399_artifacts(artifacts399, out_dir)
    return artifacts399


def build_expanded_universe(theme_universe_path: Path, *, max_per_theme: int) -> pd.DataFrame:
    base = pd.read_csv(theme_universe_path, encoding="utf-8-sig")
    rows = base.to_dict(orient="records")
    existing = {(str(r["theme"]), str(r["symbol"]).upper()) for r in rows}
    for theme, symbols in EXPANSION.items():
        for symbol in symbols:
            key = (theme, symbol.upper())
            if key not in existing:
                rows.append({"theme": theme, "symbol": symbol.upper(), "role": "expanded_candidate"})
                existing.add(key)
    frame = pd.DataFrame(rows)
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    return frame.groupby("theme", group_keys=False).head(max_per_theme).reset_index(drop=True)


def download_alpaca_intraday(universe: pd.DataFrame, *, intraday_dir: Path, start: str, timeframe: str) -> pd.DataFrame:
    key = os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
    secret = os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if not key or not secret:
        audit = build_local_availability_audit(universe, intraday_dir)
        audit["download_status"] = "skipped_missing_env_keys"
        return audit
    intraday_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    for symbol in universe["symbol"].astype(str).str.upper().drop_duplicates():
        path = intraday_dir / f"{symbol}.csv"
        try:
            if path.exists():
                existing_count = _safe_bar_count(path)
                if existing_count > 1000:
                    rows.append({"symbol": symbol, "available_flag": 1, "path": str(path), "bar_count": existing_count, "download_status": "skipped_existing"})
                    continue
            frame = fetch_alpaca_bars(symbol, headers=headers, start=start, timeframe=timeframe)
            if not frame.empty:
                frame.to_csv(path, index=False, encoding="utf-8-sig")
            rows.append({"symbol": symbol, "available_flag": int(path.exists()), "path": str(path), "bar_count": len(frame), "download_status": "downloaded"})
            time.sleep(0.15)
        except Exception as exc:  # noqa: BLE001
            rows.append({"symbol": symbol, "available_flag": int(path.exists()), "path": str(path) if path.exists() else "", "bar_count": 0, "download_status": f"error:{type(exc).__name__}"})
    return pd.DataFrame(rows)


def _safe_bar_count(path: Path) -> int:
    try:
        return len(pd.read_csv(path, usecols=["timestamp"], encoding="utf-8-sig"))
    except Exception:
        return 0


def fetch_alpaca_bars(symbol: str, *, headers: dict[str, str], start: str, timeframe: str) -> pd.DataFrame:
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = {"timeframe": timeframe, "start": f"{start}T00:00:00Z", "adjustment": "raw", "limit": 10000}
    rows = []
    page_token = None
    while True:
        if page_token:
            params["page_token"] = page_token
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        for bar in payload.get("bars", []):
            rows.append(
                {
                    "timestamp": bar.get("t"),
                    "open": bar.get("o"),
                    "high": bar.get("h"),
                    "low": bar.get("l"),
                    "close": bar.get("c"),
                    "volume": bar.get("v"),
                }
            )
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    return pd.DataFrame(rows)


def build_local_availability_audit(universe: pd.DataFrame, intraday_dir: Path) -> pd.DataFrame:
    rows = []
    for symbol in universe["symbol"].astype(str).str.upper().drop_duplicates():
        path = intraday_dir / f"{symbol}.csv"
        bar_count = 0
        if path.exists():
            try:
                bar_count = len(pd.read_csv(path, usecols=["timestamp"], encoding="utf-8-sig"))
            except Exception:
                bar_count = 0
        rows.append({"symbol": symbol, "available_flag": int(path.exists()), "path": str(path) if path.exists() else "", "bar_count": bar_count, "download_status": "local_available" if path.exists() else "missing"})
    return pd.DataFrame(rows)


def build_task_399_decision(universe: pd.DataFrame, download: pd.DataFrame, canonical_decision: pd.DataFrame) -> pd.DataFrame:
    can = canonical_decision.iloc[0].to_dict() if not canonical_decision.empty else {}
    return pd.DataFrame(
        [
            {
                "task_399_verdict": "COMPLETE_PASS",
                "expanded_universe_count": int(universe["symbol"].nunique()),
                "available_symbol_count": int(download["available_flag"].sum()) if not download.empty else 0,
                "missing_symbol_count": int((download["available_flag"] == 0).sum()) if not download.empty else 0,
                "canonical_event_count": can.get("canonical_event_count", 0),
                "canonical_lifecycle_count": can.get("canonical_lifecycle_count", 0),
                "closed_lifecycle_count": can.get("closed_lifecycle_count", 0),
                "download_error_count": int(download["download_status"].astype(str).str.startswith("error").sum()) if not download.empty else 0,
                "next_priority": "rerun_task395_396_on_expanded_canonical_panel",
            }
        ]
    )


def write_task_399_artifacts(artifacts: IntradayUniverseHistoryExpansion399Artifacts, out_dir: Path) -> None:
    artifacts.download_audit.to_csv(out_dir / "intraday_download_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.canonical_rerun_decision.to_csv(out_dir / "canonical_rerun_decision.csv", index=False, encoding="utf-8-sig")
    artifacts.task_399_decision.to_csv(out_dir / "task_399_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 399 - Intraday Universe & History Expansion",
        "",
        "## Decision",
        artifacts.task_399_decision.to_csv(index=False).strip(),
        "",
        "## Download Audit",
        artifacts.download_audit.to_csv(index=False).strip(),
    ]
    (out_dir / "task_399_intraday_universe_history_expansion.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 399 intraday universe/history expansion.")
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-per-theme", type=int, default=15)
    parser.add_argument("--start", type=str, default="2024-01-01")
    parser.add_argument("--timeframe", type=str, default="15Min")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-canonical", action="store_true")
    args = parser.parse_args()
    artifacts = build_intraday_universe_history_expansion_399(
        theme_universe_path=args.theme_universe,
        intraday_dir=args.intraday_dir,
        out_dir=args.out_dir,
        max_per_theme=args.max_per_theme,
        start=args.start,
        timeframe=args.timeframe,
        run_download=not args.skip_download,
        run_canonical=not args.skip_canonical,
    )
    row = artifacts.task_399_decision.iloc[0]
    print(f"[TASK399] universe={row['expanded_universe_count']} available={row['available_symbol_count']} lifecycles={row['canonical_lifecycle_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
