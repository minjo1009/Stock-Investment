import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const detailRoutes = [
  {
    file: "app/brain/candidate/[candidateId].tsx",
    requiredTerms: ["Candidate Detail v1", "Validation Status", "Review Actions", "Scaffold Boundary"],
  },
  {
    file: "app/brain/chain/[chainId].tsx",
    requiredTerms: ["Chain Detail v1", "Chain Summary", "Chain Validation", "Evidence Chain", "Scaffold Boundary"],
  },
  {
    file: "app/portfolio/position/[positionId].tsx",
    requiredTerms: ["Position Detail v1", "Validation Status", "Review Actions", "Scaffold Boundary"],
  },
  {
    file: "app/orders/[orderId].tsx",
    requiredTerms: ["Order Detail v1", "Validation Status", "Review Actions", "Scaffold Boundary"],
  },
];
const forbiddenTerms = [
  "confidenceScore",
  "candidateScore",
  "candidateRank",
  "chainConfidence",
  "submitOrder",
  "placeOrder",
  "sendLiveOrder",
];
const findings = [];

for (const route of detailRoutes) {
  const path = join(process.cwd(), route.file);
  if (!existsSync(path)) {
    findings.push(`${route.file}: missing detail route`);
    continue;
  }

  const content = readFileSync(path, "utf8");
  for (const term of route.requiredTerms) {
    if (!content.includes(term)) {
      findings.push(`${route.file}: missing v1 term ${term}`);
    }
  }
  for (const term of ["Read-only", "NOT_AUTHORITY"]) {
    if (!content.includes(term)) {
      findings.push(`${route.file}: missing boundary term ${term}`);
    }
  }
  for (const term of forbiddenTerms) {
    if (content.includes(term)) {
      findings.push(`${route.file}: forbidden detail v1 term ${term}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[DETAIL_V1_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[DETAIL_V1_OK] detail routes preserve v1 read-only boundaries");
