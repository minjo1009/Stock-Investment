import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { BlockerList, SourceFreshnessBadge, StatusRow } from "../generic";
import type { SystemReadModel } from "../../read-models";
import { spacing } from "../../theme/tokens";

type SystemHealthProps = ViewProps & {
  system: SystemReadModel;
};

export function SystemHealth({ system, ...props }: SystemHealthProps) {
  return (
    <CardContainer {...props}>
      <Badge label={system.controlState.runMode} tone="readOnly" />
      <AppText variant="title">System Health</AppText>
      <StatusRow
        label="Kill switch"
        value={system.controlState.killSwitchActive ? "active" : "inactive"}
        state={system.controlState.killSwitchActive ? "blocked" : "unknown"}
        sourceRef={system.controlState.sourcePath}
      />
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {system.sourceFreshness.map((sourceState) => (
          <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} compact />
        ))}
      </View>
      <BlockerList blockers={system.blockers} />
      {system.validatorStatus.map((validator) => (
        <StatusRow
          key={validator.validatorId}
          label={validator.command}
          value={validator.latestStatus}
          state="unknown"
          sourceRef={validator.reportPath}
        />
      ))}
    </CardContainer>
  );
}
