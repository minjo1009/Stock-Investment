import { View, type ViewProps } from "react-native";

import { AppText, Badge } from "../foundation";
import type { ComponentState } from "../../read-models/common";
import { colors, spacing } from "../../theme/tokens";

type StatusRowProps = ViewProps & {
  label: string;
  value: string;
  state?: ComponentState;
  sourceRef?: string;
};

const stateLabels: Record<ComponentState, string> = {
  fresh: "Fresh",
  stale: "Stale",
  missing: "Missing",
  unknown: "Unknown",
  blocked: "Blocked",
  readOnly: "read-only",
  disabled: "Disabled",
};

export function StatusRow({
  label,
  sourceRef,
  state = "unknown",
  style,
  value,
  ...props
}: StatusRowProps) {
  return (
    <View
      {...props}
      style={[
        {
          borderBottomColor: colors.border,
          borderBottomWidth: 1,
          gap: spacing.sm,
          paddingVertical: spacing.sm,
        },
        style,
      ]}
    >
      <View
        style={{
          alignItems: "center",
          flexDirection: "row",
          gap: spacing.sm,
          justifyContent: "space-between",
        }}
      >
        <AppText>{label}</AppText>
        <Badge label={stateLabels[state]} tone={state} />
      </View>
      <AppText variant="caption">{value}</AppText>
      {sourceRef ? <AppText variant="caption">{sourceRef}</AppText> : null}
    </View>
  );
}
