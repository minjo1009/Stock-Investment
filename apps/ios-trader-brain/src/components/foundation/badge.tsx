import { View, type ViewStyle } from "react-native";

import { colors, radii, spacing, typography } from "../../theme/tokens";
import { AppText } from "./app-text";

export type BadgeTone =
  | "neutral"
  | "blocked"
  | "readOnly"
  | "fresh"
  | "stale"
  | "missing"
  | "unknown"
  | "disabled";

type BadgeProps = {
  label: string;
  tone?: BadgeTone;
};

const toneStyles: Record<BadgeTone, ViewStyle> = {
  neutral: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
  },
  blocked: {
    backgroundColor: colors.blockedSurface,
    borderColor: colors.blockedBorder,
  },
  readOnly: {
    backgroundColor: colors.readOnlySurface,
    borderColor: colors.readOnlyBorder,
  },
  fresh: {
    backgroundColor: colors.freshSurface,
    borderColor: colors.freshBorder,
  },
  stale: {
    backgroundColor: colors.staleSurface,
    borderColor: colors.staleBorder,
  },
  missing: {
    backgroundColor: colors.missingSurface,
    borderColor: colors.missingBorder,
  },
  unknown: {
    backgroundColor: colors.unknownSurface,
    borderColor: colors.unknownBorder,
  },
  disabled: {
    backgroundColor: colors.disabledSurface,
    borderColor: colors.disabledBorder,
  },
};

export function Badge({ label, tone = "neutral" }: BadgeProps) {
  return (
    <View
      style={[
        {
          alignSelf: "flex-start",
          borderRadius: radii.badge,
          borderWidth: 1,
          paddingHorizontal: spacing.sm,
          paddingVertical: spacing.xs,
        },
        toneStyles[tone],
      ]}
    >
      <AppText style={typography.badge}>{label}</AppText>
    </View>
  );
}
