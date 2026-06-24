import { StyleSheet, View } from "react-native";

import { AppText } from "../foundation";
import { colors, mobile, spacing } from "../../theme/tokens";

type MainTabHeaderProps = {
  title: string;
};

export function MainTabHeader({ title }: MainTabHeaderProps) {
  return (
    <View style={styles.header}>
      <View style={styles.side}>
        <AppText accessibilityLabel="뒤로가기" style={styles.icon}>
          {"<"}
        </AppText>
      </View>

      <AppText numberOfLines={1} style={styles.title}>
        {title}
      </AppText>

      <View style={[styles.side, styles.rightSide]}>
        <AppText accessibilityLabel="검색" style={styles.icon}>
          ⌕
        </AppText>
        <AppText accessibilityLabel="메뉴" style={styles.icon}>
          ≡
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "center",
    backgroundColor: "#F9FAFB",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 88,
    paddingHorizontal: 32,
    width: "100%",
  },
  side: {
    alignItems: "center",
    flexDirection: "row",
    minWidth: 88,
  },
  rightSide: {
    gap: spacing.xs,
    justifyContent: "flex-end",
  },
  icon: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "700",
    lineHeight: 28,
    minHeight: mobile.touchTarget,
    minWidth: mobile.touchTarget,
    textAlign: "center",
    textAlignVertical: "center",
  },
  title: {
    color: colors.ink,
    flex: 1,
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 24,
    textAlign: "center",
  },
});
