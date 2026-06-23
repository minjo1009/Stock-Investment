import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const findings = [];
const contractPath = join(process.cwd(), "src/qa/visual-regression-contract.json");

if (!existsSync(contractPath)) {
  findings.push("visual-regression-contract.json must exist");
} else {
  const contract = JSON.parse(readFileSync(contractPath, "utf8"));
  if (contract.contractVersion !== "visual-regression-contract-v1") findings.push("contractVersion must be visual-regression-contract-v1");
  if (contract.authority !== "NOT_AUTHORITY") findings.push("authority must remain NOT_AUTHORITY");
  if (contract.diffStatus !== "NOT_RUN_NO_NATIVE_BASELINE") findings.push("diffStatus must not claim a visual diff run");
  if (!existsSync(join(process.cwd(), contract.sourceManifest))) findings.push("sourceManifest must point to an existing manifest");
  for (const state of ["read-only", "blocked", "stale", "missing", "unknown", "not-authority"]) {
    if (!contract.requiredStates?.includes(state)) findings.push(`requiredStates missing ${state}`);
  }
}

if (findings.length > 0) {
  console.error("[VISUAL_REGRESSION_CONTRACT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[VISUAL_REGRESSION_CONTRACT_OK] visual regression contract exists; native diff not claimed");
