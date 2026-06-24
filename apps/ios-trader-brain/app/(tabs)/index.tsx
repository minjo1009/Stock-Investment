import { StyleSheet, View } from "react-native";

import { HomeRelativeReturnChartCard } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { SourceFreshnessBadge } from "../../src/components/generic";
import { ScreenContainer } from "../../src/components/layout";
import { homeFixture } from "../../src/read-models/homeFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

const MONEY_UNKNOWN = "UNKNOWN";
const PERCENT_UNKNOWN = "UNKNOWN";

export default function HomeRoute() {
  const home = homeFixture;
  const portfolio = home.portfolioSnapshot;
  const brain = home.brainSnapshot;

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <PortfolioHeroCard
        accountValue={portfolio.accountValue}
        investedCash={portfolio.investedCash}
        maxDrawdownPct={portfolio.maxDrawdownPct}
        openPnl={portfolio.openPnl}
        totalReturnPct={portfolio.totalReturnPct}
        winRatePct={portfolio.winRatePct}
      />

      <HomeRelativeReturnChartCard chart={home.relativeReturnChart} />

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.sectionTitle}>
            보유 포트폴리오
          </AppText>
          <AppText variant="caption">
            수익 금액이 큰 순서로 최대 5개까지 보여주는 영역입니다.
          </AppText>
        </View>
        <EmptyStateCard
          body="권위 있는 포트폴리오 보유 목록이 연결되기 전까지 임의 종목을 만들지 않습니다."
          title="보유 중인 포트폴리오가 없습니다."
        />
      </CardContainer>

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.sectionTitle}>
            투자 일지
          </AppText>
          <AppText variant="caption">
            월별 거래 기록과 메모가 연결되면 이곳에서 확인합니다.
          </AppText>
        </View>

        <View style={styles.monthRail}>
          {["6월", "5월", "4월", "3월"].map((month, index) => (
            <View key={month} style={[styles.monthPill, index === 0 ? styles.monthPillSelected : null]}>
              <AppText style={index === 0 ? styles.monthTextSelected : styles.monthText}>
                {month}
              </AppText>
            </View>
          ))}
        </View>

        <EmptyStateCard
          body="거래내역이 붙기 전까지 매수·매도 기록, 수량, 손익, 메모를 추정하지 않습니다."
          title="해당 월의 거래내역이 없습니다."
        />
      </CardContainer>

      <CardContainer style={styles.attentionCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.sectionTitle}>
            오늘 확인할 것
          </AppText>
          <AppText variant="caption">
            시스템 상태가 아니라 투자 화면을 완성하기 위해 필요한 데이터 연결 항목입니다.
          </AppText>
        </View>
        <View style={styles.attentionList}>
          <AttentionItem
            eyebrow="성과 차트"
            title="평가금·원금 시계열 연결 필요"
            body={home.relativeReturnChart.sourceState.blockerReason}
            meta="가짜 차트는 표시하지 않습니다"
          />
          <AttentionItem
            eyebrow="브레인"
            title="후보 상태와 차단 사유 확인"
            body={brain.sourceState.blockerReason}
            meta={`후보 ${brain.candidateCount}개 · 차단 ${brain.blockedCount}개 · 검토 전용 ${brain.reviewOnlyCount}개`}
          />
        </View>
      </CardContainer>

      <CardContainer style={styles.safetyCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.secondaryTitle}>
            데이터 출처 상태
          </AppText>
          <AppText variant="caption">
            Fresh {home.sourceSummary.freshCount} · Stale {home.sourceSummary.staleCount} · Missing {home.sourceSummary.missingCount} · Unknown {home.sourceSummary.unknownCount}
          </AppText>
        </View>
        <View style={styles.sourceBadgeRow}>
          <Badge label="읽기 전용 · read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
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
  return (
    <CardContainer style={styles.heroCard}>
      <View style={styles.heroAmountBlock}>
        <AppText style={styles.heroLabel}>평가금</AppText>
        <View style={styles.evaluationRow}>
          <AppText style={styles.evaluationValue}>{displayMoney(accountValue)}</AppText>
          <AppText style={styles.evaluationUnit}>원</AppText>
        </View>
        <AppText style={styles.changeText}>
          전월 대비 {displayCompactMoney(openPnl)} ({displayCompactPercent(totalReturnPct)})
        </AppText>
      </View>

      <View style={styles.heroDivider} />

      <View style={styles.principalRow}>
        <AppText style={styles.heroLabel}>원금</AppText>
        <AppText style={styles.principalValue}>{displayMoney(investedCash)} 원</AppText>
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
    return MONEY_UNKNOWN;
  }

  return value.toLocaleString("ko-KR");
}

function displaySignedMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return MONEY_UNKNOWN;
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toLocaleString("ko-KR")}원`;
}

function displayCompactMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }

  return displaySignedMoney(value);
}

function displayPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return PERCENT_UNKNOWN;
  }

  return `${value.toFixed(1)}%`;
}

function displaySignedPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return PERCENT_UNKNOWN;
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function displayCompactPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }

  return displaySignedPercent(value);
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
    backgroundColor: "#F6F7F9",
    gap: 32,
    marginHorizontal: 0,
    maxWidth: 390,
    paddingBottom: 32,
    paddingHorizontal: 20,
    paddingTop: 24,
    width: "100%",
  },
  heroCard: {
    ...elevatedCard,
    gap: spacing.md,
    marginTop: 24,
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
    gap: spacing.sm,
  },
  evaluationValue: {
    color: colors.ink,
    fontSize: 38,
    fontWeight: "800",
    lineHeight: 42,
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
    color: colors.ink,
    fontSize: 24,
    fontWeight: "700",
    lineHeight: 30,
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
  },
  kpiLabel: {
    color: colors.mutedInk,
    fontSize: 13,
    fontWeight: "400",
    lineHeight: 16,
  },
  kpiValue: {
    color: colors.ink,
    fontSize: 18,
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
    gap: spacing.md,
    padding: spacing.lg,
  },
  sectionHeader: {
    gap: spacing.xs,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: "700",
    lineHeight: 32,
  },
  secondaryTitle: {
    fontSize: 18,
    fontWeight: "700",
    lineHeight: 24,
  },
  emptyStateCard: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
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
  },
  monthPill: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: 8,
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
    backgroundColor: colors.surfaceMuted,
    borderStyle: "dashed",
    gap: spacing.md,
  },
  attentionList: {
    gap: spacing.md,
  },
  attentionItem: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.md,
  },
  attentionEyebrow: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: mobile.touchTarget,
    minWidth: 56,
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
    borderStyle: "dashed",
    gap: spacing.md,
  },
  sourceBadgeRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
});
