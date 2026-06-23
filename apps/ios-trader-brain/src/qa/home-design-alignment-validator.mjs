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

function expectIncludes(source, tokens, context) {
  for (const token of tokens) {
    expect(source.includes(token), `${context} must include ${token}`);
  }
}

function expectExcludes(source, tokens, context) {
  for (const token of tokens) {
    expect(!source.includes(token), `${context} must not include ${token}`);
  }
}

const homeRoute = readText("app/(tabs)/index.tsx");
const common = readText("src/read-models/common.ts");
const homeFixture = readText("src/read-models/homeFixture.ts");
const homeJson = readJson("src/mocks/fixtures/home.json");
const chartCard = readText("src/components/domain/home-relative-return-chart-card.tsx");
const packageJson = readJson("package.json");

expectIncludes(homeRoute, ["오늘의 투자 요약", "HomeRelativeReturnChartCard", "오늘 확인할 것"], "HOME route");
expectExcludes(
  homeRoute,
  ["계좌 스냅샷", "운영 제한 상태", "비활성화된 기능", "catalog-manifest", "apps/ios-trader-brain", "src/mocks"],
  "HOME visible source"
);
expect(!homeRoute.includes("sourceRefs={item.sourceRefs}"), "HOME attention cards must not render raw source refs");
expect(!homeRoute.includes("subtitle={item.route}"), "HOME attention cards must not render raw route subtitles");

expectIncludes(
  common,
  ["HomeRelativeReturnChart", "RelativeReturnChartPoint", "ChartResolution", "relativeReturnChart"],
  "read model contract"
);
expectIncludes(
  chartCard,
  ["QQQ 대비 수익 / MDD", "Daily", "1H", "30m", "15m", "5m", "ChartWithSourceState", "showTechnicalDetails={false}"],
  "HOME relative return chart card"
);
expectExcludes(
  chartCard + homeFixture,
  ["mockSeries", "sampleData", "synthetic", "fake", "Math.random", "generateChart", "generateOhlc", "generateReturns"],
  "chart implementation"
);

const relativeChart = homeJson?.relativeReturnChart;
expect(relativeChart?.chartId === "home-relative-return-vs-qqq", "HOME fixture must define relative return chart id");
expect(relativeChart?.benchmarkSymbol === "QQQ", "HOME fixture chart benchmark must be QQQ");
expect(relativeChart?.chartState?.status !== "READY", "HOME fixture chart must not be READY without authority");
expect(
  relativeChart?.chartState?.status === "SOURCE_NOT_ATTACHED" ||
    relativeChart?.chartState?.status === "CHART_MISSING",
  "HOME fixture chart must be SOURCE_NOT_ATTACHED or CHART_MISSING"
);
expect(Array.isArray(relativeChart?.points) && relativeChart.points.length === 0, "HOME fixture chart points must be empty");
expect(
  JSON.stringify(relativeChart?.allowedResolutions ?? []) === JSON.stringify(["1D", "1H", "30M", "15M", "5M"]),
  "HOME fixture chart must expose Daily/1H/30m/15m/5m resolutions"
);

expect(homeJson?.governance?.strategyAcceptance === "NOT_ACCEPTED", "strategy acceptance must remain NOT_ACCEPTED");
expect(
  homeJson?.governance?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  "deployment readiness must remain diagnostic-only"
);
expect(homeJson?.governance?.realCapital === "FORBIDDEN", "real capital must remain FORBIDDEN");
expect(homeJson?.governance?.brokerMutationPermitted === false, "broker mutation must remain false");
expect(homeJson?.governance?.paperPermission === false, "paper permission must remain false");
expect(homeJson?.governance?.livePermission === false, "live permission must remain false");

expect(
  packageJson?.scripts?.["validate:home-design-alignment"] ===
    "node src/qa/home-design-alignment-validator.mjs",
  "package script validate:home-design-alignment must exist"
);
expect(
  packageJson?.scripts?.test?.includes("validate:home-design-alignment"),
  "npm test must include home design alignment validator"
);

if (findings.length > 0) {
  console.error("[HOME_DESIGN_ALIGNMENT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[HOME_DESIGN_ALIGNMENT_OK] HOME follows product-first design alignment without fake chart data");
