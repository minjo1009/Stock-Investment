import { StyleSheet, View } from "react-native";

import { FreshnessBanner, MobileV1StatusRail } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { BlockerList, SourceFreshnessBadge, StatusRow } from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { portfolioFixture } from "../../src/read-models/portfolioFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

const allocationSegments = [
  { label: "해외주식", ratio: null, color: "#00C4B3" },
  { label: "국내주식", ratio: null, color: "#4E8DF5" },
  { label: "현금", ratio: null, color: "#A0A0A0" },
  { label: "기타", ratio: null, color: "#F59E0B" },
];

const sortOptions = ["평가금 순", "수익률 순", "수익금 순", "비중 순"];
const disabledActions = ["매수 차단", "매도 차단", "노트 준비중", "알림 준비중"];

export default function PortfolioRoute() {
  const portfolio = portfolioFixture;
  const summary = portfolio.portfolioSummary;
  const firstPosition = portfolio.positions[0];

  return (
    <ScreenContainer contentContainerStyle={styles.screen}>
      <View style={styles.header}>
        <AppText style={styles.backIcon}>‹</AppText>
        <AppText style={styles.headerTitle}>포트폴리오</AppText>
        <View style={styles.headerActions}>
          <AppText style={styles.headerIcon}>⌕</AppText>
          <AppText style={styles.headerIcon}>≡</AppText>
        </View>
      </View>

      <PortfolioSummaryCard
        totalEvaluation={displayMoney(summary.totalMarketValue)}
        costBasis={displayMoney(summary.investedCash)}
        totalPnl={displayMoney(summary.unrealizedPnl)}
        totalReturn={displayPercent(summary.exposurePct)}
        positionCount={displayCount(summary.positionCount)}
        winRate={displayPercent(summary.winRatePct)}
        maxDrawdown={displayPercent(summary.maxDrawdownPct)}
        updatedAt="업데이트: UNKNOWN"
      />

      <PortfolioAllocationCard />

      <CardContainer style={styles.holdingsCard}>
        <View style={styles.listHeader}>
          <View>
            <AppText style={styles.sectionTitle}>보유 종목</AppText>
            <AppText variant="caption">{displayCount(summary.positionCount)}종목 / broker truth BLOCKED</AppText>
          </View>
          <Badge label="필터 없음" tone="readOnly" />
        </View>

        <View style={styles.sortRow}>
          {sortOptions.map((option, index) => (
            <View key={option} style={[styles.sortChip, index === 0 ? styles.sortChipActive : null]}>
              <AppText variant="caption" style={index === 0 ? styles.sortChipTextActive : styles.sortChipText}>
                {option}
              </AppText>
            </View>
          ))}
        </View>

        <HoldingRow
          name="권위 데이터 대기"
          ticker={firstPosition?.symbol ?? "UNKNOWN"}
          quantity={displayCount(firstPosition?.quantity ?? null)}
          weight="비중 UNKNOWN"
          evaluation={displayMoney(firstPosition?.marketValue ?? null)}
          costBasis="원금 UNKNOWN"
          pnl={displayMoney(firstPosition?.unrealizedPnl ?? null)}
          yieldValue="수익률 UNKNOWN"
          state={firstPosition?.brokerTruthState ?? "UNKNOWN"}
        />

        <View style={styles.disabledActionRow}>
          {disabledActions.map((action) => (
            <View key={action} style={styles.disabledActionChip}>
              <AppText variant="caption" style={styles.disabledActionText}>
                {action}
              </AppText>
            </View>
          ))}
        </View>
      </CardContainer>

      <SectionContainer title="데이터 상태" description="이 영역은 보조 계층입니다. 실제 계좌/브로커 권위 데이터가 붙기 전까지 값은 UNKNOWN입니다.">
        <FreshnessBanner
          generatedAt={portfolio.generatedAt}
          sourceSummary={portfolio.sourceSummary}
          title="포트폴리오 데이터 출처 상태"
        />
        <MobileV1StatusRail
          items={[
            { label: "보유 종목", value: displayCount(summary.positionCount), tone: "readOnly" },
            { label: "계좌 상태", value: "UNKNOWN", tone: "unknown" },
            { label: "브로커 검증", value: "BLOCKED", tone: "blocked" },
          ]}
          subtitle="Phone-first v1 / read-only"
          title="포트폴리오 보조 상태"
        />
        {firstPosition?.sourceStates.map((sourceState) => (
          <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
        ))}
      </SectionContainer>

      <SectionContainer title="운영 제한" description="거래 변경 기능은 보조 정보로만 표시되며 실행 핸들러가 없습니다.">
        <StatusRow
          label="전략 승인"
          value={`Strategy ${portfolio.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={portfolio.governance.controlStateSource}
        />
        <StatusRow
          label="배포 상태"
          value={`Deployment ${portfolio.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={portfolio.governance.authorityReportPath}
        />
        <StatusRow
          label="실자본"
          value={`Real capital ${portfolio.governance.realCapital}`}
          state="blocked"
          sourceRef={portfolio.governance.controlStateSource}
        />
        <BlockerList blockers={portfolio.blockers} />
      </SectionContainer>
    </ScreenContainer>
  );
}

type PortfolioSummaryCardProps = {
  totalEvaluation: string;
  costBasis: string;
  totalPnl: string;
  totalReturn: string;
  positionCount: string;
  winRate: string;
  maxDrawdown: string;
  updatedAt: string;
};

function PortfolioSummaryCard({
  costBasis,
  maxDrawdown,
  positionCount,
  totalEvaluation,
  totalPnl,
  totalReturn,
  updatedAt,
  winRate,
}: PortfolioSummaryCardProps) {
  return (
    <CardContainer style={styles.summaryCard}>
      <View style={styles.summaryTopRow}>
        <View style={styles.summaryTitleBlock}>
          <AppText style={styles.cardLabel}>총 평가금</AppText>
          <View style={styles.valueRow}>
            <AppText style={styles.primaryValue}>{totalEvaluation}</AppText>
            <AppText style={styles.currencyUnit}>원</AppText>
          </View>
        </View>
      </View>
      <Badge label="read-only · NOT_AUTHORITY" tone="readOnly" />

      <View style={styles.summaryDivider} />

      <View style={styles.summaryMetricGrid}>
        <MetricPair label="원금" value={`${costBasis}원`} />
        <MetricPair label="총 손익" value={totalPnl} valueStyle={styles.unknownValue} />
        <MetricPair label="수익률" value={totalReturn} valueStyle={styles.unknownValue} />
        <MetricPair label="보유" value={`${positionCount}종목`} />
      </View>

      <View style={styles.kpiRow}>
        <KpiPill label="승률" value={winRate} />
        <KpiPill label="MDD" value={maxDrawdown} tone="negative" />
        <KpiPill label="데이터" value="UNKNOWN" />
      </View>

      <AppText variant="caption" style={styles.timestamp}>
        {updatedAt} · NOT_AUTHORITY
      </AppText>
    </CardContainer>
  );
}

function PortfolioAllocationCard() {
  return (
    <CardContainer style={styles.allocationCard}>
      <View style={styles.sectionHeader}>
        <View>
          <AppText style={styles.sectionTitle}>자산 배분</AppText>
          <AppText variant="caption">자산유형 기준 / 권위 데이터 연결 전</AppText>
        </View>
        <Badge label="SOURCE_NOT_ATTACHED" tone="missing" />
      </View>

      <View style={styles.segmentControl}>
        {["자산유형", "지역", "통화", "섹터"].map((label, index) => (
          <View key={label} style={[styles.segmentChip, index === 0 ? styles.segmentChipActive : null]}>
            <AppText variant="caption" style={index === 0 ? styles.segmentTextActive : styles.segmentText}>
              {label}
            </AppText>
          </View>
        ))}
      </View>

      <View style={styles.allocationBar}>
        {allocationSegments.map((segment) => (
          <View
            key={segment.label}
            style={[
              styles.allocationSegment,
              { backgroundColor: segment.color, flex: 1 },
            ]}
          />
        ))}
      </View>

      <View style={styles.legendGrid}>
        {allocationSegments.map((segment) => (
          <View key={segment.label} style={styles.legendRow}>
            <View style={[styles.legendSwatch, { backgroundColor: segment.color }]} />
            <View style={styles.legendTextBlock}>
              <AppText style={styles.legendLabel}>{segment.label}</AppText>
              <AppText variant="caption">비중 UNKNOWN · 평가금 UNKNOWN</AppText>
            </View>
          </View>
        ))}
      </View>
    </CardContainer>
  );
}

type HoldingRowProps = {
  name: string;
  ticker: string;
  quantity: string;
  weight: string;
  evaluation: string;
  costBasis: string;
  pnl: string;
  yieldValue: string;
  state: string;
};

function HoldingRow({
  costBasis,
  evaluation,
  name,
  pnl,
  quantity,
  state,
  ticker,
  weight,
  yieldValue,
}: HoldingRowProps) {
  return (
    <View style={styles.holdingRow}>
      <View style={styles.assetIcon}>
        <AppText style={styles.assetIconText}>{ticker.slice(0, 1)}</AppText>
      </View>
      <View style={styles.holdingNameBlock}>
        <View style={styles.holdingTitleRow}>
          <AppText style={styles.holdingName}>{name}</AppText>
          <Badge label={state} tone="blocked" />
        </View>
        <AppText variant="caption">
          {ticker} · {quantity} · {weight}
        </AppText>
        <AppText variant="caption">평단가 UNKNOWN · 실현손익 UNKNOWN</AppText>
      </View>
      <View style={styles.holdingValueBlock}>
        <AppText style={styles.holdingValue}>{evaluation}원</AppText>
        <AppText variant="caption">{costBasis}</AppText>
        <AppText style={styles.unknownValue}>{pnl}</AppText>
        <AppText variant="caption">{yieldValue}</AppText>
      </View>
    </View>
  );
}

type MetricPairProps = {
  label: string;
  value: string;
  valueStyle?: object;
};

function MetricPair({ label, value, valueStyle }: MetricPairProps) {
  return (
    <View style={styles.metricPair}>
      <AppText variant="caption">{label}</AppText>
      <AppText style={[styles.metricValue, valueStyle]}>{value}</AppText>
    </View>
  );
}

function KpiPill({ label, tone, value }: { label: string; tone?: "negative"; value: string }) {
  return (
    <View style={styles.kpiPill}>
      <AppText variant="caption">{label}</AppText>
      <AppText style={[styles.kpiValue, tone === "negative" ? styles.negativeValue : null]}>{value}</AppText>
    </View>
  );
}

function displayMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return new Intl.NumberFormat("ko-KR").format(value);
}

function displayPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return `${value.toFixed(2)}%`;
}

