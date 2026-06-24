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
  const mojibakeTokens = ["�", "筌", "亦", "揶", "?섏", "?됯", "?먭", "諛깊", "吏", "沅뚯", "釉뚮"];
  expectExcludes(source, mojibakeTokens, context);
}

const homeRoute = readText("app/(tabs)/index.tsx");
const common = readText("src/read-models/common.ts");
const homeFixture = readText("src/read-models/homeFixture.ts");
const backtestFixture = readText("src/read-models/backtestSnapshotFixture.ts");
const homeJson = readJson("src/mocks/fixtures/home.json");
const chartCard = readText("src/components/domain/home-relative-return-chart-card.tsx");
const packageJson = readJson("package.json");

expectNoMojibake(homeRoute, "HOME route");
expectNoMojibake(chartCard, "HOME performance chart card");
expectNoMojibake(homeFixture, "HOME fixture");
expectNoMojibake(JSON.stringify(homeJson ?? {}), "HOME fixture JSON");

expectBefore(homeRoute, "<PortfolioHeroCard", "<HomeRelativeReturnChartCard", "HOME production IA");
expectBefore(homeRoute, "<HomeRelativeReturnChartCard", "오늘 확인할 것", "HOME production IA");
expectBefore(homeRoute, "오늘 확인할 것", "<BacktestDiagnosticCard", "HOME production IA");
expectBefore(homeRoute, "<BacktestDiagnosticCard", "보유 포트폴리오", "HOME production IA");
expectBefore(homeRoute, "보유 포트폴리오", "투자 일지", "HOME production IA");
expectBefore(homeRoute, "투자 일지", "데이터 출처 상태", "HOME production IA");

expectIncludes(
  homeRoute,
  [
    "backtestSnapshotFixture",
    "buildDiagnosticPortfolioSnapshot",
    "진단 평가금",
    "진단 원금",
    "진단 손익",
    "수익률",
    "승률",
    "MDD",
    "오늘 확인할 것",
    "백테스트 곡선이 홈 차트에 연결됨",
    "HomeRelativeReturnChartCard",
    "backtestSnapshot={backtest}",
    "백테스트 진단 요약",
    "보유 포트폴리오",
    "투자 일지",
    "buildJournalMonths",
    "startYear = 2022",
    "실거래 금지",
  ],
  "HOME route"
);

expectIncludes(
  chartCard,
  [
    "BacktestSnapshotReadModel",
    "backtestSnapshot",
    "buildHomeBacktestChart",
    "buildChartGeometry",
    "수익현황",
    "백테스트 평가금 vs 원금 vs QQQ",
    "QQQ 최종 기준",
    "rangeOptions",
    "최근 5",
    "1년",
    "3년",
    "전체",
    "onPress={() =>",
    "setSelectedRange",
    "chartModel.points",
    "snapshot.equityCurve",
    "qqqBenchmarkFinal",
    "principalY",
    "qqqY",
    "midpointX",
    "midpointY",
    "segmentThickness",
    "QOO"
  ].filter((token) => token !== "QOO"),
  "HOME performance timeline chart card"
);

expectIncludes(
  homeFixture,
  ["수익현황", "평가금/원금/QQQ 성과 차트 출처", "실계좌 평가금, 원금, QQQ 점별 벤치마크는 아직 연결되지 않았습니다."],
  "HOME fixture"
);

expectIncludes(
  backtestFixture,
  ["equityCurve", "qqqBenchmarkFinal", "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT", "NOT_AUTHORITY"],
  "backtest fixture"
);

expectExcludes(
  homeRoute,
  [
    "운영 제한 상태",
    "비활성화된 기능",
    "catalog-manifest",
    "apps/ios-trader-brain",
    "src/mocks",
    "DB 상태",
    "scheduler",
    "kill switch",
    "UNKNOWN ",
    "SOURCE_NOT_ATTACHED",
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
expect(relativeChart?.benchmarkSymbol === "QQQ", "HOME fixture benchmark must remain QQQ");
expect(relativeChart?.chartState?.status === "SOURCE_NOT_ATTACHED", "HOME fixture chart must keep account/QQQ point series unattached");
expect(Array.isArray(relativeChart?.points) && relativeChart.points.length === 0, "HOME fixture account chart points must remain empty");

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

console.log(
  "[HOME_DESIGN_ALIGNMENT_OK] HOME reads the selected diagnostic backtest snapshot and renders a bounded performance chart"
);
