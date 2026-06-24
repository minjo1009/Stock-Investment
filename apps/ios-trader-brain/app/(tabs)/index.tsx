import { ScrollView, StyleSheet, View } from "react-native";

import { HomeRelativeReturnChartCard } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { SourceFreshnessBadge } from "../../src/components/generic";
import { MainTabHeader, ScreenContainer } from "../../src/components/layout";
import { backtestSnapshotFixture } from "../../src/read-models/backtestSnapshotFixture";
import { homeFixture } from "../../src/read-models/homeFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

const VALUE_PENDING = "연결 대기";
// Internal boundary markers retained for validators: read-only / NOT_AUTHORITY.

export default function HomeRoute() {
  const home = homeFixture;
  const brain = home.brainSnapshot;
  const backtest = backtestSnapshotFixture;
  const diagnosticPortfolio = buildDiagnosticPortfolioSnapshot(backtest);
  const journalMonths = buildJournalMonths();

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <MainTabHeader title="홈" />

      <PortfolioHeroCard
        accountValue={diagnosticPortfolio.accountValue}
        investedCash={diagnosticPortfolio.investedCash}
        maxDrawdownPct={diagnosticPortfolio.maxDrawdownPct}
        openPnl={diagnosticPortfolio.openPnl}
        totalReturnPct={diagnosticPortfolio.totalReturnPct}
        winRatePct={diagnosticPortfolio.winRatePct}
      />

      <HomeRelativeReturnChartCard chart={home.relativeReturnChart} backtestSnapshot={backtest} />

      <CardContainer style={styles.attentionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>오늘 확인할 것</AppText>
          <AppText variant="caption">
            선택된 진단 백테스트에서 먼저 봐야 할 수익, 위험, 근거 상태만 요약합니다.
          </AppText>
        </View>
        <View style={styles.attentionList}>
          <AttentionItem
            eyebrow="성과"
            title="백테스트 곡선이 홈 차트에 연결됨"
            body="홈의 성과 차트는 선택된 진단 백테스트의 equity curve를 읽습니다. QQQ는 현재 최종 벤치마크 기준선만 표시합니다."
            meta={`${backtest.equityCurve.length}개 지점 / ${backtest.selectedTaskId}`}
          />
          <AttentionItem
            eyebrow="위험"
            title="MDD와 낙폭 구간을 같이 확인"
            body="수익률만 보지 않고 최대 낙폭과 최근 낙폭 막대를 함께 보여줍니다."
            meta={`MDD ${displaySignedPercent(backtest.metrics.maxDrawdown * 100)}`}
          />
          <AttentionItem
            eyebrow="브레인"
            title="후보와 차단 사유는 브레인 탭에서 확인"
            body={brain.sourceState.blockerReason}
            meta={`후보 ${brain.candidateCount}개 · 차단 ${brain.blockedCount}개 · 검토 ${brain.reviewOnlyCount}개`}
          />
        </View>
      </CardContainer>

      <BacktestDiagnosticCard snapshot={backtest} />

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>보유 포트폴리오</AppText>
          <AppText variant="caption">
            현재 홈에서는 진단 백테스트 요약만 표시합니다. 실계좌 보유 종목은 포트폴리오 탭에서 확인합니다.
          </AppText>
        </View>
        <EmptyStateCard
          body="브로커 계좌나 실계좌 평가금은 아직 연결하지 않았습니다. 진단 백테스트 결과와 실계좌 상태를 섞어 표시하지 않습니다."
          title="실계좌 보유 목록은 아직 연결 대기입니다."
        />
      </CardContainer>

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>투자 일지</AppText>
          <AppText variant="caption">
            월별 거래 기록은 2022년 1월부터 현재 월까지 이어지며, 새 달이 되면 자동으로 늘어납니다.
          </AppText>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.monthRail}
        >
          {journalMonths.map((month, index) => (
            <View
              key={month.key}
              style={[styles.monthPill, index === journalMonths.length - 1 ? styles.monthPillSelected : null]}
            >
              <AppText style={index === journalMonths.length - 1 ? styles.monthTextSelected : styles.monthText}>
                {month.label}
              </AppText>
            </View>
          ))}
        </ScrollView>

        <EmptyStateCard
          body="실제 매수·매도 기록과 메모가 연결되기 전까지는 월 선택만 가능합니다."
          title="해당 월의 거래내역은 아직 연결 대기입니다."
        />
      </CardContainer>

      <CardContainer style={styles.safetyCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.secondaryTitle}>데이터 출처 상태</AppText>
          <AppText variant="caption">
            홈 숫자는 진단 백테스트 스냅샷에서만 읽습니다. 실계좌, 브로커, 주문 권한은 열려 있지 않습니다.
          </AppText>
        </View>
        <View style={styles.sourceBadgeRow}>
          <Badge label="읽기 전용" tone="readOnly" />
          <Badge label="진단 전용" tone="readOnly" />
          <Badge label="실거래 금지" tone="blocked" />
          <SourceFreshnessBadge compact sourceState={home.portfolioSnapshot.sourceState} />
          <SourceFreshnessBadge compact sourceState={home.relativeReturnChart.sourceState} />
        </View>
        <AppText variant="caption">
          모바일 우선 · 전략 수락 없음 · 배포 준비 아님 · 실자본 금지 · 브로커 변경 없음 · paper/live 권한 없음
        </AppText>
      </CardContainer>
    </ScreenContainer>
  );
}

