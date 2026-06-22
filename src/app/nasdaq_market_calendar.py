from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")
DEFAULT_OPEN = time(9, 30)
DEFAULT_CLOSE = time(16, 0)


@dataclass(frozen=True)
class CalendarDay:
    session_date: date
    status: str
    open_et: time | None
    close_et: time | None
    name: str
    source: str


def _parse_time(value: str, fallback: time | None = None) -> time | None:
    text = str(value or "").strip()
    if not text:
        return fallback
    hour, minute = text.split(":", 1)
    return time(int(hour), int(minute))


def load_calendar(path: Path) -> tuple[dict[date, CalendarDay], set[int]]:
    rows: dict[date, CalendarDay] = {}
    years: set[int] = set()
    if not path.exists():
        return rows, years
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            session_date = date.fromisoformat(str(raw.get("date") or "").strip())
            status = str(raw.get("status") or "").strip().lower()
            open_et = _parse_time(str(raw.get("open_et") or ""), DEFAULT_OPEN if status == "early_close" else None)
            close_et = _parse_time(str(raw.get("close_et") or ""), DEFAULT_CLOSE if status == "regular" else None)
            rows[session_date] = CalendarDay(
                session_date=session_date,
                status=status,
                open_et=open_et,
                close_et=close_et,
                name=str(raw.get("name") or ""),
                source=str(raw.get("source") or ""),
            )
            years.add(session_date.year)
    return rows, years


def _to_eastern(at: datetime | None = None) -> datetime:
    value = at or datetime.now(UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(EASTERN)


def calendar_status(
    *,
    at: datetime | None = None,
    calendar_csv: Path = Path("config/nasdaq_market_calendar.csv"),
    trade_start_offset_minutes: int = 5,
    trade_end_buffer_minutes: int = 10,
    eod_delay_minutes: int = 30,
) -> dict[str, object]:
    eastern_now = _to_eastern(at)
    session_date = eastern_now.date()
    rows, covered_years = load_calendar(calendar_csv)
    special = rows.get(session_date)

    if session_date.year not in covered_years:
        return {
            "calendar_source_status": "CALENDAR_YEAR_NOT_COVERED",
            "calendar_csv": str(calendar_csv),
            "covered_years": sorted(covered_years),
            "eastern_time": eastern_now.strftime("%Y-%m-%d %H:%M:%S"),
            "session_date": session_date.isoformat(),
            "market_open_flag": 0,
            "trading_window_open_flag": 0,
            "eod_due_flag": 0,
            "reason": "CALENDAR_SOURCE_MISSING_FOR_YEAR",
        }

    if eastern_now.weekday() >= 5:
        reason = "WEEKEND"
        open_dt = close_dt = None
        market_open = False
    elif special and special.status == "closed":
        reason = f"CLOSED:{special.name}"
        open_dt = close_dt = None
        market_open = False
    else:
        reason = "EARLY_CLOSE" if special and special.status == "early_close" else "REGULAR_SESSION"
        open_time = special.open_et if special and special.open_et else DEFAULT_OPEN
        close_time = special.close_et if special and special.close_et else DEFAULT_CLOSE
        open_dt = datetime.combine(session_date, open_time, tzinfo=EASTERN)
        close_dt = datetime.combine(session_date, close_time, tzinfo=EASTERN)
        market_open = open_dt <= eastern_now <= close_dt

    if open_dt is None or close_dt is None:
        trade_start = trade_end = eod_due_at = None
        trading_window_open = False
        eod_due = False
    else:
        trade_start = open_dt + timedelta(minutes=trade_start_offset_minutes)
        trade_end = close_dt - timedelta(minutes=trade_end_buffer_minutes)
        eod_due_at = close_dt + timedelta(minutes=eod_delay_minutes)
        trading_window_open = trade_start <= eastern_now <= trade_end
        eod_due = eastern_now >= eod_due_at

    return {
        "calendar_source_status": "PRIMARY_PASS",
        "calendar_csv": str(calendar_csv),
        "covered_years": sorted(covered_years),
        "eastern_time": eastern_now.strftime("%Y-%m-%d %H:%M:%S"),
        "session_date": session_date.isoformat(),
        "session_status": special.status if special else ("weekend" if eastern_now.weekday() >= 5 else "regular"),
        "session_name": special.name if special else "",
        "source": special.source if special else "regular_weekday_from_nasdaq_trading_hours",
        "market_open_flag": int(market_open),
        "trading_window_open_flag": int(trading_window_open),
        "eod_due_flag": int(eod_due),
        "market_open_et": "" if open_dt is None else open_dt.strftime("%H:%M"),
        "market_close_et": "" if close_dt is None else close_dt.strftime("%H:%M"),
        "trade_start_et": "" if trade_start is None else trade_start.strftime("%H:%M"),
        "trade_end_et": "" if trade_end is None else trade_end.strftime("%H:%M"),
        "eod_due_et": "" if eod_due_at is None else eod_due_at.strftime("%H:%M"),
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calendar-csv", type=Path, default=Path("config/nasdaq_market_calendar.csv"))
    parser.add_argument("--at-iso", type=str, default="")
    parser.add_argument("--trade-start-offset-minutes", type=int, default=5)
    parser.add_argument("--trade-end-buffer-minutes", type=int, default=10)
    parser.add_argument("--eod-delay-minutes", type=int, default=30)
    args = parser.parse_args()
    at = datetime.fromisoformat(args.at_iso) if args.at_iso else None
    print(
        json.dumps(
            calendar_status(
                at=at,
                calendar_csv=args.calendar_csv,
                trade_start_offset_minutes=args.trade_start_offset_minutes,
                trade_end_buffer_minutes=args.trade_end_buffer_minutes,
                eod_delay_minutes=args.eod_delay_minutes,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
