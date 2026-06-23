import type { Meta, StoryObj } from "@storybook/react-native-web-vite";
import { View } from "react-native";

import { ReviewCard, ScreenSummary, TimelineList } from "../components/domain";
import { spacing } from "../theme/tokens";

function ScreenSummaryStory({ variant }: { variant: "default" | "blocked" | "stale" | "missing" | "unknown" }) {
  return (
    <View style={{ gap: spacing.md }}>
      <ScreenSummary
        badges={[
          { label: "read-only", tone: "readOnly" },
          { label: variant, tone: variant === "default" ? "readOnly" : variant },
          { label: "NOT_AUTHORITY", tone: "blocked" },
        ]}
        description="Fixture-backed screen summary for Storybook smoke. It has no runtime, broker, or DB connection."
        footer="Missing and stale inputs remain visible and never become negative evidence."
        links={[
          {
            href: "/brain",
            label: "Open review surface",
            helperText: "Read-only route hint for fixture screens.",
          },
        ]}
        metrics={[
          { label: "Rows", value: 2, state: "readOnly" },
          { label: "Blocked", value: variant === "blocked" ? 2 : 1, state: "blocked" },
          { label: "Unknown", value: variant === "unknown" ? "UNKNOWN" : 0, state: "unknown" },
        ]}
        title="Screen summary"
      />

      <ReviewCard
        badges={[
          { label: "review", tone: "readOnly" },
          { label: variant === "default" ? "read-only" : variant, tone: variant === "default" ? "readOnly" : variant },
        ]}
        body="Review card keeps display data separate from authority data."
        href="/system"
        metrics={[
          { label: "Sources", value: 1, state: variant === "stale" ? "stale" : "unknown" },
          { label: "Blockers", value: variant === "blocked" ? 1 : 0, state: variant === "blocked" ? "blocked" : "readOnly" },
        ]}
        sourceRefs={["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"]}
        title="Read-only review card"
      />

      <TimelineList
        items={[
          {
            label: "Authority",
            value: "Fixture data is not authority.",
            state: "blocked",
          },
          {
            label: "Freshness",
            value: variant === "missing" ? "MISSING" : variant.toUpperCase(),
            state: variant === "default" ? "readOnly" : variant,
          },
        ]}
      />
    </View>
  );
}

const meta = {
  title: "Domain/ScreenSummary",
  component: ScreenSummaryStory,
} satisfies Meta<typeof ScreenSummaryStory>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { variant: "default" } };
export const Blocked: Story = { args: { variant: "blocked" } };
export const Stale: Story = { args: { variant: "stale" } };
export const Missing: Story = { args: { variant: "missing" } };
export const Unknown: Story = { args: { variant: "unknown" } };
