import { StyleSheet, View, type ViewProps } from "react-native";

import { AppText, Badge } from "../foundation";
import type { ChartResolution, HomeRelativeReturnChart } from "../../read-models";
import { colors, mobile, spacing } from "../../theme/tokens";
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
  style,
  ...props
}: HomeRelativeReturnChartCardProps) {
  const hasSourceBackedSeries = chart.chartState.status === "READY" && chart.points.length > 0;

  return (
    <ChartWithSourceState
      chartState={chart.chartState}
      description="포트폴리오 수익률, QQQ 벤치마크, MDD가 같은 시간축으로 연결되기 전에는 가짜 선을 그리지 않습니다."
      showTechnicalDetails={false}
      style={[styles.card, style]}
      title="QQQ 대비 수익 / MDD"
      {...props}
    >
      <View style={styles.content}>
        <View style={styles.legendRow}>
          <Badge label="포트폴리오" tone={hasSourceBackedSeries ? "fresh" : "unknown"} />
          <Badge label="QQQ 기준" tone={hasSourceBackedSeries ? "fresh" : "unknown"} />
          <Badge label="MDD" tone={hasSourceBackedSeries ? "fresh" : "missing"} />
        </View>

        <View style={styles.resolutionRow}>
          {chart.allowedResolutions.map((resolution) => {
            const selected = resolution === chart.selectedResolution;
            return (
              <View
                key={resolution}
                style={[styles.resolutionChip, selected ? styles.resolutionChipSelected : null]}
              >
                <AppText
                  variant="caption"
                  style={selected ? styles.resolutionChipTextSelected : styles.resolutionChipText}
                >
                  {resolutionLabels[resolution]}
                </AppText>
              </View>
            );
          })}
        </View>

        <View style={styles.chartFrame}>
          <View style={styles.chartGrid}>
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
          </View>
          <View style={styles.emptyState}>
            <AppText style={styles.emptyTitle}>차트 데이터 연결 대기</AppText>
            <AppText variant="caption" style={styles.emptyBody}>
              권위 있는 포트폴리오 수익 곡선과 QQQ 벤치마크 시계열이 붙으면 이 영역에
              수익률과 MDD가 함께 표시됩니다.
            </AppText>
          </View>
        </View>

        <View style={styles.statusLine}>
          <AppText variant="caption">
            현재 상태: {chart.sourceState.freshnessStatus}
          </AppText>
          <AppText variant="caption">차트 포인트: {chart.points.length}</AppText>
        </View>
      </View>
    </ChartWithSourceState>
  );
}

const elevatedCard = {
  shadowColor: "#111827",
  shadowOffset: { height: 8, width: 0 },
  shadowOpacity: 0.06,
  shadowRadius: 16,
  elevation: 2,
};

const styles = StyleSheet.create({
  card: {
    ...elevatedCard,
  },
  content: {
    gap: spacing.md,
  },
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  resolutionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  resolutionChip: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: mobile.touchTarget,
    minWidth: 52,
    paddingHorizontal: spacing.sm,
  },
  resolutionChipSelected: {
    backgroundColor: colors.ink,
    borderColor: colors.ink,
  },
  resolutionChipText: {
    color: colors.mutedInk,
    fontWeight: "700",
  },
  resolutionChipTextSelected: {
    color: colors.surface,
    fontWeight: "700",
  },
  chartFrame: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 184,
    overflow: "hidden",
    padding: spacing.md,
  },
  chartGrid: {
    bottom: 0,
    justifyContent: "space-evenly",
    left: 0,
    paddingHorizontal: spacing.md,
    position: "absolute",
    right: 0,
    top: 0,
  },
  gridLine: {
    backgroundColor: "#DDE3EA",
    height: 1,
    opacity: 0.9,
  },
  emptyState: {
    alignItems: "center",
    flex: 1,
    gap: spacing.sm,
    justifyContent: "center",
    minHeight: 156,
    paddingHorizontal: spacing.md,
  },
  emptyTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
    textAlign: "center",
  },
  emptyBody: {
    maxWidth: 320,
    textAlign: "center",
  },
  statusLine: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between",
  },
});
