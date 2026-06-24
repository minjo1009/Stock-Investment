import { Link } from "expo-router";
import { ScrollView, StyleSheet, View } from "react-native";

import { FreshnessBanner, MobileV1StatusRail } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { BlockerList, StatusRow } from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { brainFixture } from "../../src/read-models/brainFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

const issue = {
  theme: "AI 인프라",
  interpretation:
    "데이터센터 투자가 이어지면서 전력, 냉각, 서버 부품 수요가 함께 커질 가능성이 있습니다.",
  conviction: 78,
  state: "검토",
};

const newsItems = [
  {
    id: "source-ai-capex",
    title: "대형 클라우드 기업의 설비투자 확대 언급",
    source: "공식 IR",
    publishedAt: "오늘 오전",
    summary: "AI 서버와 데이터센터 증설 계획이 다시 확인됐습니다.",
    interpretation: "전력 인프라와 고효율 장비 공급망에는 긍정적인 재료입니다.",
    route: "/brain/chain/fixture-chain" as const,
  },
  {
    id: "source-power-grid",
    title: "전력망 병목과 냉각 수요가 동시 부각",
    source: "산업 뉴스",
    publishedAt: "어제",
    summary: "신규 데이터센터 허가 과정에서 전력 공급 문제가 반복되고 있습니다.",
    interpretation: "단기 수급보다 인프라 병목을 해결하는 기업이 더 주목받을 수 있습니다.",
    route: "/brain/chain/fixture-chain" as const,
  },
  {
    id: "source-policy-risk",
    title: "AI 전력 사용량 규제 논의 확대",
    source: "정책 브리핑",
    publishedAt: "2일 전",
    summary: "일부 지역에서 전력 사용량과 탄소 배출 기준을 강화하는 논의가 나왔습니다.",
    interpretation: "성장 테마는 유지되지만, 지역별 허가 속도는 위험 요인으로 봐야 합니다.",
    route: "/brain/chain/fixture-chain" as const,
  },
];

const relationChains = [
  "전력망 투자 → 데이터센터 증설 → 냉각·전력 장비 관심",
  "금리 안정 → 장기 CAPEX 재개 → 반도체 장비 심리 개선",
  "규제 논의 → 허가 지연 가능성 → 과열 종목 변동성 확대",
];

const candidates = [
  {
    id: "fixture-candidate-review",
    symbol: "FIXA",
    name: "인프라 후보 A",
    description: "전력·냉각 장비",
    state: "검토 유지",
    conviction: 72,
    risk: "공식 출처 연결 전",
    next: "근거 확인",
    route: "/brain/candidate/fixture-candidate-review" as const,
  },
  {
    id: "fixture-candidate-blocked",
    symbol: "FIXB",
    name: "검토 후보 B",
    description: "AI 서버 부품",
    state: "검토 필요",
    conviction: 54,
    risk: "원문 신선도 미확인",
    next: "대기",
    route: "/brain/candidate/fixture-candidate-blocked" as const,
  },
  {
    id: "fixture-candidate-risk",
    symbol: "FIXC",
    name: "주의 후보 C",
    description: "정책 민감주",
    state: "주의",
    conviction: 41,
    risk: "규제 노출",
    next: "추적",
    route: "/brain/candidate/fixture-candidate-review" as const,
  },
];

const risks = [
  {
    title: "정책 불확실성",
    body: "전력 사용량 규제가 강해지면 데이터센터 증설 속도가 늦어질 수 있습니다.",
    tone: "주의",
  },
  {
    title: "수급 변동성",
    body: "단기 급등 종목은 실적 확인 전까지 가격 변동이 커질 수 있습니다.",
    tone: "관망",
  },
  {
    title: "출처 미연결",
    body: "일부 뉴스와 후보는 아직 권위 원문이 연결되지 않아 판단을 확정할 수 없습니다.",
    tone: "차단",
  },
];

