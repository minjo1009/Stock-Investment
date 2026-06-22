from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from src.data.env_loader import load_repo_env


DEFAULT_STREAM_URL_TEMPLATE = "wss://stream.data.alpaca.markets/v2/{feed}"
DEFAULT_CHANNELS = ("quotes", "statuses", "lulds")
MESSAGE_TYPE_TO_CHANNEL = {
    "q": "quotes",
    "s": "statuses",
    "l": "lulds",
    "t": "trades",
    "b": "bars",
    "u": "updatedBars",
    "c": "corrections",
    "x": "cancelErrors",
}


@dataclass(frozen=True)
class StreamArchiveConfig:
    symbols: tuple[str, ...]
    output_dir: Path
    feed: str = "sip"
    channels: tuple[str, ...] = DEFAULT_CHANNELS
    duration_seconds: int | None = None
    stream_url_template: str = DEFAULT_STREAM_URL_TEMPLATE


class JsonlArchiveWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_records(self, records: Iterable[dict[str, object]]) -> int:
        count = 0
        handles: dict[Path, object] = {}
        try:
            for record in records:
                path = self._path_for_record(record)
                if path not in handles:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    handles[path] = path.open("a", encoding="utf-8")
                handles[path].write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
        finally:
            for handle in handles.values():
                handle.close()
        return count

    def _path_for_record(self, record: dict[str, object]) -> Path:
        recv_ts = str(record.get("recv_ts_utc", "unknown"))
        date_part = recv_ts[:10] if len(recv_ts) >= 10 else "unknown_date"
        channel = str(record.get("channel", "unknown"))
        symbol = str(record.get("symbol", "UNKNOWN")).upper()
        return self.output_dir / f"trade_date={date_part}" / f"channel={channel}" / f"{symbol}.jsonl"


def normalize_stream_payload(payload: list[dict[str, object]], *, recv_ts_utc: str | None = None, recv_monotonic_ns: int | None = None) -> list[dict[str, object]]:
    recv_ts_utc = recv_ts_utc or _utc_now_iso()
    recv_monotonic_ns = recv_monotonic_ns if recv_monotonic_ns is not None else time.monotonic_ns()
    records: list[dict[str, object]] = []
    for index, message in enumerate(payload):
        message_type = str(message.get("T", "unknown"))
        symbol = str(message.get("S", "") or message.get("symbol", "") or "UNKNOWN").upper()
        raw_json = json.dumps(message, ensure_ascii=False, sort_keys=True)
        records.append(
            {
                "recv_ts_utc": recv_ts_utc,
                "recv_monotonic_ns": recv_monotonic_ns,
                "message_index": index,
                "channel": MESSAGE_TYPE_TO_CHANNEL.get(message_type, message_type),
                "message_type": message_type,
                "symbol": symbol,
                "event_ts_utc": message.get("t"),
                "raw_message_json": raw_json,
                "raw_message_hash": hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
            }
        )
    return records


async def run_archive(config: StreamArchiveConfig) -> int:
    try:
        import websockets
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("websockets package is required for live stream archiving") from exc

    load_repo_env()
    api_key = os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")

    url = config.stream_url_template.format(feed=config.feed)
    writer = JsonlArchiveWriter(config.output_dir)
    start = time.monotonic()
    written = 0
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}
    connect_params = inspect.signature(websockets.connect).parameters
    connect_kwargs = {"additional_headers": headers} if "additional_headers" in connect_params else {"extra_headers": headers}
    async with websockets.connect(url, **connect_kwargs) as websocket:
        raw = await websocket.recv()
        payload = json.loads(raw)
        if not isinstance(payload, list):
            payload = [payload]
        written += writer.write_records(normalize_stream_payload(payload, recv_ts_utc=_utc_now_iso(), recv_monotonic_ns=time.monotonic_ns()))
        await websocket.send(json.dumps({"action": "auth", "key": api_key, "secret": secret_key}))
        raw = await websocket.recv()
        payload = json.loads(raw)
        if not isinstance(payload, list):
            payload = [payload]
        written += writer.write_records(normalize_stream_payload(payload, recv_ts_utc=_utc_now_iso(), recv_monotonic_ns=time.monotonic_ns()))
        subscribe = {"action": "subscribe"}
        for channel in config.channels:
            subscribe[channel] = list(config.symbols)
        await websocket.send(json.dumps(subscribe))
        while True:
            remaining = None
            if config.duration_seconds is not None:
                remaining = config.duration_seconds - (time.monotonic() - start)
                if remaining <= 0:
                    break
            try:
                raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            except TimeoutError:
                break
            recv_ts = _utc_now_iso()
            recv_ns = time.monotonic_ns()
            payload = json.loads(raw)
            if not isinstance(payload, list):
                payload = [payload]
            records = normalize_stream_payload(payload, recv_ts_utc=recv_ts, recv_monotonic_ns=recv_ns)
            written += writer.write_records(records)
    return written


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_symbols(raw: str) -> tuple[str, ...]:
    return tuple(symbol.strip().upper() for symbol in raw.split(",") if symbol.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive Alpaca stock stream messages with local receive timestamps.")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols, e.g. AAPL,AMD,NVDA")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/alpaca_stock_stream_archive"))
    parser.add_argument("--feed", default="sip")
    parser.add_argument("--channels", default="quotes,statuses,lulds")
    parser.add_argument("--duration-seconds", type=int, default=300)
    args = parser.parse_args()
    config = StreamArchiveConfig(
        symbols=_parse_symbols(args.symbols),
        output_dir=args.output_dir,
        feed=args.feed,
        channels=tuple(channel.strip() for channel in args.channels.split(",") if channel.strip()),
        duration_seconds=args.duration_seconds,
    )
    written = asyncio.run(run_archive(config))
    print(f"[STREAM_ARCHIVE] written={written} output_dir={config.output_dir}")


if __name__ == "__main__":
    main()
