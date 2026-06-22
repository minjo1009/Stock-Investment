import { Badge } from "../components/foundation";
import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

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

export const StaleUnknown: Story = {
  args: {
    label: "Unknown source",
    tone: "neutral",
  },
};
