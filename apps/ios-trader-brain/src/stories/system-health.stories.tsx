import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { SystemHealth } from "../components/domain";
import systemHealth from "../mocks/fixtures/system-health.json";
import type { SystemReadModel } from "../read-models";

const fixture = systemHealth as SystemReadModel;

const meta = {
  title: "Domain/SystemHealth",
  component: SystemHealth,
} satisfies Meta<typeof SystemHealth>;

export default meta;

type Story = StoryObj<typeof meta>;

const args = { system: fixture };

export const FreshSource: Story = { args };
export const StaleSource: Story = { args };
export const MissingSource: Story = { args };
export const UnknownSource: Story = { args };
export const Blocked: Story = { args };
export const DisabledAction: Story = { args };
export const ChartMissing: Story = { args };
export const SourceNotAttached: Story = { args };
