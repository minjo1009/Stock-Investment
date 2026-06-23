import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import { DisabledActionBar } from "../../../src/components/domain";
import { AppText, Badge, CardContainer, type BadgeTone } from "../../../src/components/foundation";
import { BlockerList, MetricCard, StatusRow } from "../../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { chainDetailFixture } from "../../../src/read-models/chainDetailFixture";
import { spacing } from "../../../src/theme/tokens";

export default function ChainDetailRoute() {
  const params = useLocalSearchParams<{ chainId?: string }>();
  const chain = chainDetailFixture;
  const routeChainId = Array.isArray(params.chainId) ? params.chainId[0] : params.chainId;
  const routeMismatch = routeChainId !== undefined && routeChainId !== chain.chainId;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="Chain Detail v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">{chain.chainId}</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed chain view. Layer presence is not source authority.
        </AppText>
      </View>

      <SectionContainer title="Chain Summary" description="Layer presence is display evidence, not authority.">
        <StatusRow label="Chain ID" value={chain.chainId} state="readOnly" />
        <StatusRow
          label="Route match"
          value={routeMismatch ? "ROUTE_MISMATCH" : "FIXTURE_ROUTE"}
          state={routeMismatch ? "blocked" : "readOnly"}
        />
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Layers" value={chain.layers.length} state="readOnly" />
          <MetricCard label="Present" value={countStatus("PRESENT")} state="fresh" />
          <MetricCard label="Blocked" value={countStatus("BLOCKED")} state="blocked" />
          <MetricCard label="Missing" value={countStatus("MISSING")} state="missing" />
          <MetricCard label="Unknown" value={countStatus("UNKNOWN")} state="unknown" />
        </View>
      </SectionContainer>

      <SectionContainer title="Chain Validation" description="Counts are fixture display only.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Present" value={countStatus("PRESENT")} state="fresh" />
          <MetricCard label="Stale" value={countStatus("STALE")} state="stale" />
          <MetricCard label="Missing" value={countStatus("MISSING")} state="missing" />
          <MetricCard label="Blocked" value={countStatus("BLOCKED")} state="blocked" />
          <MetricCard label="Unknown" value={countStatus("UNKNOWN")} state="unknown" />
        </View>
      </SectionContainer>

      <SectionContainer title="Evidence Chain" description="This is a review trace, not a trading decision chain.">
        <View style={{ gap: spacing.sm }}>
          {chain.layers.map((layer) => (
            <CardContainer key={layer.layer}>
              <Badge label={layer.status} tone={toneForLayerStatus(layer.status)} />
              <AppText variant="title">{layer.layer}</AppText>
              <AppText variant="caption">{layer.blockerReason ?? "No blocker supplied by fixture."}</AppText>
              <AppText variant="caption">Artifacts: {joinOrUnknown(layer.artifactRefs)}</AppText>
              <AppText variant="caption">Provenance: {joinOrUnknown(layer.provenanceRefs)}</AppText>
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Blocked / Missing Evidence" description="Missing layers remain blockers, not negative evidence.">
        <BlockerList blockers={chain.blockers} />
      </SectionContainer>

      <SectionContainer title="Disabled Actions" description="Chain review has no mutation authority.">
        <DisabledActionBar actions={chain.disabledActions} />
      </SectionContainer>

      <SectionContainer title="Scaffold Boundary" description="Route params are display-only.">
        <StatusRow label="Route chainId" value={routeChainId ?? "UNKNOWN"} state={routeMismatch ? "blocked" : "readOnly"} />
        <StatusRow label="Fixture chainId" value={chain.chainId} state="readOnly" />
        <StatusRow
          label="Strategy"
          value={`Strategy ${chain.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={chain.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${chain.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={chain.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${chain.governance.realCapital}`}
          state="blocked"
          sourceRef={chain.governance.controlStateSource}
        />
      </SectionContainer>
    </ScreenContainer>
  );

  function countStatus(status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN") {
    return chain.layers.filter((layer) => layer.status === status).length;
  }
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}

function toneForLayerStatus(status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN"): BadgeTone {
  if (status === "PRESENT") return "fresh";
  if (status === "STALE") return "stale";
  if (status === "MISSING") return "missing";
  if (status === "BLOCKED") return "blocked";
  return "unknown";
}
