import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

// SUPERSEDED_BY_USER_CLARIFICATION:
// HISTORICAL_ARTIFACT_ONLY
// NOT_ACTIVE_VALIDATOR
// NOT_REQUIRED_BY_TEST_OR_LINT
// DO_NOT_REENABLE_WITHOUT_USER_APPROVAL
// Task3811 is retained as a historical artifact only. It is not part of the
// active frontend test command path, and "10 loops" means captured GPT-Codex
// work cycles rather than ten validators.

const appRoot = process.cwd();
const fixtureDir = join(appRoot, "src/mocks/fixtures");
const findings = [];
const passedLoops = [];

const screenFixtureFiles = [
  "home.json",
  "brain.json",
  "candidate-detail.json",
  "chain-detail.json",
  "portfolio.json",
  "position-detail.json",
  "orders.json",
  "order-detail.json",
  "system-health.json",
];

const domainComponents = [
  "src/components/domain/decision-header.tsx",
  "src/components/domain/evidence-list.tsx",
  "src/components/domain/validation-readiness-panel.tsx",
  "src/components/domain/risk-gate.tsx",
  "src/components/domain/disabled-action-bar.tsx",
  "src/components/domain/chart-with-source-state.tsx",
  "src/components/domain/system-health.tsx",
  "src/components/domain/order-state-summary.tsx",
];

const domainStories = [
  "src/stories/decision-header.stories.tsx",
  "src/stories/evidence-list.stories.tsx",
  "src/stories/validation-readiness-panel.stories.tsx",
  "src/stories/risk-gate.stories.tsx",
  "src/stories/disabled-action-bar.stories.tsx",
  "src/stories/chart-with-source-state.stories.tsx",
  "src/stories/system-health.stories.tsx",
  "src/stories/order-state-summary.stories.tsx",
];

const storyStates = [
  "FreshSource",
  "StaleSource",
  "MissingSource",
  "UnknownSource",
  "Blocked",
  "DisabledAction",
  "ChartMissing",
  "SourceNotAttached",
];

function fail(loop, message) {
  findings.push(`${loop}: ${message}`);
}

function pass(loop) {
  passedLoops.push(loop);
}

function readJson(file) {
  return JSON.parse(readFileSync(join(fixtureDir, file), "utf8"));
}

function walk(value, visitor, path = "$") {
  visitor(value, path);
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(item, visitor, `${path}[${index}]`));
  } else if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) {
      walk(item, visitor, `${path}.${key}`);
    }
  }
}

function collectFiles(dir, files = []) {
  if (!existsSync(dir)) return files;
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      collectFiles(fullPath, files);
    } else if ([".ts", ".tsx", ".js", ".jsx", ".json"].includes(extname(entry))) {
      files.push(fullPath);
    }
  }
  return files;
}

const fixtures = Object.fromEntries(screenFixtureFiles.map((file) => [file, readJson(file)]));