export default function BrainRoute() {
  const brain = brainFixture;
  const updatedAt = "최근 업데이트: 오전 9:32";

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <View style={styles.header}>
        <View>
          <AppText variant="title" style={styles.headerTitle}>
            브레인
          </AppText>
          <AppText variant="caption">{updatedAt}</AppText>
        </View>
        <View style={styles.headerIcons}>
          <AppText style={styles.iconText}>⌕</AppText>
        </View>
      </View>

      <CardContainer style={styles.issueCard}>
        <View style={styles.issueHeader}>
          <AppText variant="caption">오늘의 이슈</AppText>
          <AppText style={styles.issueTheme}>{issue.theme}</AppText>
          <Badge label={issue.state} tone="stale" />
        </View>
        <AppText style={styles.issueBody}>{issue.interpretation}</AppText>
        <View style={styles.convictionRow}>
          <AppText style={styles.convictionLabel}>확신 수준</AppText>
          <View style={styles.convictionTrack}>
            <View style={[styles.convictionFill, { width: `${issue.conviction}%` }]} />
          </View>
          <AppText style={styles.convictionValue}>{issue.conviction}%</AppText>
        </View>
      </CardContainer>

      <SectionHeader title="최신 뉴스와 해석" caption="원문 정보와 브레인의 해석을 함께 봅니다." />
      <View style={styles.cardStack}>
        {newsItems.map((item) => (
          <CardContainer key={item.id} style={styles.newsCard}>
            <View style={styles.newsMetaRow}>
              <AppText style={styles.newsTitle} numberOfLines={1}>
                {item.title}
              </AppText>
              <AppText variant="caption">
                {item.source} · {item.publishedAt}
              </AppText>
            </View>
            <AppText style={styles.newsSummary} numberOfLines={2}>
              {item.summary}
            </AppText>
            <View style={styles.interpretationBox}>
              <AppText variant="caption" style={styles.interpretationLabel}>
                브레인 해석
              </AppText>
              <AppText variant="caption" style={styles.interpretationText}>
                {item.interpretation}
              </AppText>
            </View>
            <Link href={item.route}>
              <AppText variant="caption" style={styles.linkText}>
                원문 보기
              </AppText>
            </Link>
          </CardContainer>
        ))}
      </View>

      <SectionHeader title="관계 맵" caption="사건이 어떤 종목과 테마로 이어지는지 봅니다." />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.horizontalRail}>
        {relationChains.map((chain) => (
          <Link key={chain} href="/brain/chain/fixture-chain" style={styles.relationLink}>
            <CardContainer style={styles.relationCard}>
              <AppText numberOfLines={2} style={styles.relationText}>{chain}</AppText>
            </CardContainer>
          </Link>
        ))}
      </ScrollView>

      <SectionHeader title="후보 종목" caption="브레인이 보고 있는 후보를 가볍게 넘겨봅니다." />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.candidateRail}>
        {candidates.map((candidate) => (
          <Link key={candidate.id} href={candidate.route} style={styles.candidateLink}>
            <CardContainer style={styles.candidateCard}>
              <View>
                <AppText style={styles.candidateSymbol}>{candidate.symbol}</AppText>
                <AppText variant="caption" numberOfLines={1}>{candidate.name}</AppText>
                <AppText variant="caption" numberOfLines={1}>{candidate.description}</AppText>
              </View>
              <View style={styles.candidateCenter}>
                <Badge label={candidate.state} tone={candidate.state === "주의" ? "blocked" : "readOnly"} />
                <AppText style={styles.candidateConviction}>{candidate.conviction}%</AppText>
                <View style={styles.miniGauge}>
                  <View style={[styles.miniGaugeFill, { width: `${candidate.conviction}%` }]} />
                </View>
              </View>
              <View>
                <AppText variant="caption">위험: {candidate.risk}</AppText>
                <AppText variant="caption">다음: {candidate.next}</AppText>
              </View>
            </CardContainer>
          </Link>
        ))}
      </ScrollView>

      <SectionHeader title="위험 요약" caption="지금 판단에서 먼저 봐야 할 위험 요인입니다." />
      <View style={styles.cardStack}>
        {risks.map((risk) => (
          <CardContainer key={risk.title} style={styles.riskCard}>
            <View style={styles.riskTitleRow}>
              <AppText style={styles.riskTitle}>{risk.title}</AppText>
              <Badge label={risk.tone} tone={risk.tone === "차단" ? "blocked" : "stale"} />
            </View>
            <AppText variant="caption">{risk.body}</AppText>
          </CardContainer>
        ))}
      </View>

      <SectionContainer
        title="보조 확인"
        description="아래 정보는 화면의 주인공이 아니라, 읽기 전용 상태를 확인하는 보조 계층입니다."
      >
        <MobileV1StatusRail
          items={[
            { label: "후보", value: brain.scannerSummary.candidateCount, tone: "readOnly" },
            { label: "차단", value: brain.scannerSummary.blockedCount, tone: "blocked" },
            { label: "권한", value: "읽기 전용", tone: "readOnly" },
          ]}
          subtitle="Phone-first v1 / read-only / NOT_AUTHORITY"
          title="브레인 화면 상태"
        />
        <FreshnessBanner
          generatedAt={brain.generatedAt}
          sourceSummary={brain.sourceSummary}
          title="데이터 신선도"
        />
        <StatusRow
          label="전략 상태"
          value={`Strategy ${brain.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <StatusRow
          label="실계좌"
          value={`Real capital ${brain.governance.realCapital}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <BlockerList blockers={brain.blockers} />
      </SectionContainer>
    </ScreenContainer>
  );
}

