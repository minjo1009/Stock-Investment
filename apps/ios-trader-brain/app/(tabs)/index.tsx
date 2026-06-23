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

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="HOME v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">HOME</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Current payload is not backend truth,
          source truth, broker truth, or product readiness evidence.
        </AppText>
      </View>

      <MobileV1StatusRail
        items={[
          { label: "Mode", value: "mobile web", tone: "readOnly" },
          { label: "Broker", value: "blocked", tone: "blocked" },
          { label: "Capital", value: home.governance.realCapital, tone: "blocked" },
        ]}
        subtitle="Phone-first v1"
        title="Read-only cockpit preview"
      />

      <FreshnessBanner
        generatedAt={home.generatedAt}
        sourceSummary={home.sourceSummary}
        title="Home source state is review-only"
      />

      <ScreenSummary
        badges={[
          { label: "fixture-backed", tone: "readOnly" },
          { label: home.governance.strategyAcceptance, tone: "blocked" },
          { label: "kill switch active", tone: "blocked" },
        ]}
        description="Read-only overview for operator scanning. Values are display fixtures until an authority source is selected."
        footer="Missing and stale inputs stay visible and never become negative evidence."
        links={[
          {
            href: "/brain",
            label: "Review candidate queue",
            helperText: "Open the read-only BRAIN queue.",
          },
          {
            href: "/system",
            label: "Check operating state",
            helperText: "Open source, validator, and hard-state status.",
          },
        ]}
        metrics={[
          { label: "Candidates", value: home.brainSnapshot.candidateCount, state: "readOnly" },
          { label: "Blocked items", value: home.brainSnapshot.blockedCount, state: "blocked" },
          { label: "Stale sources", value: home.sourceSummary.staleCount, state: "stale" },
          { label: "Unknown sources", value: home.sourceSummary.unknownCount, state: "unknown" },
        ]}
        title="Morning review surface"
      />

      <SectionContainer title="Attention Required" description="Blocked and unknown items stay visible before any summary comfort.">
        <View style={{ gap: spacing.sm }}>
          {home.attentionQueue.map((item) => (
            <ReviewCard
              key={item.itemId}
              badges={[
                { label: item.severity, tone: "blocked" },
                { label: item.kind, tone: "readOnly" },
              ]}
              body={item.reason}
              href={item.route}
              hrefLabel="Open read-only destination"
              sourceRefs={item.sourceRefs}
              subtitle={item.route}
              title={item.label}
            />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Next Review Surfaces" description="Inspection routes only; no trading permission is implied.">
        <View style={{ gap: spacing.sm }}>
          {[
            { href: "/brain", label: "BRAIN", subtitle: "Candidate and source review queue" },
            { href: "/portfolio", label: "PORTFOLIO", subtitle: "Fixture-backed holdings and risk review" },
            { href: "/orders", label: "ORDERS", subtitle: "Blocked order lifecycle inspection" },
            { href: "/system", label: "SYSTEM", subtitle: "Governance and source state review" },
          ].map((surface) => (
            <ReviewCard
              key={surface.href}
              badges={[
                { label: "read-only", tone: "readOnly" },
                { label: "NOT_AUTHORITY", tone: "blocked" },
              ]}
              body="Open the review surface. This is not a signal, recommendation, or execution path."
              href={surface.href}
              hrefLabel="Open review surface"
              subtitle={surface.subtitle}
              title={surface.label}
            />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Portfolio Snapshot" description="Fixture values stay unknown until an authority path exists.">
        <View style={{ gap: spacing.sm }}>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            <MetricCard label="Account value" value={displayMoney(home.portfolioSnapshot.accountValue)} state="unknown" />
            <MetricCard label="Cash" value={displayMoney(home.portfolioSnapshot.cash)} state="unknown" />
            <MetricCard label="Invested cash" value={displayMoney(home.portfolioSnapshot.investedCash)} state="unknown" />
            <MetricCard label="Open PnL" value={displayMoney(home.portfolioSnapshot.openPnl)} state="unknown" />
            <MetricCard label="Realized PnL" value={displayMoney(home.portfolioSnapshot.realizedPnl)} state="unknown" />
          </View>
          <SourceFreshnessBadge sourceState={home.portfolioSnapshot.sourceState} />
          {home.portfolioSnapshot.sourceState.blockerReason ? (
            <AppText variant="caption">{home.portfolioSnapshot.sourceState.blockerReason}</AppText>
          ) : null}
        </View>
      </SectionContainer>

      <SectionContainer title="Freshness Summary" description="Fresh does not imply permission; stale or missing remains visible.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Fresh" value={home.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="Stale" value={home.sourceSummary.staleCount} state="stale" />
          <MetricCard label="Missing" value={home.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown" value={home.sourceSummary.unknownCount} state="unknown" />
          <MetricCard label="Strict gate open" value={home.sourceSummary.strictGateOpenCount} state="blocked" />
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {home.freshnessSummary.map((sourceState) => (
            <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Blocker Summary" description="Fixture blockers are displayed as blockers, not negative evidence.">
        <UiStatePanel
          message="Missing, stale, and unknown source states stay visible. They are blockers for interpretation, not negative trading evidence."
          state="blocked"
          title="Unknown is not a failed investment view"
        />
        <BlockerList blockers={[...home.blockers, ...home.blockerSummary]} />
      </SectionContainer>

      <SectionContainer title="Governance Boundary" description="Visible hard state for this scaffold screen.">
        <StatusRow
          label="Strategy"
          value={`Strategy ${home.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={home.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${home.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={home.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${home.governance.realCapital}`}
          state="blocked"
          sourceRef={home.governance.controlStateSource}
        />
        <StatusRow
          label="Kill switch"
          value={home.governance.killSwitchActive ? "active" : "inactive"}
          state={home.governance.killSwitchActive ? "blocked" : "unknown"}
        />
      </SectionContainer>

      <SectionContainer title="Disabled Actions" description="Trading mutation remains disabled by governance.">
        <DisabledActionBar actions={home.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}

function displayMoney(value: number | null) {
  if (value === null) {
    return "UNKNOWN";
  }

  return value;
}
