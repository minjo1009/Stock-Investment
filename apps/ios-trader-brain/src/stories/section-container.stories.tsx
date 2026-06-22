import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { AppText } from "../components/foundation";
import { SectionContainer } from "../components/layout";

const meta = {
  title: "Layout/SectionContainer",
  component: SectionContainer,
} satisfies Meta<typeof SectionContainer>;

export default meta;

type Story = StoryObj<typeof meta>;

const renderSection = (args: { title?: string; description?: string }) => (
  <SectionContainer
    title={args.title ?? "Section"}
    description={args.description}
  >
    <AppText>Component state is supplied through props only.</AppText>
  </SectionContainer>
);

export const Default: Story = {
  args: {
    description: "Default read-only section.",
    title: "Decision Summary",
  },
  render: renderSection,
};
export const ReadOnly: Story = {
  args: {
    description: "read-only section state.",
    title: "Review Section",
  },
  render: renderSection,
};
export const Blocked: Story = {
  args: {
    description: "Governance blocker visible.",
    title: "Blocked Section",
  },
  render: renderSection,
};
export const Stale: Story = {
  args: {
    description: "Stale source state visible.",
    title: "Stale Section",
  },
  render: renderSection,
};
export const Missing: Story = {
  args: {
    description: "Missing source state visible.",
    title: "Missing Section",
  },
  render: renderSection,
};
export const Unknown: Story = {
  args: {
    description: "Unknown state visible.",
    title: "Unknown Section",
  },
  render: renderSection,
};
export const DisabledAction: Story = {
  args: {
    description: "Action controls remain disabled.",
    title: "Disabled Action Section",
  },
  render: renderSection,
};
