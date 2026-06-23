import { View } from "react-native";

import {
  DisabledActionBar,
  FreshnessBanner,
  MobileScanListItem,
  MobileV1StatusRail,
  ScreenSummary,
} from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import {
  BlockerList,
  MetricCard,
  StatusRow,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { brainFixture } from "../../src/read-models/brainFixture";
import { spacing } from "../../src/theme/tokens";

export default function BrainRoute() {
  const brain = brainFixture;
  const scanner = brain.scannerSummary;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="읽기전용" tone="readOnly" />
          <Badge label="모바일 우선 v1" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">후보 탐색</AppText>
        <AppText variant="caption">
          현재 화면은 scaffold-only 후보 검토 미리보기입니다. 점수·순위·확신도는 만들지 않고,
          후보 상태와 차단 사유만 읽기전용으로 보여줍니다.
        </AppText>
      </View>

      <ScreenSummary
        description="오늘 볼 후보를 먼저 확인합니다. 검토 가능과 차단 상태는 매매 지시가 아닙니다."
        footer="미래 수익률, 실현 라벨, 사후 결과는 후보 정렬에 쓰지 않습니다."
        links={[
          {
            href: "/brain/candidate/fixture-candidate-review",
            label: "검토 후보 상세",
            helperText: "후보의 논리와 근거 상태를 읽기전용으로 봅니다.",
          },
          {
            href: "/brain/chain/fixture-chain",
            label: "근거 체인 보기",
            helperText: "출처와 판단 흐름을 계층별로 확인합니다.",
          },
        ]}
        metrics={[
          { label: "후보 수", value: displayCount(scanner.candidateCount), state: "readOnly" },
          { label: "검토 가능", value: displayCount(scanner.reviewOnlyCount), state: "readOnly" },
          { label: "차단됨", value: displayCount(scanner.blockedCount), state: "blocked" },
          { label: "근거 부족", value: displayCount(scanner.weakEvidenceCount), state: "unknown" },
        ]}
        title="오늘의 후보 검토"
      />

      <MobileV1StatusRail
        items={[
          { label: "후보", value: displayCount(scanner.candidateCount), tone: "readOnly" },
          { label: "차단", value: displayCount(scanner.blockedCount), tone: "blocked" },
          { label: "상태", value: "읽기전용", tone: "readOnly" },
        ]}
        subtitle="Phone-first v1 / 모바일 우선 v1"
        title="후보 검토 대기열"
      />

      <SectionContainer title="검토 대기열" description="후보 행은 매매 지시가 아니라 검토 대상입니다.">
        <View style={{ gap: spacing.sm }}>
          {brain.candidates.map((candidate) => (
            <MobileScanListItem
              key={candidate.candidateId}
              badges={[
                {
                  label: lifecycleLabel(candidate.lifecycleState),
                  tone: candidate.lifecycleState === "BLOCKED" ? "blocked" : "readOnly",
                },
                {
                  label: decisionLabel(candidate.decisionState),
                  tone: candidate.decisionState === "BLOCKED" ? "blocked" : "readOnly",
                },
                {
                  label: validationLabel(candidate.validationState),
                  tone: candidate.validationState === "BLOCKED" ? "blocked" : "unknown",
                },
              ]}
              body={candidate.reasonSummary ?? "UNKNOWN"}
              href={candidate.route}
              hrefLabel="읽기전용 상세 열기"
              metrics={[
                { label: "근거 수준", value: evidenceLabel(candidate.evidenceStrength), state: "unknown" },
                { label: "출처 수", value: candidate.sourceStates.length, state: "readOnly" },
                { label: "확인 필요", value: candidate.blockers.length, state: candidate.blockers.length > 0 ? "blocked" : "readOnly" },
              ]}
              sourceRefs={candidate.sourceStates.flatMap((sourceState) => sourceState.provenanceRefs)}
              subtitle={candidate.displayName}
              title={candidate.symbol}
            />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="근거 상태" description="근거 상태는 보조 정보입니다. UNKNOWN은 부정 판단이 아닙니다.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="누락" value={brain.sourceSummary.missingCount} state="missing" />
          <MetricCard label="확인 불가" value={brain.sourceSummary.unknownCount} state="unknown" />
          <MetricCard label="엄격 게이트 열림" value={brain.sourceSummary.strictGateOpenCount} state="blocked" />
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="최신" value={brain.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="오래됨" value={brain.sourceSummary.staleCount} state="stale" />
        </View>
        <FreshnessBanner
          generatedAt={brain.generatedAt}
          sourceSummary={brain.sourceSummary}
          title="브레인 데이터 상태"
        />
        <CardContainer>
          <Badge label="Forbidden filters" tone="blocked" />
          {brain.filters.forbiddenFilterKeys.map((filterKey) => (
            <AppText key={filterKey} variant="caption">
              {filterKey}
            </AppText>
          ))}
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="운영 제한 상태" description="읽기전용 경계와 권한 상태는 하단에서 확인합니다.">
        <StatusRow
          label="전략 상태"
          value={`Strategy ${brain.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <StatusRow
          label="배포 상태"
          value={`Deployment ${brain.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={brain.governance.authorityReportPath}
        />
        <StatusRow
          label="실자본"
          value={`Real capital ${brain.governance.realCapital}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <BlockerList blockers={brain.blockers} />
      </SectionContainer>

      <SectionContainer title="비활성화된 기능" description="후보 검토는 전략·브로커 상태를 변경하지 않습니다.">
        <DisabledActionBar actions={brain.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}

function displayCount(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "UNKNOWN";
  }

  return value;
}

function lifecycleLabel(value: string) {
  if (value === "REVIEW_ONLY") return "검토 가능";
  if (value === "BLOCKED") return "차단됨";
  return "UNKNOWN";
}

function decisionLabel(value: string) {
  if (value === "REVIEW_ONLY") return "검토";
  if (value === "BLOCKED") return "차단";
  if (value === "NO_TRADE") return "대기";
  return "UNKNOWN";
}

function validationLabel(value: string) {
  if (value === "PARTIAL") return "부분";
  if (value === "BLOCKED") return "차단";
  if (value === "NOT_VALIDATED") return "미검증";
  return "UNKNOWN";
}

function evidenceLabel(value: string) {
  if (value === "PARTIAL") return "부분";
  if (value === "NONE") return "부족";
  if (value === "SOURCE_BACKED") return "출처 있음";
  if (value === "WEAK") return "약함";
  return "UNKNOWN";
}
