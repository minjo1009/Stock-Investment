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
const mainTabHeader = readText("src/components/layout/main-tab-header.tsx");

const tabFiles = {
  home: "app/(tabs)/index.tsx",
  brain: "app/(tabs)/brain.tsx",
  portfolio: "app/(tabs)/portfolio.tsx",
  orders: "app/(tabs)/orders.tsx",
  system: "app/(tabs)/system.tsx",
};
const tabTitles = {
  home: "홈",
  brain: "브레인",
  portfolio: "포트폴리오",
  orders: "주문",
  system: "시스템",
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
expect(mainTabHeader.includes("MainTabHeader"), "MainTabHeader component must exist");
expect(mainTabHeader.includes("minHeight: 88"), "MainTabHeader must preserve shared header height");
expect(mainTabHeader.includes("paddingHorizontal: 32"), "MainTabHeader must preserve 32px side padding");
expect(mainTabHeader.includes("minWidth: 88"), "MainTabHeader side slots must keep title centered");
expect(mainTabHeader.includes("검색") && mainTabHeader.includes("메뉴"), "MainTabHeader must expose search and menu affordances");

for (const [tabId, file] of Object.entries(tabFiles)) {
  const source = readText(file);
  expect(source.includes(`MainTabHeader title="${tabTitles[tabId]}"`), `${tabId} must use the shared MainTabHeader`);
  if (tabId === "home") {
    expect(source.includes("HomeRelativeReturnChartCard"), "home must render the QQQ relative return chart card");
    expect(source.includes("Phone-first v1") || source.includes("모바일"), "home must visibly mark mobile-first posture");
  } else if (tabId === "portfolio") {
    expect(source.includes("tableCard"), "portfolio must render fixed-height holdings table card");
    expect(source.includes("detailCard"), "portfolio must render stock detail card");
    expect(source.includes("backtestSnapshotFixture"), "portfolio must read the selected backtest snapshot fixture");
    expect(source.includes("백테스트 진단"), "portfolio must render the backtest diagnostic summary");
    expect(source.includes("진단 전용"), "portfolio backtest summary must remain diagnostic-only");
    expect(source.includes("buildBacktestHoldingRows"), "portfolio must map backtest position summaries into the holdings table");
    expect(source.includes("diagnosticPositions"), "portfolio must use selected diagnostic positions before placeholder holdings");
    expect(source.includes("보유종목"), "portfolio must render holdings table title");
    expect(source.includes("선택 종목"), "portfolio must preserve stock detail marker as Korean product copy");
    expect(source.includes("DiagnosticPortfolioChart"), "portfolio must render the diagnostic performance chart component");
    expect(source.includes("buildEquityCurveWindow"), "portfolio chart buttons must map to a filtered equity-curve window");
    expect(source.includes("slideChartWindow"), "portfolio chart slider controls must update the visible chart window");
    expect(source.includes('"3D"') && source.includes('"5D"'), "portfolio chart must expose 3D and 5D range buttons");
    expect(source.includes("chartWindowOffset"), "portfolio chart must track slider offset state");
    expect(source.includes("chartSource.status"), "portfolio chart must preserve source-status gating");
    expect(source.includes("chartPlotSize"), "portfolio chart must measure the rendered plot size before drawing");
    expect(source.includes("updateChartPlotSize"), "portfolio chart must update geometry from the actual chart container");
    expect(source.includes("selectChartPoint"), "portfolio chart must support tap/crosshair-style point selection");
    expect(source.includes("chartGuideLine"), "portfolio chart must render value guide lines");
    expect(source.includes("chartSelectedValueBubble"), "portfolio chart must render selected point readout");
    expect(source.includes("buildChartGeometry(points, chartSize)"), "portfolio chart geometry must use actual chart size");
    expect(source.includes("midpointX") && source.includes("midpointY"), "portfolio chart segments must be midpoint-positioned inside the measured plot box");
    expect(source.includes("segmentThickness"), "portfolio chart segment placement must account for rendered line thickness");
    expect(source.includes("setSelectedHoldingId"), "portfolio must support local row selection");
    expect(source.includes("toggleIndicator"), "portfolio must support local indicator toggles");
    expect(source.includes("출처 연결 대기"), "portfolio data must remain source-not-attached until authority is connected");
    expect(source.includes('id: "position-watch-review"'), "portfolio must include seven-row scroll QA fixture coverage");
    expect(source.includes("height: 360"), "portfolio holdings table card must use fixed card height");
    expect(source.includes("height: 228"), "portfolio table body must show three 76px rows by default");
    expect(source.includes("height: 76"), "portfolio table rows must use 76px row height");
    expect(source.includes("width: 84"), "portfolio metric columns must fit multiple columns in the visible table layer");
    expect(source.includes("adjustsFontSizeToFit"), "portfolio metric text must auto-fit inside table cells");
    expect(source.includes("minimumFontScale={0.78}"), "portfolio metric text must keep a bounded auto-fit floor");
    expect(source.includes("stickyHeaderCell"), "portfolio must preserve the previous fixed-name-column table layer");
    expect(!source.includes("readableRowsScroller"), "portfolio must not replace the table layer with vertical summary cards");
    expect(source.includes('region: "진단"'), "portfolio diagnostic row subtitle must stay compact enough for the fixed name column");
    expect(source.includes("진단손익"), "portfolio table headers must use short readable labels");
    expect(!source.includes("매도가능 ${holding.sellableQuantity}"), "portfolio table must not use long secondary labels that force ellipsis");
    expect(source.includes("nestedScrollEnabled"), "portfolio table must enable nested ScrollView behavior");
    expect(source.includes("showsVerticalScrollIndicator"), "portfolio table must expose vertical scroll indicator");
    expect(source.includes("showsHorizontalScrollIndicator"), "portfolio table must expose horizontal scroll indicator");
    expect(source.includes("bounces"), "portfolio table scroll views must enable iOS bounces");
    expect(source.includes("MobileV1StatusRail"), `${tabId} must render MobileV1StatusRail`);
    expect(source.includes("Phone-first v2") || source.includes("모바일 우선"), `${tabId} must visibly mark phone-first v2 posture`);
  } else {
    expect(source.includes("MobileV1StatusRail"), `${tabId} must render MobileV1StatusRail`);
    expect(source.includes("Phone-first v1") || source.includes("모바일 우선"), `${tabId} must visibly mark phone-first v1 posture`);
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
