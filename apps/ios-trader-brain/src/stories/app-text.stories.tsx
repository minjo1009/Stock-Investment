import { AppText } from "../components/foundation";
import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

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
    children: "read-only",
    variant: "caption",
  },
};

export const Blocked: Story = {
  args: {
    children: "Blocked: requires governance change",
    variant: "body",
  },
};

export const StaleUnknown: Story = {
  args: {
    children: "UNKNOWN_SOURCE_FRESHNESS",
    variant: "caption",
  },
};

export const Title: Story = {
  args: {
    children: "Decision Summary",
    variant: "title",
  },
};
