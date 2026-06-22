"""Read-only adapters between runtime catalog payloads and brain contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from brain.contracts import FrontendReadModel


PAPER_OPS_RUNTIME_CONTRACT_VERSION = "paper-ops-runtime-v1"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def build_frontend_read_model_from_paper_ops_catalog(
    payload: Mapping[str, Any],
    *,
    read_model_id: str,
    runtime_decision_id: str,
    provenance_path: str,
) -> FrontendReadModel:
    """Build an L7 read model from an already-built paper ops runtime catalog.

    This function intentionally does not call the catalog builder, write files,
    submit orders, run replay, or mutate broker/runtime state.
    """

    if payload.get("contract_version") != PAPER_OPS_RUNTIME_CONTRACT_VERSION:
        raise ValueError("unsupported paper ops runtime catalog version")

    rules = _as_mapping(payload.get("rules"))
    if rules.get("ui_reads_catalog_only") is not True:
        raise ValueError("catalog must enforce ui_reads_catalog_only")
    if rules.get("deployment_claim_allowed") is not False:
        raise ValueError("catalog must not allow deployment claims")
    if rules.get("missing_source_approximation_allowed") is not False:
        raise ValueError("catalog must not allow missing source approximation")

    data_quality = _as_mapping(payload.get("data_quality"))
    quality_status = str(data_quality.get("data_quality_status") or "UNKNOWN")
    quality_flags = _as_tuple(data_quality.get("data_quality_flags"))
    policy_compare = _as_mapping(payload.get("policy_compare_audit"))
    strict_asof_status = str(policy_compare.get("strict_asof_status") or "")

    blocker_flags: list[str] = list(quality_flags)
    if strict_asof_status and strict_asof_status != "PASS":
        blocker_flags.append(f"STRICT_ASOF_{strict_asof_status}")

    return FrontendReadModel(
        read_model_id=read_model_id,
        runtime_decision_id=runtime_decision_id,
        source_tier="paper_shadow_runtime_catalog",
        display_status=quality_status,
        provenance_paths=(provenance_path,),
        blocker_flags=tuple(blocker_flags),
        read_only=True,
    )
