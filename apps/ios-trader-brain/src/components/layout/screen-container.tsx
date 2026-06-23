import { Platform, ScrollView, type ScrollViewProps } from "react-native";

import { colors, mobile, spacing } from "../../theme/tokens";

type ScreenContainerProps = ScrollViewProps & {
  padded?: boolean;
};

export function ScreenContainer({
  contentContainerStyle,
  padded = true,
  style,
  ...props
}: ScreenContainerProps) {
  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      {...props}
      style={[{ backgroundColor: colors.background, flex: 1 }, style]}
      contentContainerStyle={[
        {
          boxSizing: "border-box",
          gap: spacing.lg,
          marginHorizontal: "auto",
          maxWidth: mobile.contentMaxWidth,
          padding: padded ? spacing.lg : 0,
          paddingBottom: spacing.xl,
          width: (padded && Platform.OS === "web"
            ? `calc(100% - ${spacing.lg * 2}px)`
            : "100%") as "100%",
        },
        contentContainerStyle,
      ]}
    />
  );
}
