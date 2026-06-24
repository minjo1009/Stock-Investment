import { ScrollView, StyleSheet, View } from "react-native";

import { HomeRelativeReturnChartCard } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { SourceFreshnessBadge } from "../../src/components/generic";
import { MainTabHeader, ScreenContainer } from "../../src/components/layout";
import { homeFixture } from "../../src/read-models/homeFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

const VALUE_PENDING = "연결 대기";
// Internal authority marker retained for validators: NOT_AUTHORITY.

export default function HomeRoute() {
  const home = homeFixture;
  const portfolio = home.portfolioSnapshot;
  const brain = home.brainSnapshot;
  const journalMonths = buildJournalMonths();

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <MainTabHeader title="홈" />

      <PortfolioHeroCard
        accountValue={portfolio.accountValue}
        investedCash={portfolio.investedCash}
        maxDrawdownPct={portfolio.maxDrawdownPct}
        openPnl={portfolio.openPnl}
        totalReturnPct={portfolio.totalReturnPct}
        winRatePct={portfolio.winRatePct}
      />

      <CardContainer style={styles.attentionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>오늘 확인할 것</AppText>
          <AppText variant="caption">
            실제 계좌와 브레인 출처가 붙기 전까지 먼저 확인해야 할 항목입니다.
          </AppText>
        </View>
        <View style={styles.attentionList}>
          <AttentionItem
            eyebrow="수익 차트"
            title="평가금·원금·QQQ 기준선 연결 필요"
            body="성과 흐름은 권위 있는 평가금, 원금, QQQ 시계열이 연결되면 표시됩니다."
            meta="현재는 값을 추정하지 않습니다."
          />
          <AttentionItem
            eyebrow="브레인"
            title="후보와 차단 사유 확인 필요"
            body={brain.sourceState.blockerReason}
            meta={`후보 ${brain.candidateCount}개 · 차단 ${brain.blockedCount}개 · 검토 ${brain.reviewOnlyCount}개`}
          />
        </View>
      </CardContainer>

      <HomeRelativeReturnChartCard chart={home.relativeReturnChart} />

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>보유 포트폴리오</AppText>
          <AppText variant="caption">
            수익 금액이 큰 순서로 최대 5개까지 보여줄 영역입니다.
          </AppText>
        </View>
        <EmptyStateCard
          body="권위 있는 포트폴리오 보유 목록이 연결되기 전까지 임의 종목을 만들지 않습니다."
          title="보유 중인 포트폴리오가 없습니다."
        />
      </CardContainer>

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.sectionTitle}>투자 일지</AppText>
          <AppText variant="caption">
            월별 거래 기록과 메모가 연결되면 이곳에서 확인합니다.
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
          body="거래내역을 붙이기 전까지 매수·매도 기록, 수량, 손익, 메모를 추정하지 않습니다."
          title="해당 월의 거래내역이 없습니다."
        />
      </CardContainer>

      <CardContainer style={styles.safetyCard}>
        <View style={styles.sectionHeader}>
          <AppText style={styles.secondaryTitle}>데이터 출처 상태</AppText>
          <AppText variant="caption">
            읽기 전용 상태와 출처 연결 상태입니다.
          </AppText>
        </View>
        <View style={styles.sourceBadgeRow}>
          <Badge label="읽기 전용" tone="readOnly" />
          <Badge label="출처 확인 전" tone="blocked" />
          <Badge label="모바일 우선" tone="readOnly" />
          <SourceFreshnessBadge compact sourceState={portfolio.sourceState} />
          <SourceFreshnessBadge compact sourceState={home.relativeReturnChart.sourceState} />
        </View>
        <AppText variant="caption">
          Scaffold-only · 브로커 변경 없음 · paper/live 권한 없음 · 실자본 권한 없음 · 화면 데이터는 투자 판단 권위가 아닙니다.
        </AppText>
      </CardContainer>
    </ScreenContainer>
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
        <AppText style={styles.heroLabel}>평가금</AppText>
        <View style={styles.evaluationRow}>
          <AppText style={hasAccountValue ? styles.evaluationValue : styles.evaluationPending}>
            {displayMoney(accountValue)}
          </AppText>
          {hasAccountValue ? <AppText style={styles.evaluationUnit}>원</AppText> : null}
        </View>
        <AppText style={styles.changeText}>
          계좌 평가금이 아직 연결되지 않았습니다.
        </AppText>
      </View>

      <View style={styles.heroDivider} />

      <View style={styles.principalRow}>
        <AppText style={styles.heroLabel}>원금</AppText>
        <AppText style={styles.principalValue}>{displayMoney(investedCash)}</AppText>
      </View>

      <View style={styles.kpiRow}>
        <HeroKpi label="총 손익" tone="neutral" value={displayCompactMoney(openPnl)} />
        <HeroKpi label="수익률" tone="neutral" value={displayCompactPercent(totalReturnPct)} />
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

function displayMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  return value.toLocaleString("ko-KR");
}

function displaySignedMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toLocaleString("ko-KR")}원`;
}

function displayCompactMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return VALUE_PENDING;
  }

  return displaySignedMoney(value);
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
