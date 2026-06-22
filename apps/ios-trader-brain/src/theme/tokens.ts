import type { TextStyle } from "react-native";

export const colors = {
  background: "#F7F8FA",
  surface: "#FFFFFF",
  surfaceMuted: "#EEF1F4",
  border: "#D8DEE6",
  ink: "#111827",
  mutedInk: "#4B5563",
  freshSurface: "#E8F7EF",
  freshBorder: "#75C99A",
  staleSurface: "#FFF7E6",
  staleBorder: "#E8B84C",
  missingSurface: "#FFF1F0",
  missingBorder: "#FFB4AB",
  unknownSurface: "#F3F4F6",
  unknownBorder: "#C7CED8",
  readOnlySurface: "#E8F2FF",
  readOnlyBorder: "#9BC4FF",
  blockedSurface: "#FFF1F0",
  blockedBorder: "#FFB4AB",
  disabledSurface: "#F4F0FF",
  disabledBorder: "#C4B5FD",
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export const radii = {
  badge: 999,
  card: 8,
};

export const typography: Record<string, TextStyle> = {
  title: {
    fontSize: 24,
    fontWeight: "700",
    lineHeight: 30,
  },
  body: {
    fontSize: 16,
    fontWeight: "400",
    lineHeight: 22,
  },
  caption: {
    color: colors.mutedInk,
    fontSize: 13,
    fontWeight: "400",
    lineHeight: 18,
  },
  badge: {
    fontSize: 12,
    fontWeight: "700",
    lineHeight: 16,
  },
};
