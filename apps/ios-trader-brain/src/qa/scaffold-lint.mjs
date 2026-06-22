import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const requiredFiles = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
  "app/(tabs)/system.tsx",
  "src/components/foundation/app-text.tsx",
  "src/components/foundation/badge.tsx",
  "src/components/foundation/card-container.tsx",
  "src/components/layout/screen-container.tsx",
  "src/components/layout/section-container.tsx",
  "src/components/generic/metric-card.tsx",
  "src/components/generic/status-row.tsx",
  "src/components/generic/source-freshness-badge.tsx",
  "src/components/generic/blocker-list.tsx",
  "src/components/domain/decision-header.tsx",
  "src/components/domain/evidence-list.tsx",
  "src/components/domain/validation-readiness-panel.tsx",
  "src/components/domain/risk-gate.tsx",
  "src/components/domain/disabled-action-bar.tsx",
  "src/components/domain/chart-with-source-state.tsx",
  "src/components/domain/system-health.tsx",
  "src/components/domain/order-state-summary.tsx",
  "src/read-models/common.ts",
  "src/read-models/index.ts",
  "src/qa/frontend-safety-validator.mjs",
  "src/qa/read-model-fixture-validator.mjs",
  "src/qa/scaffold-lint.mjs",
  "src/qa/storybook-smoke-test.mjs",
  "src/mocks/fixtures/foundation-states.ts",
  "src/mocks/fixtures/catalog-manifest.json",
  "src/mocks/fixtures/home.json",
  "src/mocks/fixtures/brain.json",
  "src/mocks/fixtures/candidate-detail.json",
  "src/mocks/fixtures/chain-detail.json",
  "src/mocks/fixtures/portfolio.json",
  "src/mocks/fixtures/position-detail.json",
  "src/mocks/fixtures/orders.json",
  "src/mocks/fixtures/order-detail.json",
  "src/mocks/fixtures/system-health.json",
  "src/stories/app-text.stories.tsx",
  "src/stories/badge.stories.tsx",
  "src/stories/card-container.stories.tsx",
  "src/stories/screen-container.stories.tsx",
  "src/stories/section-container.stories.tsx",
  "src/stories/metric-card.stories.tsx",
  "src/stories/status-row.stories.tsx",
  "src/stories/source-freshness-badge.stories.tsx",
  "src/stories/blocker-list.stories.tsx",
  "src/stories/decision-header.stories.tsx",
  "src/stories/evidence-list.stories.tsx",
  "src/stories/validation-readiness-panel.stories.tsx",
  "src/stories/risk-gate.stories.tsx",
  "src/stories/disabled-action-bar.stories.tsx",
  "src/stories/chart-with-source-state.stories.tsx",
  "src/stories/system-health.stories.tsx",
  "src/stories/order-state-summary.stories.tsx",
  ".storybook/main.ts",
  ".storybook/preview.ts",
];

const missing = requiredFiles.filter((file) => !existsSync(join(process.cwd(), file)));

if (missing.length > 0) {
  console.error("[SCAFFOLD_LINT_FAIL] missing required files");
  for (const file of missing) {
    console.error(`- ${file}`);
  }
  process.exit(1);
}

const tabLayout = readFileSync(join(process.cwd(), "app/(tabs)/_layout.tsx"), "utf8");
const forbiddenTabs = ["backtest", "paper", "live"];
const tabFindings = forbiddenTabs.filter((tab) => new RegExp(`name:\\s*["']${tab}["']`, "i").test(tabLayout));

if (tabFindings.length > 0) {
  console.error("[SCAFFOLD_LINT_FAIL] lifecycle states must not be top-level tabs");
  for (const tab of tabFindings) {
    console.error(`- ${tab}`);
  }
  process.exit(1);
}

console.log("[SCAFFOLD_LINT_OK] scaffold files and tab boundaries are present");