{
  const loop = "Loop 1 fixture catalog authority";
  const manifest = readJson("catalog-manifest.json");
  if (manifest.authority !== "NOT_AUTHORITY") fail(loop, "catalog must remain NOT_AUTHORITY");
  if (manifest.readPath !== "json_catalog") fail(loop, "catalog readPath must remain json_catalog");
  for (const file of screenFixtureFiles) {
    if (!manifest.fixtureFiles.includes(file)) fail(loop, `${file} missing from catalog manifest`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 2 governance hard state";
  for (const [file, fixture] of Object.entries(fixtures)) {
    const governance = fixture.governance;
    if (governance.strategyAcceptance !== "NOT_ACCEPTED") fail(loop, `${file} strategy status changed`);
    if (governance.deploymentReadiness !== "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY") {
      fail(loop, `${file} deployment status changed`);
    }
    if (governance.realCapital !== "FORBIDDEN") fail(loop, `${file} real-capital status changed`);
    if (governance.brokerMutationPermitted !== false) fail(loop, `${file} broker mutation opened`);
    if (governance.paperPermission !== false) fail(loop, `${file} paper permission opened`);
    if (governance.livePermission !== false) fail(loop, `${file} live permission opened`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 3 freshness coverage";
  const statuses = new Set();
  for (const fixture of Object.values(fixtures)) {
    walk(fixture, (value) => {
      if (value && typeof value === "object" && "sourceLabel" in value && "freshnessStatus" in value) {
        statuses.add(value.freshnessStatus);
      }
    });
  }
  for (const status of ["FRESH", "STALE", "MISSING", "UNKNOWN"]) {
    if (!statuses.has(status)) fail(loop, `${status} coverage missing`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 4 disabled action coverage";
  let actionCount = 0;
  for (const fixture of Object.values(fixtures)) {
    walk(fixture, (value, path) => {
      if (value && typeof value === "object" && "actionState" in value) {
        actionCount += 1;
        if (value.actionState !== "disabled") fail(loop, `${path} action is not disabled`);
        if (!value.disabledReason) fail(loop, `${path} missing disabledReason`);
        if (!Array.isArray(value.requiredGovernanceChange) || value.requiredGovernanceChange.length === 0) {
          fail(loop, `${path} missing requiredGovernanceChange`);
        }
      }
    });
  }
  if (actionCount === 0) fail(loop, "no disabled actions found");
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 5 domain contract files";
  for (const file of domainComponents) {
    if (!existsSync(join(appRoot, file))) fail(loop, `${file} missing`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 6 domain story state matrix";
  for (const file of domainStories) {
    const fullPath = join(appRoot, file);
    if (!existsSync(fullPath)) {
      fail(loop, `${file} missing`);
      continue;
    }
    const content = readFileSync(fullPath, "utf8");
    for (const state of storyStates) {
      if (!new RegExp(`export\\s+const\\s+${state}\\b`).test(content)) {
        fail(loop, `${file} missing ${state}`);
      }
    }
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 7 story fixture attachment";
  for (const file of domainStories) {
    const content = readFileSync(join(appRoot, file), "utf8");
    if (!content.includes("../mocks/fixtures/")) fail(loop, `${file} does not import fixture JSON`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 8 placeholder tabs only";
  const tabs = {
    "app/(tabs)/index.tsx": "HOME",
    "app/(tabs)/brain.tsx": "BRAIN",
    "app/(tabs)/portfolio.tsx": "PORTFOLIO",
    "app/(tabs)/orders.tsx": "ORDERS",
    "app/(tabs)/system.tsx": "SYSTEM",
  };
  for (const [file, title] of Object.entries(tabs)) {
    const content = readFileSync(join(appRoot, file), "utf8");
    if (!content.includes("PlaceholderScreen")) fail(loop, `${file} no longer uses PlaceholderScreen`);
    if (!content.includes(`title="${title}"`)) fail(loop, `${file} title changed from ${title}`);
    if (content.includes("../components/domain") || content.includes("../../src/components/domain")) {
      fail(loop, `${file} imports domain UI before product screen authorization`);
    }
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 9 chart source blocker states";
  const chartStatuses = new Set();
  for (const fixture of Object.values(fixtures)) {
    walk(fixture, (value) => {
      if (value && typeof value === "object" && "chartId" in value && "status" in value) {
        chartStatuses.add(value.status);
      }
    });
  }
  for (const status of ["CHART_MISSING", "SOURCE_NOT_ATTACHED"]) {
    if (!chartStatuses.has(status)) fail(loop, `${status} coverage missing`);
  }
  const chartComponent = readFileSync(join(appRoot, "src/components/domain/chart-with-source-state.tsx"), "utf8");
  for (const forbidden of ["Math.random", "synthetic", "fallbackData", "candles"]) {
    if (chartComponent.includes(forbidden)) fail(loop, `chart component contains ${forbidden}`);
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

{
  const loop = "Loop 10 integration boundary scan";
  const patterns = [
    /\bfrom\s+["'][^"']*(kis|alpaca|broker|trading\.db)[^"']*["']/i,
    /\bimport\s*\([^)]*(kis|alpaca|broker|trading\.db)[^)]*\)/i,
    /\bexpo-sqlite\b/i,
    /\bsqlite3\b/i,
  ];
  for (const root of ["app", "src"]) {
    for (const file of collectFiles(join(appRoot, root))) {
      const relativePath = relative(appRoot, file).replaceAll("\\", "/");
      if (relativePath.startsWith("src/qa/")) continue;
      const content = readFileSync(file, "utf8");
      for (const pattern of patterns) {
        if (pattern.test(content)) fail(loop, `${relativePath} matches ${pattern}`);
      }
    }
  }
  if (!findings.some((finding) => finding.startsWith(loop))) pass(loop);
}

if (findings.length > 0) {
  console.error("[PRE_SCREEN_GPT_LOOP_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

for (const loop of passedLoops) {
  console.log(`[LOOP_OK] ${loop}`);
}
console.log("[PRE_SCREEN_GPT_LOOP_OK] 10 pre-screen gates passed");
