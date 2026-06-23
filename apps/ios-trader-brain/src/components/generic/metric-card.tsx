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
  fresh: "정상",
  stale: "오래됨",
  missing: "누락",
  unknown: "UNKNOWN",
  blocked: "확인 필요",
  readOnly: "읽기전용",
  disabled: "비활성",
};

export function MetricCard({
  helperText,
  label,
  state = "unknown",
  style,
  unit,
  value,
  ...props
}: MetricCardProps) {
  const displayValue = value === null ? "UNKNOWN" : `${value}${unit ? ` ${unit}` : ""}`;

  return (
    <CardContainer
      {...props}
      style={[
        {
          flexBasis: "47%",
          flexGrow: 1,
          minWidth: 132,
          padding: spacing.md,
        },
        style,
      ]}
    >
      <View style={{ gap: spacing.sm }}>
        <View style={{ alignItems: "flex-start", gap: spacing.xs }}>
          <AppText variant="caption">{label}</AppText>
          <Badge label={stateLabels[state]} tone={state} />
        </View>
        <AppText
          variant="title"
          style={displayValue === "UNKNOWN" ? { fontSize: 20, lineHeight: 24 } : undefined}
        >
          {displayValue}
        </AppText>
        {helperText ? <AppText variant="caption">{helperText}</AppText> : null}
      </View>
    </CardContainer>
  );
}
