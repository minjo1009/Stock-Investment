import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { StatusRow } from "../components/generic";

const meta = {
  title: "Generic/StatusRow",
  component: StatusRow,
} satisfies Meta<typeof StatusRow>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: "Source status",
    value: "Visible status row",
    state: "fresh",
  },
};

export const ReadOnly: Story = {
  args: {
    label: "Frontend mode",
    value: "read-only",
    state: "readOnly",
  },
};

export const Blocked: Story = {
  args: {
    label: "Governance",
    value: "Blocked by current operating state",
    state: "blocked",
    sourceRef: "docs/operating_system/project_operating_state.md",
  },
};

export const Stale: Story = {
  args: {
    label: "Freshness",
    value: "Stale input must stay visible",
    state: "stale",
  },
};

export const Missing: Story = {
  args: {
    label: "Source",
    value: "Missing required source",
    state: "missing",
  },
};

export const Unknown: Story = {
  args: {
    label: "Runtime state",
    value: "Unknown state cannot be inferred",
    state: "unknown",
  },
};

export const DisabledAction: Story = {
  args: {
    label: "Action state",
    value: "Disabled by governance",
    state: "disabled",
  },
};
