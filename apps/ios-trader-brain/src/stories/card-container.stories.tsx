import { AppText, CardContainer } from "../components/foundation";
import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

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
      <AppText>No broker mutation.</AppText>
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
      <AppText>Requires governance change before any action.</AppText>
    </CardContainer>
  ),
};

export const StaleUnknown: Story = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Unknown source</AppText>
      <AppText>Missing or stale data remains UNKNOWN, never negative evidence.</AppText>
    </CardContainer>
  ),
};
