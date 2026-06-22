import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { ChartWithSourceState } from "../components/domain";
import candidateDetail from "../mocks/fixtures/candidate-detail.json";
import type { CandidateDetailReadModel } from "../read-models";

const fixture = candidateDetail as CandidateDetailReadModel;
const chartMissing = fixture.sections.risk.chartStates[0];
const sourceNotAttached = fixture.sections.risk.chartStates[1];

const meta = {
  title: "Domain/ChartWithSourceState",
  component: ChartWithSourceState,
} satisfies Meta<typeof ChartWithSourceState>;

export default meta;

type Story = StoryObj<typeof meta>;

export const FreshSource: Story = { args: { chartState: { chartId: "ready-fixture", status: "READY", sourceIds: ["fixture-source-fresh"], blockerReason: null } } };
export const StaleSource: Story = { args: { chartState: { chartId: "stale-fixture", status: "STALE", sourceIds: ["fixture-source-stale"], blockerReason: "Stale chart source." } } };
export const MissingSource: Story = { args: { chartState: chartMissing } };
export const UnknownSource: Story = { args: { chartState: { chartId: "unknown-fixture", status: "UNKNOWN", sourceIds: [], blockerReason: "Unknown chart source." } } };
export const Blocked: Story = { args: { chartState: chartMissing } };
export const DisabledAction: Story = { args: { chartState: sourceNotAttached } };
export const ChartMissing: Story = { args: { chartState: chartMissing } };
export const SourceNotAttached: Story = { args: { chartState: sourceNotAttached } };
