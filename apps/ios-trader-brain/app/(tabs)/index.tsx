import { View } from "react-native";

import {
  DisabledActionBar,
  FreshnessBanner,
  MobileV1StatusRail,
  ReviewCard,
  ScreenSummary,
} from "../../src/components/domain";
import { AppText, Badge } from "../../src/components/foundation";
import {
  BlockerList,
  MetricCard,
  SourceFreshnessBadge,
  StatusRow,
  UiStatePanel,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { homeFixture } from "../../src/read-models/homeFixture";
import { spacing } from "../../src/theme/tokens";

export default function HomeRoute() {
  const home = homeFixture;
  const portfolioSnapshot = home.portfolioSnapshot;

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
          현재 화면은 scaffold-only 읽기전용 미리보기입니다. 계좌·수익·위험 정보는
          권한 있는 데이터가 없으면 UNKNOWN으로 표시합니다.
        </AppText>
      </View>

      <ScreenSummary
        description="계좌·수익·위험을 먼저 확인합니다. 값이 없으면 0으로 바꾸지 않고 UNKNOWN으로 둡니다."
        footer="UNKNOWN은 손실이나 실패가 아니라 아직 권한 있는 근거가 없다는 뜻입니다."
        links={[
          {
            href: "/portfolio",
            label: "포트폴리오 보기",
            helperText: "보유·현금·위험 상태를 읽기전용으로 확인합니다.",
          },
          {
            href: "/brain",
            label: "후보 흐름 보기",
            helperText: "오늘 검토할 후보와 차단 사유를 확인합니다.",
          },
        ]}
        metrics={[
          { label: "투자금", value: displayMoney(portfolioSnapshot.investedCash), state: "unknown" },
          { label: "계좌현황", value: displayMoney(portfolioSnapshot.accountValue), state: "unknown" },
          { label: "수익현황", value: displayPercent(portfolioSnapshot.totalReturnPct), state: "unknown" },
          { label: "승률현황", value: displayPercent(portfolioSnapshot.winRatePct), state: "unknown" },
          { label: "MDD", value: displayPercent(portfolioSnapshot.maxDrawdownPct), state: "unknown" },
        ]}
        title="오늘의 투자 요약"
      />

      <MobileV1StatusRail
        items={[
          { label: "화면", value: "읽기전용", tone: "readOnly" },
          { label: "계좌", value: "UNKNOWN", tone: "unknown" },
          { label: "실자본", value: home.governance.realCapital, tone: "blocked" },
        ]}
        subtitle="Phone-first v1 / 모바일 우선 v1"
        title="읽기전용 투자 대시보드"
      />

      <SectionContainer title="오늘 확인할 항목" description="후보·포지션·주문·시스템 중 먼저 볼 항목입니다.">
        <View style={{ gap: spacing.sm }}>
          {[
            { href: "/portfolio", label: "계좌와 보유 확인", subtitle: "현금·투자금·손익·위험을 확인합니다." },
            { href: "/brain", label: "후보 흐름 확인", subtitle: "검토 후보와 차단 사유를 확인합니다." },
            { href: "/orders", label: "주문 상태 확인", subtitle: "실행이 아니라 차단된 주문 상태를 봅니다." },
            { href: "/system", label: "데이터 상태 확인", subtitle: "출처·신선도·운영 제한을 확인합니다." },
          ].map((surface) => (
            <ReviewCard
              key={surface.href}
              badges={[
                { label: "읽기전용", tone: "readOnly" },
                { label: "확인", tone: "unknown" },
              ]}
              body="이동해도 주문·브로커·실자본 동작은 발생하지 않습니다."
              href={surface.href}
              hrefLabel="열기"
              subtitle={surface.subtitle}
              title={surface.label}
            />
          ))}
          {home.attentionQueue.map((item) => (
            <ReviewCard
              key={item.itemId}
              badges={[
                { label: item.severity, tone: "blocked" },
                { label: item.kind, tone: "readOnly" },
              ]}
              body={item.reason}
              href={item.route}
              hrefLabel="읽기전용으로 열기"
              sourceRefs={item.sourceRefs}
              subtitle={item.route}
              title={item.label}
            />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="계좌 스냅샷" description="권한 있는 계좌 데이터가 없으면 UNKNOWN으로 표시합니다.">
        <View style={{ gap: spacing.sm }}>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            <MetricCard label="현금" value={displayMoney(portfolioSnapshot.cash)} state="unknown" />
            <MetricCard label="투자금" value={displayMoney(portfolioSnapshot.investedCash)} state="unknown" />
            <MetricCard label="평가손익" value={displayMoney(portfolioSnapshot.openPnl)} state="unknown" />
            <MetricCard label="실현손익" value={displayMoney(portfolioSnapshot.realizedPnl)} state="unknown" />
          </View>
          <SourceFreshnessBadge sourceState={portfolioSnapshot.sourceState} />
          {portfolioSnapshot.sourceState.blockerReason ? (
            <AppText variant="caption">{portfolioSnapshot.sourceState.blockerReason}</AppText>
          ) : null}
        </View>
      </SectionContainer>

      <SectionContainer title="데이터 상태" description="보조 정보입니다. 신선도는 권한이나 매매 가능 상태가 아닙니다.">
        <FreshnessBanner
          generatedAt={home.generatedAt}
          sourceSummary={home.sourceSummary}
          title="홈 데이터 상태"
        />
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="정상" value={home.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="오래됨" value={home.sourceSummary.staleCount} state="stale" />
          <MetricCard label="누락" value={home.sourceSummary.missingCount} state="missing" />
          <MetricCard label="UNKNOWN" value={home.sourceSummary.unknownCount} state="unknown" />
          <MetricCard label="엄격 게이트 열림" value={home.sourceSummary.strictGateOpenCount} state="blocked" />
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {home.freshnessSummary.map((sourceState) => (
            <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="확인 필요 상태" description="차단과 UNKNOWN은 부정 판단이 아니라 해석 보류 조건입니다.">
        <UiStatePanel
          message="누락, 오래됨, UNKNOWN은 화면에서 계속 보입니다. 이것은 투자 실패 신호가 아니라 해석 차단 조건입니다."
          state="blocked"
          title="UNKNOWN은 손실 판단이 아닙니다"
        />
        <BlockerList blockers={[...home.blockers, ...home.blockerSummary]} />
      </SectionContainer>

      <SectionContainer title="운영 제한 상태" description="보조 안전 정보입니다. 화면 권한을 열지 않습니다.">
        <StatusRow
          label="전략 상태"
          value={`Strategy ${home.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={home.governance.controlStateSource}
        />
        <StatusRow
          label="배포 상태"
          value={`Deployment ${home.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={home.governance.authorityReportPath}
        />
        <StatusRow
          label="실자본"
          value={`Real capital ${home.governance.realCapital}`}
          state="blocked"
          sourceRef={home.governance.controlStateSource}
        />
        <StatusRow
          label="킬스위치"
          value={home.governance.killSwitchActive ? "active" : "inactive"}
          state={home.governance.killSwitchActive ? "blocked" : "unknown"}
        />
      </SectionContainer>

      <SectionContainer title="비활성화된 기능" description="거래 변경 기능은 계속 비활성 상태입니다.">
        <DisabledActionBar actions={home.disabledActions} />
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
