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
  /\bonPress\s*=/,
  /\bonSubmit\s*=/,
  /\bonExecute\s*=/,
  /\bfetch\s*\(/,
  /\bexpo-sqlite\b/i,
  /\bsqlite3\b/i,
];
const findings = [];

for (const file of routeFiles) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing route file`);
    continue;
  }
  const content = readFileSync(path, "utf8");
  for (const token of ["Read-only", "NOT_AUTHORITY"]) {
    if (!content.includes(token)) {
      findings.push(`${file}: missing visible ${token} boundary`);
    }
  }
  if (!/Scaffold-only|scaffold-only/.test(content)) {
    findings.push(`${file}: missing scaffold-only copy`);
  }
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(content)) {
      findings.push(`${file}: forbidden interactive or integration pattern ${pattern}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[SCAFFOLD_SCREEN_BOUNDARY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[SCAFFOLD_SCREEN_BOUNDARY_OK] route surfaces preserve read-only scaffold boundaries");
