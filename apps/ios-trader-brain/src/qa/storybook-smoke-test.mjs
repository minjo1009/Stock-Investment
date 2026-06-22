import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const storyFiles = [
  "src/stories/app-text.stories.tsx",
  "src/stories/badge.stories.tsx",
  "src/stories/card-container.stories.tsx",
  "src/stories/screen-container.stories.tsx",
  "src/stories/section-container.stories.tsx",
  "src/stories/metric-card.stories.tsx",
  "src/stories/status-row.stories.tsx",
  "src/stories/source-freshness-badge.stories.tsx",
  "src/stories/blocker-list.stories.tsx",
];

const requiredExports = [
  "Default",
  "ReadOnly",
  "Blocked",
  "Stale",
  "Missing",
  "Unknown",
  "DisabledAction",
];
const findings = [];

for (const file of storyFiles) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing story file`);
    continue;
  }

  const content = readFileSync(path, "utf8");
  for (const exportName of requiredExports) {
    if (!new RegExp(`export\\s+const\\s+${exportName}\\b`).test(content)) {
      findings.push(`${file}: missing ${exportName} story export`);
    }
  }
}

if (findings.length > 0) {
  console.error("[STORYBOOK_SMOKE_FAIL]");
  for (const finding of findings) {
    console.error(`- ${finding}`);
  }
  process.exit(1);
}

console.log("[STORYBOOK_SMOKE_OK] required foundation stories are present");
