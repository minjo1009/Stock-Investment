from __future__ import annotations

LEGACY_L2_NEWS_BUILDER_QUARANTINED = True


def build_news_event_primitives(*args, **kwargs):
    raise RuntimeError(
        "Legacy L2 news builder is quarantined by TASK-4136. "
        "Use the L2 intake contract and feature-admission gate before any "
        "news or macro row is converted into a trading feature candidate."
    )