function SectionHeader({ title, caption }: { title: string; caption: string }) {
  return (
    <View style={styles.sectionHeader}>
      <AppText style={styles.sectionTitle}>{title}</AppText>
      <AppText variant="caption">{caption}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#F9FAFB",
    gap: spacing.lg,
    marginHorizontal: 0,
    maxWidth: 390,
    paddingBottom: 32,
    paddingHorizontal: 20,
    paddingTop: 24,
    width: "100%",
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 56,
    paddingHorizontal: 16,
  },
  headerTitle: {
    color: "#1F2937",
  },
  headerIcons: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  iconText: {
    fontSize: 20,
    minHeight: mobile.touchTarget,
    minWidth: mobile.touchTarget,
    textAlign: "center",
    textAlignVertical: "center",
  },
  issueCard: {
    borderColor: "#E5E7EB",
    borderRadius: 16,
    minHeight: 120,
    padding: spacing.lg,
  },
  issueHeader: {
    alignItems: "stretch",
    flexDirection: "column",
    gap: spacing.md,
  },
  issueTheme: {
    color: "#1F2937",
    fontSize: 20,
    fontWeight: "800",
    lineHeight: 26,
  },
  issueBody: {
    color: "#374151",
    fontSize: 14,
    lineHeight: 20,
  },
  convictionRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
  },
  convictionLabel: {
    color: "#6B7280",
    fontSize: 13,
    fontWeight: "600",
    minWidth: 56,
  },
  convictionTrack: {
    backgroundColor: "#E5E7EB",
    borderRadius: 999,
    flex: 1,
    height: 8,
    overflow: "hidden",
  },
  convictionFill: {
    backgroundColor: "#00A9CE",
    borderRadius: 999,
    height: "100%",
  },
  convictionValue: {
    color: "#1F2937",
    fontSize: 16,
    fontWeight: "700",
    minWidth: 36,
    textAlign: "right",
  },
  sectionHeader: {
    gap: spacing.xs,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    color: "#1F2937",
    fontSize: 20,
    fontWeight: "800",
    lineHeight: 26,
  },
  cardStack: {
    gap: spacing.md,
  },
  newsCard: {
    borderColor: "#E5E7EB",
    borderRadius: 12,
    minHeight: 140,
    maxWidth: "100%",
    overflow: "hidden",
  },
  newsMetaRow: {
    gap: spacing.xs,
    minWidth: 0,
  },
  newsTitle: {
    color: "#1F2937",
    flexShrink: 1,
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 22,
  },
  newsSummary: {
    color: "#374151",
    fontSize: 14,
    lineHeight: 20,
  },
  interpretationBox: {
    backgroundColor: "#F3F4F6",
    borderRadius: 12,
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
  },
  interpretationLabel: {
    color: "#374151",
    fontWeight: "800",
  },
  interpretationText: {
    color: "#374151",
    flexShrink: 1,
    lineHeight: 18,
  },
  linkText: {
    color: "#007C99",
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  horizontalRail: {
    gap: spacing.md,
    paddingRight: spacing.lg,
  },
  relationLink: {
    textDecorationLine: "none",
  },
  relationCard: {
    borderColor: "#E5E7EB",
    borderRadius: 16,
    minHeight: 80,
    width: 300,
  },
  relationText: {
    color: "#1F2937",
    fontSize: 15,
    fontWeight: "700",
    lineHeight: 22,
  },
  candidateRail: {
    gap: spacing.md,
    paddingRight: spacing.lg,
  },
  candidateLink: {
    textDecorationLine: "none",
  },
  candidateCard: {
    borderColor: "#E5E7EB",
    borderRadius: 16,
    height: 200,
    justifyContent: "space-between",
    width: 152,
  },
  candidateSymbol: {
    color: "#1F2937",
    fontSize: 18,
    fontWeight: "800",
  },
  candidateCenter: {
    gap: spacing.sm,
    alignItems: "flex-start",
  },
  candidateConviction: {
    color: "#1F2937",
    fontSize: 18,
    fontWeight: "800",
  },
  miniGauge: {
    backgroundColor: "#E5E7EB",
    borderRadius: 999,
    height: 6,
    overflow: "hidden",
  },
  miniGaugeFill: {
    backgroundColor: "#00A9CE",
    borderRadius: 999,
    height: "100%",
  },
  riskCard: {
    backgroundColor: colors.surface,
    borderColor: "#E5E7EB",
    borderRadius: 12,
  },
  riskTitleRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.sm,
  },
  riskTitle: {
    color: "#1F2937",
    fontSize: 16,
    fontWeight: "700",
  },
});
