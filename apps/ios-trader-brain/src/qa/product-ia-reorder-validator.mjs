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
    "수익현황",
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

expectBefore(portfolio, "tableCard", "detailCard", "PORTFOLIO V2 IA");
expectIncludes(
  portfolio,
  [
    "보유종목",
    "가로 스크롤 표",
    "3개 행 기본 표시",
    "수익률순",
    "평가금액순",
    "보유기간순",
    "평가손익",
    "보유수량",
    "평가금액",
    "보유기간",
    "MDD",
    "선택 종목",
    "차트 데이터 연결 대기",
    "VWAP",
    "거래량",
    "이동평균",
    "시스템선",
    "오른쪽 핸들: NOW 고정",
    "매수 근거",
    "최신 뉴스",
    "출처 연결 대기",
    "NOT_AUTHORITY",
    "read-only",
  ],
  "PORTFOLIO production v2"
);
expect(portfolio.includes("setSelectedHoldingId"), "PORTFOLIO V2 must support local row selection");
expect(portfolio.includes("setSelectedRange"), "PORTFOLIO V2 must support local range selection");
expect(portfolio.includes("toggleIndicator"), "PORTFOLIO V2 must support local indicator toggles");

expectBefore(brain, "오늘의 이슈", "최신 뉴스와 해석", "BRAIN v5 IA");
expectBefore(brain, "최신 뉴스와 해석", "관계 맵", "BRAIN v5 IA");
expectBefore(brain, "관계 맵", "후보 종목", "BRAIN v5 IA");
expectBefore(brain, "후보 종목", "위험 요약", "BRAIN v5 IA");
expectBefore(brain, "위험 요약", "보조 확인", "BRAIN v5 IA");
expectIncludes(
  brain,
  [
    "브레인",
    "최근 업데이트",
    "확신 수준",
    "브레인 해석",
    "원문 보기",
    "전력망 투자 → 데이터센터 증설",
    "검토 유지",
    "검토 필요",
    "주의",
    "모바일 우선 · 읽기 전용 · 출처 확인 전",
  ],
  "BRAIN production v5"
);
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
  "[PRODUCT_IA_REORDER_OK] HOME/PORTFOLIO/BRAIN keep product-first Korean IA with Portfolio V2 table-detail structure, QQQ comparison, clickable timeframe chips, and dynamic journal months"
);
