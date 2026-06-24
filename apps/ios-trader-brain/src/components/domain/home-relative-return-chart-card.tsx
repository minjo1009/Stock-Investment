import { StyleSheet, View, type ViewProps } from "react-native";

import { AppText, Badge } from "../foundation";
import type { HomeRelativeReturnChart } from "../../read-models";
import { colors, mobile, spacing } from "../../theme/tokens";
import { ChartWithSourceState } from "./chart-with-source-state";

type HomeRelativeReturnChartCardProps = ViewProps & {
  chart: HomeRelativeReturnChart;
};

const timeframeLabels = ["1M", "3M", "6M", "1Y", "ALL"];

export function HomeRelativeReturnChartCard({
  chart,
  style,
  ...props
}: HomeRelativeReturnChartCardProps) {
  const hasSourceBackedSeries = chart.chartState.status === "READY" && chart.points.length > 0;

  return (
    <ChartWithSourceState
      chartState={chart.chartState}
      description="평가금, 원금, QQQ 기준선이 같은 시간축으로 연결되기 전에는 가짜 선을 그리지 않습니다."
      showTechnicalDetails={false}
      style={[styles.card, style]}
      title="Performance"
      {...props}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <AppText style={styles.cardTitle}>평가금 vs 원금 vs QQQ</AppText>
            <View style={styles.legendRow}>
              <LegendDot color="#2E7D32" label="평가금" />
              <LegendDot color="#8E8E93" label="원금" />
              <LegendDot color="#2563EB" label="QQQ" />
            </View>
          </View>

          <View style={styles.timeframeRow}>
            {timeframeLabels.map((label, index) => (
              <View key={label} style={[styles.timeframeChip, index === 0 ? styles.timeframeChipSelected : null]}>
                <AppText
                  variant="caption"
                  style={index === 0 ? styles.timeframeTextSelected : styles.timeframeText}
                >
                  {label}
                </AppText>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.kpiOverlay}>
          <Badge label="승률 UNKNOWN" tone="unknown" />
          <Badge label="MDD UNKNOWN" tone="missing" />
          <Badge label="QQQ 기준 대기" tone="unknown" />
        </View>

        <View style={styles.chartFrame}>
          <View style={styles.chartGrid}>
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
          </View>
          {hasSourceBackedSeries ? null : (
            <View style={styles.emptyState}>
              <AppText style={styles.emptyTitle}>차트 데이터 연결 대기</AppText>
              <AppText variant="caption" style={styles.emptyBody}>
                권위 있는 포트폴리오 평가금 곡선, 원금 시계열, QQQ 벤치마크가 붙으면
                이 영역에 세 개의 선이 표시됩니다.
              </AppText>
            </View>
          )}
        </View>

        <View style={styles.statusLine}>
          <AppText variant="caption">현재 상태: {chart.sourceState.freshnessStatus}</AppText>
          <AppText variant="caption">차트 포인트: {chart.points.length}</AppText>
        </View>
      </View>
    </ChartWithSourceState>
  );
}

type LegendDotProps = {
  color: string;
  label: string;
};

function LegendDot({ color, label }: LegendDotProps) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.legendDot, { backgroundColor: color }]} />
      <AppText variant="caption">{label}</AppText>
    </View>
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
    gap: spacing.md,
    minHeight: 280,
    padding: spacing.lg,
  },
  content: {
    gap: spacing.md,
  },
  header: {
    gap: spacing.md,
  },
  headerText: {
    gap: spacing.xs,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
    lineHeight: 24,
  },
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  legendItem: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.xs,
  },
  legendDot: {
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  timeframeRow: {
    flexDirection: "row",
    gap: spacing.xs,
  },
  timeframeChip: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    justifyContent: "center",
    minHeight: mobile.touchTarget,
  },
  timeframeChipSelected: {
    backgroundColor: "#E0E0E0",
  },
  timeframeText: {
    color: colors.mutedInk,
    fontWeight: "700",
  },
  timeframeTextSelected: {
    color: colors.ink,
    fontWeight: "800",
  },
  kpiOverlay: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  chartFrame: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 132,
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
    minHeight: 104,
    paddingHorizontal: spacing.sm,
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
