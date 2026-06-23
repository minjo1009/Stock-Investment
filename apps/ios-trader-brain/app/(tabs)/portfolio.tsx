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
  SourceFreshnessBadge,
  StatusRow,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { portfolioFixture } from "../../src/read-models/portfolioFixture";
import { spacing } from "../../src/theme/tokens";

export default function PortfolioRoute() {
  const portfolio = portfolioFixture;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="PORTFOLIO v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">PORTFOLIO</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Position rows are not broker truth or
          account truth.
        </AppText>
      </View>

      <MobileV1StatusRail
        items={[
          { label: "Positions", value: portfolio.positions.length, tone: "readOnly" },
          { label: "Broker", value: "not truth", tone: "blocked" },
          { label: "Unknown", value: portfolio.sourceSummary.unknownCount, tone: "unknown" },
        ]}
        subtitle="Phone-first v1"
        title="Portfolio values remain non-authority"
      />

      <FreshnessBanner
        generatedAt={portfolio.generatedAt}
        sourceSummary={portfolio.sourceSummary}
        title="Portfolio source and broker truth remain non-authority"
      />

      <ScreenSummary
        badges={[
          { label: "fixture-backed", tone: "readOnly" },
          { label: "broker truth blocked", tone: "blocked" },
          { label: portfolio.governance.strategyAcceptance, tone: "blocked" },
        ]}
        description="Read-only holdings surface for reviewing position-shaped data before any authoritative account path exists."
        footer="Null broker/account values remain UNKNOWN and are never rendered as zero."
        links={[
          {
            href: "/portfolio/position/fixture-position-unknown",
            label: "Open sample position detail",
            helperText: "Inspect broker-truth blockers and reconciliation state.",
          },
          {
            href: "/orders",
            label: "Review order lifecycle",
            helperText: "Compare position blockers with order blockers.",
          },
        ]}
        metrics={[
          { label: "Positions", value: portfolio.positions.length, state: "readOnly" },
          { label: "Fresh", value: portfolio.sourceSummary.freshCount, state: "fresh" },
          { label: "Missing", value: portfolio.sourceSummary.missingCount, state: "missing" },
          { label: "Unknown", value: portfolio.sourceSummary.unknownCount, state: "unknown" },
        ]}
        title="Read-only portfolio review"
      />

      <SectionContainer title="Holdings Requiring Review" description="Position rows show inspection blockers, not broker truth or performance.">
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
                hrefLabel="Open read-only position detail"
                metrics={[
                  { label: "Broker truth", value: position.brokerTruthState, state: "blocked" },
                  { label: "Sources", value: position.sourceStates.length, state: "readOnly" },
                  { label: "Blockers", value: position.blockers.length, state: "blocked" },
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

      <SectionContainer title="Governance Boundary" description="Broker truth remains blocked.">
        <StatusRow
          label="Strategy"
          value={`Strategy ${portfolio.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={portfolio.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${portfolio.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={portfolio.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${portfolio.governance.realCapital}`}
          state="blocked"
          sourceRef={portfolio.governance.controlStateSource}
        />
        <BlockerList blockers={portfolio.blockers} />
      </SectionContainer>

      <SectionContainer title="Disabled Actions" description="Broker sync is visible only as disabled.">
        <DisabledActionBar actions={portfolio.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}
