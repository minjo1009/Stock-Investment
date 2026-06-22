import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { MetricCard } from "../components/generic";

const meta = {
  title: "Generic/MetricCard",
  component: MetricCard,
} satisfies Meta<typeof MetricCard>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: "Source count",
    value: 3,
    state: "fresh",
  },
};

export const ReadOnly: Story = {
  args: {
    label: "Mode",
    value: "read-only",
    state: "readOnly",
  },
};

export const Blocked: Story = {
  args: {
    helperText: "Governance state blocks action.",
    label: "Gate",
    value: "closed",
    state: "blocked",
  },
};

export const Stale: Story = {
  args: {
    label: "Latest source",
    value: "2026-06-01",
    state: "stale",
  },
};

export const Missing: Story = {
  args: {
    helperText: "Null renders as a dash.",
    label: "Required source count",
    value: null,
    state: "missing",
  },
};

export const Unknown: Story = {
  args: {
    label: "Runtime state",
    value: "UNKNOWN",
    state: "unknown",
  },
};

export const DisabledAction: Story = {
  args: {
    helperText: "Action state is disabled by governance.",
    label: "Action",
    value: "disabled",
    state: "disabled",
  },
};