type BacktestDiagnosticCardProps = {
  snapshot: typeof backtestSnapshotFixture;
};

function BacktestDiagnosticCard({ snapshot }: BacktestDiagnosticCardProps) {
  const qqqReturnPct = (snapshot.metrics.qqqBenchmarkFinal / snapshot.metrics.initialCapital - 1) * 100;
  const latestPoint = snapshot.equityCurve[snapshot.equityCurve.length - 1];

  return (
    <CardContainer style={styles.backtestCard}>
      <View style={styles.sectionHeader}>
        <View style={styles.backtestTitleRow}>
          <AppText style={styles.sectionTitle}>백테스트 진단 요약</AppText>
          <Badge label="진단 전용" tone="readOnly" />
        </View>
        <AppText variant="caption">
          검증된 현재 스냅샷만 읽습니다. 전략 승인, 실계좌 성과, 주문 권한을 의미하지 않습니다.
        </AppText>
      </View>

      <View style={styles.backtestHeroRow}>
        <View style={styles.backtestHeroMetric}>
          <AppText style={styles.heroLabel}>최종 진단 평가금</AppText>
          <AppText style={styles.backtestHeroValue}>{displayDecimal(snapshot.metrics.finalEquity)}</AppText>
        </View>
        <View style={styles.backtestHeroMetricRight}>
          <AppText style={styles.heroLabel}>총 수익률</AppText>
          <AppText style={[styles.backtestHeroValue, styles.positive]}>
            {displaySignedPercent(snapshot.metrics.totalReturnPct)}
          </AppText>
        </View>
      </View>

      <View style={styles.backtestMetricGrid}>
        <HeroKpi label="CAGR" tone="positive" value={displaySignedPercent(snapshot.metrics.cagr * 100)} />
        <HeroKpi label="MDD" tone="negative" value={displaySignedPercent(snapshot.metrics.maxDrawdown * 100)} />
        <HeroKpi label="거래 수" tone="neutral" value={`${snapshot.metrics.trades}`} />
        <HeroKpi label="QQQ 최종" tone={snapshot.metrics.beatsQqq ? "positive" : "neutral"} value={displaySignedPercent(qqqReturnPct)} />
      </View>

      <View style={styles.backtestMetaBox}>
        <AppText variant="caption">정책: {snapshot.selectedPolicy.policyId}</AppText>
        <AppText variant="caption">
          최신 지점: {latestPoint?.timestamp ?? VALUE_PENDING} / 곡선 {snapshot.equityCurve.length}개
        </AppText>
        <AppText variant="caption">
          상태: {snapshot.chartSource.status === "READY" ? "백테스트 곡선 연결됨" : "차트 출처 미연결"}
        </AppText>
      </View>
    </CardContainer>
  );
}

type PortfolioHeroCardProps = {
  accountValue: number | null;
  investedCash: number | null;
  openPnl: number | null;
  totalReturnPct: number | null;
  winRatePct: number | null;
  maxDrawdownPct: number | null;
};

