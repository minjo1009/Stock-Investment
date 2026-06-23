import { Badge, type BadgeTone } from "../foundation";

export type EvidenceStatus =
  | "ACTUAL"
  | "DERIVED"
  | "ESTIMATE"
  | "ASSUMPTION"
  | "INFERENCE"
  | "UNKNOWN"
  | "BLOCKER";

type EvidenceStatusChipProps = {
  status: EvidenceStatus;
  label?: string;
};

const toneByStatus: Record<EvidenceStatus, BadgeTone> = {
  ACTUAL: "fresh",
  DERIVED: "readOnly",
  ESTIMATE: "unknown",
  ASSUMPTION: "unknown",
  INFERENCE: "unknown",
  UNKNOWN: "unknown",
  BLOCKER: "blocked",
};

export function EvidenceStatusChip({ label, status }: EvidenceStatusChipProps) {
  return <Badge label={label ? `${label}: ${status}` : status} tone={toneByStatus[status]} />;
}
