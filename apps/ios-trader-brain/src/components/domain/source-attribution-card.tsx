import { View } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { EvidenceStatusChip, SourceFreshnessBadge } from "../generic";
import type { EvidenceStatus } from "../generic";
import type { SourceState } from "../../read-models";
import { spacing } from "../../theme/tokens";

type SourceAttributionCardProps = {
  authority: string;
  sourceRefs?: string[];
  sourceStates?: SourceState[];
  status?: EvidenceStatus;
  timestamp?: string | null;
  title: string;
};

export function SourceAttributionCard({
  authority,
  sourceRefs = [],
  sourceStates = [],
  status = "UNKNOWN",
  timestamp,
  title,
}: SourceAttributionCardProps) {
  const refs = [
    ...sourceRefs,
    ...sourceStates.flatMap((sourceState) => sourceState.provenanceRefs),
  ];

  return (
    <CardContainer>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <EvidenceStatusChip label="Evidence status" status={status} />
        <Badge label="read-only attribution" tone="readOnly" />
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText>{title}</AppText>
        <AppText variant="caption">Authority: {authority}</AppText>
        <AppText variant="caption">Timestamp: {timestamp ?? "UNAVAILABLE"}</AppText>
      </View>
      {sourceStates.length > 0 ? (
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {sourceStates.map((sourceState) => (
            <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
          ))}
        </View>
      ) : null}
      {refs.length > 0 ? (
        <View style={{ gap: spacing.xs }}>
          {refs.slice(0, 5).map((sourceRef) => (
            <AppText key={sourceRef} ellipsizeMode="middle" numberOfLines={1} variant="caption">
              {sourceRef}
            </AppText>
          ))}
        </View>
      ) : (
        <AppText variant="caption">SOURCE_NOT_ATTACHED</AppText>
      )}
    </CardContainer>
  );
}
