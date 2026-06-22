import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { AppText } from "../components/foundation";

const meta = {
  title: "Foundation/AppText",
  component: AppText,
} satisfies Meta<typeof AppText>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: "read-only observation text",
  },
};

export const ReadOnly: Story = {
  args: {
    children: "read-only frontend surface",
    variant: "caption",
  },
};

export const Blocked: Story = {
  args: {
    children: "Blocked: requires governance change",
  },
};

export const Stale: Story = {
  args: {
    children: "STALE_SOURCE_FRESHNESS",
    variant: "caption",
  },
};

export const Missing: Story = {
  args: {
    children: "MISSING_SOURCE",
    variant: "caption",
  },
};

export const Unknown: Story = {
  args: {
    children: "UNKNOWN_SOURCE_FRESHNESS",
    variant: "caption",
  },
};

export const DisabledAction: Story = {
  args: {
    children: "Action disabled by governance",
    variant: "caption",
  },
};
