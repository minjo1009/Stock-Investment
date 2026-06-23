import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function readText(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath}: missing`);
    return "";
  }
  return readFileSync(path, "utf8");
}

function readJson(relativePath) {
  const source = readText(relativePath);
  if (!source) return null;
  try {
    return JSON.parse(source);
  } catch (error) {
    findings.push(`${relativePath}: invalid JSON ${error.message}`);
    return null;
  }
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const packageJson = readJson("package.json");
const contract = readJson("src/qa/mobile-viewport-evidence-contract.json");
const manifest = readJson("src/qa/mobile-viewport-capture-manifest.json");
const runbook = readText("../../docs/reports/task_3871_mobile_frontend_v1_gpt_10_loop/visual_qa_runbook.md");

expect(packageJson?.scripts?.["validate:mobile-screenshot-evidence"] === "node src/qa/mobile-screenshot-evidence-validator.mjs", "validate:mobile-screenshot-evidence script must exist");
expect(contract?.evidenceScope === "WEB_PREVIEW_EVIDENCE_ONLY", "contract must remain web-preview-only");
expect(contract?.captureStatus === "CAPTURE_REQUIRED_NOT_RUN", "contract must not claim screenshot capture");
expect(contract?.hardState?.strategyAcceptance === "NOT_ACCEPTED", "strategy acceptance must remain NOT_ACCEPTED");
expect(contract?.hardState?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment readiness must remain diagnostic-only");
expect(contract?.hardState?.realCapital === "FORBIDDEN", "real capital must remain FORBIDDEN");
for (const forbidden of ["IOS_DEVICE_EVIDENCE", "IOS_SIMULATOR_EVIDENCE", "TESTFLIGHT_EVIDENCE", "APP_STORE_EVIDENCE", "DEPLOYMENT_EVIDENCE"]) {
  expect(contract?.forbiddenEvidenceClaims?.includes(forbidden), `contract must forbid ${forbidden}`);
}
for (const disallowed of ["iphone", "ipad", "testflight", "appstore", "native-ios"]) {
  expect(contract?.disallowedCaptureSources?.includes(disallowed), `contract must disallow ${disallowed} capture source claims`);
}
expect(manifest?.nativeEvidence === "NO_NATIVE_EVIDENCE", "manifest must state NO_NATIVE_EVIDENCE");
expect(manifest?.simulatorEvidence === "NO_IOS_SIMULATOR_EVIDENCE", "manifest must state NO_IOS_SIMULATOR_EVIDENCE");
expect(manifest?.testFlightEvidence === "NO_TESTFLIGHT_EVIDENCE", "manifest must state NO_TESTFLIGHT_EVIDENCE");
expect(Array.isArray(manifest?.routes) && manifest.routes.length === 9, "manifest must include nine web preview routes");
expect(Array.isArray(manifest?.viewports) && manifest.viewports.length === 3, "manifest must include three viewport targets");
expect(runbook.includes("Web Preview Evidence Only"), "runbook must state Web Preview Evidence Only");
expect(runbook.includes("Not Native Evidence"), "runbook must state Not Native Evidence");
expect(runbook.includes("Not Deployment Evidence"), "runbook must state Not Deployment Evidence");
expect(!/DEPLOYMENT_READY\s*=\s*true|REAL_CAPITAL_ALLOWED|PAPER_PERMISSION_GRANTED/.test(runbook), "runbook must not soften hard state");

if (findings.length > 0) {
  console.error("[MOBILE_SCREENSHOT_EVIDENCE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_SCREENSHOT_EVIDENCE_OK] mobile screenshot evidence remains web-preview-only and capture-not-run");