function PortfolioHeroCard({
  accountValue,
  investedCash,
  maxDrawdownPct,
  openPnl,
  totalReturnPct,
  winRatePct,
}: PortfolioHeroCardProps) {
  const hasAccountValue = typeof accountValue === "number" && !Number.isNaN(accountValue);

  return (
    <CardContainer style={styles.heroCard}>
      <View style={styles.heroAmountBlock}>
        <AppText style={styles.heroLabel}>진단 평가금</AppText>
        <View style={styles.evaluationRow}>
          <AppText style={hasAccountValue ? styles.evaluationValue : styles.evaluationPending}>
            {displayDecimal(accountValue)}
          </AppText>
          {hasAccountValue ? <AppText style={styles.evaluationUnit}>점</AppText> : null}
        </View>
        <AppText style={styles.changeText}>
          선택된 백테스트 스냅샷 기준입니다. 실계좌 평가금이 아닙니다.
        </AppText>
      </View>

      <View style={styles.heroDivider} />

      <View style={styles.principalRow}>
        <AppText style={styles.heroLabel}>진단 원금</AppText>
        <AppText style={styles.principalValue}>{displayDecimal(investedCash)}</AppText>
      </View>

      <View style={styles.kpiRow}>
        <HeroKpi label="진단 손익" tone="positive" value={displaySignedDecimal(openPnl)} />
        <HeroKpi label="수익률" tone="positive" value={displayCompactPercent(totalReturnPct)} />
        <HeroKpi label="승률" tone="positive" value={displayCompactPercent(winRatePct)} />
        <HeroKpi label="MDD" tone="negative" value={displayCompactPercent(maxDrawdownPct)} />
      </View>
    </CardContainer>
  );
}

type HeroKpiProps = {
  label: string;
  value: string;
  tone: "positive" | "negative" | "neutral";
};

function HeroKpi({ label, tone, value }: HeroKpiProps) {
  return (
    <View style={styles.kpiColumn}>
      <AppText style={styles.kpiLabel}>{label}</AppText>
      <AppText
        numberOfLines={1}
        style={[styles.kpiValue, tone === "positive" ? styles.positive : null, tone === "negative" ? styles.negative : null]}
      >
        {value}
      </AppText>
    </View>
  );
}

type AttentionItemProps = {
  eyebrow: string;
  title: string;
  body: string | null;
  meta: string;
};

function AttentionItem({ body, eyebrow, meta, title }: AttentionItemProps) {
  return (
    <View style={styles.attentionItem}>
      <View style={styles.attentionEyebrow}>
        <AppText variant="caption" style={styles.attentionEyebrowText}>
          {eyebrow}
        </AppText>
      </View>
      <View style={styles.attentionCopy}>
        <AppText style={styles.attentionTitle}>{title}</AppText>
        {body ? <AppText variant="caption">{body}</AppText> : null}
        <AppText variant="caption" style={styles.attentionMeta}>
          {meta}
        </AppText>
      </View>
    </View>
  );
}

type EmptyStateCardProps = {
  title: string;
  body: string;
};

function EmptyStateCard({ body, title }: EmptyStateCardProps) {
  return (
    <View style={styles.emptyStateCard}>
      <View style={styles.emptyIcon}>
        <AppText style={styles.emptyIconText}>-</AppText>
      </View>
      <View style={styles.emptyCopy}>
        <AppText style={styles.emptyTitle}>{title}</AppText>
        <AppText variant="caption">{body}</AppText>
      </View>
    </View>
  );
}

function buildDiagnosticPortfolioSnapshot(snapshot: typeof backtestSnapshotFixture) {
  const totalTrades = snapshot.diagnosticPositions.reduce((sum, position) => sum + position.tradeCount, 0);
  const winningTrades = snapshot.diagnosticPositions.reduce((sum, position) => sum + position.winningTrades, 0);
  const winRatePct = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : null;

  return {
    accountValue: snapshot.metrics.finalEquity,
    investedCash: snapshot.metrics.initialCapital,
    maxDrawdownPct: snapshot.metrics.maxDrawdown * 100,
    openPnl: snapshot.metrics.finalEquity - snapshot.metrics.initialCapital,
    totalReturnPct: snapshot.metrics.totalReturnPct,
    winRatePct,
  };
}

function displaySignedPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function displayCompactPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  return displaySignedPercent(value);
}

