import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { EvidenceStatusChip } from "../components/generic";

const meta = {
  title: "Generic/EvidenceStatusChip",
  component: EvidenceStatusChip,
} satisfies Meta<typeof EvidenceStatusChip>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Actual: Story = { args: { status: "ACTUAL" } };
export const Derived: Story = { args: { status: "DERIVED" } };
export const Estimate: Story = { args: { status: "ESTIMATE" } };
export const Assumption: Story = { args: { status: "ASSUMPTION" } };
export const Inference: Story = { args: { status: "INFERENCE" } };
export const Unknown: Story = { args: { status: "UNKNOWN" } };
export const Blocker: Story = { args: { status: "BLOCKER" } };
