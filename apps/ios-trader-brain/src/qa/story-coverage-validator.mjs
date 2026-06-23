import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const regressionCriticalStories = [
  {
    component: "Badge",
    file: "src/stories/badge.stories.tsx",
    requiredExports: ["Default", "ReadOnly", "Blocked", "Stale", "Missing", "Unknown", "DisabledAction"],
    requiredTerms: ["Foundation/Badge", "component: Badge"],
  },
  {
    component: "StatusRow",
    file: "src/stories/status-row.stories.tsx",
    requiredExports: ["Default", "ReadOnly", "Blocked", "Stale", "Missing", "Unknown", "DisabledAction"],
    requiredTerms: ["Generic/StatusRow", "component: StatusRow"],
  },
];
const findings = [];

for (const story of regressionCriticalStories) {
  const path = join(process.cwd(), story.file);
  if (!existsSync(path)) {
    findings.push(`${story.component}: missing story file ${story.file}`);
    continue;
  }

  const content = readFileSync(path, "utf8");
  for (const term of story.requiredTerms) {
    if (!content.includes(term)) {
      findings.push(`${story.component}: missing story marker ${term}`);
    }
  }
  for (const exportName of story.requiredExports) {
    if (!new RegExp(`export\\s+const\\s+${exportName}\\b`).test(content)) {
      findings.push(`${story.component}: missing ${exportName} story export`);
    }
  }
}

if (findings.length > 0) {
  console.error("[STORY_COVERAGE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[STORY_COVERAGE_OK] Badge story found; StatusRow story found");
