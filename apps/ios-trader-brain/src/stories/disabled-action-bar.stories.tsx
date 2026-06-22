import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { DisabledActionBar } from "../components/domain";
import candidateDetail from "../mocks/fixtures/candidate-detail.json";
import type { CandidateDetailReadModel } from "../read-models";

const fixture = candidateDetail as CandidateDetailReadModel;

const meta = {
  title: "Domain/DisabledActionBar",
  component: DisabledActionBar,
} satisfies Meta<typeof DisabledActionBar>;

export default meta;

type Story = StoryObj<typeof meta>;

const args = { actions: fixture.sections.nextAction.disabledTradingActions };

export const FreshSource: Story = { args };
export const StaleSource: Story = { args };
export const MissingSource: Story = { args };
export const UnknownSource: Story = { args };
export const Blocked: Story = { args };
export const DisabledAction: Story = { args };
export const ChartMissing: Story = { args };
export const SourceNotAttached: Story = { args };
