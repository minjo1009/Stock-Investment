import { View, type ViewProps } from "react-native";

import { AppText, Badge, type BadgeTone } from "../foundation";
import { spacing } from "../../theme/tokens";

export type ProductDetailHeaderBadge = {
  label: string;
  tone: BadgeTone;
};

type ProductDetailHeaderProps = ViewProps & {
  badges: ProductDetailHeaderBadge[];
  description: string;
  title: string;
};

export function ProductDetailHeader({
  badges,
  description,
  title,
  ...props
}: ProductDetailHeaderProps) {
  return (
    <View {...props} style={[{ gap: spacing.sm, width: "100%" }, props.style]}>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {badges.map((badge) => (
          <Badge key={`${badge.label}-${badge.tone}`} label={badge.label} tone={badge.tone} />
        ))}
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="title">{title}</AppText>
        <AppText variant="caption">{description}</AppText>
      </View>
    </View>
  );
}