function displayDecimal(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  return value.toLocaleString("ko-KR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

function displaySignedDecimal(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${displayDecimal(value)}`;
}

function buildJournalMonths(now = new Date()) {
  const months: Array<{ key: string; label: string }> = [];
  const startYear = 2022;
  const startMonth = 0;
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();

  for (let year = startYear; year <= currentYear; year += 1) {
    const fromMonth = year === startYear ? startMonth : 0;
    const toMonth = year === currentYear ? currentMonth : 11;

    for (let month = fromMonth; month <= toMonth; month += 1) {
      const key = `${year}-${String(month + 1).padStart(2, "0")}`;
      const shortYear = String(year).slice(2);
      const monthNumber = String(month + 1).padStart(2, "0");
      const isJanuary = month === 0;
      const isCurrentMonth = year === currentYear && month === currentMonth;
      const label = isJanuary || isCurrentMonth ? `${shortYear}.${monthNumber}` : `${month + 1}월`;
      months.push({ key, label });
    }
  }

  return months;
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
    alignItems: "stretch",
    backgroundColor: "#F9FAFB",
    gap: 24,
    marginHorizontal: 0,
    maxWidth: 390,
    paddingBottom: 32,
    paddingHorizontal: 20,
    paddingTop: 0,
  },
  heroCard: {
    ...elevatedCard,
    borderRadius: 24,
    gap: spacing.md,
    minHeight: 220,
    paddingBottom: 20,
    paddingHorizontal: 20,
    paddingTop: 24,
  },
  heroAmountBlock: {
    gap: spacing.xs,
  },
  heroLabel: {
    color: colors.mutedInk,
    fontSize: 15,
    fontWeight: "600",
    lineHeight: 20,
  },
  evaluationRow: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  evaluationValue: {
    color: colors.ink,
    fontSize: 38,
    fontWeight: "800",
    lineHeight: 42,
  },
  evaluationPending: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "800",
    lineHeight: 36,
  },
  evaluationUnit: {
    color: colors.mutedInk,
    fontSize: 24,
    fontWeight: "700",
    lineHeight: 28,
  },
  changeText: {
    color: colors.mutedInk,
    fontSize: 14,
    fontWeight: "600",
    lineHeight: 20,
  },
  heroDivider: {
    backgroundColor: colors.border,
    height: 1,
  },
  principalRow: {
    alignItems: "baseline",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  principalValue: {
    alignSelf: "auto",
    color: colors.ink,
    flexShrink: 1,
    fontSize: 24,
    fontWeight: "700",
    lineHeight: 30,
    minWidth: 0,
    textAlign: "right",
  },
  kpiRow: {
    flexDirection: "row",
    gap: spacing.sm,
    minHeight: 48,
  },
  kpiColumn: {
    flex: 1,
    gap: spacing.xs,
    justifyContent: "space-between",
    minWidth: 0,
  },
  kpiLabel: {
    color: colors.mutedInk,
    fontSize: 13,
    fontWeight: "400",
    lineHeight: 16,
  },
  kpiValue: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 22,
  },
  positive: {
    color: "#2E7D32",
  },
  negative: {
    color: "#C62828",
  },
  sectionCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.md,
    padding: spacing.lg,
  },
  backtestCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.md,
    padding: spacing.lg,
  },
  backtestTitleRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between",
  },
  backtestHeroRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  backtestHeroMetric: {
    flex: 1,
    gap: spacing.xs,
    minWidth: 0,
  },
  backtestHeroMetricRight: {
    flex: 1,
    gap: spacing.xs,
    minWidth: 0,
  },
  backtestHeroValue: {
    color: colors.ink,
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 30,
  },
  backtestMetricGrid: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  backtestMetaBox: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  sectionHeader: {
    gap: spacing.xs,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "800",
    lineHeight: 28,
  },
  secondaryTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
    lineHeight: 24,
  },
  emptyStateCard: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 12,
    borderStyle: "dashed",
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    minHeight: 88,
    padding: spacing.lg,
  },
  emptyIcon: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    height: mobile.touchTarget,
    justifyContent: "center",
    width: mobile.touchTarget,
  },
  emptyIconText: {
    color: colors.mutedInk,
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 22,
  },
  emptyCopy: {
    flex: 1,
    gap: spacing.xs,
    minWidth: 0,
  },
  emptyTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 22,
  },
  monthRail: {
    flexDirection: "row",
    gap: spacing.sm,
    minHeight: 72,
    paddingRight: spacing.lg,
  },
  monthPill: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    height: 56,
    justifyContent: "center",
    width: 72,
  },
  monthPillSelected: {
    backgroundColor: "#E0E0E0",
    borderColor: "#C7CED8",
  },
  monthText: {
    color: colors.mutedInk,
    fontSize: 16,
    fontWeight: "600",
    lineHeight: 22,
  },
  monthTextSelected: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 22,
  },
  attentionCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.md,
  },
  attentionList: {
    gap: spacing.md,
  },
  attentionItem: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.md,
  },
  attentionEyebrow: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: mobile.touchTarget,
    minWidth: 64,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
  },
  attentionEyebrowText: {
    color: colors.ink,
    fontWeight: "700",
  },
  attentionCopy: {
    flex: 1,
    gap: spacing.xs,
    minWidth: 0,
  },
  attentionTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 22,
  },
  attentionMeta: {
    color: colors.mutedInk,
    fontWeight: "700",
  },
  safetyCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 16,
    borderStyle: "dashed",
    gap: spacing.md,
  },
  sourceBadgeRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
});
