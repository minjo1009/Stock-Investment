import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { ProductDetailHeader } from "../components/layout";

const meta = {
  title: "Layout/ProductDetailHeader",
  component: ProductDetailHeader,
} satisfies Meta<typeof ProductDetailHeader>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    badges: [
      { label: "Candidate Detail v1", tone: "readOnly" },
      { label: "Read-only", tone: "readOnly" },
      { label: "NOT_AUTHORITY", tone: "blocked" },
    ],
    description: "Scaffold-only fixture-backed view.",
    title: "NVDA",
  },
};

export const BlockedState: Story = {
  args: {
    badges: [
      { label: "Order Detail v1", tone: "readOnly" },
      { label: "blocked", tone: "blocked" },
      { label: "NOT_AUTHORITY", tone: "blocked" },
    ],
    description: "Broker truth and mutation remain blocked.",
    title: "fixture-order-blocked",
  },
};

export const UnknownState: Story = {
  args: {
    badges: [
      { label: "Position Detail v1", tone: "readOnly" },
      { label: "unknown", tone: "unknown" },
      { label: "Read-only", tone: "readOnly" },
    ],
    description: "Missing account evidence remains UNKNOWN.",
    title: "UNKNOWN_POSITION",
  },
};
