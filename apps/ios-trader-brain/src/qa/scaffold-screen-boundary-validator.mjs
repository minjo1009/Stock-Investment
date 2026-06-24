import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const routeFiles = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
  "app/(tabs)/system.tsx",
  "app/brain/candidate/[candidateId].tsx",
  "app/brain/chain/[chainId].tsx",
  "app/portfolio/position/[positionId].tsx",
  "app/orders/[orderId].tsx",
];

const forbiddenPatterns = [
  /\bonSubmit\s*=/,
  /\bonExecute\s*=/,
  /\bfetch\s*\(/,
  /\bexpo-sqlite\b/i,
  /\bsqlite3\b/i,
];

const findings = [];

function hasReadOnlyBoundary(content) {
  return (
    content.includes("Read-only") ||
    content.includes("read-only") ||
    content.includes("읽기 전용") ||
    content.includes("읽기전용")
  );
}

function hasProductBoundary(content) {
  return /Scaffold-only|scaffold-only|fixture-backed|production V1|Phone-first v1|Phone-first v2|NOT_AUTHORITY/.test(content);
}

for (const file of routeFiles) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing route file`);
    continue;
  }

  const content = readFileSync(path, "utf8");
  if (!hasReadOnlyBoundary(content)) {
    findings.push(`${file}: missing visible read-only boundary`);
  }
  if (!content.includes("NOT_AUTHORITY")) {
    findings.push(`${file}: missing visible NOT_AUTHORITY boundary`);
  }
  if (!hasProductBoundary(content)) {
    findings.push(`${file}: missing scaffold/product-boundary copy`);
  }
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(content)) {
      findings.push(`${file}: forbidden integration or submit pattern ${pattern}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[SCAFFOLD_SCREEN_BOUNDARY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[SCAFFOLD_SCREEN_BOUNDARY_OK] route surfaces preserve read-only scaffold/product boundaries");
