import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { AppText, CardContainer } from "../components/foundation";

const meta = {
  title: "Foundation/CardContainer",
  component: CardContainer,
} satisfies Meta<typeof CardContainer>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Read-only shell</AppText>
      <AppText>No mutation surface.</AppText>
    </CardContainer>
  ),
};

export const ReadOnly: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Review surface</AppText>
      <AppText>Inspect evidence and source freshness only.</AppText>
    </CardContainer>
  ),
};

export const Blocked: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Blocked</AppText>
      <AppText>Requires governance change before action controls can exist.</AppText>
    </CardContainer>
  ),
};

export const Stale: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Stale source</AppText>
      <AppText>Stale data remains a blocker, not a permission signal.</AppText>
    </CardContainer>
  ),
};

export const Missing: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Missing source</AppText>
      <AppText>Missing data renders as missing, not zero.</AppText>
    </CardContainer>
  ),
};

export const Unknown: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Unknown source</AppText>
      <AppText>Unknown source state is not negative evidence.</AppText>
    </CardContainer>
  ),
};

export const DisabledAction: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Disabled action</AppText>
      <AppText>Governance blocks action affordances at the component layer.</AppText>
    </CardContainer>
  ),
};
