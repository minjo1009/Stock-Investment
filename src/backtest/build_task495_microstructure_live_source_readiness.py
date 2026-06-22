from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data.alpaca_stock_stream_archive import DEFAULT_CHANNELS, StreamArchiveConfig
from src.data.full_depth_book_archive import FullDepthBookArchive


DEFAULT_OUT_DIR = Path("docs/reports/task_495_microstructure_live_source_readiness")


def build_task495_microstructure_live_source_readiness(
    *,
    symbols: tuple[str, ...] = ("AAPL", "AMD", "NVDA"),
    feed: str = "sip",
    archive_output_dir: Path = Path("data/raw/alpaca_stock_stream_archive"),
    out_dir: Path = DEFAULT_OUT_DIR,
) -> dict[str, pd.DataFrame]:
    stream_config = StreamArchiveConfig(symbols=symbols, output_dir=archive_output_dir, feed=feed, channels=DEFAULT_CHANNELS, duration_seconds=300)
    depth_status = FullDepthBookArchive(output_dir=Path("data/raw/full_depth_book_archive")).readiness()
    contract = pd.DataFrame(
        [
            {
                "source_name": "raw_receive_timestamp",
                "source_type": "local_archive_metadata",
                "implementation_status": "implemented_in_live_archive",
                "historical_backfill_available_flag": 0,
                "live_capture_available_flag": 1,
                "fake_or_inferred_flag": 0,
                "implementation_detail": "recv_ts_utc and recv_monotonic_ns are attached at WebSocket receive time.",
            },
            {
                "source_name": "stock_quotes_nbbo",
                "source_type": "alpaca_stock_stream",
                "implementation_status": "implemented_in_live_archive",
                "historical_backfill_available_flag": 1,
                "live_capture_available_flag": 1,
                "fake_or_inferred_flag": 0,
                "implementation_detail": "quotes channel archived as raw JSONL with event timestamp and local receive timestamp.",
            },
            {
                "source_name": "stock_trading_status",
                "source_type": "alpaca_stock_stream",
                "implementation_status": "implemented_in_live_archive",
                "historical_backfill_available_flag": 0,
                "live_capture_available_flag": 1,
                "fake_or_inferred_flag": 0,
                "implementation_detail": "statuses channel can be subscribed and archived; historical status is not reconstructed.",
            },
            {
                "source_name": "stock_luld",
                "source_type": "alpaca_stock_stream",
                "implementation_status": "implemented_in_live_archive",
                "historical_backfill_available_flag": 0,
                "live_capture_available_flag": 1,
                "fake_or_inferred_flag": 0,
                "implementation_detail": "lulds channel can be subscribed and archived; historical LULD is not reconstructed.",
            },
            {
                "source_name": "full_depth_book",
                "source_type": "external_direct_depth_provider_required",
                "implementation_status": depth_status.source_status,
                "historical_backfill_available_flag": 0,
                "live_capture_available_flag": 0,
                "fake_or_inferred_flag": 0,
                "implementation_detail": depth_status.reason,
            },
        ]
    )
    archive_contract = pd.DataFrame(
        [
            {
                "feed": stream_config.feed,
                "symbols": ",".join(stream_config.symbols),
                "channels": ",".join(stream_config.channels),
                "output_dir": str(stream_config.output_dir),
                "archive_format": "jsonl_partitioned_by_trade_date_channel_symbol",
                "required_fields": "recv_ts_utc|recv_monotonic_ns|event_ts_utc|raw_message_json|raw_message_hash|channel|symbol",
                "exact_replay_note": "Replay may use only archived messages with recv_ts_utc <= decision_cutoff_recv_ts_utc.",
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task495",
                "task_name": "Microstructure Live Source Readiness",
                "raw_receive_timestamp_implemented_flag": 1,
                "status_luld_live_archive_implemented_flag": 1,
                "full_depth_book_implemented_flag": int(depth_status.implemented_flag),
                "full_depth_book_blocked_reason": depth_status.reason,
                "fake_depth_or_luld_used_flag": 0,
                "task_495_status": "LIVE_QUOTE_STATUS_LULD_ARCHIVE_READY_FULL_DEPTH_PROVIDER_REQUIRED",
                "strategy_acceptance_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    contract.to_csv(out_dir / "microstructure_live_source_contract.csv", index=False)
    archive_contract.to_csv(out_dir / "alpaca_stream_archive_contract.csv", index=False)
    decision.to_csv(out_dir / "task_495_decision.csv", index=False)
    (out_dir / "task_495_microstructure_live_source_readiness.md").write_text(build_report(contract, archive_contract, decision), encoding="utf-8")
    return {"contract": contract, "archive_contract": archive_contract, "decision": decision}


def build_report(contract: pd.DataFrame, archive_contract: pd.DataFrame, decision: pd.DataFrame) -> str:
    row = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 495 - Microstructure Live Source Readiness",
            "",
            "## Quant Expert Report",
            "",
            "- raw receive timestamp: implemented through live WebSocket archive metadata",
            "- status/LULD: implemented as live Alpaca stock stream archive channels",
            "- quote/spread/NBBO size: implemented through Alpaca quotes, historical and live",
            "- full depth book: not available from Alpaca stock API; direct-depth provider integration required",
            "- fake/inferred microstructure: NO",
            f"- Status: {row['task_495_status']}",
            "",
            "## Source Contract",
            "",
            _csv_block(contract),
            "",
            "## Archive Contract",
            "",
            _csv_block(archive_contract),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "실시간 quote/status/LULD는 저장할 수 있게 만들었다. 각 메시지에는 우리가 받은 시각을 붙인다. 하지만 full depth book은 Alpaca 주식 API에 없어서 가짜로 만들지 않았다. 이건 별도 direct-depth 데이터 공급자가 필요하다.",
        ]
    )


def _csv_block(df: pd.DataFrame) -> str:
    return "```csv\n" + df.to_csv(index=False) + "```"


def _parse_symbols(raw: str) -> tuple[str, ...]:
    return tuple(symbol.strip().upper() for symbol in raw.split(",") if symbol.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="AAPL,AMD,NVDA")
    parser.add_argument("--feed", default="sip")
    parser.add_argument("--archive-output-dir", type=Path, default=Path("data/raw/alpaca_stock_stream_archive"))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task495_microstructure_live_source_readiness(
        symbols=_parse_symbols(args.symbols),
        feed=args.feed,
        archive_output_dir=args.archive_output_dir,
        out_dir=args.out_dir,
    )
    row = artifacts["decision"].iloc[0]
    print(f"[TASK495] status={row['task_495_status']} full_depth={row['full_depth_book_implemented_flag']}")


if __name__ == "__main__":
    main()
