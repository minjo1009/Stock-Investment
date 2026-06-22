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
const domainStoryFiles = [
  "src/stories/decision-header.stories.tsx",
  "src/stories/evidence-list.stories.tsx",
  "src/stories/validation-readiness-panel.stories.tsx",
  "src/stories/risk-gate.stories.tsx",
  "src/stories/disabled-action-bar.stories.tsx",
  "src/stories/chart-with-source-state.stories.tsx",
  "src/stories/system-health.stories.tsx",
  "src/stories/order-state-summary.stories.tsx",
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
const requiredDomainExports = [
  "FreshSource",
  "StaleSource",
  "MissingSource",
  "UnknownSource",
  "Blocked",
  "DisabledAction",
  "ChartMissing",
  "SourceNotAttached",
];
const findings = [];

function validateStoryFile(file, exportNames) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing story file`);
    return;
  }

  const content = readFileSync(path, "utf8");
  for (const exportName of exportNames) {
    if (!new RegExp(`export\\s+const\\s+${exportName}\\b`).test(content)) {
      findings.push(`${file}: missing ${exportName} story export`);
    }
  }
}

for (const file of storyFiles) {
  validateStoryFile(file, requiredExports);
}

for (const file of domainStoryFiles) {
  validateStoryFile(file, requiredDomainExports);
}

if (findings.length > 0) {
  console.error("[STORYBOOK_SMOKE_FAIL]");
  for (const finding of findings) {
    console.error(`- ${finding}`);
  }
  process.exit(1);
}

console.log("[STORYBOOK_SMOKE_OK] required foundation and domain stories are present");
