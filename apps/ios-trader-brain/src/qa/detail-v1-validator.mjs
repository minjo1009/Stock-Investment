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
const productDetailSections = ["Overview", "Evidence", "Source", "Risk", "Validation"];
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
  if (!content.includes("MobileV1StatusRail")) {
    findings.push(`${route.file}: missing mobile v1 status rail`);
  }
  let previousSectionIndex = -1;
  for (const section of productDetailSections) {
    const sectionMarker = `title="${section}"`;
    const sectionIndex = content.indexOf(sectionMarker);
    if (sectionIndex === -1) {
      findings.push(`${route.file}: missing Product Detail section ${section}`);
      continue;
    }
    if (sectionIndex < previousSectionIndex) {
      findings.push(`${route.file}: Product Detail section order is not Overview > Evidence > Source > Risk > Validation`);
    }
    previousSectionIndex = sectionIndex;
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
