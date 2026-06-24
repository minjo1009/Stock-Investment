import { useMemo, useState } from "react";
import {
  Pressable,
  StyleSheet,
  View,
  type GestureResponderEvent,
  type LayoutChangeEvent,
  type ViewProps,
} from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { BacktestSnapshotReadModel } from "../../read-models/backtestSnapshotFixture";
import type { HomeRelativeReturnChart } from "../../read-models";
import { colors, mobile, spacing } from "../../theme/tokens";

type HomeRelativeReturnChartCardProps = ViewProps & {
  chart: HomeRelativeReturnChart;
  backtestSnapshot?: BacktestSnapshotReadModel;
};

const rangeOptions = [
  { label: "최근 5", pointCount: 5 },
  { label: "1년", pointCount: 12 },
  { label: "3년", pointCount: 36 },
  { label: "전체", pointCount: null },
] as const;

type RangeLabel = (typeof rangeOptions)[number]["label"];

export function HomeRelativeReturnChartCard({
  backtestSnapshot,
  chart,
  style,
  ...props
}: HomeRelativeReturnChartCardProps) {
  const [selectedRange, setSelectedRange] = useState<RangeLabel>("1년");
  const [selectedPointIndex, setSelectedPointIndex] = useState<number | null>(null);
  const [plotSize, setPlotSize] = useState({ height: 156, width: 300 });
  const selectedRangeConfig = rangeOptions.find((option) => option.label === selectedRange) ?? rangeOptions[1];
  const chartModel = useMemo(
    () => buildHomeBacktestChart(backtestSnapshot, selectedRangeConfig.pointCount),
    [backtestSnapshot, selectedRangeConfig.pointCount]
  );
  const geometry = useMemo(() => buildChartGeometry(chartModel.points, plotSize, chartModel.qqqReturnPct), [
    chartModel.points,
    chartModel.qqqReturnPct,
    plotSize,
  ]);
  const selectedPoint =
    selectedPointIndex !== null && chartModel.points.length > 0
      ? chartModel.points[Math.min(chartModel.points.length - 1, Math.max(0, selectedPointIndex))]
      : chartModel.points[chartModel.points.length - 1] ?? null;
  const selectedGeometry =
    selectedPointIndex !== null && geometry.points.length > 0
      ? geometry.points[Math.min(geometry.points.length - 1, Math.max(0, selectedPointIndex))]
      : geometry.points[geometry.points.length - 1] ?? null;
  const hasBacktestSeries = chartModel.points.length > 0;
  const sourceStatusText =
    backtestSnapshot?.chartSource.status === "READY"
      ? "백테스트 곡선 연결"
      : chart.chartState.status === "READY"
        ? "홈 차트 연결"
        : "차트 출처 대기";

  function updatePlotSize(event: LayoutChangeEvent) {
    const { height, width } = event.nativeEvent.layout;
    setPlotSize({
      height: Math.max(120, Math.round(height)),
      width: Math.max(220, Math.round(width)),
    });
  }

  function selectPoint(event: GestureResponderEvent) {
    if (chartModel.points.length === 0) {
      setSelectedPointIndex(null);
      return;
    }

    const relativeX = Math.max(0, Math.min(plotSize.width, event.nativeEvent.locationX));
    const nextIndex =
      chartModel.points.length === 1
        ? 0
        : Math.round((relativeX / Math.max(1, plotSize.width - 54)) * (chartModel.points.length - 1));
    setSelectedPointIndex(Math.max(0, Math.min(chartModel.points.length - 1, nextIndex)));
  }

  return (
    <CardContainer style={[styles.card, style]} {...props}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <AppText style={styles.sectionTitle}>수익현황</AppText>
            <AppText style={styles.cardTitle}>백테스트 평가금 vs 원금 vs QQQ</AppText>
            <View style={styles.legendRow}>
              <LegendDot color="#34C759" label="백테스트" />
              <LegendDot color="#9CA3AF" label="원금" />
              <LegendDot color="#60A5FA" label="QQQ 최종 기준" />
            </View>
          </View>

          <View style={styles.rangeRow}>
            {rangeOptions.map((option) => {
              const isSelected = selectedRange === option.label;

              return (
                <Pressable
                  accessibilityLabel={`성과 기간 ${option.label}`}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                  key={option.label}
                  onPress={() => {
                    setSelectedRange(option.label);
                    setSelectedPointIndex(null);
                  }}
                  style={({ pressed }) => [
                    styles.rangeChip,
                    isSelected ? styles.rangeChipSelected : null,
                    pressed ? styles.rangeChipPressed : null,
                  ]}
                >
                  <AppText
                    variant="caption"
                    style={isSelected ? styles.rangeTextSelected : styles.rangeText}
                  >
                    {option.label}
                  </AppText>
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={styles.kpiOverlay}>
          <Badge label={`수익률 ${displaySignedPercent(chartModel.latestReturnPct)}`} tone="readOnly" />
          <Badge label={`MDD ${displaySignedPercent(chartModel.visibleMddPct)}`} tone="blocked" />
          <Badge label={`QQQ ${displaySignedPercent(chartModel.qqqReturnPct)}`} tone="readOnly" />
        </View>

        <Pressable
          accessibilityLabel="홈 백테스트 성과 차트"
          accessibilityRole="button"
          onLayout={updatePlotSize}
          onPress={selectPoint}
          onPressIn={selectPoint}
          style={styles.chartFrame}
        >
          <View style={styles.chartGrid}>
            {geometry.guideLines.map((line) => (
              <View key={`guide-${line.label}`} style={[styles.chartGuideLine, { top: line.y }]}>
                <AppText style={styles.chartGuideText}>{line.label}</AppText>
              </View>
            ))}
          </View>

          {hasBacktestSeries ? (
            <>
              <View style={[styles.principalLine, { top: geometry.principalY }]} />
              <View style={[styles.qqqLine, { top: geometry.qqqY }]} />
              {geometry.points.map((point) => (
                <View
                  key={`drawdown-${point.key}`}
                  style={[
                    styles.drawdownBar,
                    {
                      height: point.drawdownHeight,
                      left: point.x,
                    },
                  ]}
                />
              ))}
              {geometry.segments.map((segment) => (
                <View
                  key={segment.key}
                  style={[
                    styles.chartLineSegment,
                    {
                      left: segment.left,
                      top: segment.top,
                      transform: [{ rotateZ: `${segment.angle}deg` }],
                      width: segment.width,
                    },
                  ]}
                />
              ))}
              {selectedGeometry ? (
                <>
                  <View style={[styles.chartCrosshair, { left: selectedGeometry.x }]} />
                  <View style={[styles.chartPointMarker, { left: selectedGeometry.x - 5, top: selectedGeometry.y - 5 }]} />
                  <View
                    style={[
                      styles.selectedBubble,
                      {
                        left: Math.min(Math.max(0, selectedGeometry.x - 54), Math.max(0, plotSize.width - 128)),
                        top: Math.max(4, selectedGeometry.y - 34),
                      },
                    ]}
                  >
                    <AppText style={styles.selectedBubbleText}>
                      {formatChartDate(selectedPoint?.timestamp)} · {displaySignedPercent(selectedPoint?.portfolioReturnPct ?? null)}
                    </AppText>
                  </View>
                </>
              ) : null}
            </>
          ) : (
            <View style={styles.emptyState}>
              <AppText style={styles.emptyTitle}>차트 연결 대기</AppText>
              <AppText variant="caption" style={styles.emptyBody}>
                권위 있는 평가금, 원금, QQQ 벤치마크가 붙기 전에는 임의 곡선을 만들지 않습니다.
              </AppText>
            </View>
          )}
        </Pressable>

        <View style={styles.statusLine}>
          <AppText variant="caption">선택 기간: {selectedRange}</AppText>
          <AppText variant="caption">데이터 상태: {sourceStatusText}</AppText>
        </View>
        <AppText variant="caption" style={styles.note}>
          QQQ는 현재 점별 곡선이 아니라 최종 벤치마크 값 기준선입니다. 실계좌 성과나 거래 권한을 의미하지 않습니다.
        </AppText>
      </View>
    </CardContainer>
  );
}

type LegendDotProps = {
  color: string;
  label: string;
};

type HomeChartPoint = {
  drawdownPct: number;
  equity: number;
  key: string;
  portfolioReturnPct: number;
  timestamp: string;
};

function LegendDot({ color, label }: LegendDotProps) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.legendDot, { backgroundColor: color }]} />
      <AppText variant="caption">{label}</AppText>
    </View>
  );
}

