import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const storyPath = join(process.cwd(), "src/stories/ui-state-panel.stories.tsx");
const componentPath = join(process.cwd(), "src/components/generic/ui-state-panel.tsx");
const findings = [];

if (!existsSync(componentPath)) findings.push("UiStatePanel component must exist");
if (!existsSync(storyPath)) {
  findings.push("UiStatePanel stories must exist");
} else {
  const story = readFileSync(storyPath, "utf8");
  for (const state of ["Default", "Loading", "Empty", "Error", "Blocked", "Stale", "Missing", "Unknown"]) {
    if (!story.includes(`export const ${state}`)) findings.push(`story missing ${state}`);
  }
  if (!story.includes("NOT_AUTHORITY")) findings.push("story must preserve NOT_AUTHORITY language");
  if (!story.includes("Missing source state remains unknown")) findings.push("story must preserve missing/unknown boundary");
}

if (findings.length > 0) {
  console.error("[UI_STATE_COVERAGE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[UI_STATE_COVERAGE_OK] UI state component covers blocked/stale/missing/unknown fixture states");
