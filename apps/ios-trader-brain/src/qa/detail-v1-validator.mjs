import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const detailRoutes = [
  {
    file: "app/brain/candidate/[candidateId].tsx",
    mode: "brain-candidate-v5",
    requiredTerms: ["지금의 생각", "해석", "근거", "위험 요인", "대응", "보조 확인"],
    orderedSections: ["지금의 생각", "해석", "근거", "위험 요인", "대응", "보조 확인"],
  },
  {
    file: "app/brain/chain/[chainId].tsx",
    mode: "brain-evidence-v5",
    requiredTerms: ["근거 상세", "요약", "핵심 포인트", "브레인 해석과 예측", "원문 전문", "보조 확인"],
    orderedSections: ["근거 상세", "요약", "핵심 포인트", "브레인 해석과 예측", "원문 전문", "보조 확인"],
  },
  {
    file: "app/portfolio/position/[positionId].tsx",
    mode: "product-detail-v1",
    requiredTerms: ["Position Detail v1", "Validation Status", "Review Actions", "Scaffold Boundary"],
    orderedSections: ['title="Overview"', 'title="Evidence"', 'title="Source"', 'title="Risk"', 'title="Validation"'],
  },
  {
    file: "app/orders/[orderId].tsx",
    mode: "product-detail-v1",
    requiredTerms: ["Order Detail v1", "Validation Status", "Review Actions", "Scaffold Boundary"],
    orderedSections: ['title="Overview"', 'title="Evidence"', 'title="Source"', 'title="Risk"', 'title="Validation"'],
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
      findings.push(`${route.file}: missing ${route.mode} term ${term}`);
    }
  }
  for (const term of ["read-only", "NOT_AUTHORITY"]) {
    if (!content.includes(term) && !content.includes(term === "read-only" ? "Read-only" : term)) {
      findings.push(`${route.file}: missing boundary term ${term}`);
    }
  }
  if (!content.includes("MobileV1StatusRail")) {
    findings.push(`${route.file}: missing mobile v1 status rail`);
  }
  const renderContent = content.slice(Math.max(0, content.indexOf("return (")));
  let previousSectionIndex = -1;
  for (const section of route.orderedSections) {
    const sectionIndex = renderContent.indexOf(section);
    if (sectionIndex === -1) {
      findings.push(`${route.file}: missing ordered section marker ${section}`);
      continue;
    }
    if (sectionIndex < previousSectionIndex) {
      findings.push(`${route.file}: section order is not preserved for ${route.mode}`);
    }
    previousSectionIndex = sectionIndex;
  }
  for (const term of forbiddenTerms) {
    if (content.includes(term)) {
      findings.push(`${route.file}: forbidden detail term ${term}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[DETAIL_V1_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[DETAIL_V1_OK] detail routes preserve read-only boundaries with Brain v5 detail hierarchy");
