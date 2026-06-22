import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { SourceFreshnessBadge } from "../components/generic";
import { fixtureSourceStates } from "../mocks/fixtures/foundation-states";

const meta = {
  title: "Generic/SourceFreshnessBadge",
  component: SourceFreshnessBadge,
} satisfies Meta<typeof SourceFreshnessBadge>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    sourceState: fixtureSourceStates.fresh,
  },
};

export const ReadOnly: Story = {
  args: {
    compact: true,
    sourceState: fixtureSourceStates.fresh,
  },
};

export const Blocked: Story = {
  args: {
    sourceState: fixtureSourceStates.stale,
  },
};

export const Stale: Story = {
  args: {
    sourceState: fixtureSourceStates.stale,
  },
};

export const Missing: Story = {
  args: {
    sourceState: fixtureSourceStates.missing,
  },
};

export const Unknown: Story = {
  args: {
    sourceState: fixtureSourceStates.unknown,
  },
};

export const DisabledAction: Story = {
  args: {
    compact: true,
    sourceState: fixtureSourceStates.unknown,
  },
};
