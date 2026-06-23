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

  const metricRows = [
    {
      label: "투자금",
      value: displayMoney(portfolio.investedCash),
      state: "확인 필요",
    },
    {
      label: "현금",
      value: displayMoney(portfolio.cash),
      state: "확인 필요",
    },
    {
      label: "수익현황",
      value: displayPercent(portfolio.totalReturnPct),
      state: "QQQ 비교 대기",
    },
    {
      label: "승률현황",
      value: displayPercent(portfolio.winRatePct),
      state: "집계 대기",
    },
    {
      label: "MDD",
      value: displayPercent(portfolio.maxDrawdownPct),
      state: "차트 연결 대기",
    },
  ];

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <View style={styles.header}>
        <View style={styles.statusRow}>
          <Badge label="읽기 전용 · read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
          <Badge label="모바일 우선" tone="readOnly" />
        </View>
        <View style={styles.headerCopy}>
          <AppText variant="caption">오늘의 계좌현황</AppText>
          <AppText variant="title" style={styles.pageTitle}>
            포트폴리오 운영 대시보드
          </AppText>
          <AppText variant="caption" style={styles.pageDescription}>
            계좌, 수익, 위험을 먼저 보고 출처와 권한 상태는 아래에서 확인합니다.
          </AppText>
        </View>
      </View>

      <CardContainer style={styles.heroCard}>
        <View style={styles.heroTop}>
          <View style={styles.heroCopy}>
            <AppText variant="caption">계좌 평가액</AppText>
            <AppText style={styles.primaryFigure}>{displayMoney(portfolio.accountValue)}</AppText>
            <AppText variant="caption">
              브로커 원장과 연결되기 전까지 실제 잔고로 해석하지 않습니다.
            </AppText>
          </View>
          <View style={styles.heroPill}>
            <AppText variant="caption" style={styles.heroPillText}>
              {portfolio.sourceState.freshnessStatus}
            </AppText>
          </View>
        </View>

        <View style={styles.metricGrid}>
          {metricRows.map((metric) => (
            <View key={metric.label} style={styles.metricTile}>
              <AppText variant="caption">{metric.label}</AppText>
              <AppText style={styles.metricValue}>{metric.value}</AppText>
              <AppText variant="caption">{metric.state}</AppText>
            </View>
          ))}
        </View>
      </CardContainer>

      <HomeRelativeReturnChartCard chart={home.relativeReturnChart} />

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.sectionTitle}>
            오늘 확인할 것
          </AppText>
          <AppText variant="caption">
            단순 이동 링크가 아니라 지금 막힌 원인과 확인 순서를 보여줍니다.
          </AppText>
        </View>

        <View style={styles.attentionList}>
          <AttentionItem
            eyebrow="수익 차트"
            title="QQQ 대비 수익과 MDD 소스 연결 필요"
            body={home.relativeReturnChart.sourceState.blockerReason}
            meta="가짜 차트는 표시하지 않습니다"
          />
          <AttentionItem
            eyebrow="브레인"
            title="후보 상태와 차단 사유 확인"
            body={brain.sourceState.blockerReason}
            meta={`후보 ${brain.candidateCount}개 · 차단 ${brain.blockedCount}개 · 검토 전용 ${brain.reviewOnlyCount}개`}
          />
          {home.attentionQueue.map((item) => (
            <AttentionItem
              key={item.itemId}
              eyebrow={item.severity}
              title={item.label}
              body={item.reason}
              meta="출처가 부족한 항목은 판단 보류로 유지합니다"
            />
          ))}
        </View>
      </CardContainer>

      <CardContainer style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <AppText variant="title" style={styles.sectionTitle}>
            데이터 출처 상태
          </AppText>
          <AppText variant="caption">
            최신성·누락·불명 상태는 보조 정보로 유지하며 투자 판단 근거로 승격하지 않습니다.
          </AppText>
        </View>
        <View style={styles.sourceBadgeRow}>
          <SourceFreshnessBadge compact sourceState={portfolio.sourceState} />
          <SourceFreshnessBadge compact sourceState={home.relativeReturnChart.sourceState} />
          <SourceFreshnessBadge compact sourceState={brain.sourceState} />
        </View>
        <View style={styles.sourceSummaryRow}>
          <MiniCount label="Fresh" value={home.sourceSummary.freshCount} />
          <MiniCount label="Stale" value={home.sourceSummary.staleCount} />
          <MiniCount label="Missing" value={home.sourceSummary.missingCount} />
          <MiniCount label="Unknown" value={home.sourceSummary.unknownCount} />
        </View>
      </CardContainer>

      <CardContainer style={styles.safetyCard}>
        <AppText variant="caption">
          read-only · Scaffold-only · 브로커 변경 없음 · paper/live 권한 없음 · 실자본 권한 없음.
        </AppText>
      </CardContainer>
    </ScreenContainer>
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

type MiniCountProps = {
  label: string;
  value: number;
};

function MiniCount({ label, value }: MiniCountProps) {
  return (
    <View style={styles.miniCount}>
      <AppText variant="caption">{label}</AppText>
      <AppText style={styles.miniCountValue}>{value}</AppText>
    </View>
  );
}

function displayMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return MONEY_UNKNOWN;
  }

  return `$${value.toLocaleString("en-US")}`;
}

function displayPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return PERCENT_UNKNOWN;
  }

  return `${value.toFixed(1)}%`;
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
    gap: spacing.xl,
    maxWidth: 342,
    padding: 20,
    paddingBottom: 32,
    width: "100%",
  },
  header: {
    gap: spacing.md,
  },
  statusRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  headerCopy: {
    gap: spacing.xs,
  },
  pageTitle: {
    fontSize: 24,
    lineHeight: 32,
  },
  pageDescription: {
    maxWidth: mobile.contentMaxWidth - 40,
  },
  heroCard: {
    ...elevatedCard,
    gap: spacing.xl,
  },
  heroTop: {
    alignItems: "flex-start",
    flexDirection: "column",
    gap: spacing.md,
  },
  heroCopy: {
    flex: 1,
    gap: spacing.xs,
  },
  primaryFigure: {
    color: colors.ink,
    fontSize: 36,
    fontWeight: "800",
    lineHeight: 44,
  },
  heroPill: {
    backgroundColor: colors.unknownSurface,
    borderColor: colors.unknownBorder,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: mobile.touchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  heroPillText: {
    color: colors.mutedInk,
    fontWeight: "700",
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  metricTile: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexBasis: "48%",
    flexGrow: 1,
    gap: spacing.xs,
    minHeight: 92,
    padding: spacing.md,
  },
  metricValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
  },
  sectionCard: {
    ...elevatedCard,
  },
  sectionHeader: {
    gap: spacing.xs,
  },
  sectionTitle: {
    fontSize: 24,
    lineHeight: 32,
  },
  attentionList: {
    gap: spacing.md,
  },
  attentionItem: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
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
  sourceBadgeRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  sourceSummaryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  miniCount: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexBasis: "22%",
    flexGrow: 1,
    gap: spacing.xs,
    minHeight: 68,
    padding: spacing.sm,
  },
  miniCountValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
  },
  safetyCard: {
    backgroundColor: colors.surfaceMuted,
    borderStyle: "dashed",
  },
});
