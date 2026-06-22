-- T601-0 Candidate Funnel Events Schema
-- Design contract only. This file defines the required event table shape
-- before implementation begins.

CREATE TABLE IF NOT EXISTS candidate_funnel_events (
    candidate_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    generated_time TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (
        stage IN (
            'GENERATED',
            'RANKED',
            'ELIGIBLE',
            'ORDERED',
            'FILLED',
            'CLOSED'
        )
    ),
    rank_score REAL,
    eligibility TEXT,
    cooldown_reason TEXT,
    skip_reason TEXT,
    order_id TEXT,
    fill_id TEXT,
    source_snapshot_id TEXT,
    decision_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (candidate_id, stage, created_at)
);

CREATE INDEX IF NOT EXISTS idx_candidate_funnel_events_symbol_time
    ON candidate_funnel_events (symbol, generated_time);

CREATE INDEX IF NOT EXISTS idx_candidate_funnel_events_order_fill
    ON candidate_funnel_events (order_id, fill_id);

CREATE INDEX IF NOT EXISTS idx_candidate_funnel_events_decision_snapshot
    ON candidate_funnel_events (decision_id, source_snapshot_id);
