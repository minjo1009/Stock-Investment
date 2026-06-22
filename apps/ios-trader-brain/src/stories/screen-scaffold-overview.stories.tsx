import type { Meta, StoryObj } from "@storybook/react-native-web-vite";
import { View } from "react-native";

import { AppText, Badge, CardContainer } from "../components/foundation";
import { BlockerList, MetricCard } from "../components/generic";
import { SectionContainer } from "../components/layout";
import { brainFixture } from "../read-models/brainFixture";
import { chainDetailFixture } from "../read-models/chainDetailFixture";
import { homeFixture } from "../read-models/homeFixture";
import { orderDetailFixture } from "../read-models/orderDetailFixture";
import { ordersFixture } from "../read-models/ordersFixture";
import { portfolioFixture } from "../read-models/portfolioFixture";
import { positionDetailFixture } from "../read-models/positionDetailFixture";
import { systemHealthFixture } from "../read-models/systemHealthFixture";
import { spacing } from "../theme/tokens";

type OverviewVariant =
  | "default"
  | "freshSource"
  | "staleSource"
  | "missingSource"
  | "unknownSource"
  | "blocked"
  | "disabledAction"
  | "chartMissing"
  | "sourceNotAttached";

function ScreenScaffoldOverview({ variant }: { variant: OverviewVariant }) {
  return (
    <View style={{ gap: spacing.md }}>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <Badge label="Screen scaffold v0" tone="readOnly" />
        <Badge label="Read-only" tone="readOnly" />
        <Badge label="NOT_AUTHORITY" tone="blocked" />
      </View>

      <SectionContainer
        title="Screen Coverage"
        description="Fixture-backed screen assembly coverage for Storybook smoke only."
      >
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Tabs" value={5} state="readOnly" />
          <MetricCard label="Details" value={4} state="readOnly" />
          <MetricCard label="Variant" value={variant} state={stateForVariant(variant)} />
        </View>
      </SectionContainer>

      <SectionContainer title="Tab Fixtures" description="No fixture is source authority.">
        <View style={{ gap: spacing.sm }}>
          <FixtureCard label="HOME" route="/" blockers={homeFixture.blockers.length} />
          <FixtureCard label="BRAIN" route="/brain" blockers={brainFixture.blockers.length} />
          <FixtureCard label="PORTFOLIO" route="/portfolio" blockers={portfolioFixture.blockers.length} />
          <FixtureCard label="ORDERS" route="/orders" blockers={ordersFixture.blockers.length} />
          <FixtureCard label="SYSTEM" route="/system" blockers={systemHealthFixture.blockers.length} />
        </View>
      </SectionContainer>

      <SectionContainer title="Detail Fixtures" description="Route params remain display-only in scaffold mode.">
        <View style={{ gap: spacing.sm }}>
          <FixtureCard
            label="Candidate Detail"
            route="/brain/candidate/fixture-candidate-review"
            blockers={brainFixture.candidates[0]?.blockers.length ?? 0}
          />
          <FixtureCard
            label="Position Detail"
            route="/portfolio/position/fixture-position-unknown"
            blockers={positionDetailFixture.blockers.length}
          />
          <FixtureCard
            label="Order Detail"
            route="/orders/fixture-order-blocked"
            blockers={orderDetailFixture.blockers.length}
          />
          <FixtureCard
            label="Chain Detail"
            route="/brain/chain/fixture-chain"
            blockers={chainDetailFixture.blockers.length}
          />
        </View>
      </SectionContainer>

      <SectionContainer title="Governance Blockers" description="Blocked states are visible, not interpreted.">
        <BlockerList blockers={[...homeFixture.blockers, ...systemHealthFixture.blockers]} />
      </SectionContainer>
    </View>
  );
}

function FixtureCard({
  blockers,
  label,
  route,
}: {
  blockers: number;
  label: string;
  route: string;
}) {
  return (
    <CardContainer>
      <Badge label={blockers > 0 ? "BLOCKED" : "READ_ONLY"} tone={blockers > 0 ? "blocked" : "readOnly"} />
      <AppText variant="title">{label}</AppText>
      <AppText variant="caption">{route}</AppText>
      <MetricCard label="Blockers" value={blockers} state={blockers > 0 ? "blocked" : "readOnly"} />
    </CardContainer>
  );
}

function stateForVariant(variant: OverviewVariant) {
  if (variant === "freshSource") return "fresh";
  if (variant === "staleSource") return "stale";
  if (variant === "missingSource") return "missing";
  if (variant === "blocked" || variant === "disabledAction") return "blocked";
  return "unknown";
}

const meta = {
  title: "Screens/ScaffoldOverview",
  component: ScreenScaffoldOverview,
} satisfies Meta<typeof ScreenScaffoldOverview>;

export default meta;

type Story = StoryObj<typeof meta>;

export const FreshSource: Story = { args: { variant: "freshSource" } };
export const StaleSource: Story = { args: { variant: "staleSource" } };
export const MissingSource: Story = { args: { variant: "missingSource" } };
export const UnknownSource: Story = { args: { variant: "unknownSource" } };
export const Blocked: Story = { args: { variant: "blocked" } };
export const DisabledAction: Story = { args: { variant: "disabledAction" } };
export const ChartMissing: Story = { args: { variant: "chartMissing" } };
export const SourceNotAttached: Story = { args: { variant: "sourceNotAttached" } };
