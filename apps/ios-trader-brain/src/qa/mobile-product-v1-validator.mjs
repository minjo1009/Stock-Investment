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
    expect(source.includes("Phone-first v1") || source.includes("모바일"), "home must visibly mark mobile-first posture");
  } else if (tabId === "portfolio") {
    expect(source.includes("tableCard"), "portfolio must render fixed-height holdings table card");
    expect(source.includes("detailCard"), "portfolio must render stock detail card");
    expect(source.includes("보유종목"), "portfolio must render holdings table title");
    expect(source.includes("Stock Detail"), "portfolio must preserve stock detail marker");
    expect(source.includes("차트 데이터 연결 대기"), "portfolio chart must fail closed until authority is connected");
    expect(source.includes("setSelectedHoldingId"), "portfolio must support local row selection");
    expect(source.includes("toggleIndicator"), "portfolio must support local indicator toggles");
    expect(source.includes("SOURCE_NOT_ATTACHED"), "portfolio data must remain source-not-attached until authority is connected");
    expect(source.includes("MobileV1StatusRail"), `${tabId} must render MobileV1StatusRail`);
    expect(source.includes("Phone-first v2"), `${tabId} must visibly mark phone-first v2`);
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
  expect(!/onSubmit=\{|onExecute=\{|fetch\s*\(|axios|react-query|swr|graphql-request/.test(source), `${tabId} must not add submit handlers or frontend API clients`);
}

expect(packageJson?.scripts?.["validate:mobile-product-v1"] === "node src/qa/mobile-product-v1-validator.mjs", "package script validate:mobile-product-v1 must exist");
expect(packageJson?.scripts?.test?.includes("validate:mobile-product-v1"), "npm test must include mobile product v1 validator");

if (findings.length > 0) {
  console.error("[MOBILE_PRODUCT_V1_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_PRODUCT_V1_OK] mobile product surfaces preserve read-only phone-first boundaries with Portfolio V2");
