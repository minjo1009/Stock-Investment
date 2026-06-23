import type { ReactNode } from "react";
import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { ChartSourceState } from "../../read-models";
import { spacing } from "../../theme/tokens";

type ChartWithSourceStateProps = ViewProps & {
  chartState: ChartSourceState;
  children?: ReactNode;
  description?: string;
  showTechnicalDetails?: boolean;
  title?: string;
};

function toneForChartStatus(status: ChartSourceState["status"]) {
  if (status === "READY") return "fresh";
  if (status === "STALE") return "stale";
  if (status === "CHART_MISSING" || status === "SOURCE_NOT_ATTACHED") return "missing";
  return "unknown";
}

export function ChartWithSourceState({
  chartState,
  children,
  description,
  showTechnicalDetails = true,
  title = "Chart Source State",
  ...props
}: ChartWithSourceStateProps) {
  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.sm }}>
        <Badge label={chartState.status} tone={toneForChartStatus(chartState.status)} />
        <AppText variant="title">{title}</AppText>
        {description ? <AppText variant="caption">{description}</AppText> : null}
        {children}
        {showTechnicalDetails ? (
          <>
            <AppText variant="caption">{chartState.chartId}</AppText>
            <AppText variant="caption">
              sources: {chartState.sourceIds.length === 0 ? "-" : chartState.sourceIds.join(", ")}
            </AppText>
          </>
        ) : null}
        {chartState.blockerReason ? (
          <AppText variant="caption">{chartState.blockerReason}</AppText>
        ) : null}
      </View>
    </CardContainer>
  );
}
