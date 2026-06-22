import { ScrollView, View } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { colors, spacing } from "../../theme/tokens";

type PlaceholderScreenProps = {
  title: "HOME" | "BRAIN" | "PORTFOLIO" | "ORDERS" | "SYSTEM";
};

const guardrails = [
  "read-only",
  "no broker mutation",
  "no paper/live permission",
  "no real-capital permission",
];

export function PlaceholderScreen({ title }: PlaceholderScreenProps) {
  return (
    <ScrollView
      style={{ backgroundColor: colors.background, flex: 1 }}
      contentContainerStyle={{ gap: spacing.lg, padding: spacing.lg }}
      contentInsetAdjustmentBehavior="automatic"
    >
      <CardContainer>
        <View style={{ gap: spacing.sm }}>
          <AppText variant="title">{title}</AppText>
          <AppText>
            Placeholder tab shell for future component-first implementation.
          </AppText>
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {guardrails.map((guardrail) => (
            <Badge key={guardrail} label={guardrail} tone="readOnly" />
          ))}
        </View>
      </CardContainer>
    </ScrollView>
  );
}
