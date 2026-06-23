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
  {
    component: "DecisionHeader",
    file: "src/stories/decision-header.stories.tsx",
    requiredExports: ["FreshSource", "StaleSource", "MissingSource", "UnknownSource", "Blocked", "DisabledAction"],
    requiredTerms: ["Domain/DecisionHeader", "component: DecisionHeader"],
  },
  {
    component: "EvidenceList",
    file: "src/stories/evidence-list.stories.tsx",
    requiredExports: ["FreshSource", "StaleSource", "MissingSource", "UnknownSource", "Blocked", "DisabledAction"],
    requiredTerms: ["Domain/EvidenceList", "component: EvidenceList"],
  },
  {
    component: "RiskGate",
    file: "src/stories/risk-gate.stories.tsx",
    requiredExports: ["FreshSource", "StaleSource", "MissingSource", "UnknownSource", "Blocked", "DisabledAction"],
    requiredTerms: ["Domain/RiskGate", "component: RiskGate"],
  },
  {
    component: "DisabledActionBar",
    file: "src/stories/disabled-action-bar.stories.tsx",
    requiredExports: ["FreshSource", "StaleSource", "MissingSource", "UnknownSource", "Blocked", "DisabledAction"],
    requiredTerms: ["Domain/DisabledActionBar", "component: DisabledActionBar"],
  },
  {
    component: "MobileV1StatusRail",
    file: "src/stories/mobile-v1-status-rail.stories.tsx",
    requiredExports: ["NotAccepted", "DiagnosticOnly", "Forbidden"],
    requiredTerms: ["Domain/MobileV1StatusRail", "component: MobileV1StatusRail"],
  },
  {
    component: "ProductDetailHeader",
    file: "src/stories/product-detail-header.stories.tsx",
    requiredExports: ["Default", "BlockedState", "UnknownState"],
    requiredTerms: ["Layout/ProductDetailHeader", "component: ProductDetailHeader"],
  },
  {
    component: "ProductDetailSection",
    file: "src/stories/product-detail-section.stories.tsx",
    requiredExports: ["Overview", "Evidence", "Source", "Risk", "Validation"],
    requiredTerms: ["Layout/ProductDetailSection", "component: ProductDetailSection"],
  },
  {
    component: "MobileScanListItem",
    file: "src/stories/mobile-scan-list-item.stories.tsx",
    requiredExports: ["BrainCandidate", "PortfolioPosition", "OrderRow"],
    requiredTerms: ["Domain/MobileScanListItem", "component: MobileScanListItem"],
  },
  {
    component: "EvidenceStatusChip",
    file: "src/stories/evidence-status-chip.stories.tsx",
    requiredExports: ["Actual", "Derived", "Estimate", "Assumption", "Inference", "Unknown", "Blocker"],
    requiredTerms: ["Generic/EvidenceStatusChip", "component: EvidenceStatusChip"],
  },
  {
    component: "FreshnessBanner",
    file: "src/stories/freshness-banner.stories.tsx",
    requiredExports: ["Default", "Blocked"],
    requiredTerms: ["Domain/FreshnessBanner", "component: FreshnessBanner"],
  },
  {
    component: "SourceAttributionCard",
    file: "src/stories/source-attribution-card.stories.tsx",
    requiredExports: ["Default", "Blocked"],
    requiredTerms: ["Domain/SourceAttributionCard", "component: SourceAttributionCard"],
  },
  {
    component: "NavigationContextBar",
    file: "src/stories/navigation-context-bar.stories.tsx",
    requiredExports: ["CandidatePath", "OrderPath"],
    requiredTerms: ["Layout/NavigationContextBar", "component: NavigationContextBar"],
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

console.log("[STORY_COVERAGE_OK] regression-critical foundation and domain stories found");
