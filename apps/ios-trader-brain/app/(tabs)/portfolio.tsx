import { View } from "react-native";

import {
  DisabledActionBar,
  FreshnessBanner,
  MobileScanListItem,
  MobileV1StatusRail,
  ScreenSummary,
} from "../../src/components/domain";
import { AppText, Badge } from "../../src/components/foundation";
import {
  BlockerList,
  MetricCard,
  SourceFreshnessBadge,
  StatusRow,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { portfolioFixture } from "../../src/read-models/portfolioFixture";
import { spacing } from "../../src/theme/tokens";

export default function PortfolioRoute() {
  const portfolio = portfolioFixture;
  const summary = portfolio.portfolioSummary;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="읽기전용" tone="readOnly" />
          <Badge label="모바일 우선 v1" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">투자 현황</AppText>
        <AppText variant="caption">
          현재 화면은 scaffold-only 보유자산 미리보기입니다. 계좌·손익·위험 값은
          권한 있는 데이터가 없으면 UNKNOWN으로 표시합니다.
        </AppText>
      </View>

      <ScreenSummary
        description="보유자산의 규모, 손익, 위험을 먼저 확인합니다. 값이 없으면 0으로 바꾸지 않습니다."
        footer="UNKNOWN은 아직 권한 있는 계좌 근거가 없다는 뜻입니다."
        links={[
          {
            href: "/portfolio/position/fixture-position-unknown",
            label: "보유 종목 상세",
            helperText: "포지션의 근거와 차단 상태를 읽기전용으로 봅니다.",
          },
          {
            href: "/orders",
            label: "주문 상태 확인",
            helperText: "포지션과 연결된 주문 차단 상태를 확인합니다.",
          },
        ]}
        metrics={[
          { label: "투자금", value: displayMoney(summary.investedCash), state: "unknown" },
          { label: "현금", value: displayMoney(summary.cash), state: "unknown" },
          { label: "평가금액", value: displayMoney(summary.totalMarketValue), state: "unknown" },
          { label: "평가손익", value: displayMoney(summary.unrealizedPnl), state: "unknown" },
          { label: "실현손익", value: displayMoney(summary.realizedPnl), state: "unknown" },
          { label: "익스포저", value: displayPercent(summary.exposurePct), state: "unknown" },
          { label: "MDD", value: displayPercent(summary.maxDrawdownPct), state: "unknown" },
          { label: "승률", value: displayPercent(summary.winRatePct), state: "unknown" },
        ]}
        title="보유자산 요약"
      />

      <MobileV1StatusRail
        items={[
          { label: "보유 종목", value: displayCount(summary.positionCount), tone: "readOnly" },
          { label: "계좌 상태", value: "UNKNOWN", tone: "unknown" },
          { label: "확인 필요", value: portfolio.sourceSummary.unknownCount, tone: "unknown" },
        ]}
        subtitle="Phone-first v1 / 모바일 우선 v1"
        title="읽기전용 포트폴리오"
      />

      <SectionContainer title="보유 종목" description="보유 행은 계좌 진실이 아니라 읽기전용 검토 행입니다.">
        <View style={{ gap: spacing.sm }}>
          {portfolio.positions.map((position) => (
            <View key={position.positionId} style={{ gap: spacing.sm }}>
              <MobileScanListItem
                badges={[
                  { label: position.thesisState, tone: "unknown" },
                  { label: position.brokerTruthState, tone: "blocked" },
                ]}
                body="Position row is fixture-backed and cannot prove account or broker truth."
                href={position.route}
                hrefLabel="읽기전용 상세 열기"
                metrics={[
                  { label: "보유수량", value: displayMoney(position.quantity), state: "unknown" },
                  { label: "평가금액", value: displayMoney(position.marketValue), state: "unknown" },
                  { label: "평가손익", value: displayMoney(position.unrealizedPnl), state: "unknown" },
                ]}
                sourceRefs={position.sourceStates.flatMap((sourceState) => sourceState.provenanceRefs)}
                subtitle={position.positionId}
                title={position.symbol}
              />
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {position.sourceStates.map((sourceState) => (
                  <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
                ))}
              </View>
              <BlockerList blockers={position.blockers} />
            </View>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="데이터 상태" description="보조 정보입니다. 출처 상태는 계좌·손익 요약 뒤에서 확인합니다.">
        <FreshnessBanner
          generatedAt={portfolio.generatedAt}
          sourceSummary={portfolio.sourceSummary}
          title="포트폴리오 데이터 상태"
        />
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="정상" value={portfolio.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="오래됨" value={portfolio.sourceSummary.staleCount} state="stale" />
          <MetricCard label="누락" value={portfolio.sourceSummary.missingCount} state="missing" />
          <MetricCard label="UNKNOWN" value={portfolio.sourceSummary.unknownCount} state="unknown" />
        </View>
      </SectionContainer>

      <SectionContainer title="운영 제한 상태" description="브로커와 권한 상태는 보조 안전 정보로 유지합니다.">
        <StatusRow
          label="전략 상태"
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

      <SectionContainer title="비활성화된 기능" description="브로커 동기화와 거래 변경 기능은 계속 비활성입니다.">
        <DisabledActionBar actions={portfolio.disabledActions} />
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

function displayCount(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return value;
}
