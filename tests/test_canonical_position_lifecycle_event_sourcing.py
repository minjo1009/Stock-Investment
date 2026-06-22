from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.canonical_position_lifecycle_event_sourcing import (
    append_canonical_position_event,
    build_canonical_lifecycle_id,
    list_canonical_position_events,
    start_canonical_position_lifecycle,
)
from state.store import get_continuation_lifecycle, initialize_store


class TestCanonicalPositionLifecycleEventSourcing(unittest.TestCase):
    def test_entry_creates_canonical_lifecycle_and_records_entry_event(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            initialize_store(db_path)

            start = start_canonical_position_lifecycle(
                db_path,
                lifecycle_id="LIFECYCLE|AMD|2026-05-08|ORD-1",
                symbol="AMD",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-1",
                entry_fill_id="FILL-1",
                quantity=10,
                price=164.25,
            )

            lifecycle = get_continuation_lifecycle(db_path, start.lifecycle_id)
            events = list_canonical_position_events(db_path, lifecycle_id=start.lifecycle_id)
            self.assertIsNotNone(lifecycle)
            self.assertEqual(lifecycle["identity_origin"], "canonical_entry_event")
            self.assertEqual(lifecycle["identity_confidence"], 1.0)
            self.assertEqual([event["canonical_event_type"] for event in events], ["ENTRY"])
            self.assertEqual(events[0]["event_type"], "ENTRY")
            self.assertEqual(events[0]["event_source"], "SOURCE_CAPTURED")
            self.assertEqual(events[0]["lifecycle_id"], start.lifecycle_id)
            self.assertEqual(events[0]["price"], 164.25)

    def test_add_scale_reduce_exit_are_stored_under_the_same_lifecycle_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            start = start_canonical_position_lifecycle(
                db_path,
                lifecycle_id="LIFECYCLE|NVDA|2026-05-08|ORD-10",
                symbol="NVDA",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-10",
                quantity=5,
                price=910.0,
                size_multiplier=0.5,
            )

            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="ADD",
                event_timestamp="2026-05-08T13:38:00Z",
                order_id="ORD-11",
                quantity=2,
                price=914.0,
                size_multiplier=0.7,
            )
            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="SCALE",
                event_timestamp="2026-05-08T13:52:00Z",
                order_id="ORD-12",
                quantity=2,
                price=921.0,
                size_multiplier=1.0,
            )
            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="REDUCE",
                event_timestamp="2026-05-08T14:20:00Z",
                order_id="ORD-13",
                quantity=-3,
                price=930.0,
                size_multiplier=0.6,
            )
            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="EXIT",
                event_timestamp="2026-05-08T15:00:00Z",
                order_id="ORD-14",
                quantity=-6,
                price=935.0,
                size_multiplier=0.0,
            )

            events = list_canonical_position_events(db_path, lifecycle_id=start.lifecycle_id)
            self.assertEqual(
                [event["canonical_event_type"] for event in events],
                ["ENTRY", "ADD", "SCALE", "REDUCE", "EXIT"],
            )
            self.assertEqual({event["lifecycle_id"] for event in events}, {start.lifecycle_id})
            self.assertEqual([int(event["add_depth"]) for event in events], [0, 1, 1, 1, 1])
            self.assertEqual([int(event["scale_depth"]) for event in events], [0, 0, 1, 1, 1])
            closed = get_continuation_lifecycle(db_path, start.lifecycle_id)
            self.assertEqual(closed["ended_at"], "2026-05-08T15:00:00Z")

    def test_post_entry_events_require_explicit_existing_lifecycle_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            initialize_store(db_path)

            with self.assertRaisesRegex(ValueError, "lifecycle_id is required"):
                append_canonical_position_event(
                    db_path,
                    lifecycle_id="",
                    event_type="ADD",
                    event_timestamp="2026-05-08T13:38:00Z",
                )
            with self.assertRaisesRegex(ValueError, "unknown canonical lifecycle_id"):
                append_canonical_position_event(
                    db_path,
                    lifecycle_id="LIFECYCLE|AMD|MISSING",
                    event_type="ADD",
                    event_timestamp="2026-05-08T13:38:00Z",
                )

    def test_canonical_layer_rejects_date_only_timestamps_and_out_of_order_events(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            with self.assertRaisesRegex(ValueError, "intraday timestamp precision"):
                start_canonical_position_lifecycle(
                    db_path,
                    lifecycle_id="LIFECYCLE|AMD|BAD-DATE",
                    symbol="AMD",
                    entry_timestamp="2026-05-08",
                )

            start = start_canonical_position_lifecycle(
                db_path,
                lifecycle_id="LIFECYCLE|AMD|2026-05-08|ORD-20",
                symbol="AMD",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-20",
            )
            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="ADD",
                event_timestamp="2026-05-08T13:38:00Z",
            )
            with self.assertRaisesRegex(ValueError, "timestamp order"):
                append_canonical_position_event(
                    db_path,
                    lifecycle_id=start.lifecycle_id,
                    event_type="SCALE",
                    event_timestamp="2026-05-08T13:35:00Z",
                )

    def test_closed_lifecycle_cannot_receive_more_position_events(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "trading.db")
            start = start_canonical_position_lifecycle(
                db_path,
                lifecycle_id="LIFECYCLE|MSFT|2026-05-08|ORD-30",
                symbol="MSFT",
                entry_timestamp="2026-05-08T13:31:00Z",
                entry_order_id="ORD-30",
            )
            append_canonical_position_event(
                db_path,
                lifecycle_id=start.lifecycle_id,
                event_type="EXIT",
                event_timestamp="2026-05-08T13:45:00Z",
            )
            with self.assertRaisesRegex(ValueError, "already closed"):
                append_canonical_position_event(
                    db_path,
                    lifecycle_id=start.lifecycle_id,
                    event_type="ADD",
                    event_timestamp="2026-05-08T13:46:00Z",
                )

    def test_generated_lifecycle_id_is_entry_time_identity_not_symbol_session_recovery(self) -> None:
        lifecycle_id = build_canonical_lifecycle_id(
            symbol="AMD",
            entry_timestamp="2026-05-08T13:31:00Z",
            entry_order_id="ORD-100",
        )
        self.assertEqual(lifecycle_id, "LIFECYCLE|AMD|2026-05-08|ORD-100")


if __name__ == "__main__":
    unittest.main()
