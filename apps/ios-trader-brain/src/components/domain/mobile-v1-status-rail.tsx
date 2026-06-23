import { View } from "react-native";

import { colors, mobile, spacing } from "../../theme/tokens";
import { AppText, Badge, CardContainer } from "../foundation";
import type { BadgeTone } from "../foundation/badge";

export type MobileV1StatusRailItem = {
  label: string;
  value: string | number;
  tone?: BadgeTone;
};

type MobileV1StatusRailProps = {
  items: MobileV1StatusRailItem[];
  subtitle: string;
  title: string;
};

export function MobileV1StatusRail({ items, subtitle, title }: MobileV1StatusRailProps) {
  return (
    <CardContainer
      style={{
        borderColor: colors.readOnlyBorder,
        maxWidth: mobile.contentMaxWidth,
        width: "100%",
      }}
    >
      <View style={{ gap: spacing.sm }}>
        <View style={{ gap: spacing.xs }}>
          <AppText variant="caption">{subtitle}</AppText>
          <AppText>{title}</AppText>
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {items.map((item) => (
            <View
              key={item.label}
              style={{
                borderColor: colors.border,
                borderRadius: 8,
                borderWidth: 1,
                minHeight: mobile.touchTarget,
                minWidth: 96,
                padding: spacing.sm,
              }}
            >
              <AppText variant="caption">{item.label}</AppText>
              <Badge label={String(item.value)} tone={item.tone ?? "readOnly"} />
            </View>
          ))}
        </View>
      </View>
    </CardContainer>
  );
}
