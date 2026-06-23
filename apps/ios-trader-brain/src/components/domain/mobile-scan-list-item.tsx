import { Link, type Href } from "expo-router";
import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer, type BadgeTone } from "../foundation";
import { MetricCard } from "../generic";
import type { ComponentState } from "../../read-models";
import { mobile, spacing } from "../../theme/tokens";

type ScanBadge = {
  label: string;
  tone?: BadgeTone;
};

type ScanMetric = {
  label: string;
  value: string | number | null;
  state?: ComponentState;
};

type MobileScanListItemProps = ViewProps & {
  badges: ScanBadge[];
  body: string;
  href: string;
  hrefLabel: string;
  metrics: ScanMetric[];
  sourceRefs?: string[];
  subtitle?: string | null;
  title: string;
};

export function MobileScanListItem({
  badges,
  body,
  href,
  hrefLabel,
  metrics,
  sourceRefs = [],
  subtitle,
  title,
  ...props
}: MobileScanListItemProps) {
  return (
    <CardContainer {...props} style={[{ minHeight: mobile.touchTarget, padding: spacing.md }, props.style]}>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <Badge label="Read-only" tone="readOnly" />
        <Badge label="NOT_AUTHORITY" tone="blocked" />
        {badges.map((badge) => (
          <Badge key={`${badge.label}-${badge.tone ?? "readOnly"}`} label={badge.label} tone={badge.tone ?? "readOnly"} />
        ))}
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="title">{title}</AppText>
        {subtitle ? <AppText>{subtitle}</AppText> : null}
        <AppText numberOfLines={2} variant="caption">
          {body}
        </AppText>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {metrics.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            state={metric.state ?? "unknown"}
            value={metric.value}
          />
        ))}
      </View>
      <Link href={href as Href}>
        <AppText variant="caption">{hrefLabel}</AppText>
      </Link>
      {sourceRefs.slice(0, 2).map((sourceRef) => (
        <AppText key={sourceRef} ellipsizeMode="middle" numberOfLines={1} variant="caption">
          {sourceRef}
        </AppText>
      ))}
    </CardContainer>
  );
}
