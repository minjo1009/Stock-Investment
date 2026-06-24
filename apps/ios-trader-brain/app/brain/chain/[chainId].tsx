import { Link, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, View } from "react-native";

import { DisabledActionBar, MobileV1StatusRail, SourceAttributionCard } from "../../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../../src/components/foundation";
import { BlockerList, StatusRow } from "../../../src/components/generic";
import { NavigationContextBar, ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { chainDetailFixture } from "../../../src/read-models/chainDetailFixture";
import { spacing } from "../../../src/theme/tokens";

const keyPoints = [
  "AI 서버 증설 계획이 유지된다는 표현이 반복됩니다. (긍정적)",
  "전력과 냉각 인프라가 병목으로 언급됩니다. (긍정적)",
  "지역별 허가와 규제 속도는 다르게 나타납니다. (주의)",
  "원문 연결이 완전하지 않은 항목은 판단을 확정하지 않습니다. (차단)",
];

const sourceText =
  "이 영역은 원문 전문이 연결될 자리입니다. 현재 화면은 fixture-backed read-only 상태이므로 실제 기사 전문, IR 문서, 기자명, 외부 URL을 권위 데이터로 주장하지 않습니다. 원문이 연결되면 문단, 핵심 수치, 중요한 문장을 그대로 보여주고 브레인의 해석과 분리해 표시합니다.";

export default function ChainDetailRoute() {
  const params = useLocalSearchParams<{ chainId?: string }>();
  const chain = chainDetailFixture;
  const routeChainId = Array.isArray(params.chainId) ? params.chainId[0] : params.chainId;
  const routeMismatch = routeChainId !== undefined && routeChainId !== chain.chainId;

  return (
    <ScreenContainer contentContainerStyle={styles.screen}>
      <NavigationContextBar
        crumbs={[
          { href: "/", label: "홈" },
          { href: "/brain", label: "브레인" },
          { href: "/brain/candidate/fixture-candidate-review", label: "후보 상세" },
          { label: "근거 상세" },
        ]}
        note="원문과 해석은 분리해서 표시합니다. fixture-backed read-only. NOT_AUTHORITY."
      />

      <CardContainer style={styles.headerCard}>
        <View style={styles.headerTop}>
          <View style={styles.headerText}>
            <AppText variant="caption">근거 상세</AppText>
            <AppText style={styles.title}>대형 클라우드 기업의 AI 인프라 투자 발언</AppText>
            <AppText variant="caption">공식 IR · 발행일 미확정 · 기자명/회사명 대기</AppText>
          </View>
          <Badge label="원문 대기" tone="unknown" />
        </View>
        <Link href="/brain">
          <AppText variant="caption" style={styles.linkText}>
            브레인 홈으로 돌아가기
          </AppText>
        </Link>
      </CardContainer>

      <SectionContainer title="요약" description="원문에서 먼저 확인할 내용입니다.">
        <CardContainer style={styles.summaryCard}>
          <AppText style={styles.summaryText}>
            AI 인프라 투자가 유지될 가능성이 언급됐고, 데이터센터 전력·냉각 병목이 함께 부각됩니다.
          </AppText>
          <View style={styles.interpretationBox}>
            <AppText style={styles.interpretationText}>
              브레인 해석: 이 소식은 단기 가격보다 인프라 공급망의 중기 수요를 확인하는 자료로 보는 편이 적절합니다.
            </AppText>
          </View>
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="핵심 포인트" description="문서에서 눈여겨볼 문장과 의미입니다.">
        <View style={styles.cardStack}>
          {keyPoints.map((point) => (
            <CardContainer key={point} style={styles.pointCard}>
              <AppText style={styles.pointBullet}>• {point}</AppText>
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="브레인 해석과 예측" description="원문과 분리된 해석 영역입니다.">
        <CardContainer style={styles.deepInterpretation}>
          <AppText style={styles.paragraph}>
            경제적으로는 AI 인프라 투자가 전력, 냉각, 서버 부품으로 파급되는지 확인하는 자료입니다.
            정치적으로는 전력 사용량 규제와 지역별 허가 속도가 성장 속도를 제한할 수 있습니다.
          </AppText>
          <AppText style={styles.paragraph}>
            가격 움직임은 아직 예측으로 확정하지 않습니다. 출처와 시간 기준이 연결되기 전까지는
            후보 검토와 위험 관찰 수준에 머물러야 합니다.
          </AppText>
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="원문 전문" description="권위 원문이 붙으면 이 영역에 그대로 표시합니다.">
        <CardContainer style={styles.sourceCard}>
          <ScrollView style={styles.sourceBox} nestedScrollEnabled>
            <AppText style={styles.sourceText}>{sourceText}</AppText>
          </ScrollView>
          <View style={styles.copyHint}>
            <Badge label="텍스트 복사 준비 중" tone="disabled" />
            <Badge label="외부 링크 대기" tone="unknown" />
          </View>
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="보조 확인" description="출처와 권한 상태는 하단에서 확인합니다.">
        <MobileV1StatusRail
          items={[
            { label: "계층", value: chain.layers.length, tone: "readOnly" },
            { label: "출처", value: "대기", tone: "unknown" },
            { label: "권한", value: "읽기 전용", tone: "readOnly" },
          ]}
          subtitle="Evidence Detail v5 / read-only / NOT_AUTHORITY"
          title="근거 상세 상태"
        />
        <SourceAttributionCard
          authority="Fixture evidence detail; not source authority"
          sourceRefs={chain.layers.flatMap((layer) => layer.provenanceRefs)}
          status="BLOCKER"
          timestamp={chain.generatedAt}
          title="원문 출처 상태"
        />
        <StatusRow
          label="Route chainId"
          value={routeChainId ?? "UNKNOWN"}
          state={routeMismatch ? "blocked" : "readOnly"}
        />
        <StatusRow
          label="전략 상태"
          value={`Strategy ${chain.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={chain.governance.controlStateSource}
        />
        <StatusRow
          label="실계좌"
          value={`Real capital ${chain.governance.realCapital}`}
          state="blocked"
          sourceRef={chain.governance.controlStateSource}
        />
        <BlockerList blockers={chain.blockers} />
        <DisabledActionBar actions={chain.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#F9FAFB",
  },
  headerCard: {
    borderColor: "#E5E7EB",
    borderRadius: 16,
  },
  headerTop: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
  headerText: {
    flex: 1,
    gap: spacing.xs,
  },
  title: {
    color: "#1F2937",
    fontSize: 20,
    fontWeight: "800",
    lineHeight: 26,
  },
  linkText: {
    color: "#007C99",
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  summaryCard: {
    borderRadius: 12,
  },
  summaryText: {
    color: "#1F2937",
    fontSize: 16,
    fontWeight: "600",
    lineHeight: 24,
  },
  interpretationBox: {
    backgroundColor: "#EDF2FA",
    borderRadius: 12,
    padding: spacing.md,
  },
  interpretationText: {
    color: "#1F2937",
    fontSize: 14,
    lineHeight: 21,
  },
  cardStack: {
    gap: spacing.md,
  },
  pointCard: {
    borderRadius: 12,
    paddingVertical: spacing.md,
  },
  pointBullet: {
    color: "#374151",
    fontSize: 14,
    lineHeight: 21,
  },
  deepInterpretation: {
    backgroundColor: "#EDF2FA",
    borderColor: "#D7E3F7",
    borderRadius: 12,
  },
  paragraph: {
    color: "#1F2937",
    fontSize: 15,
    lineHeight: 23,
  },
  sourceCard: {
    borderRadius: 12,
  },
  sourceBox: {
    backgroundColor: "#F9FAFB",
    borderColor: "#E5E7EB",
    borderRadius: 12,
    borderWidth: 1,
    maxHeight: 220,
    padding: spacing.md,
  },
  sourceText: {
    color: "#374151",
    fontSize: 14,
    lineHeight: 22,
  },
  copyHint: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
});
