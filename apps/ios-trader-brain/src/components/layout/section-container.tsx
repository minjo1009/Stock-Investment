import { View, type ViewProps } from "react-native";

import { AppText, CardContainer } from "../foundation";
import { spacing } from "../../theme/tokens";

type SectionContainerProps = ViewProps & {
  title: string;
  description?: string;
};

export function SectionContainer({
  children,
  description,
  title,
  ...props
}: SectionContainerProps) {
  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="title">{title}</AppText>
        {description ? <AppText variant="caption">{description}</AppText> : null}
      </View>
      {children}
    </CardContainer>
  );
}
