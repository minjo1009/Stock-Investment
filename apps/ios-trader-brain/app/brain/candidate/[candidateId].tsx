import { Link, useLocalSearchParams } from "expo-router";
import { StyleSheet, View } from "react-native";

import { DisabledActionBar, MobileV1StatusRail, SourceAttributionCard } from "../../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../../src/components/foundation";
import { BlockerList, StatusRow } from "../../../src/components/generic";
import { NavigationContextBar, ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { candidateDetailFixture } from "../../../src/read-models/candidateDetailFixture";
import { spacing } from "../../../src/theme/tokens";

const evidenceGroups = [
  {
    title: "주요 근거",
    items: [
      {
        title: "AI 설비투자 확대 발언",
        source: "공식 IR",
        summary: "대형 고객사의 장기 투자 계획이 유지되고 있습니다.",
        strength: "강함",
      },
      {
        title: "전력 인프라 공급 병목",
        source: "산업 뉴스",
        summary: "데이터센터 전력 수요가 병목으로 반복 확인됩니다.",
        strength: "보통",
      },
    ],
  },
  {
    title: "반대 근거",
    items: [
      {
        title: "정책 규제 논의",
        source: "정책 브리핑",
        summary: "지역별 전력 규제가 증설 속도를 늦출 수 있습니다.",
        strength: "보통",
      },
    ],
  },
];

const risks = [
  { title: "정책 불확실성", state: "주의", body: "전력 사용량 규제가 강화되면 투자 속도가 늦어질 수 있습니다." },
  { title: "실적 확인 전 변동성", state: "관망", body: "테마 기대가 먼저 반영된 구간에서는 실적 전 가격 흔들림이 커질 수 있습니다." },
];

const responses = ["추가 검토 필요", "대기 유지", "관찰 강화", "투자일지 기록"];

export default function CandidateDetailRoute() {
  const params = useLocalSearchParams<{ candidateId?: string }>();
  const candidate = candidateDetailFixture;
  const routeCandidateId = Array.isArray(params.candidateId)
    ? params.candidateId[0]
    : params.candidateId;
  const routeMismatch =
    routeCandidateId !== undefined && routeCandidateId !== candidate.candidateId;

  return (
    <ScreenContainer contentContainerStyle={styles.screen}>
      <NavigationContextBar
        crumbs={[
          { href: "/", label: "홈" },
          { href: "/brain", label: "브레인" },
          { label: "후보 상세" },
        ]}
        note="fixture-backed read-only detail. NOT_AUTHORITY."
      />

      <CardContainer style={styles.heroCard}>
        <View style={styles.heroTop}>
          <View>
            <AppText variant="caption">지금의 생각</AppText>
            <AppText style={styles.symbol}>{candidate.symbol}</AppText>
            <AppText variant="caption">AI 인프라 · 전력 장비 테마</AppText>
          </View>
          <Badge label="승격 예정 아님" tone="blocked" />
        </View>
        <View style={styles.decisionBand}>
          <AppText style={styles.decisionText}>검토 유지</AppText>
          <AppText variant="caption">확신 수준 72% · 실적 발표 전 확인 필요</AppText>
        </View>
        <View style={styles.gaugeTrack}>
          <View style={styles.gaugeFill} />
        </View>
      </CardContainer>

      <SectionContainer
        title="해석"
        description="왜 이 후보를 보고 있는지 쉬운 문장으로 정리합니다."
      >
        <CardContainer style={styles.readingCard}>
          <AppText style={styles.paragraph}>
            데이터센터 증설이 이어지면 전력과 냉각 인프라 수요가 함께 커질 가능성이 있습니다.
            이 후보는 그 흐름 안에서 장비 교체와 신규 설치 수요를 받을 수 있는 종목으로 관찰됩니다.
          </AppText>
          <AppText style={styles.paragraph}>
            다만 아직 권위 원문과 실적 연결이 완전히 확인된 상태는 아닙니다. 지금은 판단을 확정하기보다
            원문과 실적 일정을 함께 확인하는 단계입니다.
          </AppText>
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="근거" description="판단을 뒷받침하거나 반박하는 자료입니다.">
        <View style={styles.cardStack}>
          {evidenceGroups.map((group) => (
            <CardContainer key={group.title} style={styles.evidenceGroup}>
              <AppText style={styles.groupTitle}>{group.title}</AppText>
              {group.items.map((item) => (
                <View key={item.title} style={styles.evidenceItem}>
                  <View style={styles.rowBetween}>
                    <AppText style={styles.evidenceTitle}>{item.title}</AppText>
                    <Badge label={item.strength} tone="readOnly" />
                  </View>
                  <AppText variant="caption">
                    {item.source} · {item.summary}
                  </AppText>
                  <Link href="/brain/chain/fixture-chain">
                    <AppText variant="caption" style={styles.linkText}>
                      상세 보기
                    </AppText>
                  </Link>
                </View>
              ))}
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="위험 요인" description="부정적으로 작용할 수 있는 부분입니다.">
        <View style={styles.cardStack}>
          {risks.map((risk) => (
            <CardContainer key={risk.title} style={styles.riskCard}>
              <View style={styles.rowBetween}>
                <AppText style={styles.riskTitle}>{risk.title}</AppText>
                <Badge label={risk.state} tone="stale" />
              </View>
              <AppText variant="caption">{risk.body}</AppText>
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer
        title="대응"
        description="아래 항목은 읽기 전용 제안입니다. 투자일지나 주문 상태를 바꾸지 않습니다."
      >
        <View style={styles.responseGrid}>
          {responses.map((response) => (
            <View key={response} style={styles.responsePill}>
              <AppText style={styles.responseText}>{response}</AppText>
              <AppText variant="caption">disabled · read-only</AppText>
            </View>
          ))}
        </View>
        <DisabledActionBar actions={candidate.disabledActions} />
      </SectionContainer>

      <SectionContainer title="보조 확인" description="권한과 출처 상태는 하단에서만 확인합니다.">
        <MobileV1StatusRail
          items={[
            { label: "상태", value: "검토", tone: "readOnly" },
            { label: "출처", value: "부분", tone: "unknown" },
            { label: "권한", value: "읽기 전용", tone: "readOnly" },
          ]}
          subtitle="Candidate Detail v5 / read-only / NOT_AUTHORITY"
          title="후보 상세 상태"
        />
        <SourceAttributionCard
          authority="Fixture candidate detail; not source authority"
          sourceStates={candidate.sections.risk.sourceStates}
          status="BLOCKER"
          timestamp={candidate.generatedAt}
          title="후보 출처 상태"
        />
        <StatusRow
          label="Route candidateId"
          value={routeCandidateId ?? "UNKNOWN"}
          state={routeMismatch ? "blocked" : "readOnly"}
        />
        <StatusRow
          label="전략 상태"
          value={`Strategy ${candidate.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={candidate.governance.controlStateSource}
        />
        <StatusRow
          label="실계좌"
          value={`Real capital ${candidate.governance.realCapital}`}
          state="blocked"
          sourceRef={candidate.governance.controlStateSource}
        />
        <BlockerList blockers={candidate.blockers} />
      </SectionContainer>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#F9FAFB",
  },
  heroCard: {
    borderColor: "#E5E7EB",
    borderRadius: 16,
  },
  heroTop: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  symbol: {
    color: "#1F2937",
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 30,
  },
  decisionBand: {
    backgroundColor: "#EDF2FA",
    borderRadius: 12,
    gap: spacing.xs,
    padding: spacing.md,
  },
  decisionText: {
    color: "#1F2937",
    fontSize: 20,
    fontWeight: "800",
  },
  gaugeTrack: {
    backgroundColor: "#E5E7EB",
    borderRadius: 999,
    height: 8,
    overflow: "hidden",
  },
  gaugeFill: {
    backgroundColor: "#00A9CE",
    borderRadius: 999,
    height: "100%",
    width: "72%",
  },
  readingCard: {
    borderRadius: 12,
  },
  paragraph: {
    color: "#374151",
    fontSize: 16,
    lineHeight: 24,
  },
  cardStack: {
    gap: spacing.md,
  },
  evidenceGroup: {
    borderRadius: 12,
  },
  groupTitle: {
    color: "#1F2937",
    fontSize: 18,
    fontWeight: "800",
  },
  evidenceItem: {
    borderTopColor: "#E5E7EB",
    borderTopWidth: 1,
    gap: spacing.xs,
    paddingTop: spacing.md,
  },
  rowBetween: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.sm,
  },
  evidenceTitle: {
    color: "#1F2937",
    flex: 1,
    fontSize: 16,
    fontWeight: "700",
  },
  linkText: {
    color: "#007C99",
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  riskCard: {
    borderRadius: 12,
  },
  riskTitle: {
    color: "#1F2937",
    flex: 1,
    fontSize: 16,
    fontWeight: "700",
  },
  responseGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  responsePill: {
    backgroundColor: "#F3F4F6",
    borderColor: "#E5E7EB",
    borderRadius: 12,
    borderWidth: 1,
    minHeight: 44,
    minWidth: 132,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  responseText: {
    color: "#1F2937",
    fontSize: 14,
    fontWeight: "700",
  },
});
