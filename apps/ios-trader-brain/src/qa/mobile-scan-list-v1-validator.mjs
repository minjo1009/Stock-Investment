import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];
const tabRoutes = [
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
];

function readText(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath}: missing`);
    return "";
  }
  return readFileSync(path, "utf8");
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

function hasReadOnlyBoundary(source) {
  return (
    source.includes("Read-only") ||
    source.includes("read-only") ||
    source.includes("읽기 전용") ||
    source.includes("읽기전용")
  );
}

const packageJson = JSON.parse(readText("package.json") || "{}");
const component = readText("src/components/domain/mobile-scan-list-item.tsx");

expect(component.includes("MobileScanListItem"), "MobileScanListItem component must exist");
expect(component.includes("minHeight: mobile.touchTarget"), "MobileScanListItem must preserve 44px touch-target minimum");
expect(hasReadOnlyBoundary(component), "MobileScanListItem must show Read-only boundary");
expect(component.includes("NOT_AUTHORITY"), "MobileScanListItem must show NOT_AUTHORITY boundary");
expect(component.includes("flexWrap: \"wrap\""), "MobileScanListItem must wrap content on phone widths");
expect(!/overflow:\s*["']hidden["']/.test(component), "MobileScanListItem must not hide overflow");
expect(!/onPress=\{|onSubmit=\{|onExecute=\{|fetch\s*\(|useState|useEffect/.test(component), "MobileScanListItem must remain props-only with no integration or state");
expect(packageJson?.scripts?.["validate:mobile-scan-list-v1"] === "node src/qa/mobile-scan-list-v1-validator.mjs", "package script validate:mobile-scan-list-v1 must exist");
expect(packageJson?.scripts?.test?.includes("validate:mobile-scan-list-v1"), "npm test must include mobile scan list validator");

for (const route of tabRoutes) {
  const source = readText(route);
  if (route.includes("portfolio")) {
    expect(source.includes("HoldingNameCell"), `${route}: must use Portfolio V2 table name cells`);
    expect(source.includes("MetricCell"), `${route}: must use Portfolio V2 metric cells`);
    expect(source.includes("보유종목"), `${route}: must preserve holdings table header`);
  } else if (route.includes("brain")) {
    expect(source.includes("오늘의 이슈"), `${route}: must render Brain v5 issue card`);
    expect(source.includes("최신 뉴스와 해석"), `${route}: must render Brain v5 news interpretation list`);
    expect(source.includes("관계 맵"), `${route}: must render Brain v5 cause-effect map`);
    expect(source.includes("후보 종목"), `${route}: must render Brain v5 candidate slider`);
    expect(source.includes("위험 요약"), `${route}: must render Brain v5 risk summary`);
    expect(source.includes("원문 보기"), `${route}: must link to evidence detail`);
  } else {
    expect(source.includes("MobileScanListItem"), `${route}: must use MobileScanListItem`);
  }
  expect(source.includes("MobileV1StatusRail"), `${route}: must preserve phone-first rail`);
  expect(hasReadOnlyBoundary(source), `${route}: must preserve Read-only boundary`);
  expect(source.includes("NOT_AUTHORITY"), `${route}: must preserve NOT_AUTHORITY boundary`);
  expect(!/sort\s*\(|filter\s*\([^=]*(score|rank|confidence|outcome)|fetch\s*\(|axios|react-query|swr|graphql-request/.test(source), `${route}: must not add assignment sorting/filtering logic or integration clients`);
  expect(!/submitOrder|placeOrder|sendLiveOrder|approveOrder|cancelOrder/.test(source), `${route}: must not add order mutation language or handlers`);
}

if (findings.length > 0) {
  console.error("[MOBILE_SCAN_LIST_V1_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_SCAN_LIST_V1_OK] tab rows preserve mobile scan, Brain v5 cards, Portfolio V2 table, and read-only boundaries");
