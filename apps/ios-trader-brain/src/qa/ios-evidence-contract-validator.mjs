import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const findings = [];
const contractPath = join(process.cwd(), "src/qa/ios-evidence-contract.json");

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const contract = existsSync(contractPath) ? JSON.parse(readFileSync(contractPath, "utf8")) : null;

expect(Boolean(contract), "ios-evidence-contract.json must exist");
if (contract) {
  expect(contract.contractVersion === "ios-evidence-contract-v1", "contractVersion must be ios-evidence-contract-v1");
  expect(contract.authority === "NOT_AUTHORITY", "iOS evidence must remain NOT_AUTHORITY");
  expect(contract.captureStatus === "NOT_RUN_WINDOWS_ENVIRONMENT", "captureStatus must not claim native capture");
  expect(contract.artifactRoot?.startsWith("data/artifacts/task_3843_frontend_platform_qa_10_loop/"), "artifactRoot must be task-scoped");
  expect(Array.isArray(contract.requiredRoutes) && contract.requiredRoutes.length >= 9, "requiredRoutes must include tab and detail routes");
  expect(Array.isArray(contract.requiredPresets) && contract.requiredPresets.includes("iphone-current"), "requiredPresets must include iphone-current");
  expect(contract.blockedExternalActions?.includes("iOS simulator screenshot capture"), "simulator capture must remain explicitly blocked here");
}

if (findings.length > 0) {
  console.error("[IOS_EVIDENCE_CONTRACT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[IOS_EVIDENCE_CONTRACT_OK] native iOS evidence contract exists; capture not claimed");
