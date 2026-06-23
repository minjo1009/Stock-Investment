import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { UiStatePanel } from "../components/generic";

const meta = {
  title: "Generic/UiStatePanel",
  component: UiStatePanel,
  args: {
    state: "default",
    title: "Read-only fixture state",
    message: "This panel is fixture-backed and NOT_AUTHORITY.",
  },
} satisfies Meta<typeof UiStatePanel>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    state: "loading",
    title: "Loading fixture",
    message: "Waiting for a scaffold-only fixture snapshot.",
  },
};

export const Empty: Story = {
  args: {
    state: "empty",
    title: "No fixture rows",
    message: "Missing rows are unknown, not negative evidence.",
  },
};

export const Error: Story = {
  args: {
    state: "error",
    title: "Fixture parse blocked",
    message: "The screen must remain blocked until source evidence is restored.",
  },
};

export const Blocked: Story = {
  args: {
    state: "blocked",
    title: "Action blocked",
    message: "No broker mutation, paper/live permission, or real-capital permission.",
  },
};

export const Stale: Story = {
  args: {
    state: "stale",
    title: "Source stale",
    message: "Stale source state is a blocker, not a sell signal.",
  },
};

export const Missing: Story = {
  args: {
    state: "missing",
    title: "Source missing",
    message: "Missing source state remains unknown until authoritative evidence exists.",
  },
};

export const Unknown: Story = {
  args: {
    state: "unknown",
    title: "State unknown",
    message: "Unknown state cannot be converted into an execution decision.",
  },
};
