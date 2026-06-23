import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];
const detailRoutes = [
  "app/brain/candidate/[candidateId].tsx",
  "app/brain/chain/[chainId].tsx",
  "app/portfolio/position/[positionId].tsx",
  "app/orders/[orderId].tsx",
];
const requiredSections = [
  { id: "overview", title: "Overview" },
  { id: "evidence", title: "Evidence" },
  { id: "risk", title: "Risk" },
  { id: "validation", title: "Validation" },
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

const packageJson = JSON.parse(readText("package.json") || "{}");
const productDetailSection = readText("src/components/layout/product-detail-section.tsx");
const screenContainer = readText("src/components/layout/screen-container.tsx");

expect(productDetailSection.includes("sectionId"), "ProductDetailSection must expose sectionId metadata");
expect(productDetailSection.includes("product-detail-section-${sectionId}"), "ProductDetailSection must expose stable section testID");
expect(screenContainer.includes("ScrollView"), "ScreenContainer must preserve vertical ScrollView support");
expect(!/overflow:\s*["']hidden["']/.test(screenContainer), "ScreenContainer must not hide overflow");
expect(packageJson?.scripts?.["validate:mobile-scroll-journey"] === "node src/qa/mobile-scroll-journey-validator.mjs", "package script validate:mobile-scroll-journey must exist");
expect(packageJson?.scripts?.test?.includes("validate:mobile-scroll-journey"), "npm test must include mobile scroll journey validator");

for (const route of detailRoutes) {
  const source = readText(route);
  let previousIndex = -1;

  expect(source.includes("ProductDetailSection"), `${route}: must use ProductDetailSection`);
  expect(source.includes("MobileV1StatusRail"), `${route}: Overview must include MobileV1StatusRail`);
  expect(!/\bscrollTo\b|\buseRef\b|\buseState\b|\buseEffect\b|\brouter\.push\b/.test(source), `${route}: must not add scroll control, state, effects, or navigation changes`);
  expect(!/overflow:\s*["']hidden["']/.test(source), `${route}: must not hide overflow`);
  expect(!/onPress=\{|onSubmit=\{|onExecute=\{|fetch\s*\(/.test(source), `${route}: must not add handlers or integration calls`);

  for (const section of requiredSections) {
    const marker = `sectionId="${section.id}" title="${section.title}"`;
    const sectionIndex = source.indexOf(marker);
    expect(sectionIndex !== -1, `${route}: missing section marker ${marker}`);
    if (sectionIndex !== -1 && previousIndex !== -1) {
      expect(sectionIndex > previousIndex, `${route}: sections must be ordered Overview > Evidence > Risk > Validation`);
    }
    if (sectionIndex !== -1) previousIndex = sectionIndex;
  }
}

if (findings.length > 0) {
  console.error("[MOBILE_SCROLL_JOURNEY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_SCROLL_JOURNEY_OK] detail routes preserve mobile section reachability metadata");
