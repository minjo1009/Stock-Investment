import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { MobileV1StatusRail } from "../components/domain";

const meta = {
  title: "Domain/MobileV1StatusRail",
  component: MobileV1StatusRail,
} satisfies Meta<typeof MobileV1StatusRail>;

export default meta;

type Story = StoryObj<typeof meta>;

export const NotAccepted: Story = {
  args: {
    items: [
      { label: "Strategy", value: "NOT_ACCEPTED", tone: "blocked" },
      { label: "Broker", value: "false", tone: "blocked" },
      { label: "Mode", value: "read-only", tone: "readOnly" },
    ],
    subtitle: "Phone-first v1",
    title: "Strategy remains not accepted",
  },
};

export const DiagnosticOnly: Story = {
  args: {
    items: [
      { label: "Deploy", value: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", tone: "blocked" },
      { label: "Paper", value: "false", tone: "blocked" },
      { label: "Live", value: "false", tone: "blocked" },
    ],
    subtitle: "Phone-first v1",
    title: "Deployment remains diagnostic only",
  },
};

export const Forbidden: Story = {
  args: {
    items: [
      { label: "Capital", value: "FORBIDDEN", tone: "blocked" },
      { label: "Mutation", value: "false", tone: "blocked" },
      { label: "Authority", value: "NOT_AUTHORITY", tone: "blocked" },
    ],
    subtitle: "Phone-first v1",
    title: "Real capital remains forbidden",
  },
};
