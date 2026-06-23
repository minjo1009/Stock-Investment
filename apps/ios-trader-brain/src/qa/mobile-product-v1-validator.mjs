import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function readText(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath} must exist`);
    return "";
  }
  return readFileSync(path, "utf8");
}

function readJson(relativePath) {
  const source = readText(relativePath);
  if (!source) return null;
  try {
    return JSON.parse(source);
  } catch (error) {
    findings.push(`${relativePath} must be valid JSON: ${error.message}`);
    return null;
  }
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const contract = readJson("src/qa/mobile-product-v1-contract.json");
const packageJson = readJson("package.json");
const tokens = readText("src/theme/tokens.ts");
const screenContainer = readText("src/components/layout/screen-container.tsx");
const rail = readText("src/components/domain/mobile-v1-status-rail.tsx");

const tabFiles = {
  home: "app/(tabs)/index.tsx",
  brain: "app/(tabs)/brain.tsx",
  portfolio: "app/(tabs)/portfolio.tsx",
  orders: "app/(tabs)/orders.tsx",
  system: "app/(tabs)/system.tsx",
};

expect(contract?.authority === "NOT_AUTHORITY", "mobile product contract authority must remain NOT_AUTHORITY");
expect(contract?.gptCaptureStatus === "CAPTURED_LOOP_1", "GPT Loop 1 capture status must be recorded");
expect(contract?.representativeProductScreen === "brain", "BRAIN must be the representative product screen for Loop 1");
expect(contract?.hardState?.strategyAcceptance === "NOT_ACCEPTED", "strategy acceptance must remain NOT_ACCEPTED");
expect(contract?.hardState?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment readiness must remain diagnostic-only");
expect(contract?.hardState?.realCapital === "FORBIDDEN", "real capital must remain FORBIDDEN");
expect(contract?.hardState?.brokerMutationPermitted === false, "broker mutation must remain false");
expect(contract?.hardState?.paperPermission === false, "paper permission must remain false");
expect(contract?.hardState?.livePermission === false, "live permission must remain false");
expect(contract?.nextRequiredEvidence === "ACTUAL_PHONE_SCREENSHOT_QA", "actual phone screenshot QA must remain the next evidence requirement");
expect(Array.isArray(contract?.requiredViewports) && contract.requiredViewports.length === 3, "three mobile product viewports must be declared");

expect(tokens.includes("contentMaxWidth: 430"), "mobile content max width must be 430");
expect(tokens.includes("touchTarget: 44"), "mobile touch target must be 44");
expect(screenContainer.includes("maxWidth: mobile.contentMaxWidth"), "ScreenContainer must enforce mobile max content width");
expect(rail.includes("MobileV1StatusRail"), "MobileV1StatusRail component must exist");
expect(rail.includes("minHeight: mobile.touchTarget"), "MobileV1StatusRail must preserve touch-target sizing");

for (const [tabId, file] of Object.entries(tabFiles)) {
  const source = readText(file);
  if (tabId === "home") {
    expect(source.includes("HomeRelativeReturnChartCard"), "home must render the QQQ relative return chart card");
    expect(source.includes("모바일 우선") || source.includes("Phone-first v1"), "home must visibly mark mobile-first posture");
    expect(!source.includes("운영 제한 상태"), "home must not let operating restriction copy dominate the first screen");
    expect(!source.includes("비활성화된 기능"), "home must not render disabled action rail on the first screen");
  } else {
    expect(source.includes("MobileV1StatusRail"), `${tabId} must render MobileV1StatusRail`);
    expect(source.includes("Phone-first v1"), `${tabId} must visibly mark phone-first v1`);
  }
  expect(
    source.includes("Read-only") ||
      source.includes("read-only") ||
      source.includes("읽기 전용") ||
      source.includes("읽기전용"),
    `${tabId} must preserve read-only copy`
  );
  expect(source.includes("NOT_AUTHORITY"), `${tabId} must preserve NOT_AUTHORITY copy`);
  expect(!/onPress=\{|onSubmit=\{|onExecute=\{|fetch\s*\(|axios|react-query|swr|graphql-request/.test(source), `${tabId} must not add handlers or frontend API clients`);
}

expect(packageJson?.scripts?.["validate:mobile-product-v1"] === "node src/qa/mobile-product-v1-validator.mjs", "package script validate:mobile-product-v1 must exist");
expect(packageJson?.scripts?.test?.includes("validate:mobile-product-v1"), "npm test must include mobile product v1 validator");

if (findings.length > 0) {
  console.error("[MOBILE_PRODUCT_V1_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_PRODUCT_V1_OK] mobile product v1 surfaces preserve read-only phone-first boundaries");
