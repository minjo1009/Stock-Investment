import { View } from "react-native";

import {
  DisabledActionBar,
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

      <SectionContainer title="Portfolio Summary" description="Null account values render as UNKNOWN, not zero.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Positions" value={portfolio.positions.length} state="readOnly" />
          <MetricCard label="Fresh" value={portfolio.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="Stale" value={portfolio.sourceSummary.staleCount} state="stale" />
          <MetricCard label="Missing" value={portfolio.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown" value={portfolio.sourceSummary.unknownCount} state="unknown" />
        </View>
      </SectionContainer>

      <SectionContainer title="Positions" description="Position detail routes are read-only scaffold links.">
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
                  { label: "Quantity", value: displayUnknown(position.quantity), state: "unknown" },
                  { label: "Market value", value: displayUnknown(position.marketValue), state: "unknown" },
                  { label: "Unrealized PnL", value: displayUnknown(position.unrealizedPnl), state: "unknown" },
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

      <SectionContainer title="Disabled Actions" description="Broker sync is visible only as disabled.">
        <DisabledActionBar actions={portfolio.disabledActions} />
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
    </ScreenContainer>
  );
}

function displayUnknown(value: number | null) {
  return value === null ? "UNKNOWN" : value;
}
