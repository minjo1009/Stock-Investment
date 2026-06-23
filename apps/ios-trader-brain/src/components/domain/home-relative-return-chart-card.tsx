import { View, type ViewProps } from "react-native";

import { AppText, Badge } from "../foundation";
import type { ChartResolution, HomeRelativeReturnChart } from "../../read-models";
import { colors, spacing } from "../../theme/tokens";
import { ChartWithSourceState } from "./chart-with-source-state";

type HomeRelativeReturnChartCardProps = ViewProps & {
  chart: HomeRelativeReturnChart;
};

const resolutionLabels: Record<ChartResolution, string> = {
  "1D": "Daily",
  "1H": "1H",
  "30M": "30m",
  "15M": "15m",
  "5M": "5m",
};

export function HomeRelativeReturnChartCard({
  chart,
  ...props
}: HomeRelativeReturnChartCardProps) {
  const hasSourceBackedSeries = chart.chartState.status === "READY" && chart.points.length > 0;

  return (
    <ChartWithSourceState
      chartState={chart.chartState}
      description="소스 연결 전에는 가짜 선을 그리지 않습니다."
      showTechnicalDetails={false}
      title="QQQ 대비 수익 / MDD"
      {...props}
    >
      <View style={{ gap: spacing.md }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label={chart.title} tone="readOnly" />
          <Badge label={`${chart.benchmarkSymbol} 기준`} tone="unknown" />
          <Badge label="read-only" tone="readOnly" />
        </View>

        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.xs }}>
          {chart.allowedResolutions.map((resolution) => {
            const selected = resolution === chart.selectedResolution;
            return (
              <View
                key={resolution}
                style={{
                  backgroundColor: selected ? colors.ink : colors.surfaceMuted,
                  borderRadius: 8,
                  minHeight: 28,
                  paddingHorizontal: spacing.sm,
                  paddingVertical: spacing.xs,
                }}
              >
                <AppText
                  variant="caption"
                  style={{ color: selected ? colors.surface : colors.mutedInk }}
                >
                  {resolutionLabels[resolution]}
                </AppText>
              </View>
            );
          })}
        </View>

        <View
          style={{
            backgroundColor: colors.surfaceMuted,
            borderColor: colors.border,
            borderRadius: 8,
            borderWidth: 1,
            minHeight: 144,
            padding: spacing.md,
            gap: spacing.sm,
          }}
        >
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            <Badge label="Portfolio" tone={hasSourceBackedSeries ? "fresh" : "unknown"} />
            <Badge label="QQQ" tone={hasSourceBackedSeries ? "fresh" : "unknown"} />
            <Badge label="MDD" tone={hasSourceBackedSeries ? "fresh" : "missing"} />
          </View>
          <AppText variant="title">차트 데이터 연결 대기</AppText>
          <AppText variant="caption">
            포트폴리오, QQQ, MDD 시계열이 연결되면 차트로 표시됩니다.
          </AppText>
        </View>

        <AppText variant="caption">
          현재 상태: {chart.sourceState.freshnessStatus} / 엄격 게이트 닫힘
        </AppText>
      </View>
    </ChartWithSourceState>
  );
}
