import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import { DisabledActionBar, MobileV1StatusRail, ScreenSummary, TimelineList } from "../../../src/components/domain";
import { AppText, Badge, CardContainer, type BadgeTone } from "../../../src/components/foundation";
import { BlockerList, MetricCard, StatusRow } from "../../../src/components/generic";
import { ProductDetailHeader, ProductDetailSection, ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { chainDetailFixture } from "../../../src/read-models/chainDetailFixture";
import { spacing } from "../../../src/theme/tokens";

export default function ChainDetailRoute() {
  const params = useLocalSearchParams<{ chainId?: string }>();
  const chain = chainDetailFixture;
  const routeChainId = Array.isArray(params.chainId) ? params.chainId[0] : params.chainId;
  const routeMismatch = routeChainId !== undefined && routeChainId !== chain.chainId;

  return (
    <ScreenContainer>
      <ProductDetailHeader
        badges={[
          { label: "Chain Detail v1", tone: "readOnly" },
          { label: "Read-only", tone: "readOnly" },
          { label: "NOT_AUTHORITY", tone: "blocked" },
        ]}
        description="Scaffold-only fixture-backed chain view. Layer presence is not source authority."
        title={chain.chainId}
      />

      <ProductDetailSection sectionId="overview" title="Overview" description="Read chain identity and layer counts before evidence detail.">
        <MobileV1StatusRail
          items={[
            { label: "Layers", value: chain.layers.length, tone: "readOnly" },
            { label: "Blocked", value: countStatus("BLOCKED"), tone: "blocked" },
            { label: "Unknown", value: countStatus("UNKNOWN"), tone: "unknown" },
          ]}
          subtitle="Product Detail v1"
          title="Evidence chain is review-only"
        />
        <ScreenSummary
          badges={[
            { label: "fixture-backed", tone: "readOnly" },
            { label: routeMismatch ? "route mismatch" : "fixture route", tone: routeMismatch ? "blocked" : "readOnly" },
            { label: chain.governance.strategyAcceptance, tone: "blocked" },
          ]}
          description="Read-only evidence-chain view for checking whether layer, artifact, and provenance references are visible."
          footer="Layer presence is not source authority and cannot authorize a decision."
          links={[
            {
              href: "/brain",
              label: "Back to review queue",
              helperText: "Return to candidate rows.",
            },
            {
              href: "/brain/candidate/fixture-candidate-review",
              label: "Open candidate detail",
              helperText: "Compare chain evidence with the candidate detail frame.",
            },
          ]}
          metrics={[
            { label: "Layers", value: chain.layers.length, state: "readOnly" },
            { label: "Present", value: countStatus("PRESENT"), state: "fresh" },
            { label: "Blocked", value: countStatus("BLOCKED"), state: "blocked" },
            { label: "Unknown", value: countStatus("UNKNOWN"), state: "unknown" },
          ]}
          title="Evidence chain review"
        />

        <TimelineList
          items={chain.layers.map((layer) => ({
            label: layer.layer,
            value: layer.blockerReason ?? "No blocker supplied by fixture.",
            state: statusToComponentState(layer.status),
            helperText: joinOrUnknown(layer.provenanceRefs),
          }))}
        />

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
      </ProductDetailSection>

      <ProductDetailSection sectionId="evidence" title="Evidence" description="This is a review trace, not a trading decision chain.">
        <SectionContainer title="Evidence Chain" description="Fixture-backed evidence layers only.">
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
      </ProductDetailSection>

      <ProductDetailSection sectionId="risk" title="Risk" description="Missing layers remain blockers, not negative evidence.">
        <SectionContainer title="Blocked / Missing Evidence" description="Missing layers remain blockers, not negative evidence.">
          <BlockerList blockers={chain.blockers} />
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="validation" title="Validation" description="Validation counts are fixture display only.">
        <SectionContainer title="Chain Validation" description="Counts are fixture display only.">
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            <MetricCard label="Present" value={countStatus("PRESENT")} state="fresh" />
            <MetricCard label="Stale" value={countStatus("STALE")} state="stale" />
            <MetricCard label="Missing" value={countStatus("MISSING")} state="missing" />
            <MetricCard label="Blocked" value={countStatus("BLOCKED")} state="blocked" />
            <MetricCard label="Unknown" value={countStatus("UNKNOWN")} state="unknown" />
          </View>
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
      </ProductDetailSection>
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

function statusToComponentState(status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN") {
  if (status === "PRESENT") return "fresh";
  if (status === "STALE") return "stale";
  if (status === "MISSING") return "missing";
  if (status === "BLOCKED") return "blocked";
  return "unknown";
}