function displayCount(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return new Intl.NumberFormat("ko-KR").format(value);
}

const elevatedCard = {
  shadowColor: "#111827",
  shadowOffset: { height: 8, width: 0 },
  shadowOpacity: 0.06,
  shadowRadius: 16,
  elevation: 2,
};

const styles = StyleSheet.create({
  screen: {
    gap: 24,
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 56,
  },
  backIcon: {
    color: colors.mutedInk,
    fontSize: 30,
    fontWeight: "500",
    lineHeight: 36,
    minWidth: 44,
  },
  headerTitle: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
  },
  headerActions: {
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "flex-end",
    minWidth: 44,
  },
  headerIcon: {
    color: colors.mutedInk,
    fontSize: 20,
    fontWeight: "700",
    lineHeight: 28,
    minWidth: 24,
    textAlign: "center",
  },
  summaryCard: {
    ...elevatedCard,
    borderRadius: 24,
    gap: spacing.lg,
    minHeight: 220,
    padding: 20,
  },
  summaryTopRow: {
    alignItems: "flex-start",
    flexDirection: "column",
    justifyContent: "flex-start",
    gap: spacing.md,
  },
  summaryTitleBlock: {
    flex: 1,
    gap: spacing.xs,
  },
  cardLabel: {
    color: "#6C6C6C",
    fontSize: 15,
    fontWeight: "700",
    lineHeight: 20,
  },
  valueRow: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  primaryValue: {
    color: "#1A1A1A",
    fontSize: 36,
    fontWeight: "900",
    lineHeight: 42,
  },
  currencyUnit: {
    color: "#6C6C6C",
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 30,
  },
  summaryDivider: {
    backgroundColor: "#E0E0E0",
    height: 1,
  },
  summaryMetricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  metricPair: {
    flexBasis: "45%",
    flexGrow: 1,
    gap: spacing.xs,
  },
  metricValue: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 22,
  },
  unknownValue: {
    color: "#A0A0A0",
    fontWeight: "800",
  },
  negativeValue: {
    color: "#E01E5A",
  },
  kpiRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  kpiPill: {
    backgroundColor: "#F6F7F9",
    borderColor: "#E0E0E0",
    borderRadius: 12,
    borderWidth: 1,
    flexBasis: "45%",
    flexGrow: 1,
    gap: spacing.xs,
    minHeight: mobile.touchTarget,
    padding: spacing.sm,
  },
  kpiValue: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 20,
  },
  timestamp: {
    color: "#6C6C6C",
  },
  allocationCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.lg,
    padding: spacing.lg,
  },
  sectionHeader: {
    alignItems: "flex-start",
    flexDirection: "column",
    gap: spacing.md,
    justifyContent: "space-between",
  },
  sectionTitle: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
  },
  segmentControl: {
    borderBottomColor: "#E0E0E0",
    borderBottomWidth: 1,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  segmentChip: {
    paddingBottom: spacing.sm,
  },
  segmentChipActive: {
    borderBottomColor: "#00C4B3",
    borderBottomWidth: 2,
  },
  segmentText: {
    color: "#6C6C6C",
    fontWeight: "700",
  },
  segmentTextActive: {
    color: "#00C4B3",
    fontWeight: "800",
  },
  allocationBar: {
    borderRadius: 999,
    flexDirection: "row",
    height: 48,
    overflow: "hidden",
  },
  allocationSegment: {
    minWidth: 24,
  },
  legendGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  legendRow: {
    alignItems: "center",
    flexBasis: "45%",
    flexDirection: "row",
    flexGrow: 1,
    gap: spacing.sm,
  },
  legendSwatch: {
    borderRadius: 5,
    height: 10,
    width: 10,
  },
  legendTextBlock: {
    flex: 1,
  },
  legendLabel: {
    color: "#1A1A1A",
    fontSize: 14,
    fontWeight: "800",
    lineHeight: 18,
  },
  holdingsCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.lg,
    padding: spacing.lg,
  },
  listHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
  sortRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  sortChip: {
    backgroundColor: "#F6F7F9",
    borderRadius: 8,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  sortChipActive: {
    backgroundColor: "#DFF8F5",
  },
  sortChipText: {
    color: "#6C6C6C",
    fontWeight: "700",
  },
  sortChipTextActive: {
    color: "#008A80",
    fontWeight: "800",
  },
  holdingRow: {
    alignItems: "center",
    borderColor: "#E0E0E0",
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    minHeight: 88,
    padding: spacing.lg,
  },
  assetIcon: {
    alignItems: "center",
    backgroundColor: "#DFF8F5",
    borderRadius: 16,
    height: 32,
    justifyContent: "center",
    width: 32,
  },
  assetIconText: {
    color: "#008A80",
    fontSize: 16,
    fontWeight: "900",
    lineHeight: 20,
  },
  holdingNameBlock: {
    flex: 1,
    gap: spacing.xs,
  },
  holdingTitleRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  holdingName: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
  },
  holdingValueBlock: {
    alignItems: "flex-end",
    gap: 2,
    maxWidth: 116,
  },
  holdingValue: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 22,
    textAlign: "right",
  },
  disabledActionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  disabledActionChip: {
    backgroundColor: "#F6F7F9",
    borderColor: "#E0E0E0",
    borderRadius: 12,
    borderWidth: 1,
    minHeight: mobile.touchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  disabledActionText: {
    color: "#6C6C6C",
    fontWeight: "800",
  },
});
