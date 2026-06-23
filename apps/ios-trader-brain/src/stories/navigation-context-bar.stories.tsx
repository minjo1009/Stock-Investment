import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { NavigationContextBar } from "../components/layout";

const meta = {
  title: "Layout/NavigationContextBar",
  component: NavigationContextBar,
} satisfies Meta<typeof NavigationContextBar>;

export default meta;

type Story = StoryObj<typeof meta>;

export const CandidatePath: Story = {
  args: {
    crumbs: [
      { href: "/", label: "HOME" },
      { href: "/brain", label: "BRAIN" },
      { label: "Candidate Detail" },
    ],
    note: "Read-only path with no mutation authority.",
  },
};

export const OrderPath: Story = {
  args: {
    crumbs: [
      { href: "/", label: "HOME" },
      { href: "/orders", label: "ORDERS" },
      { label: "Order Detail" },
    ],
    note: "Order path is observation-only.",
  },
};
