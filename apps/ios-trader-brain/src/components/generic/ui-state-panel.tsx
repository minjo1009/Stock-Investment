import { View } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { spacing, typography } from "../../theme/tokens";

export type UiStateKind = "default" | "loading" | "empty" | "error" | "blocked" | "stale" | "missing" | "unknown";

type UiStatePanelProps = {
  state: UiStateKind;
  title: string;
  message: string;
};

const badgeToneByState: Record<UiStateKind, "neutral" | "blocked" | "stale" | "missing" | "unknown"> = {
  default: "neutral",
  loading: "neutral",
  empty: "neutral",
  error: "blocked",
  blocked: "blocked",
  stale: "stale",
  missing: "missing",
  unknown: "unknown",
};

export function UiStatePanel({ state, title, message }: UiStatePanelProps) {
  return (
    <CardContainer>
      <View style={{ gap: spacing.xs }}>
        <Badge label={state.toUpperCase()} tone={badgeToneByState[state]} />
        <AppText style={typography.badge}>{title}</AppText>
        <AppText variant="caption">{message}</AppText>
      </View>
    </CardContainer>
  );
}
