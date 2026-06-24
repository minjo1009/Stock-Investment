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

function expect(condition, message) {
  if (!condition) findings.push(message);
}

function expectIncludes(source, tokens, context) {
  for (const token of tokens) {
    expect(source.includes(token), `${context} must include ${token}`);
  }
}

function expectBefore(source, first, second, context) {
  const firstIndex = source.indexOf(first);
  const secondIndex = source.indexOf(second);
  expect(firstIndex >= 0, `${context} must include ${first}`);
  expect(secondIndex >= 0, `${context} must include ${second}`);
  expect(firstIndex >= 0 && secondIndex >= 0 && firstIndex < secondIndex, `${context} must show ${first} before ${second}`);
}

const home = readText("app/(tabs)/index.tsx");
const portfolio = readText("app/(tabs)/portfolio.tsx");
const brain = readText("app/(tabs)/brain.tsx");
const chartCard = readText("src/components/domain/home-relative-return-chart-card.tsx");
const layout = readText("app/(tabs)/_layout.tsx");
const readModels = readText("src/read-models/common.ts");

expectBefore(layout, 'name: "index"', 'name: "portfolio"', "tab order");
expectBefore(layout, 'name: "portfolio"', 'name: "brain"', "tab order");

expectBefore(home, "<PortfolioHeroCard", "<HomeRelativeReturnChartCard", "HOME IA");
expect(home.includes("buildJournalMonths"), "HOME must keep dynamic investment journal months");
expect(home.includes("NOT_AUTHORITY"), "HOME must preserve NOT_AUTHORITY boundary");

expectIncludes(
  chartCard,
  [
    "Performance",
    "평가금 vs 원금 vs QQQ",
    "QQQ",
    "Pressable",
    "onPress={() => setSelectedTimeframe(option.label)}",
    "1D",
    "1M",
    "3M",
    "6M",
    "1Y",
    "ALL",
  ],
  "HOME chart card"
);

expectBefore(portfolio, "<PortfolioSummaryCard", "<PortfolioAllocationCard", "PORTFOLIO IA");
expectBefore(portfolio, "<PortfolioAllocationCard", "보유 종목", "PORTFOLIO IA");
expectBefore(portfolio, "보유 종목", "데이터 상태", "PORTFOLIO IA");
expectIncludes(
  portfolio,
  [
    "포트폴리오",
    "총 평가금",
    "원금",
    "총 손익",
    "수익률",
    "자산 배분",
    "자산유형",
    "지역",
    "통화",
    "섹터",
    "평가금 순",
    "수익률 순",
    "수익금 순",
    "비중 순",
    "매수 차단",
    "매도 차단",
    "SOURCE_NOT_ATTACHED",
    "broker truth BLOCKED",
  ],
  "PORTFOLIO production v1"
);
expect(portfolio.includes("read-only") || portfolio.includes("Read-only"), "PORTFOLIO must preserve read-only boundary");
expect(portfolio.includes("NOT_AUTHORITY"), "PORTFOLIO must preserve NOT_AUTHORITY boundary");

expectBefore(brain, "<ScreenSummary", "<MobileV1StatusRail", "BRAIN IA");
expect(
  brain.includes("read-only") || brain.includes("Read-only") || brain.includes("읽기 전용") || brain.includes("읽기전용"),
  "BRAIN must preserve read-only boundary"
);
expect(brain.includes("NOT_AUTHORITY"), "BRAIN must preserve NOT_AUTHORITY boundary");

expectIncludes(readModels, ["totalReturnPct", "winRatePct", "maxDrawdownPct", "portfolioSummary", "scannerSummary", "HomeRelativeReturnChart"], "read model contract types");
expect(!/candidate_score|candidate_rank|confidence_score/.test(readModels), "read models must not invent candidate score/rank/confidence fields");
expect(!/onSubmit=\{|onExecute=\{|fetch\s*\(|axios|react-query|swr|graphql-request/.test(home + portfolio + brain), "product IA screens must remain submit/API-free");

if (findings.length > 0) {
  console.error("[PRODUCT_IA_REORDER_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log(
  "[PRODUCT_IA_REORDER_OK] HOME/PORTFOLIO/BRAIN keep product-first Korean IA with portfolio production v1, QQQ comparison, clickable timeframe chips, and dynamic journal months"
);
