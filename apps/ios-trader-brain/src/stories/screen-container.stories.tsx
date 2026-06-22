import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { AppText } from "../components/foundation";
import { ScreenContainer } from "../components/layout";

const meta = {
  title: "Layout/ScreenContainer",
  component: ScreenContainer,
} satisfies Meta<typeof ScreenContainer>;

export default meta;

type Story = StoryObj<typeof meta>;

const renderState = (label: string) => (
  <ScreenContainer>
    <AppText variant="title">{label}</AppText>
    <AppText>read-only foundation layout</AppText>
  </ScreenContainer>
);

export const Default: Story = { render: () => renderState("Default") };
export const ReadOnly: Story = { render: () => renderState("read-only") };
export const Blocked: Story = { render: () => renderState("Blocked") };
export const Stale: Story = { render: () => renderState("Stale") };
export const Missing: Story = { render: () => renderState("Missing") };
export const Unknown: Story = { render: () => renderState("Unknown") };
export const DisabledAction: Story = {
  render: () => renderState("Disabled action"),
};
