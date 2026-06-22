import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { EvidenceItem } from "../../read-models";
import { spacing } from "../../theme/tokens";

type EvidenceListProps = ViewProps & {
  evidence: EvidenceItem[];
};

function toneForFreshness(status: EvidenceItem["freshnessStatus"]) {
  if (status === "FRESH") return "fresh";
  if (status === "STALE") return "stale";
  if (status === "MISSING") return "missing";
  if (status === "UNKNOWN") return "unknown";
  return "neutral";
}

export function EvidenceList({ evidence, ...props }: EvidenceListProps) {
  if (evidence.length === 0) {
    return (
      <CardContainer {...props}>
        <Badge label="Missing" tone="missing" />
        <AppText>No evidence supplied by the read model.</AppText>
      </CardContainer>
    );
  }

  return (
    <View {...props} style={{ gap: spacing.sm }}>
      {evidence.map((item) => (
        <CardContainer key={item.evidenceId}>
          <Badge label={item.freshnessStatus} tone={toneForFreshness(item.freshnessStatus)} />
          <AppText>{item.label}</AppText>
          <AppText variant="caption">
            {item.value === null ? "-" : String(item.value)}
            {item.unit ? ` ${item.unit}` : ""}
          </AppText>
          <AppText variant="caption">source: {item.sourceId}</AppText>
          {item.provenanceRefs.map((ref) => (
            <AppText key={ref} variant="caption">
              {ref}
            </AppText>
          ))}
        </CardContainer>
      ))}
    </View>
  );
}
