import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { BlockerList } from "../components/generic";
import { fixtureBlockers } from "../mocks/fixtures/foundation-states";

const meta = {
  title: "Generic/BlockerList",
  component: BlockerList,
} satisfies Meta<typeof BlockerList>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    blockers: fixtureBlockers.blocked,
  },
};

export const ReadOnly: Story = {
  args: {
    blockers: [],
    emptyLabel: "No blocker rows supplied by read-only fixture.",
  },
};

export const Blocked: Story = {
  args: {
    blockers: fixtureBlockers.blocked,
  },
};

export const Stale: Story = {
  args: {
    blockers: fixtureBlockers.blocked,
  },
};

export const Missing: Story = {
  args: {
    blockers: fixtureBlockers.missing,
  },
};

export const Unknown: Story = {
  args: {
    blockers: fixtureBlockers.unknown,
  },
};

export const DisabledAction: Story = {
  args: {
    blockers: fixtureBlockers.blocked,
  },
};
