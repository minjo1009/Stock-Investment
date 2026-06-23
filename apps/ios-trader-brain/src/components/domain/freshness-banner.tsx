import { View } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { MetricCard } from "../generic";
import type { AppShellReadModel } from "../../read-models";
import { spacing } from "../../theme/tokens";

type FreshnessBannerProps = {
  generatedAt: string;
  sourceSummary: AppShellReadModel["sourceSummary"];
  title?: string;
};

export function FreshnessBanner({
  generatedAt,
  sourceSummary,
  title = "Fixture freshness boundary",
}: FreshnessBannerProps) {
  const hasBlockedSource =
    sourceSummary.staleCount > 0 ||
    sourceSummary.missingCount > 0 ||
    sourceSummary.unknownCount > 0 ||
    sourceSummary.strictGateOpenCount === 0;

  return (
    <CardContainer>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <Badge label={hasBlockedSource ? "SOURCE REVIEW REQUIRED" : "SOURCE SNAPSHOT"} tone={hasBlockedSource ? "blocked" : "readOnly"} />
        <Badge label="NOT_AUTHORITY" tone="blocked" />
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText>{title}</AppText>
        <AppText variant="caption">
          Generated fixture: {generatedAt}. Passing display checks does not prove freshness,
          permission, or source authority.
        </AppText>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <MetricCard label="Fresh" value={sourceSummary.freshCount} state="fresh" />
        <MetricCard label="Stale" value={sourceSummary.staleCount} state="stale" />
        <MetricCard label="Missing" value={sourceSummary.missingCount} state="missing" />
        <MetricCard label="Unknown" value={sourceSummary.unknownCount} state="unknown" />
        <MetricCard label="Strict gate open" value={sourceSummary.strictGateOpenCount} state="blocked" />
      </View>
    </CardContainer>
  );
}
