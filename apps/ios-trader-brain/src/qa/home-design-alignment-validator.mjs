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

function expectBefore(source, first, second, context) {
  const firstIndex = source.indexOf(first);
  const secondIndex = source.indexOf(second);
  expect(firstIndex >= 0, `${context} must include ${first}`);
  expect(secondIndex >= 0, `${context} must include ${second}`);
  expect(firstIndex >= 0 && secondIndex >= 0 && firstIndex < secondIndex, `${context} must show ${first} before ${second}`);
}

function expectNoMojibake(source, context) {
  const mojibakeTokens = ["?쎄", "?ㅻ", "?ъ", "怨", "李", "異", "鍮", "沅", "媛"];
  expectExcludes(source, mojibakeTokens, context);
}

const homeRoute = readText("app/(tabs)/index.tsx");
const common = readText("src/read-models/common.ts");
const homeFixture = readText("src/read-models/homeFixture.ts");
const homeJson = readJson("src/mocks/fixtures/home.json");
const chartCard = readText("src/components/domain/home-relative-return-chart-card.tsx");
const packageJson = readJson("package.json");

expectNoMojibake(homeRoute, "HOME route");
expectNoMojibake(chartCard, "HOME performance chart card");
expectNoMojibake(homeFixture, "HOME fixture");
expectNoMojibake(JSON.stringify(homeJson ?? {}), "HOME fixture JSON");

expectBefore(homeRoute, "<PortfolioHeroCard", "<HomeRelativeReturnChartCard", "HOME production IA");
expectBefore(homeRoute, "<HomeRelativeReturnChartCard", "보유 포트폴리오", "HOME production IA");
expectBefore(homeRoute, "보유 포트폴리오", "투자 일지", "HOME production IA");
expectBefore(homeRoute, "투자 일지", "오늘 확인할 것", "HOME production IA");

expectIncludes(
  homeRoute,
  [
    "PortfolioHeroCard",
    "평가금",
    "원금",
    "총 손익",
    "수익률",
    "승률",
    "MDD",
    "보유 포트폴리오",
    "보유 중인 포트폴리오가 없습니다.",
    "투자 일지",
    "6월",
    "해당 월의 거래내역이 없습니다.",
    "읽기 전용",
  ],
  "HOME route"
);

expectIncludes(
  chartCard,
  [
    "Performance",
    "평가금 vs 원금",
    "1M",
    "3M",
    "6M",
    "1Y",
    "ALL",
    "승률 UNKNOWN",
    "MDD UNKNOWN",
    "차트 데이터 연결 대기",
    "showTechnicalDetails={false}",
  ],
  "HOME performance timeline chart card"
);

expectExcludes(
  homeRoute,
  [
    "계좌 스냅샷",
    "운영 제한 상태",
    "비활성화된 기능",
    "catalog-manifest",
    "apps/ios-trader-brain",
    "src/mocks",
    "DB 상태",
    "scheduler",
    "kill switch",
  ],
  "HOME visible source"
);

expectExcludes(
  chartCard + homeFixture,
  ["mockSeries", "sampleData", "synthetic", "fake", "Math.random", "generateChart", "generateOhlc", "generateReturns"],
  "chart implementation"
);

const relativeChart = homeJson?.relativeReturnChart;
expect(relativeChart?.chartId === "home-relative-return-vs-qqq", "HOME fixture must define chart id");
expect(relativeChart?.chartState?.status !== "READY", "HOME fixture chart must not be READY without authority");
expect(
  relativeChart?.chartState?.status === "SOURCE_NOT_ATTACHED" ||
    relativeChart?.chartState?.status === "CHART_MISSING",
  "HOME fixture chart must be SOURCE_NOT_ATTACHED or CHART_MISSING"
);
expect(Array.isArray(relativeChart?.points) && relativeChart.points.length === 0, "HOME fixture chart points must be empty");

expect(homeJson?.governance?.strategyAcceptance === "NOT_ACCEPTED", "strategy acceptance must remain NOT_ACCEPTED");
expect(
  homeJson?.governance?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  "deployment readiness must remain diagnostic-only"
);
expect(homeJson?.governance?.realCapital === "FORBIDDEN", "real capital must remain FORBIDDEN");
expect(homeJson?.governance?.brokerMutationPermitted === false, "broker mutation must remain false");
expect(homeJson?.governance?.paperPermission === false, "paper permission must remain false");
expect(homeJson?.governance?.livePermission === false, "live permission must remain false");

expect(common.includes("HomeRelativeReturnChart"), "read model contract must keep HOME chart contract type");
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

console.log("[HOME_DESIGN_ALIGNMENT_OK] HOME follows production spec sections without fake chart data");
