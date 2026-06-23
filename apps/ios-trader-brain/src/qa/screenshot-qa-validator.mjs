import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const manifestPath = join(process.cwd(), "src/qa/screenshot-targets.json");
const requiredRouteIds = new Set([
  "home",
  "brain",
  "portfolio",
  "orders",
  "system",
  "candidate-detail",
  "position-detail",
  "order-detail",
  "chain-detail",
]);
const requiredHardState = {
  brokerMutationPermitted: false,
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  livePermission: false,
  paperPermission: false,
  realCapital: "FORBIDDEN",
  strategyAcceptance: "NOT_ACCEPTED",
};
const findings = [];

function readJson(path) {
  if (!existsSync(path)) {
    findings.push("screenshot-targets.json: missing");
    return null;
  }

  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    findings.push(`screenshot-targets.json: invalid JSON ${error.message}`);
    return null;
  }
}

const manifest = readJson(manifestPath);

if (manifest) {
  if (manifest.contractVersion !== "frontend-screenshot-qa-v1") {
    findings.push("contractVersion must be frontend-screenshot-qa-v1");
  }
  if (manifest.authority !== "NOT_AUTHORITY") {
    findings.push("authority must remain NOT_AUTHORITY");
  }
  if (manifest.captureStatus !== "TARGETS_READY_CAPTURE_NOT_RUN") {
    findings.push("captureStatus must not claim screenshot capture");
  }
  for (const [key, value] of Object.entries(requiredHardState)) {
    if (manifest.hardState?.[key] !== value) {
      findings.push(`hardState.${key} must be ${value}`);
    }
  }
  if (!Array.isArray(manifest.devicePresets) || manifest.devicePresets.length < 2) {
    findings.push("devicePresets must include compact and current iPhone widths");
  }
  if (!Array.isArray(manifest.targets)) {
    findings.push("targets must be an array");
  } else {
    const routeIds = new Set();
    for (const target of manifest.targets) {
      routeIds.add(target.routeId);
      if (!target.routePath?.startsWith("/")) {
        findings.push(`${target.routeId}: routePath must start with /`);
      }
      if (!target.artifactPath?.startsWith("data/artifacts/task_3834_frontend_screenshot_qa_baseline/")) {
        findings.push(`${target.routeId}: artifactPath must be task-scoped`);
      }
      if (!existsSync(join(process.cwd(), target.routeFile))) {
        findings.push(`${target.routeId}: routeFile missing ${target.routeFile}`);
      }
      const routeContent = existsSync(join(process.cwd(), target.routeFile))
        ? readFileSync(join(process.cwd(), target.routeFile), "utf8")
        : "";
      const hasReadOnlyBoundary =
        routeContent.includes("Read-only") || routeContent.includes("read-only") || routeContent.includes("읽기전용");
      if (!hasReadOnlyBoundary || !routeContent.includes("NOT_AUTHORITY")) {
        findings.push(`${target.routeId}: route file must preserve read-only NOT_AUTHORITY boundary`);
      }
      if (!["tab", "detail"].includes(target.surfaceType)) {
        findings.push(`${target.routeId}: surfaceType must be tab or detail`);
      }
    }
    for (const routeId of requiredRouteIds) {
      if (!routeIds.has(routeId)) {
        findings.push(`missing screenshot target ${routeId}`);
      }
    }
  }
}

if (findings.length > 0) {
  console.error("[SCREENSHOT_QA_TARGETS_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[SCREENSHOT_QA_TARGETS_OK] targets validated; screenshot capture not run");
