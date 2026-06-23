import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];
const requiredHardState = {
  brokerMutationPermitted: false,
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  livePermission: false,
  paperPermission: false,
  realCapital: "FORBIDDEN",
  strategyAcceptance: "NOT_ACCEPTED",
};

function readText(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath}: missing`);
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
    findings.push(`${relativePath}: invalid JSON ${error.message}`);
    return null;
  }
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

function hasReadOnlyBoundary(source) {
  return source.includes("Read-only") || source.includes("read-only") || source.includes("읽기전용");
}

const packageJson = readJson("package.json");
const manifest = readJson("src/qa/web-preview-manifest.json");
const rail = readText("src/components/domain/mobile-v1-status-rail.tsx");
const scanItem = readText("src/components/domain/mobile-scan-list-item.tsx");
const detailHeader = readText("src/components/layout/product-detail-header.tsx");
const detailSection = readText("src/components/layout/product-detail-section.tsx");

expect(packageJson?.scripts?.["validate:web-preflight"] === "node src/qa/web-preflight-validator.mjs", "validate:web-preflight script must exist");
expect(packageJson?.scripts?.test?.includes("validate:web-preflight"), "npm test must include validate:web-preflight");
expect(manifest?.contractVersion === "mobile-web-preview-preflight-v1", "web preview manifest contractVersion mismatch");
expect(manifest?.authority === "NOT_AUTHORITY", "web preview manifest authority must remain NOT_AUTHORITY");
expect(manifest?.captureStatus === "TARGETS_READY_CAPTURE_NOT_RUN", "web preview manifest must not claim capture");
for (const [key, value] of Object.entries(requiredHardState)) {
  expect(manifest?.hardState?.[key] === value, `hardState.${key} must be ${value}`);
}
expect(Array.isArray(manifest?.viewports) && manifest.viewports.length === 3, "web preview manifest must declare three phone viewports");
expect(Array.isArray(manifest?.routes) && manifest.routes.length === 9, "web preview manifest must declare five tabs and four details");

expect(rail.includes("MobileV1StatusRail"), "MobileV1StatusRail must exist for web preflight");
expect(scanItem.includes("MobileScanListItem"), "MobileScanListItem must exist for web preflight");
expect(detailHeader.includes("ProductDetailHeader"), "ProductDetailHeader must exist for web preflight");
expect(detailSection.includes("ProductDetailSection"), "ProductDetailSection must exist for web preflight");

for (const route of manifest?.routes ?? []) {
  expect(route.routePath?.startsWith("/"), `${route.routeId}: routePath must start with /`);
  expect(["tab", "detail"].includes(route.surfaceType), `${route.routeId}: surfaceType must be tab or detail`);
  const source = readText(route.routeFile);
  expect(hasReadOnlyBoundary(source), `${route.routeId}: route must preserve read-only copy`);
  expect(source.includes("NOT_AUTHORITY"), `${route.routeId}: route must preserve NOT_AUTHORITY copy`);
  expect(!/fetch\s*\(|axios|react-query|swr|graphql-request|expo-sqlite|sqlite3/.test(source), `${route.routeId}: route must not add runtime/API/DB client`);
  expect(!/submitOrder|placeOrder|sendLiveOrder|approveOrder|cancelOrder/.test(source), `${route.routeId}: route must not add order mutation path`);
}

if (findings.length > 0) {
  console.error("[WEB_PREFLIGHT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[WEB_PREFLIGHT_OK] mobile web preview targets are defined without capture, deployment, or mutation claims");
