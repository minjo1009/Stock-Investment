import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const fixtureDir = join(process.cwd(), "src/mocks/fixtures");
const fixtureFiles = [
  "home.json",
  "brain.json",
  "candidate-detail.json",
  "chain-detail.json",
  "portfolio.json",
  "position-detail.json",
  "orders.json",
  "order-detail.json",
  "system-health.json",
];
const forbiddenKeys = new Set([
  "candidate_score",
  "candidate_rank",
  "confidence_score",
]);
const freshnessStatuses = new Set(["FRESH", "STALE", "MISSING", "UNKNOWN", "NOT_APPLICABLE"]);
const findings = [];
const seenFreshness = new Set();

function readJson(file) {
  const path = join(fixtureDir, file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing fixture`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    findings.push(`${file}: invalid JSON ${error.message}`);
    return null;
  }
}

function walk(value, visitor, path = "$") {
  visitor(value, path);
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(item, visitor, `${path}[${index}]`));
  } else if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) {
      if (forbiddenKeys.has(key)) {
        findings.push(`${path}.${key}: forbidden invented read-model field`);
      }
      walk(item, visitor, `${path}.${key}`);
    }
  }
}

function validateShell(file, model) {
  if (!model || typeof model !== "object") {
    findings.push(`${file}: fixture must be an object`);
    return;
  }
  if (model.contractVersion !== "frontend-read-model-v1") {
    findings.push(`${file}: contractVersion must be frontend-read-model-v1`);
  }
  if (model.readPath !== "json_catalog") {
    findings.push(`${file}: readPath must be json_catalog for scaffold fixture snapshot`);
  }
  if (!model.governance) {
    findings.push(`${file}: missing governance`);
  } else {
    const governance = model.governance;
    if (governance.strategyAcceptance !== "NOT_ACCEPTED") {
      findings.push(`${file}: strategyAcceptance must remain NOT_ACCEPTED`);
    }
    if (governance.deploymentReadiness !== "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY") {
      findings.push(`${file}: deploymentReadiness must remain DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`);
    }
    if (governance.realCapital !== "FORBIDDEN") {
      findings.push(`${file}: realCapital must remain FORBIDDEN`);
    }
    for (const key of ["brokerMutationPermitted", "paperPermission", "livePermission"]) {
      if (governance[key] !== false) {
        findings.push(`${file}: governance.${key} must be false`);
      }
    }
  }
  if (!Array.isArray(model.blockers)) {
    findings.push(`${file}: blockers must be an array`);
  }
  if (!Array.isArray(model.disabledActions)) {
    findings.push(`${file}: disabledActions must be an array`);
  } else {
    validateDisabledActions(file, model.disabledActions);
  }
}

function validateDisabledActions(file, actions) {
  for (const [index, action] of actions.entries()) {
    if (action.actionState !== "disabled") {
      findings.push(`${file}: disabledActions[${index}].actionState must be disabled`);
    }
    if (!action.disabledReason) {
      findings.push(`${file}: disabledActions[${index}] missing disabledReason`);
    }
    if (!Array.isArray(action.requiredGovernanceChange) || action.requiredGovernanceChange.length === 0) {
      findings.push(`${file}: disabledActions[${index}] missing requiredGovernanceChange`);
    }
  }
}

function validateSourceState(file, path, sourceState) {
  if (
    !sourceState ||
    typeof sourceState !== "object" ||
    !("freshnessStatus" in sourceState) ||
    !("sourceLabel" in sourceState) ||
    !("strictGateAllowed" in sourceState)
  ) {
    return;
  }
  if (!freshnessStatuses.has(sourceState.freshnessStatus)) {
    findings.push(`${file}:${path}: invalid freshnessStatus ${sourceState.freshnessStatus}`);
    return;
  }
  seenFreshness.add(sourceState.freshnessStatus);
  if (!Array.isArray(sourceState.provenanceRefs)) {
    findings.push(`${file}:${path}: sourceState missing provenanceRefs`);
  }
  if (sourceState.strictGateAllowed !== false) {
    findings.push(`${file}:${path}: strictGateAllowed must remain false in scaffold fixtures`);
  }
}

function validateByFile(file, model) {
  if (!model) {
    return;
  }
  validateShell(file, model);
  walk(model, (value, path) => validateSourceState(file, path, value));

  if (file === "home.json" && !model.portfolioSnapshot) findings.push(`${file}: missing portfolioSnapshot`);
  if (file === "brain.json" && !Array.isArray(model.candidates)) findings.push(`${file}: missing candidates`);
  if (file === "candidate-detail.json" && !model.sections?.decisionSummary) {
    findings.push(`${file}: missing sections.decisionSummary`);
  }
  if (file === "chain-detail.json" && !Array.isArray(model.layers)) findings.push(`${file}: missing layers`);
  if (file === "portfolio.json" && !Array.isArray(model.positions)) findings.push(`${file}: missing positions`);
  if (file === "position-detail.json" && !model.sections?.reconciliation) {
    findings.push(`${file}: missing sections.reconciliation`);
  }
  if (file === "orders.json" && !Array.isArray(model.orderRows)) findings.push(`${file}: missing orderRows`);
  if (file === "order-detail.json" && !model.sections?.orderState) {
    findings.push(`${file}: missing sections.orderState`);
  }
  if (file === "system-health.json" && !model.controlState) findings.push(`${file}: missing controlState`);
}

const manifest = readJson("catalog-manifest.json");
if (!manifest) {
  findings.push("catalog-manifest.json: missing catalog manifest");
} else {
  if (manifest.authority !== "NOT_AUTHORITY") findings.push("catalog-manifest.json: authority must be NOT_AUTHORITY");
  if (manifest.readPath !== "json_catalog") findings.push("catalog-manifest.json: readPath must be json_catalog");
  if (!manifest.fingerprint) findings.push("catalog-manifest.json: missing fingerprint");
}

for (const file of fixtureFiles) {
  validateByFile(file, readJson(file));
}

for (const requiredStatus of ["FRESH", "STALE", "MISSING", "UNKNOWN"]) {
  if (!seenFreshness.has(requiredStatus)) {
    findings.push(`fixtures: missing ${requiredStatus} source-state coverage`);
  }
}

if (findings.length > 0) {
  console.error("[READ_MODEL_FIXTURE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[READ_MODEL_FIXTURE_OK] contract-shaped scaffold fixtures validated");
