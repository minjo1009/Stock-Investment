import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const appRoot = process.cwd();
const scanRoots = ["app", "src"];
const allowedExtensions = new Set([".ts", ".tsx", ".js", ".jsx", ".json"]);
const excludedFiles = new Set([
  "src/qa/frontend-safety-validator.mjs",
  "src/qa/required-post-scaffold-hardening.mjs",
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
  /\bKIS\b/i,
  /\bAlpaca\b/i,
  /\bbroker[_-]?submit\b/i,
  /\btrading\.db\b/i,
  /\bpaper[_-]?promote\b/i,
  /\blive[_-]?order\b/i,
];

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

    for (const term of forbiddenVisibleTerms) {
      if (content.includes(term)) {
        findings.push(`${relativePath}: forbidden visible action term ${term}`);
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
