import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { ComponentState } from "../../read-models/common";
import { spacing } from "../../theme/tokens";

type MetricCardProps = ViewProps & {
  label: string;
  value: string | number | null;
  unit?: string;
  state?: ComponentState;
  helperText?: string;
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

export function MetricCard({
  helperText,
  label,
  state = "unknown",
  unit,
  value,
  ...props
}: MetricCardProps) {
  const displayValue = value === null ? "-" : `${value}${unit ? ` ${unit}` : ""}`;

  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.sm }}>
        <View style={{ alignItems: "flex-start", gap: spacing.xs }}>
          <AppText variant="caption">{label}</AppText>
          <Badge label={stateLabels[state]} tone={state} />
        </View>
        <AppText variant="title">{displayValue}</AppText>
        {helperText ? <AppText variant="caption">{helperText}</AppText> : null}
      </View>
    </CardContainer>
  );
}
