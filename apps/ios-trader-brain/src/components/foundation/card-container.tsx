import { View, type ViewProps } from "react-native";

import { colors, radii, spacing } from "../../theme/tokens";

export function CardContainer({ style, ...props }: ViewProps) {
  return (
    <View
      {...props}
      style={[
        {
          backgroundColor: colors.surface,
          borderColor: colors.border,
          borderRadius: radii.card,
          borderWidth: 1,
          gap: spacing.md,
          padding: spacing.lg,
        },
        style,
      ]}
    />
  );
}
