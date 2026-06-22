"""Core backend acceleration adapters.

Polars and DuckDB are allowed here as acceleration engines only. They may
compute the same artifact/query results faster, but they must not change
selector, sizing, replay, paper-order, live-order, or acceptance semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

import pandas as pd

from src.infra.external_tools import (
    AggregateResult,
    compare_aggregate_results,
    duckdb_strict_gate_aggregate_result,
    pandas_strict_gate_aggregate_result,
    polars_strict_gate_aggregate_result,
    rows_sha256,
)


class BackendAccelerationEngine(StrEnum):
    AUTO = "auto"
    PANDAS = "pandas"
    POLARS = "polars"
    DUCKDB = "duckdb"


class GroupedAggregationOp(StrEnum):
    COUNT_NON_NULL = "count_non_null"
    MEAN = "mean"
    SUM = "sum"


@dataclass(frozen=True)
class GroupedAggregationMeasure:
    source_col: str
    output_col: str
    op: GroupedAggregationOp | Literal["count_non_null", "mean", "sum"]
    scale: float = 1.0

    def normalized_op(self) -> GroupedAggregationOp:
        if isinstance(self.op, GroupedAggregationOp):
            return self.op
        return GroupedAggregationOp(str(self.op))


@dataclass(frozen=True)
class BackendAccelerationDecision:
    requested_engine: BackendAccelerationEngine
    selected_engine: BackendAccelerationEngine
    fallback_used: bool
    dependency_status: str
    parity_checked: bool
    parity_pass: bool
    faster_than_pandas: bool
    pass_does_not_mean: str = (
        "strategy acceptance, deployment readiness, broker truth completion, "
        "live-source readiness, paper-order permission, live-order permission, or real-capital permission"
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_engine": self.requested_engine.value,
            "selected_engine": self.selected_engine.value,
            "fallback_used": int(self.fallback_used),
            "dependency_status": self.dependency_status,
            "parity_checked": int(self.parity_checked),
            "parity_pass": int(self.parity_pass),
            "faster_than_pandas": int(self.faster_than_pandas),
            "pass_does_not_mean": self.pass_does_not_mean,
        }


@dataclass(frozen=True)
class AcceleratedAggregateResult:
    decision: BackendAccelerationDecision
    result: AggregateResult
    pandas_baseline: AggregateResult | None = None

    def to_dict(self) -> dict[str, object]:
        payload = self.decision.to_dict()
        payload.update(self.result.to_dict())
        if self.pandas_baseline is not None:
            payload["pandas_runtime_ms"] = self.pandas_baseline.metrics.runtime_ms
            payload["pandas_checksum"] = self.pandas_baseline.metrics.aggregate_checksum
        return payload


@dataclass(frozen=True)
class GroupedAggregateMetrics:
    engine: BackendAccelerationEngine
    dependency_status: str
    runtime_ms: float
    source_row_count: int
    result_row_count: int
    aggregate_checksum: str
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine.value,
            "dependency_status": self.dependency_status,
            "runtime_ms": self.runtime_ms,
            "source_row_count": self.source_row_count,
            "result_row_count": self.result_row_count,
            "aggregate_checksum": self.aggregate_checksum,
            "error": self.error,
        }


@dataclass(frozen=True)
class GroupedAggregateResult:
    metrics: GroupedAggregateMetrics
    frame: pd.DataFrame

    def to_dict(self) -> dict[str, object]:
        payload = self.metrics.to_dict()
        payload["column_count"] = len(self.frame.columns)
        return payload


@dataclass(frozen=True)
class AcceleratedGroupedAggregateResult:
    decision: BackendAccelerationDecision
    result: GroupedAggregateResult
    pandas_baseline: GroupedAggregateResult | None = None

    def to_dict(self) -> dict[str, object]:
        payload = self.decision.to_dict()
        payload.update(self.result.to_dict())
        if self.pandas_baseline is not None:
            payload["pandas_runtime_ms"] = self.pandas_baseline.metrics.runtime_ms
            payload["pandas_checksum"] = self.pandas_baseline.metrics.aggregate_checksum
        return payload


def _normalize_engine(engine: str | BackendAccelerationEngine) -> BackendAccelerationEngine:
    if isinstance(engine, BackendAccelerationEngine):
        return engine
    try:
        return BackendAccelerationEngine(str(engine).lower())
    except ValueError as exc:
        raise ValueError(f"unsupported backend acceleration engine: {engine}") from exc


def _run_engine(engine: BackendAccelerationEngine, panel: Path, group_cols: list[str]) -> AggregateResult:
    if engine == BackendAccelerationEngine.PANDAS:
        return pandas_strict_gate_aggregate_result(panel, group_cols)
    if engine == BackendAccelerationEngine.POLARS:
        return polars_strict_gate_aggregate_result(panel, group_cols)
    if engine == BackendAccelerationEngine.DUCKDB:
        return duckdb_strict_gate_aggregate_result(panel, group_cols)
    raise ValueError("AUTO must be resolved before running an engine")


def _candidate_order(engine: BackendAccelerationEngine) -> tuple[BackendAccelerationEngine, ...]:
    if engine == BackendAccelerationEngine.AUTO:
        return (
            BackendAccelerationEngine.POLARS,
            BackendAccelerationEngine.DUCKDB,
            BackendAccelerationEngine.PANDAS,
        )
    return (engine, BackendAccelerationEngine.PANDAS) if engine != BackendAccelerationEngine.PANDAS else (engine,)


def _correctness_parity_pass(result: AggregateResult, baseline: AggregateResult) -> tuple[bool, bool]:
    comparison = compare_aggregate_results(result, baseline)
    correctness_pass = (
        comparison.row_count_match_pandas == "1"
        and comparison.join_key_null_match_pandas == "1"
        and comparison.aggregate_checksum_match_pandas == "1"
        and comparison.strict_gate_pass_total_match_pandas == "1"
    )
    return correctness_pass, comparison.faster_than_pandas == "1"


def _require_grouped_columns(frame: pd.DataFrame, keys: list[str], measures: list[GroupedAggregationMeasure]) -> None:
    missing = [col for col in [*keys, *[measure.source_col for measure in measures]] if col not in frame.columns]
    if missing:
        raise KeyError("missing grouped aggregate columns: " + "|".join(dict.fromkeys(missing)))


def _grouped_checksum(frame: pd.DataFrame, fields: list[str]) -> str:
    rows = frame.where(pd.notna(frame), "").to_dict(orient="records")
    return rows_sha256(rows, fields)


def _normalize_grouped_frame(frame: pd.DataFrame, columns: list[str], keys: list[str], sort_keys: bool) -> pd.DataFrame:
    result = frame.loc[:, columns].copy()
    if sort_keys and keys and not result.empty:
        result = result.sort_values(keys, na_position="last").reset_index(drop=True)
    else:
        result = result.reset_index(drop=True)
    return result


def _run_grouped_pandas(
    frame: pd.DataFrame,
    keys: list[str],
    measures: list[GroupedAggregationMeasure],
    *,
    dropna: bool,
    sort_keys: bool,
) -> GroupedAggregateResult:
    import time

    started = time.perf_counter()
    columns = [*keys, *[measure.output_col for measure in measures]]
    if keys:
        agg_spec: dict[str, tuple[str, str]] = {}
        for measure in measures:
            op = measure.normalized_op()
            pandas_op = "count" if op == GroupedAggregationOp.COUNT_NON_NULL else op.value
            agg_spec[measure.output_col] = (measure.source_col, pandas_op)
        result = frame.groupby(keys, dropna=dropna, as_index=False, sort=sort_keys).agg(**agg_spec)
    else:
        payload: dict[str, object] = {}
        for measure in measures:
            series = frame[measure.source_col]
            op = measure.normalized_op()
            if op == GroupedAggregationOp.COUNT_NON_NULL:
                value = series.count()
            elif op == GroupedAggregationOp.MEAN:
                value = series.mean()
            elif op == GroupedAggregationOp.SUM:
                value = series.sum()
            else:  # pragma: no cover - enum exhaustiveness
                raise ValueError(op)
            payload[measure.output_col] = value
        result = pd.DataFrame([payload])
    for measure in measures:
        if measure.scale != 1.0 and measure.output_col in result.columns:
            result[measure.output_col] = result[measure.output_col] * measure.scale
    result = _normalize_grouped_frame(result, columns, keys, sort_keys)
    return GroupedAggregateResult(
        metrics=GroupedAggregateMetrics(
            engine=BackendAccelerationEngine.PANDAS,
            dependency_status="available",
            runtime_ms=round((time.perf_counter() - started) * 1000, 6),
            source_row_count=len(frame),
            result_row_count=len(result),
            aggregate_checksum=_grouped_checksum(result, columns),
        ),
        frame=result,
    )


def _run_grouped_polars(
    frame: pd.DataFrame,
    keys: list[str],
    measures: list[GroupedAggregationMeasure],
    *,
    dropna: bool,
    sort_keys: bool,
) -> GroupedAggregateResult:
    import importlib.util
    import time

    if importlib.util.find_spec("polars") is None:
        return GroupedAggregateResult(
            metrics=GroupedAggregateMetrics(
                engine=BackendAccelerationEngine.POLARS,
                dependency_status="dependency_missing",
                runtime_ms=0.0,
                source_row_count=len(frame),
                result_row_count=0,
                aggregate_checksum="",
            ),
            frame=pd.DataFrame(),
        )

    import polars as pl

    started = time.perf_counter()
    columns = [*keys, *[measure.output_col for measure in measures]]
    pl_frame = pl.from_pandas(frame)
    if dropna and keys:
        for key in keys:
            pl_frame = pl_frame.filter(pl.col(key).is_not_null())
    expressions = []
    for measure in measures:
        op = measure.normalized_op()
        value = pl.col(measure.source_col)
        if op == GroupedAggregationOp.COUNT_NON_NULL:
            expr = value.count()
        elif op == GroupedAggregationOp.MEAN:
            expr = value.cast(pl.Float64, strict=False).mean()
        elif op == GroupedAggregationOp.SUM:
            expr = value.cast(pl.Float64, strict=False).sum()
        else:  # pragma: no cover - enum exhaustiveness
            raise ValueError(op)
        if measure.scale != 1.0:
            expr = expr * measure.scale
        expressions.append(expr.alias(measure.output_col))
    if keys:
        result = pl_frame.group_by(keys).agg(expressions)
    else:
        result = pl_frame.select(expressions)
    pandas_result = result.to_pandas()
    pandas_result = _normalize_grouped_frame(pandas_result, columns, keys, sort_keys)
    return GroupedAggregateResult(
        metrics=GroupedAggregateMetrics(
            engine=BackendAccelerationEngine.POLARS,
            dependency_status="available",
            runtime_ms=round((time.perf_counter() - started) * 1000, 6),
            source_row_count=len(frame),
            result_row_count=len(pandas_result),
            aggregate_checksum=_grouped_checksum(pandas_result, columns),
        ),
        frame=pandas_result,
    )


def _duckdb_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _run_grouped_duckdb(
    frame: pd.DataFrame,
    keys: list[str],
    measures: list[GroupedAggregationMeasure],
    *,
    dropna: bool,
    sort_keys: bool,
) -> GroupedAggregateResult:
    import importlib.util
    import time

    if importlib.util.find_spec("duckdb") is None:
        return GroupedAggregateResult(
            metrics=GroupedAggregateMetrics(
                engine=BackendAccelerationEngine.DUCKDB,
                dependency_status="dependency_missing",
                runtime_ms=0.0,
                source_row_count=len(frame),
                result_row_count=0,
                aggregate_checksum="",
            ),
            frame=pd.DataFrame(),
        )

    import duckdb

    started = time.perf_counter()
    columns = [*keys, *[measure.output_col for measure in measures]]
    con = duckdb.connect(database=":memory:")
    con.register("src", frame)
    select_parts = [_duckdb_ident(key) for key in keys]
    for measure in measures:
        source = _duckdb_ident(measure.source_col)
        output = _duckdb_ident(measure.output_col)
        op = measure.normalized_op()
        if op == GroupedAggregationOp.COUNT_NON_NULL:
            expr = f"COUNT({source})"
        elif op == GroupedAggregationOp.MEAN:
            expr = f"AVG(TRY_CAST({source} AS DOUBLE))"
        elif op == GroupedAggregationOp.SUM:
            expr = f"SUM(TRY_CAST({source} AS DOUBLE))"
        else:  # pragma: no cover - enum exhaustiveness
            raise ValueError(op)
        if measure.scale != 1.0:
            expr = f"({expr}) * {float(measure.scale)}"
        select_parts.append(f"{expr} AS {output}")
    where_sql = ""
    if dropna and keys:
        where_sql = "WHERE " + " AND ".join(f"{_duckdb_ident(key)} IS NOT NULL" for key in keys)
    group_sql = " GROUP BY " + ", ".join(_duckdb_ident(key) for key in keys) if keys else ""
    order_sql = " ORDER BY " + ", ".join(_duckdb_ident(key) for key in keys) if sort_keys and keys else ""
    result = con.execute(f"SELECT {', '.join(select_parts)} FROM src {where_sql}{group_sql}{order_sql}").fetchdf()
    result = _normalize_grouped_frame(result, columns, keys, sort_keys)
    return GroupedAggregateResult(
        metrics=GroupedAggregateMetrics(
            engine=BackendAccelerationEngine.DUCKDB,
            dependency_status="available",
            runtime_ms=round((time.perf_counter() - started) * 1000, 6),
            source_row_count=len(frame),
            result_row_count=len(result),
            aggregate_checksum=_grouped_checksum(result, columns),
        ),
        frame=result,
    )


def _run_grouped_engine(
    engine: BackendAccelerationEngine,
    frame: pd.DataFrame,
    keys: list[str],
    measures: list[GroupedAggregationMeasure],
    *,
    dropna: bool,
    sort_keys: bool,
) -> GroupedAggregateResult:
    if engine == BackendAccelerationEngine.PANDAS:
        return _run_grouped_pandas(frame, keys, measures, dropna=dropna, sort_keys=sort_keys)
    if engine == BackendAccelerationEngine.POLARS:
        return _run_grouped_polars(frame, keys, measures, dropna=dropna, sort_keys=sort_keys)
    if engine == BackendAccelerationEngine.DUCKDB:
        return _run_grouped_duckdb(frame, keys, measures, dropna=dropna, sort_keys=sort_keys)
    raise ValueError("AUTO must be resolved before running an engine")


def _grouped_parity_pass(result: GroupedAggregateResult, baseline: GroupedAggregateResult) -> bool:
    if result.metrics.dependency_status != "available" or baseline.metrics.dependency_status != "available":
        return False
    if result.metrics.result_row_count != baseline.metrics.result_row_count:
        return False
    if result.metrics.aggregate_checksum == baseline.metrics.aggregate_checksum:
        return True
    try:
        pd.testing.assert_frame_equal(
            result.frame.reset_index(drop=True),
            baseline.frame.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-10,
            atol=1e-12,
        )
    except AssertionError:
        return False
    return True


def grouped_numeric_aggregate_accelerated(
    frame: pd.DataFrame,
    keys: list[str],
    measures: list[GroupedAggregationMeasure],
    *,
    engine: str | BackendAccelerationEngine = BackendAccelerationEngine.AUTO,
    verify_with_pandas: bool = True,
    pandas_baseline: GroupedAggregateResult | None = None,
    dropna: bool = True,
    sort_keys: bool = True,
) -> AcceleratedGroupedAggregateResult:
    """Group numeric measures through Polars/DuckDB with pandas parity.

    V1 intentionally supports only count-non-null, mean, and sum. This keeps
    catalog, metrics, and source-panel migrations tied to pandas semantics
    before any accelerated result is accepted.
    """

    _require_grouped_columns(frame, keys, measures)
    requested = _normalize_engine(engine)
    baseline = pandas_baseline if verify_with_pandas and pandas_baseline is not None else None
    if verify_with_pandas and baseline is None:
        baseline = _run_grouped_pandas(frame, keys, measures, dropna=dropna, sort_keys=sort_keys)

    last_result: GroupedAggregateResult | None = None
    for candidate in _candidate_order(requested):
        result = _run_grouped_engine(candidate, frame, keys, measures, dropna=dropna, sort_keys=sort_keys)
        last_result = result
        if result.metrics.dependency_status != "available":
            continue

        parity_checked = bool(verify_with_pandas and candidate != BackendAccelerationEngine.PANDAS)
        parity_pass = True
        faster_than_pandas = False
        if parity_checked:
            parity_pass = baseline is not None and _grouped_parity_pass(result, baseline)
            faster_than_pandas = bool(baseline and result.metrics.runtime_ms < baseline.metrics.runtime_ms)
        if not parity_pass:
            continue

        return AcceleratedGroupedAggregateResult(
            decision=BackendAccelerationDecision(
                requested_engine=requested,
                selected_engine=candidate,
                fallback_used=candidate != requested and requested != BackendAccelerationEngine.AUTO,
                dependency_status=result.metrics.dependency_status,
                parity_checked=parity_checked,
                parity_pass=parity_pass,
                faster_than_pandas=faster_than_pandas,
            ),
            result=result,
            pandas_baseline=baseline,
        )

    if baseline is not None and baseline.metrics.dependency_status == "available":
        return AcceleratedGroupedAggregateResult(
            decision=BackendAccelerationDecision(
                requested_engine=requested,
                selected_engine=BackendAccelerationEngine.PANDAS,
                fallback_used=True,
                dependency_status=baseline.metrics.dependency_status,
                parity_checked=False,
                parity_pass=True,
                faster_than_pandas=False,
            ),
            result=baseline,
            pandas_baseline=baseline,
        )

    assert last_result is not None
    return AcceleratedGroupedAggregateResult(
        decision=BackendAccelerationDecision(
            requested_engine=requested,
            selected_engine=BackendAccelerationEngine.PANDAS,
            fallback_used=True,
            dependency_status=last_result.metrics.dependency_status,
            parity_checked=False,
            parity_pass=False,
            faster_than_pandas=False,
        ),
        result=last_result,
        pandas_baseline=baseline,
    )


def strict_gate_aggregate_accelerated(
    panel: Path,
    group_cols: list[str],
    *,
    engine: str | BackendAccelerationEngine = BackendAccelerationEngine.AUTO,
    verify_with_pandas: bool = True,
    pandas_baseline: AggregateResult | None = None,
) -> AcceleratedAggregateResult:
    """Aggregate strict-gate counts through the core acceleration layer.

    `AUTO` chooses Polars first, then DuckDB, then pandas. If parity checking is
    enabled, non-pandas engines must match pandas row counts, null counts,
    strict-gate totals, and aggregate checksum before they are accepted.
    """

    requested = _normalize_engine(engine)
    baseline = pandas_baseline if verify_with_pandas and pandas_baseline is not None else None
    if verify_with_pandas and baseline is None:
        baseline = pandas_strict_gate_aggregate_result(panel, group_cols)

    last_result: AggregateResult | None = None
    for candidate in _candidate_order(requested):
        result = _run_engine(candidate, panel, group_cols)
        last_result = result
        if result.metrics.dependency_status != "available":
            continue

        parity_checked = bool(verify_with_pandas and candidate != BackendAccelerationEngine.PANDAS)
        parity_pass = True
        faster_than_pandas = False
        if parity_checked:
            if baseline is None or baseline.metrics.dependency_status != "available":
                parity_pass = False
            else:
                parity_pass, faster_than_pandas = _correctness_parity_pass(result, baseline)
        if not parity_pass:
            continue

        return AcceleratedAggregateResult(
            decision=BackendAccelerationDecision(
                requested_engine=requested,
                selected_engine=candidate,
                fallback_used=candidate != requested and requested != BackendAccelerationEngine.AUTO,
                dependency_status=result.metrics.dependency_status,
                parity_checked=parity_checked,
                parity_pass=parity_pass,
                faster_than_pandas=faster_than_pandas,
            ),
            result=result,
            pandas_baseline=baseline,
        )

    if baseline is not None and baseline.metrics.dependency_status == "available":
        return AcceleratedAggregateResult(
            decision=BackendAccelerationDecision(
                requested_engine=requested,
                selected_engine=BackendAccelerationEngine.PANDAS,
                fallback_used=True,
                dependency_status=baseline.metrics.dependency_status,
                parity_checked=False,
                parity_pass=True,
                faster_than_pandas=False,
            ),
            result=baseline,
            pandas_baseline=baseline,
        )

    assert last_result is not None
    return AcceleratedAggregateResult(
        decision=BackendAccelerationDecision(
            requested_engine=requested,
            selected_engine=BackendAccelerationEngine.PANDAS,
            fallback_used=True,
            dependency_status=last_result.metrics.dependency_status,
            parity_checked=False,
            parity_pass=False,
            faster_than_pandas=False,
        ),
        result=last_result,
        pandas_baseline=baseline,
    )
