import { Platform, ScrollView, View, type ScrollViewProps } from "react-native";

import { colors, mobile, spacing } from "../../theme/tokens";

type ScreenContainerProps = ScrollViewProps & {
  padded?: boolean;
};

export function ScreenContainer({
  children,
  contentContainerStyle,
  padded = true,
  style,
  ...props
}: ScreenContainerProps) {
  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      {...props}
      style={[{ backgroundColor: colors.background, flex: 1 }, style]}
      contentContainerStyle={styles.scrollContent}
    >
      <View
        style={[
          {
            gap: spacing.lg,
            maxWidth: mobile.contentMaxWidth,
            padding: padded ? spacing.lg : 0,
            paddingBottom: spacing.xl,
            width: (Platform.OS === "web"
              ? `calc(100% - ${padded ? spacing.lg * 2 : 40}px)`
              : "100%") as "100%",
          },
          contentContainerStyle,
        ]}
      >
        {children}
      </View>
    </ScrollView>
  );
}

const styles = {
  scrollContent: {
    alignItems: "center",
    backgroundColor: colors.background,
    flexGrow: 1,
    width: "100%",
  },
} as const;
