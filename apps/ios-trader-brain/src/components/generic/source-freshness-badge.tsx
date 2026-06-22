import { Badge, type BadgeTone } from "../foundation";
import type { FreshnessStatus, SourceState } from "../../read-models/common";

type SourceFreshnessBadgeProps = {
  sourceState: SourceState;
  compact?: boolean;
};

const freshnessTone: Record<FreshnessStatus, BadgeTone> = {
  FRESH: "fresh",
  STALE: "stale",
  MISSING: "missing",
  UNKNOWN: "unknown",
  NOT_APPLICABLE: "neutral",
};

export function SourceFreshnessBadge({
  compact = false,
  sourceState,
}: SourceFreshnessBadgeProps) {
  const label = compact
    ? sourceState.freshnessStatus
    : `${sourceState.sourceLabel}: ${sourceState.freshnessStatus}`;

  return <Badge label={label} tone={freshnessTone[sourceState.freshnessStatus]} />;
}
