import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const appRoot = process.cwd();
const scanRoots = ["app", "src", ".storybook"];
const allowedExtensions = new Set([".ts", ".tsx", ".js", ".jsx", ".json"]);
const excludedFiles = new Set([
  "src/qa/frontend-safety-validator.mjs",
  "src/qa/required-post-scaffold-hardening.mjs",
  "src/qa/read-model-fixture-validator.mjs",
  "src/qa/route-link-validator.mjs",
  // Historical Task3811 artifact only; not an active validator command.
  "src/qa/pre-screen-gpt-loop-validator.mjs",
  "src/qa/scaffold-lint.mjs",
  "src/qa/scaffold-screen-boundary-validator.mjs",
  "src/qa/screenshot-qa-validator.mjs",
  "src/qa/storybook-smoke-test.mjs",
  "src/read-models/common.ts",
  "src/read-models/index.ts",
]);

const forbiddenVisibleTerms = [
  "BUY",
  "SELL",
  "EXECUTE",
  "LIVE DEPLOY",
  "REAL CAPITAL",
  "BROKER SUBMIT",
  "PLACE ORDER",
];

const forbiddenIntegrationPatterns = [
  /\bfrom\s+["'][^"']*(?:kis|alpaca|broker|trading\.db)[^"']*["']/i,
  /\brequire\(["'][^"']*(?:kis|alpaca|broker|trading\.db)[^"']*["']\)/i,
  /\bfetch\([^)]*(?:kis|alpaca|broker|paper|live|order)/i,
  /\bimport\s*\([^)]*(?:kis|alpaca|broker|trading\.db)[^)]*\)/i,
  /\bexpo-sqlite\b/i,
  /\bsqlite3\b/i,
];

const disabledContextPattern =
  /\b(disabled|blocked|actionState\s*[:=]\s*["']disabled["']|disabledReason|requiredGovernanceChange|mutationPermitted\s*[:=]\s*false)\b/i;

const handlerPattern =
  /\b(onPress|onSubmit|onExecute|onClick|handleSubmit|handleExecute|submitOrder|placeOrder|brokerSubmit)\b/i;

function walk(dir, files = []) {
  if (!existsSync(dir)) {
    return files;
  }

  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      walk(fullPath, files);
    } else if (allowedExtensions.has(extname(entry))) {
      files.push(fullPath);
    }
  }

  return files;
}

const findings = [];

for (const root of scanRoots) {
  for (const file of walk(join(appRoot, root))) {
    const relativePath = relative(appRoot, file).replaceAll("\\", "/");
    if (excludedFiles.has(relativePath)) {
      continue;
    }

    const content = readFileSync(file, "utf8");
    const lines = content.split(/\r?\n/);

    for (const term of forbiddenVisibleTerms) {
      for (const [index, line] of lines.entries()) {
        if (!line.includes(term)) {
          continue;
        }

        const start = Math.max(0, index - 8);
        const end = Math.min(lines.length, index + 9);
        const context = lines.slice(start, end).join("\n");
        const hasDisabledContext = disabledContextPattern.test(context);
        const hasHandler = handlerPattern.test(context);

        if (!hasDisabledContext || hasHandler) {
          findings.push(
            `${relativePath}:${index + 1}: forbidden visible action term ${term} without disabled/blocked governance context`
          );
        }
      }
    }

    for (const pattern of forbiddenIntegrationPatterns) {
      if (pattern.test(content)) {
        findings.push(`${relativePath}: forbidden integration pattern ${pattern}`);
      }
    }
  }
}

if (findings.length > 0) {
  console.error("[FRONTEND_SAFETY_FAIL]");
  for (const finding of findings) {
    console.error(`- ${finding}`);
  }
  process.exit(1);
}

console.log("[FRONTEND_SAFETY_OK] no forbidden enabled action or integration markers found");
