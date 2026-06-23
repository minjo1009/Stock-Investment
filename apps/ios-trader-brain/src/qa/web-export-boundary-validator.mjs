import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

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

const packageJson = readJson("package.json");
const exportManifest = readJson("dist/web-export-artifact-manifest.json");
const previewManifest = readJson("src/qa/web-preview-manifest.json");

expect(packageJson?.scripts?.["evidence:web-export"] === "node scripts/web-export-evidence.mjs", "evidence:web-export script must exist");
expect(packageJson?.scripts?.["validate:web-export-boundary"] === "node src/qa/web-export-boundary-validator.mjs", "validate:web-export-boundary script must exist");
expect(exportManifest?.authority === "NOT_AUTHORITY", "export evidence authority must remain NOT_AUTHORITY");
expect(exportManifest?.captureStatus === "LOCAL_EXPORT_EVIDENCE_ONLY", "export evidence must not claim deployment or capture");
expect(exportManifest?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "export evidence must preserve diagnostic-only deployment state");
expect(exportManifest?.realCapital === "FORBIDDEN", "export evidence must preserve FORBIDDEN real capital state");
expect(exportManifest?.brokerMutationPermitted === false, "export evidence must preserve broker mutation false");
expect(exportManifest?.indexHtmlPresent === true, "export evidence must include index.html");
expect(Number(exportManifest?.fileCount ?? 0) > 0, "export evidence must include generated files");
expect(previewManifest?.authority === "NOT_AUTHORITY", "web preview manifest must remain non-authority");

const sourceFiles = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
  "app/(tabs)/system.tsx",
  "src/components/domain/mobile-scan-list-item.tsx",
  "src/components/domain/mobile-v1-status-rail.tsx",
  "src/components/layout/product-detail-header.tsx",
  "src/components/layout/product-detail-section.tsx",
];

for (const file of sourceFiles) {
  const source = readText(file);
  expect(!/fetch\s*\(|axios|react-query|swr|graphql-request|expo-sqlite|sqlite3/.test(source), `${file}: must not add runtime/API/DB client`);
  expect(!/KIS|Alpaca|submitOrder|placeOrder|sendLiveOrder|approveOrder|cancelOrder/.test(source), `${file}: must not add broker/order mutation path`);
}

if (findings.length > 0) {
  console.error("[WEB_EXPORT_BOUNDARY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[WEB_EXPORT_BOUNDARY_OK] local web export evidence preserves non-deployment boundaries");
