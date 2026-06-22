import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const storyFiles = [
  "src/stories/app-text.stories.tsx",
  "src/stories/badge.stories.tsx",
  "src/stories/card-container.stories.tsx",
];

const requiredExports = ["Default", "ReadOnly", "Blocked", "StaleUnknown"];
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
