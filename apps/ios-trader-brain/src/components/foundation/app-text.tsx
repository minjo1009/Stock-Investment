import { Text, type TextProps, type TextStyle } from "react-native";

import { colors, typography } from "../../theme/tokens";

type AppTextVariant = "title" | "body" | "caption";

type AppTextProps = TextProps & {
  variant?: AppTextVariant;
};

const variantStyles: Record<AppTextVariant, TextStyle> = {
  title: typography.title,
  body: typography.body,
  caption: typography.caption,
};

export function AppText({ style, variant = "body", ...props }: AppTextProps) {
  return (
    <Text
      selectable
      {...props}
      style={[{ color: colors.ink }, variantStyles[variant], style]}
    />
  );
}
