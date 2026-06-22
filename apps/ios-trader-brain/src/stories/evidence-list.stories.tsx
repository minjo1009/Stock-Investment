import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { EvidenceList } from "../components/domain";
import candidateDetail from "../mocks/fixtures/candidate-detail.json";
import orderDetail from "../mocks/fixtures/order-detail.json";
import type { CandidateDetailReadModel, OrderDetailReadModel } from "../read-models";

const candidateFixture = candidateDetail as CandidateDetailReadModel;
const orderFixture = orderDetail as OrderDetailReadModel;

const meta = {
  title: "Domain/EvidenceList",
  component: EvidenceList,
} satisfies Meta<typeof EvidenceList>;

export default meta;

type Story = StoryObj<typeof meta>;

export const FreshSource: Story = { args: { evidence: [] } };
export const StaleSource: Story = { args: { evidence: orderFixture.sections.evidence } };
export const MissingSource: Story = { args: { evidence: [] } };
export const UnknownSource: Story = { args: { evidence: candidateFixture.sections.evidence } };
export const Blocked: Story = { args: { evidence: candidateFixture.sections.evidence } };
export const DisabledAction: Story = { args: { evidence: candidateFixture.sections.evidence } };
export const ChartMissing: Story = { args: { evidence: candidateFixture.sections.evidence } };
export const SourceNotAttached: Story = { args: { evidence: candidateFixture.sections.evidence } };
