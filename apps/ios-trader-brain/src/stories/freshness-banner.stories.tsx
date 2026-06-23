import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { FreshnessBanner } from "../components/domain";
import { homeFixture } from "../read-models/homeFixture";

const meta = {
  title: "Domain/FreshnessBanner",
  component: FreshnessBanner,
} satisfies Meta<typeof FreshnessBanner>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    generatedAt: homeFixture.generatedAt,
    sourceSummary: homeFixture.sourceSummary,
  },
};

export const Blocked: Story = {
  args: {
    generatedAt: homeFixture.generatedAt,
    sourceSummary: {
      freshCount: 0,
      staleCount: 1,
      missingCount: 1,
      unknownCount: 1,
      strictGateOpenCount: 0,
    },
    title: "Blocked fixture source state",
  },
};
