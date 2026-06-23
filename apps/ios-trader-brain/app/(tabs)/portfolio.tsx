import { Link, type Href } from "expo-router";
import { View } from "react-native";

import { DisabledActionBar } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
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
            <CardContainer key={position.positionId}>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                <Badge label={position.thesisState} tone="unknown" />
                <Badge label={position.brokerTruthState} tone="blocked" />
              </View>
              <AppText variant="title">{position.symbol}</AppText>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                <MetricCard label="Quantity" value={displayUnknown(position.quantity)} state="unknown" />
                <MetricCard label="Market value" value={displayUnknown(position.marketValue)} state="unknown" />
                <MetricCard label="Unrealized PnL" value={displayUnknown(position.unrealizedPnl)} state="unknown" />
              </View>
              <AppText variant="caption">Detail hint: {position.route}</AppText>
              <Link href={position.route as Href}>
                <AppText variant="caption">Open read-only position detail</AppText>
              </Link>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {position.sourceStates.map((sourceState) => (
                  <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
                ))}
              </View>
              <BlockerList blockers={position.blockers} />
            </CardContainer>
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
