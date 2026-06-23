import { View, type ViewProps } from "react-native";

import { AppText } from "../foundation";
import { spacing } from "../../theme/tokens";

type ProductDetailSectionProps = ViewProps & {
  description?: string;
  sectionId: "overview" | "evidence" | "risk" | "validation";
  title: "Overview" | "Evidence" | "Risk" | "Validation";
};

export function ProductDetailSection({
  children,
  description,
  sectionId,
  title,
  ...props
}: ProductDetailSectionProps) {
  return (
    <View
      {...props}
      testID={`product-detail-section-${sectionId}`}
      style={[{ gap: spacing.sm, width: "100%" }, props.style]}
    >
      <View style={{ gap: spacing.xs }}>
        <AppText variant="title">{title}</AppText>
        {description ? <AppText variant="caption">{description}</AppText> : null}
      </View>
      {children}
    </View>
  );
}