function buildHomeBacktestChart(snapshot: BacktestSnapshotReadModel | undefined, pointCount: number | null) {
  if (!snapshot || snapshot.equityCurve.length === 0) {
    return {
      latestReturnPct: null,
      points: [] as HomeChartPoint[],
      qqqReturnPct: null,
      visibleMddPct: null,
    };
  }

  const visiblePoints = pointCount === null ? snapshot.equityCurve : snapshot.equityCurve.slice(-pointCount);
  const latest = visiblePoints[visiblePoints.length - 1] ?? null;
  const visibleMddPct = visiblePoints.reduce(
    (minDrawdown, point) => Math.min(minDrawdown, point.drawdownPct),
    0
  );

  return {
    latestReturnPct: latest?.portfolioReturnPct ?? null,
    points: visiblePoints.map((point, index) => ({
      drawdownPct: point.drawdownPct,
      equity: point.equity,
      key: `${point.timestamp}-${index}`,
      portfolioReturnPct: point.portfolioReturnPct,
      timestamp: point.timestamp,
    })),
    qqqReturnPct: (snapshot.metrics.qqqBenchmarkFinal / snapshot.metrics.initialCapital - 1) * 100,
    visibleMddPct,
  };
}

function buildChartGeometry(points: HomeChartPoint[], chartSize: { height: number; width: number }, qqqReturnPct: number | null) {
  const rightAxisWidth = 54;
  const width = Math.max(120, chartSize.width - rightAxisWidth);
  const height = Math.max(104, chartSize.height - 18);
  const verticalPadding = 14;
  const referenceValues = [0, qqqReturnPct ?? 0];
  const returnValues = [...points.map((point) => point.portfolioReturnPct), ...referenceValues];
  const minValue = Math.min(...returnValues);
  const maxValue = Math.max(...returnValues);
  const valueRange = Math.max(1, maxValue - minValue);
  const yForValue = (value: number) =>
    verticalPadding + (height - verticalPadding * 2) - ((value - minValue) / valueRange) * (height - verticalPadding * 2);
  const xStep = points.length > 1 ? width / (points.length - 1) : width;
  const normalizedPoints = points.map((point, index) => ({
    drawdownHeight: Math.min(height * 0.28, Math.abs(point.drawdownPct) * 1.6),
    key: point.key,
    x: index * xStep,
    y: yForValue(point.portfolioReturnPct),
  }));
  const segmentThickness = 3;
  const segments = normalizedPoints.slice(1).map((point, index) => {
    const previous = normalizedPoints[index];
    const dx = point.x - previous.x;
    const dy = point.y - previous.y;
    const width = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI);
    const midpointX = (previous.x + point.x) / 2;
    const midpointY = (previous.y + point.y) / 2;

    return {
      angle,
      key: `${previous.key}-${point.key}`,
      left: midpointX - width / 2,
      top: midpointY - segmentThickness / 2,
      width,
    };
  });
  const guideValues = [maxValue, minValue + valueRange / 2, minValue];
  const guideLines = guideValues.map((value) => ({
    label: displaySignedPercent(value),
    y: yForValue(value),
  }));

  return {
    guideLines,
    points: normalizedPoints,
    principalY: yForValue(0),
    qqqY: yForValue(qqqReturnPct ?? 0),
    segments,
  };
}

function displaySignedPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatChartDate(timestamp: string | undefined) {
  if (!timestamp) return "-";
  const datePart = timestamp.slice(0, 10);
  const [year, month, day] = datePart.split("-");
  if (!year || !month || !day) return timestamp;
  return `${year.slice(2)}.${month}.${day}`;
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
    borderRadius: 20,
    gap: spacing.md,
    minHeight: 320,
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
  sectionTitle: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "800",
    lineHeight: 28,
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
  rangeRow: {
    flexDirection: "row",
    gap: spacing.xs,
  },
  rangeChip: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    justifyContent: "center",
    minHeight: mobile.touchTarget,
  },
  rangeChipPressed: {
    opacity: 0.72,
  },
  rangeChipSelected: {
    backgroundColor: "#E0E0E0",
  },
  rangeText: {
    color: colors.mutedInk,
    fontWeight: "700",
  },
  rangeTextSelected: {
    color: colors.ink,
    fontWeight: "800",
  },
  kpiOverlay: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  chartFrame: {
    backgroundColor: "#0F172A",
    borderColor: "#1F2A44",
    borderRadius: 16,
    borderWidth: 1,
    height: 174,
    overflow: "hidden",
    padding: spacing.md,
    position: "relative",
  },
  chartGrid: {
    bottom: 0,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
  },
  chartGuideLine: {
    backgroundColor: "#273449",
    height: 1,
    left: spacing.md,
    position: "absolute",
    right: spacing.md,
  },
  chartGuideText: {
    color: "#A6ADBB",
    fontSize: 10,
    fontWeight: "800",
    lineHeight: 12,
    position: "absolute",
    right: 0,
    top: -7,
  },
  principalLine: {
    backgroundColor: "#9CA3AF",
    height: 2,
    left: spacing.md,
    opacity: 0.88,
    position: "absolute",
    right: 54,
  },
  qqqLine: {
    borderColor: "#60A5FA",
    borderStyle: "dashed",
    borderTopWidth: 2,
    height: 1,
    left: spacing.md,
    opacity: 0.94,
    position: "absolute",
    right: 54,
  },
  chartLineSegment: {
    backgroundColor: "#34C759",
    borderRadius: 999,
    height: 3,
    position: "absolute",
  },
  chartPointMarker: {
    backgroundColor: "#FFFFFF",
    borderColor: "#34C759",
    borderRadius: 5,
    borderWidth: 2,
    height: 10,
    position: "absolute",
    width: 10,
  },
  chartCrosshair: {
    backgroundColor: "#FFFFFF",
    bottom: 0,
    opacity: 0.25,
    position: "absolute",
    top: 0,
    width: 1,
  },
  drawdownBar: {
    backgroundColor: "#F472B6",
    bottom: spacing.sm,
    borderRadius: 999,
    opacity: 0.76,
    position: "absolute",
    width: 4,
  },
  selectedBubble: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    minWidth: 112,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    position: "absolute",
  },
  selectedBubbleText: {
    color: "#0F172A",
    fontSize: 12,
    fontWeight: "900",
    lineHeight: 16,
  },
  emptyState: {
    alignItems: "center",
    flex: 1,
    gap: spacing.sm,
    justifyContent: "center",
    minHeight: 120,
    paddingHorizontal: spacing.sm,
  },
  emptyTitle: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 22,
    textAlign: "center",
  },
  emptyBody: {
    color: "#CBD5E1",
    maxWidth: 320,
    textAlign: "center",
  },
  statusLine: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between",
  },
  note: {
    color: colors.mutedInk,
  },
});
