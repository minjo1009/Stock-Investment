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
const layout = readText("app/(tabs)/_layout.tsx");
const readModels = readText("src/read-models/common.ts");

expectBefore(layout, 'title: "홈"', 'title: "포트폴리오"', "tab order");
expectBefore(layout, 'title: "포트폴리오"', 'title: "브레인"', "tab order");

expectBefore(home, "오늘의 투자 요약", "데이터 상태", "HOME IA");
expectBefore(home, "오늘의 투자 요약", "운영 제한 상태", "HOME IA");
expectIncludes(home, ["투자금", "계좌현황", "수익현황", "승률현황", "MDD"], "HOME top summary");
expect(home.includes("read-only") || home.includes("읽기전용"), "HOME must preserve read-only boundary");
expect(home.includes("NOT_AUTHORITY"), "HOME must preserve NOT_AUTHORITY boundary");

expectBefore(portfolio, "보유자산 요약", "데이터 상태", "PORTFOLIO IA");
expectBefore(portfolio, "보유자산 요약", "운영 제한 상태", "PORTFOLIO IA");
expectIncludes(portfolio, ["투자금", "현금", "평가금액", "평가손익", "실현손익", "익스포저", "MDD", "승률"], "PORTFOLIO top summary");
expect(portfolio.includes("read-only") || portfolio.includes("읽기전용"), "PORTFOLIO must preserve read-only boundary");
expect(portfolio.includes("NOT_AUTHORITY"), "PORTFOLIO must preserve NOT_AUTHORITY boundary");

expectBefore(brain, "오늘의 후보 검토", "데이터 상태", "BRAIN IA");
expectBefore(brain, "오늘의 후보 검토", "운영 제한 상태", "BRAIN IA");
expectIncludes(brain, ["후보 수", "검토 가능", "차단됨", "근거 부족"], "BRAIN top scanner summary");
expect(brain.includes("read-only") || brain.includes("읽기전용"), "BRAIN must preserve read-only boundary");
expect(brain.includes("NOT_AUTHORITY"), "BRAIN must preserve NOT_AUTHORITY boundary");

expectIncludes(readModels, ["totalReturnPct", "winRatePct", "maxDrawdownPct", "portfolioSummary", "scannerSummary"], "read model contract types");
expect(!/candidate_score|candidate_rank|confidence_score/.test(readModels), "read models must not invent candidate score/rank/confidence fields");
expect(!/onPress=\{|onSubmit=\{|onExecute=\{|fetch\s*\(|axios|react-query|swr|graphql-request/.test(home + portfolio + brain), "product IA screens must remain handler-free and API-free");

if (findings.length > 0) {
  console.error("[PRODUCT_IA_REORDER_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[PRODUCT_IA_REORDER_OK] HOME/PORTFOLIO/BRAIN keep product-first Korean IA with safety as secondary context");
