import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { Badge } from "../components/foundation";

const meta = {
  title: "Foundation/Badge",
  component: Badge,
} satisfies Meta<typeof Badge>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: "Review",
  },
};

export const ReadOnly: Story = {
  args: {
    label: "read-only",
    tone: "readOnly",
  },
};

export const Blocked: Story = {
  args: {
    label: "Blocked",
    tone: "blocked",
  },
};

export const Stale: Story = {
  args: {
    label: "Stale",
    tone: "stale",
  },
};

export const Missing: Story = {
  args: {
    label: "Missing",
    tone: "missing",
  },
};

export const Unknown: Story = {
  args: {
    label: "Unknown",
    tone: "unknown",
  },
};

export const DisabledAction: Story = {
  args: {
    label: "Disabled",
    tone: "disabled",
  },
};
