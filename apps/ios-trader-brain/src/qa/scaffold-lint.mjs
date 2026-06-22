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
  "src/read-models/common.ts",
  "src/mocks/fixtures/foundation-states.ts",
  "src/stories/app-text.stories.tsx",
  "src/stories/badge.stories.tsx",
  "src/stories/card-container.stories.tsx",
  "src/stories/screen-container.stories.tsx",
  "src/stories/section-container.stories.tsx",
  "src/stories/metric-card.stories.tsx",
  "src/stories/status-row.stories.tsx",
  "src/stories/source-freshness-badge.stories.tsx",
  "src/stories/blocker-list.stories.tsx",
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
