import type { StorybookConfig } from "@storybook/react-native-web-vite";

const config: StorybookConfig = {
  stories: ["../src/stories/**/*.stories.@(ts|tsx)"],
  addons: [],
  framework: {
    name: "@storybook/react-native-web-vite",
    options: {},
  },
};

export default config;
