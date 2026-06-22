import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { BlockerList, SourceFreshnessBadge } from "../generic";
import { ChartWithSourceState } from "./chart-with-source-state";
import type { BlockerState, ChartSourceState, SourceState } from "../../read-models";
import { spacing } from "../../theme/tokens";

type RiskGateProps = ViewProps & {
  blockers: BlockerState[];
  sourceStates: SourceState[];
  chartStates: ChartSourceState[];
};

export function RiskGate({
  blockers,
  chartStates,
  sourceStates,
  ...props
}: RiskGateProps) {
  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.sm }}>
        <Badge label={blockers.length > 0 ? "Blocked" : "Unknown"} tone={blockers.length > 0 ? "blocked" : "unknown"} />
        <AppText variant="title">Risk</AppText>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {sourceStates.map((sourceState) => (
          <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} compact />
        ))}
      </View>
      <BlockerList blockers={blockers} />
      <View style={{ gap: spacing.sm }}>
        {chartStates.map((chartState) => (
          <ChartWithSourceState key={chartState.chartId} chartState={chartState} />
        ))}
      </View>
    </CardContainer>
  );
}
