import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const packageJson = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const appJson = JSON.parse(readFileSync(join(root, "app.json"), "utf8"));
const easJson = existsSync(join(root, "eas.json"))
  ? JSON.parse(readFileSync(join(root, "eas.json"), "utf8"))
  : null;
const contractPath = join(root, "src/qa/dev-build-readiness.json");
const findings = [];

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const contract = existsSync(contractPath) ? JSON.parse(readFileSync(contractPath, "utf8")) : null;

expect(Boolean(contract), "dev-build-readiness.json must exist");
if (contract) {
  expect(contract.contractVersion === "ios-dev-build-readiness-v1", "contractVersion must be ios-dev-build-readiness-v1");
  expect(contract.target === "Expo Development Build / iOS-first", "target must remain Expo Development Build / iOS-first");
  expect(contract.expoGoPermitted === false, "Expo Go must not be the active target");
  expect(contract.authority === "NOT_AUTHORITY", "authority must remain NOT_AUTHORITY");
  expect(contract.executionStatus === "BLOCKED_UNTIL_MAC_OR_OPERATOR", "executionStatus must stay blocked until Mac/operator evidence");
  expect(contract.hardState?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment readiness must remain diagnostic only");
  expect(contract.hardState?.realCapital === "FORBIDDEN", "real capital must remain forbidden");
  expect(contract.hardState?.brokerMutationPermitted === false, "broker mutation must remain false");
}

expect(packageJson.main === "expo-router/entry", "main must remain expo-router/entry");
expect(Boolean(packageJson.dependencies?.["expo-dev-client"]), "expo-dev-client dependency must be installed for a development build");
expect(packageJson.scripts?.["ios:dev"]?.includes("required-post-scaffold-hardening"), "ios:dev must not silently run a build");
expect(packageJson.scripts?.["ios:dev:preflight"] === "node src/qa/dev-build-readiness-validator.mjs", "ios:dev:preflight must run this validator");
expect(appJson.expo?.ios?.supportsTablet === true, "iOS config must remain present");
expect(appJson.expo?.ios?.bundleIdentifier === "com.minjo.stockinvestment.iostraderbrain.dev", "iOS bundleIdentifier must be configured for the dev client app");
expect(appJson.expo?.plugins?.includes("expo-router"), "expo-router plugin must remain configured");
expect(easJson?.build?.development?.developmentClient === true, "EAS development profile must enable developmentClient");
expect(easJson?.build?.development?.distribution === "internal", "EAS development profile must remain internal distribution");
expect(easJson?.build?.["development-simulator"]?.ios?.simulator === true, "EAS simulator profile must set ios.simulator true");

if (findings.length > 0) {
  console.error("[DEV_BUILD_READINESS_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[DEV_BUILD_READINESS_OK] iOS dev-build target is declared; native execution remains blocked until operator evidence");
