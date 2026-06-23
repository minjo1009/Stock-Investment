import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { AppText } from "../components/foundation";
import { ProductDetailSection } from "../components/layout";

const meta = {
  title: "Layout/ProductDetailSection",
  component: ProductDetailSection,
} satisfies Meta<typeof ProductDetailSection>;

export default meta;

type Story = StoryObj<typeof meta>;

const renderSection = (args: {
  description?: string;
  sectionId: "overview" | "evidence" | "source" | "risk" | "validation";
  title: "Overview" | "Evidence" | "Source" | "Risk" | "Validation";
}) => (
  <ProductDetailSection {...args}>
    <AppText>Fixture-backed story content. No authority or trading action.</AppText>
  </ProductDetailSection>
);

export const Overview: Story = {
  args: { description: "Top status and summary.", sectionId: "overview", title: "Overview" },
  render: renderSection,
};
export const Evidence: Story = {
  args: { description: "Read-only source rows.", sectionId: "evidence", title: "Evidence" },
  render: renderSection,
};
export const Source: Story = {
  args: { description: "Source and freshness attribution.", sectionId: "source", title: "Source" },
  render: renderSection,
};
export const Risk: Story = {
  args: { description: "Blockers stay visible.", sectionId: "risk", title: "Risk" },
  render: renderSection,
};
export const Validation: Story = {
  args: { description: "Validation is not acceptance.", sectionId: "validation", title: "Validation" },
  render: renderSection,
};
