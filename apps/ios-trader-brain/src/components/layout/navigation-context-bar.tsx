import { Link, type Href } from "expo-router";
import { View } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { spacing } from "../../theme/tokens";

type NavigationCrumb = {
  href?: string;
  label: string;
};

type NavigationContextBarProps = {
  crumbs: NavigationCrumb[];
  note?: string;
};

export function NavigationContextBar({ crumbs, note }: NavigationContextBarProps) {
  return (
    <CardContainer>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <Badge label="read-only path" tone="readOnly" />
        <Badge label="no mutation" tone="blocked" />
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.xs }}>
        {crumbs.map((crumb, index) => (
          <View key={`${crumb.label}-${index}`} style={{ flexDirection: "row", gap: spacing.xs }}>
            {crumb.href ? (
              <Link href={crumb.href as Href}>
                <AppText variant="caption">{crumb.label}</AppText>
              </Link>
            ) : (
              <AppText variant="caption">{crumb.label}</AppText>
            )}
            {index < crumbs.length - 1 ? <AppText variant="caption">/</AppText> : null}
          </View>
        ))}
      </View>
      {note ? <AppText variant="caption">{note}</AppText> : null}
    </CardContainer>
  );
}
