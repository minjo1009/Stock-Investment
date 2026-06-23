import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { MobileScanListItem } from "../components/domain";

const meta = {
  title: "Domain/MobileScanListItem",
  component: MobileScanListItem,
} satisfies Meta<typeof MobileScanListItem>;

export default meta;

type Story = StoryObj<typeof meta>;

export const BrainCandidate: Story = {
  args: {
    badges: [
      { label: "REVIEW_ONLY", tone: "readOnly" },
      { label: "BLOCKED", tone: "blocked" },
    ],
    body: "Candidate row is fixture-backed and cannot authorize a trade.",
    href: "/brain/candidate/fixture-candidate-review",
    hrefLabel: "Open read-only candidate detail",
    metrics: [
      { label: "Evidence", value: "UNKNOWN", state: "unknown" },
      { label: "Blockers", value: 1, state: "blocked" },
    ],
    sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
    subtitle: "Fixture candidate",
    title: "NVDA",
  },
};

export const PortfolioPosition: Story = {
  args: {
    badges: [
      { label: "broker truth blocked", tone: "blocked" },
      { label: "unknown", tone: "unknown" },
    ],
    body: "Position row is not account or broker truth.",
    href: "/portfolio/position/fixture-position-unknown",
    hrefLabel: "Open read-only position detail",
    metrics: [
      { label: "Quantity", value: "UNKNOWN", state: "unknown" },
      { label: "PnL", value: "UNKNOWN", state: "unknown" },
    ],
    subtitle: "fixture-position-unknown",
    title: "UNKNOWN",
  },
};

export const OrderRow: Story = {
  args: {
    badges: [
      { label: "BLOCKED", tone: "blocked" },
      { label: "mutation false", tone: "blocked" },
    ],
    body: "Order row has no submit, approve, reject, or cancel handler.",
    href: "/orders/fixture-order-blocked",
    hrefLabel: "Open read-only order detail",
    metrics: [
      { label: "Symbol", value: "UNKNOWN", state: "unknown" },
      { label: "Disabled", value: 3, state: "blocked" },
    ],
    subtitle: "fixture-order-blocked",
    title: "ORDER",
  },
};
