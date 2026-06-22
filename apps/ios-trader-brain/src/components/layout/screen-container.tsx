import { ScrollView, type ScrollViewProps } from "react-native";

import { colors, spacing } from "../../theme/tokens";

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
          gap: spacing.lg,
          padding: padded ? spacing.lg : 0,
        },
        contentContainerStyle,
      ]}
    />
  );
}
