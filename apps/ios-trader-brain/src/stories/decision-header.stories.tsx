import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { DecisionHeader } from "../components/domain";
import candidateDetail from "../mocks/fixtures/candidate-detail.json";
import type { CandidateDetailReadModel } from "../read-models";

const fixture = candidateDetail as CandidateDetailReadModel;

const meta = {
  title: "Domain/DecisionHeader",
  component: DecisionHeader,
} satisfies Meta<typeof DecisionHeader>;

export default meta;

type Story = StoryObj<typeof meta>;

const baseArgs = {
  decisionSummary: fixture.sections.decisionSummary,
  governance: fixture.governance,
};

export const FreshSource: Story = { args: baseArgs };
export const StaleSource: Story = { args: baseArgs };
export const MissingSource: Story = { args: baseArgs };
export const UnknownSource: Story = { args: baseArgs };
export const Blocked: Story = { args: baseArgs };
export const DisabledAction: Story = { args: baseArgs };
export const ChartMissing: Story = { args: baseArgs };
export const SourceNotAttached: Story = { args: baseArgs };
