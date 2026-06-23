import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { SourceAttributionCard } from "../components/domain";
import { candidateDetailFixture } from "../read-models/candidateDetailFixture";

const meta = {
  title: "Domain/SourceAttributionCard",
  component: SourceAttributionCard,
} satisfies Meta<typeof SourceAttributionCard>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    authority: candidateDetailFixture.sections.decisionSummary.authority,
    sourceStates: candidateDetailFixture.sections.risk.sourceStates,
    status: "UNKNOWN",
    timestamp: candidateDetailFixture.generatedAt,
    title: "Candidate source attribution",
  },
};

export const Blocked: Story = {
  args: {
    authority: "Fixture source review only",
    sourceStates: candidateDetailFixture.sections.risk.sourceStates,
    status: "BLOCKER",
    timestamp: candidateDetailFixture.generatedAt,
    title: "Blocked source attribution",
  },
};
