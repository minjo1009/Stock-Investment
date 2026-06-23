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
const header = readText("src/components/layout/product-detail-header.tsx");

expect(header.includes("ProductDetailHeader"), "ProductDetailHeader component must exist");
expect(header.includes("flexWrap: \"wrap\""), "ProductDetailHeader badges must wrap on phone widths");
expect(header.includes("width: \"100%\""), "ProductDetailHeader must stay full-width in mobile content");
expect(!/position:\s*["']fixed["']|position:\s*["']sticky["']/.test(header), "ProductDetailHeader must not introduce sticky/fixed behavior");
expect(packageJson?.scripts?.["validate:mobile-detail-header"] === "node src/qa/mobile-detail-header-validator.mjs", "package script validate:mobile-detail-header must exist");
expect(packageJson?.scripts?.test?.includes("validate:mobile-detail-header"), "npm test must include mobile detail header validator");

for (const route of detailRoutes) {
  const source = readText(route);
  expect(source.includes("ProductDetailHeader"), `${route}: must use ProductDetailHeader`);
  expect(source.indexOf("ProductDetailHeader") < source.indexOf("sectionId=\"overview\""), `${route}: compact header must appear before Overview section`);
  expect(source.includes("Read-only"), `${route}: header must preserve Read-only badge`);
  expect(source.includes("NOT_AUTHORITY"), `${route}: header must preserve NOT_AUTHORITY badge`);
  expect(source.includes("MobileV1StatusRail"), `${route}: overview rail must remain after compact header`);
  expect(!/position:\s*["']fixed["']|position:\s*["']sticky["']/.test(source), `${route}: route must not introduce sticky/fixed header`);
  expect(!/onPress=\{|onSubmit=\{|onExecute=\{|fetch\s*\(/.test(source), `${route}: route must not add handlers or integration calls`);
}

if (findings.length > 0) {
  console.error("[MOBILE_DETAIL_HEADER_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_DETAIL_HEADER_OK] detail routes preserve compact read-only mobile headers");
