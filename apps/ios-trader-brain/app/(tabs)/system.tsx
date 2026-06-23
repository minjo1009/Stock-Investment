import { View } from "react-native";

import {
  DisabledActionBar,
  MobileV1StatusRail,
  ScreenSummary,
  SystemHealth,
  TimelineList,
} from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { MetricCard, StatusRow } from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { systemHealthFixture } from "../../src/read-models/systemHealthFixture";
import { spacing } from "../../src/theme/tokens";

export default function SystemRoute() {
  const system = systemHealthFixture;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="SYSTEM v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">SYSTEM</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed monitor. Fresh fixture rows do not imply deployment readiness.
        </AppText>
      </View>

      <MobileV1StatusRail
        items={[
          { label: "Run mode", value: system.controlState.runMode, tone: "blocked" },
          { label: "Kill", value: system.controlState.killSwitchActive ? "active" : "unknown", tone: "blocked" },
          { label: "Deploy", value: "not ready", tone: "blocked" },
        ]}
        subtitle="Phone-first v1"
        title="Operating state is diagnostic-only"
      />

      <ScreenSummary
        badges={[
          { label: "fixture-backed", tone: "readOnly" },
          { label: system.controlState.runMode, tone: "blocked" },
          { label: system.controlState.killSwitchActive ? "kill switch active" : "kill switch inactive", tone: "blocked" },
        ]}
        description="Read-only operating monitor for hard-state, freshness, validators, and artifact visibility."
        footer="Fresh fixture rows do not imply strategy acceptance, deployment readiness, or trading permission."
        links={[
          {
            href: "/brain",
            label: "Review candidate surface",
            helperText: "Confirm candidate display remains blocked/read-only.",
          },
          {
            href: "/orders",
            label: "Review order boundary",
            helperText: "Confirm order mutation remains disabled.",
          },
        ]}
        metrics={[
          { label: "Fresh", value: system.sourceSummary.freshCount, state: "fresh" },
          { label: "Stale", value: system.sourceSummary.staleCount, state: "stale" },
          { label: "Missing", value: system.sourceSummary.missingCount, state: "missing" },
          { label: "Unknown", value: system.sourceSummary.unknownCount, state: "unknown" },
        ]}
        title="Operating state review"
      />

      <TimelineList
        items={[
          {
            label: "Hard state",
            value: system.controlState.runMode,
            state: "blocked",
            helperText: system.controlState.sourcePath,
          },
          {
            label: "Kill switch",
            value: system.controlState.killSwitchActive ? "active" : "inactive",
            state: system.controlState.killSwitchActive ? "blocked" : "unknown",
          },
          {
            label: "Authority catalog",
            value: system.artifactHealth.find((artifact) => artifact.artifactId === "backend-authority-catalog")?.status ?? "UNKNOWN",
            state: "unknown",
          },
        ]}
      />

      <SectionContainer title="Operating Boundary" description="Diagnostic-only state remains visible.">
        <StatusRow
          label="Run mode"
          value={system.controlState.runMode}
          state="blocked"
          sourceRef={system.controlState.sourcePath}
        />
        <StatusRow
          label="Kill switch"
          value={system.controlState.killSwitchActive ? "active" : "inactive"}
          state={system.controlState.killSwitchActive ? "blocked" : "unknown"}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${system.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={system.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${system.governance.realCapital}`}
          state="blocked"
          sourceRef={system.governance.controlStateSource}
        />
      </SectionContainer>

      <SectionContainer title="Source State Counts" description="Stale, missing, and unknown are not hidden.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Fresh" value={system.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="Stale" value={system.sourceSummary.staleCount} state="stale" />
          <MetricCard label="Missing" value={system.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown" value={system.sourceSummary.unknownCount} state="unknown" />
        </View>
      </SectionContainer>

      <SystemHealth system={system} />

      <SectionContainer title="Artifact Health" description="Unknown artifacts remain unknown until an authority path exists.">
        <View style={{ gap: spacing.sm }}>
          {system.artifactHealth.map((artifact) => (
            <CardContainer key={artifact.artifactId}>
              <Badge label={artifact.status} tone={artifact.status === "PRESENT" ? "fresh" : "unknown"} />
              <AppText>{artifact.artifactId}</AppText>
              <AppText variant="caption">{artifact.path}</AppText>
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Disabled Actions" description="Live promotion remains disabled.">
        <DisabledActionBar actions={system.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}
