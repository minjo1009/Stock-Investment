import { Link, type Href } from "expo-router";
import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer, type BadgeTone } from "../foundation";
import { MetricCard } from "../generic";
import type { ComponentState } from "../../read-models";
import { spacing } from "../../theme/tokens";

type SummaryMetric = {
  label: string;
  value: string | number | null;
  state?: ComponentState;
  helperText?: string;
};

type SummaryLink = {
  label: string;
  href: string;
  helperText?: string;
};

type SummaryBadge = {
  label: string;
  tone?: BadgeTone;
};

type ScreenSummaryProps = ViewProps & {
  title: string;
  description: string;
  badges?: SummaryBadge[];
  metrics?: SummaryMetric[];
  links?: SummaryLink[];
  footer?: string;
};

export function ScreenSummary({
  badges = [],
  description,
  footer,
  links = [],
  metrics = [],
  title,
  ...props
}: ScreenSummaryProps) {
  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {badges.map((badge) => (
            <Badge key={badge.label} label={badge.label} tone={badge.tone ?? "readOnly"} />
          ))}
        </View>
        <AppText variant="title">{title}</AppText>
        <AppText variant="caption">{description}</AppText>
      </View>

      {metrics.length > 0 ? (
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {metrics.map((metric) => (
            <MetricCard
              key={metric.label}
              helperText={metric.helperText}
              label={metric.label}
              state={metric.state ?? "unknown"}
              value={metric.value}
            />
          ))}
        </View>
      ) : null}

      {links.length > 0 ? (
        <View style={{ gap: spacing.sm }}>
          <AppText>Read-only paths</AppText>
          {links.map((link) => (
            <View key={link.href} style={{ gap: spacing.xs }}>
              <Link href={link.href as Href}>
                <AppText variant="caption">{link.label}</AppText>
              </Link>
              {link.helperText ? <AppText variant="caption">{link.helperText}</AppText> : null}
            </View>
          ))}
        </View>
      ) : null}

      {footer ? <AppText variant="caption">{footer}</AppText> : null}
    </CardContainer>
  );
}

type ReviewCardProps = ViewProps & {
  title: string;
  subtitle?: string | null;
  body?: string | null;
  badges?: SummaryBadge[];
  metrics?: SummaryMetric[];
  href?: string;
  hrefLabel?: string;
  sourceRefs?: string[];
};

export function ReviewCard({
  badges = [],
  body,
  href,
  hrefLabel = "Open read-only detail",
  metrics = [],
  sourceRefs = [],
  subtitle,
  title,
  ...props
}: ReviewCardProps) {
  return (
    <CardContainer {...props}>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {badges.map((badge) => (
          <Badge key={badge.label} label={badge.label} tone={badge.tone ?? "readOnly"} />
        ))}
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="title">{title}</AppText>
        {subtitle ? <AppText>{subtitle}</AppText> : null}
        {body ? <AppText variant="caption">{body}</AppText> : null}
      </View>
      {metrics.length > 0 ? (
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {metrics.map((metric) => (
            <MetricCard
              key={metric.label}
              helperText={metric.helperText}
              label={metric.label}
              state={metric.state ?? "unknown"}
              value={metric.value}
            />
          ))}
        </View>
      ) : null}
      {href ? (
        <Link href={href as Href}>
          <AppText variant="caption">{hrefLabel}</AppText>
        </Link>
      ) : null}
      {sourceRefs.map((sourceRef) => (
        <AppText key={sourceRef} ellipsizeMode="middle" numberOfLines={1} variant="caption">
          {sourceRef}
        </AppText>
      ))}
    </CardContainer>
  );
}

type TimelineItem = {
  label: string;
  value: string;
  state?: ComponentState;
  helperText?: string | null;
};

type TimelineListProps = ViewProps & {
  items: TimelineItem[];
};

export function TimelineList({ items, ...props }: TimelineListProps) {
  return (
    <CardContainer {...props}>
      <Badge label="read-only trace" tone="readOnly" />
      <View style={{ gap: spacing.sm }}>
        {items.map((item) => (
          <View key={item.label} style={{ gap: spacing.xs }}>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
              <Badge label={item.state ?? "unknown"} tone={item.state ?? "unknown"} />
              <AppText>{item.label}</AppText>
            </View>
            <AppText variant="caption">{item.value}</AppText>
            {item.helperText ? <AppText variant="caption">{item.helperText}</AppText> : null}
          </View>
        ))}
      </View>
    </CardContainer>
  );
}
