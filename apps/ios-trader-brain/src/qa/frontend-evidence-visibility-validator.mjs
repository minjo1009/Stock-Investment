import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function read(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath} must exist`);
    return "";
  }
  return readFileSync(path, "utf8");
}

function expect(source, term, message) {
  if (!source.includes(term)) findings.push(message);
}

const tabFiles = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
  "app/(tabs)/system.tsx",
];

const detailFiles = [
  "app/brain/candidate/[candidateId].tsx",
  "app/brain/chain/[chainId].tsx",
  "app/portfolio/position/[positionId].tsx",
  "app/orders/[orderId].tsx",
];

for (const file of tabFiles) {
  const source = read(file);
  expect(source, "FreshnessBanner", `${file} must render FreshnessBanner`);
  expect(source, "sourceSummary", `${file} must bind source summary`);
  expect(source, "NOT_AUTHORITY", `${file} must preserve NOT_AUTHORITY`);
}

for (const file of detailFiles) {
  const source = read(file);
  expect(source, "NavigationContextBar", `${file} must render NavigationContextBar`);
  expect(source, "SourceAttributionCard", `${file} must render SourceAttributionCard`);
  expect(source, "sectionId=\"source\"", `${file} must include a Source detail section`);
  expect(source, "Read-only", `${file} must preserve read-only copy`);
}

for (const file of [
  "src/stories/evidence-status-chip.stories.tsx",
  "src/stories/freshness-banner.stories.tsx",
  "src/stories/source-attribution-card.stories.tsx",
  "src/stories/navigation-context-bar.stories.tsx",
]) {
  const source = read(file);
  expect(source, "export const", `${file} must expose Storybook states`);
}

if (findings.length > 0) {
  console.error("[FRONTEND_EVIDENCE_VISIBILITY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[FRONTEND_EVIDENCE_VISIBILITY_OK] source, freshness, unknown/blocker, and navigation context are visible");
