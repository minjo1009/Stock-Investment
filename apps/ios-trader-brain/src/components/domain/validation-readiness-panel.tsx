import { View, type ViewProps } from "react-native";

import { AppText, CardContainer } from "../foundation";
import { StatusRow } from "../generic";
import type { ValidationReadiness } from "../../read-models";
import { spacing } from "../../theme/tokens";

type ValidationReadinessPanelProps = ViewProps & {
  validationReadiness: ValidationReadiness;
};

export function ValidationReadinessPanel({
  validationReadiness,
  ...props
}: ValidationReadinessPanelProps) {
  return (
    <CardContainer {...props}>
      <AppText variant="title">Validation / Readiness</AppText>
      <View style={{ gap: spacing.xs }}>
        <StatusRow label="Split/OOS" value={validationReadiness.splitOosStatus} state="unknown" />
        <StatusRow label="Leakage" value={validationReadiness.leakageStatus} state="unknown" />
        <StatusRow label="Cost/slippage" value={validationReadiness.costSlippageStatus} state="unknown" />
        <StatusRow label="Source gate" value={validationReadiness.sourceGateStatus} state="blocked" />
      </View>
      <AppText variant="caption">{validationReadiness.readinessSummary}</AppText>
    </CardContainer>
  );
}
