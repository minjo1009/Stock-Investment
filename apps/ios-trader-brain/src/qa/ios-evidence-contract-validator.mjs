import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const findings = [];
const contractPath = join(process.cwd(), "src/qa/ios-evidence-contract.json");
const nativeTemplatePath = join(process.cwd(), "../../docs/frontend_ios/native_ios_evidence_manifest_template.json");

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const contract = existsSync(contractPath) ? JSON.parse(readFileSync(contractPath, "utf8")) : null;
const nativeTemplate = existsSync(nativeTemplatePath)
  ? JSON.parse(readFileSync(nativeTemplatePath, "utf8"))
  : null;

expect(Boolean(contract), "ios-evidence-contract.json must exist");
expect(Boolean(nativeTemplate), "native iOS evidence manifest template must exist");
if (contract) {
  expect(contract.contractVersion === "ios-evidence-contract-v1", "contractVersion must be ios-evidence-contract-v1");
  expect(contract.authority === "NOT_AUTHORITY", "iOS evidence must remain NOT_AUTHORITY");
  expect(contract.captureStatus === "NOT_RUN_WINDOWS_ENVIRONMENT", "captureStatus must not claim native capture");
  expect(contract.buildEvidenceStatus === "NOT_RUN_REQUIRES_USER_OPERATOR", "buildEvidenceStatus must remain operator-gated");
  expect(contract.bundleIdentifier === "com.minjo.stockinvestment.iostraderbrain.dev", "bundleIdentifier must match governed dev bundle id");
  for (const profile of ["development", "development-simulator", "preview-internal"]) {
    expect(contract.requiredBuildProfiles?.includes(profile), `requiredBuildProfiles missing ${profile}`);
  }
  expect(contract.artifactRoot?.startsWith("data/artifacts/task_3843_frontend_platform_qa_10_loop/"), "artifactRoot must be task-scoped");
  expect(Array.isArray(contract.requiredRoutes) && contract.requiredRoutes.length >= 9, "requiredRoutes must include tab and detail routes");
  expect(Array.isArray(contract.requiredPresets) && contract.requiredPresets.includes("iphone-current"), "requiredPresets must include iphone-current");
  expect(contract.requiredBuildEvidence?.includes("installed app bundle id"), "requiredBuildEvidence must include installed app bundle id");
  expect(contract.blockedExternalActions?.includes("EAS cloud build"), "EAS cloud build must remain blocked here");
  expect(contract.blockedExternalActions?.includes("iOS simulator screenshot capture"), "simulator capture must remain explicitly blocked here");
}
if (nativeTemplate) {
  expect(nativeTemplate.contractVersion === "native-ios-evidence-manifest-v1", "native evidence template contractVersion must be native-ios-evidence-manifest-v1");
  expect(nativeTemplate.authority === "NOT_AUTHORITY", "native evidence template must remain NOT_AUTHORITY");
  expect(nativeTemplate.captureStatus === "TEMPLATE_ONLY_NOT_RUN", "native evidence template must not claim a run");
  expect(nativeTemplate.bundleIdentifier === "com.minjo.stockinvestment.iostraderbrain.dev", "native evidence template bundle id must match app config");
  expect(nativeTemplate.buildEvidence?.easBuildId === null, "native evidence template must not include a fake EAS build id");
  expect(nativeTemplate.safetyEvidence?.brokerMutationPathReachable === "UNKNOWN", "broker mutation reachability must stay UNKNOWN until native evidence exists");
}

if (findings.length > 0) {
  console.error("[IOS_EVIDENCE_CONTRACT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[IOS_EVIDENCE_CONTRACT_OK] native iOS evidence contract exists; capture not claimed");
