import { useState } from "react";
import { Pressable, StyleSheet, View, type ViewProps } from "react-native";

import { AppText, Badge } from "../foundation";
import type { HomeRelativeReturnChart } from "../../read-models";
import { colors, mobile, spacing } from "../../theme/tokens";
import { ChartWithSourceState } from "./chart-with-source-state";

type HomeRelativeReturnChartCardProps = ViewProps & {
  chart: HomeRelativeReturnChart;
};

const timeframeOptions = [
  { label: "1D", description: "하루" },
  { label: "1M", description: "1개월" },
  { label: "3M", description: "3개월" },
  { label: "6M", description: "6개월" },
  { label: "1Y", description: "1년" },
  { label: "ALL", description: "전체" },
] as const;

type TimeframeLabel = (typeof timeframeOptions)[number]["label"];

export function HomeRelativeReturnChartCard({
  chart,
  style,
  ...props
}: HomeRelativeReturnChartCardProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeLabel>("1M");
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
            {timeframeOptions.map((option) => {
              const isSelected = selectedTimeframe === option.label;

              return (
                <Pressable
                  accessibilityLabel={`성과 기간 ${option.description}`}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                  key={option.label}
                  onPress={() => setSelectedTimeframe(option.label)}
                  style={({ pressed }) => [
                    styles.timeframeChip,
                    isSelected ? styles.timeframeChipSelected : null,
                    pressed ? styles.timeframeChipPressed : null,
                  ]}
                >
                  <AppText
                    variant="caption"
                    style={isSelected ? styles.timeframeTextSelected : styles.timeframeText}
                  >
                    {option.label}
                  </AppText>
                </Pressable>
              );
            })}
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
                선택 기간은 바뀌지만, 권위 있는 평가금 곡선, 원금 시계열, QQQ 벤치마크가 붙기 전에는
                선을 표시하지 않습니다.
              </AppText>
            </View>
          )}
        </View>

        <View style={styles.statusLine}>
          <AppText variant="caption">선택 기간: {selectedTimeframe}</AppText>
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
  timeframeChipPressed: {
    opacity: 0.72,
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
