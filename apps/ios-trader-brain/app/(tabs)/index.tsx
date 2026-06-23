import { View } from "react-native";

import {
  FreshnessBanner,
  HomeRelativeReturnChartCard,
  ReviewCard,
  ScreenSummary,
} from "../../src/components/domain";
import { AppText, Badge } from "../../src/components/foundation";
import { SourceFreshnessBadge } from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { homeFixture } from "../../src/read-models/homeFixture";
import { spacing } from "../../src/theme/tokens";

export default function HomeRoute() {
  const home = homeFixture;
  const portfolioSnapshot = home.portfolioSnapshot;
  const brainSnapshot = home.brainSnapshot;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="읽기전용" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
          <Badge label="모바일 우선" tone="readOnly" />
        </View>
        <AppText variant="title">투자 현황</AppText>
        <AppText variant="caption">
          계좌, 수익, 위험을 먼저 봅니다. 미연결 값은 UNKNOWN입니다.
        </AppText>
      </View>

      <ScreenSummary
        badges={[
          { label: "read-only", tone: "readOnly" },
          { label: "no broker mutation", tone: "blocked" },
        ]}
        description="투자금과 계좌 상태를 먼저 봅니다."
        footer="참고 화면입니다. 거래 권한은 없습니다."
        fullWidthMetrics
        metrics={[
          { label: "투자금", value: displayMoney(portfolioSnapshot.investedCash), state: "unknown" },
          { label: "계좌현황", value: displayMoney(portfolioSnapshot.accountValue), state: "unknown" },
          { label: "승률현황", value: displayPercent(portfolioSnapshot.winRatePct), state: "unknown" },
        ]}
        title="오늘의 투자 요약"
      />

      <HomeRelativeReturnChartCard chart={home.relativeReturnChart} />

      <SectionContainer
        description="이동 링크만 나열하지 않고, 지금 확인해야 할 상태와 이유를 먼저 보여줍니다."
        title="오늘 확인할 것"
      >
        <View style={{ gap: spacing.sm }}>
          <ReviewCard
            badges={[
              { label: "P1", tone: "missing" },
              { label: "수익현황", tone: "readOnly" },
            ]}
            body={home.relativeReturnChart.sourceState.blockerReason}
            href="/system"
            hrefLabel="출처 상태 확인"
            subtitle="QQQ 비교 수익과 MDD 차트는 권위 있는 시계열 연결 전까지 미표시됩니다."
            title="차트 소스 연결 필요"
          />

          <ReviewCard
            badges={[
              { label: "후보", tone: "readOnly" },
              { label: brainSnapshot.sourceState.freshnessStatus, tone: "stale" },
            ]}
            body={brainSnapshot.sourceState.blockerReason}
            href="/brain"
            hrefLabel="후보 상태 확인"
            metrics={[
              { label: "검토후보", value: brainSnapshot.candidateCount, state: "readOnly" },
              { label: "차단", value: brainSnapshot.blockedCount, state: "blocked" },
              { label: "읽기전용", value: brainSnapshot.reviewOnlyCount, state: "readOnly" },
            ]}
            subtitle="후보 수와 차단 상태를 먼저 봅니다."
            title="후보 검토 상태"
          />

          {home.attentionQueue.map((item) => (
            <ReviewCard
              key={item.itemId}
              badges={[
                { label: item.severity, tone: "blocked" },
                { label: item.kind, tone: "readOnly" },
              ]}
              body={item.reason}
              href={item.route}
              hrefLabel="상태 확인"
              subtitle="출처가 부족한 항목은 판단 보류 상태로 유지됩니다."
              title={item.label}
            />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer
        description="출처 상태는 보조 계층으로 유지합니다. 신선도는 매매 승인이나 전략 검증이 아닙니다."
        title="데이터 상태"
      >
        <FreshnessBanner
          generatedAt={home.generatedAt}
          sourceSummary={home.sourceSummary}
          title="출처 상태"
        />
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <SourceFreshnessBadge sourceState={portfolioSnapshot.sourceState} />
          <SourceFreshnessBadge sourceState={home.relativeReturnChart.sourceState} />
        </View>
      </SectionContainer>
    </ScreenContainer>
  );
}

function displayMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return value;
}

function displayPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return `${value}%`;
}
