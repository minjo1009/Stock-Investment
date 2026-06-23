import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = resolve(process.cwd(), "../..");
const baselineRoot = resolve(
  repoRoot,
  "data/artifacts/task_3836_frontend_actual_screenshot_capture"
);
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
const requiredFiles = [
  "screenshot_capture_manifest.json",
  "contact_sheet_iphone15_width.png",
  "after2/screenshot_capture_manifest_after2.json",
  "after2/contact_sheet_iphone15_width_after2.png",
];
const findings = [];

function readJson(relativePath) {
  const absolutePath = resolve(baselineRoot, relativePath);
  if (!existsSync(absolutePath)) {
    findings.push(`missing ${relativePath}`);
    return null;
  }

  try {
    return JSON.parse(readFileSync(absolutePath, "utf8").replace(/^\uFEFF/, ""));
  } catch (error) {
    findings.push(`${relativePath}: invalid JSON ${error.message}`);
    return null;
  }
}

for (const file of requiredFiles) {
  const absolutePath = resolve(baselineRoot, file);
  if (!existsSync(absolutePath)) {
    findings.push(`missing ${file}`);
    continue;
  }
  if (statSync(absolutePath).size <= 0) {
    findings.push(`${file}: empty file`);
  }
}

const beforeManifest = readJson("screenshot_capture_manifest.json");
const after2Manifest = readJson("after2/screenshot_capture_manifest_after2.json");

for (const [label, manifest] of [
  ["before", beforeManifest],
  ["after2", after2Manifest],
]) {
  if (!manifest) continue;
  if (manifest.authority !== "NOT_AUTHORITY") {
    findings.push(`${label}: authority must remain NOT_AUTHORITY`);
  }
  if (manifest.captureStatus !== "CAPTURED") {
    findings.push(`${label}: captureStatus must be CAPTURED`);
  }
  if (!Array.isArray(manifest.captures)) {
    findings.push(`${label}: captures must be an array`);
    continue;
  }

  const routeIds = new Set();
  for (const capture of manifest.captures) {
    routeIds.add(capture.routeId);
    if (capture.authority !== "NOT_AUTHORITY") {
      findings.push(`${label}/${capture.routeId}: authority must remain NOT_AUTHORITY`);
    }
    if (capture.captureStatus !== "CAPTURED") {
      findings.push(`${label}/${capture.routeId}: captureStatus must be CAPTURED`);
    }
    if (!capture.artifactPath) {
      findings.push(`${label}/${capture.routeId}: artifactPath missing`);
      continue;
    }
    const artifactPath = resolve(repoRoot, capture.artifactPath);
    if (!existsSync(artifactPath)) {
      findings.push(`${label}/${capture.routeId}: screenshot missing ${capture.artifactPath}`);
    }
  }

  for (const routeId of requiredRouteIds) {
    if (!routeIds.has(routeId)) {
      findings.push(`${label}: missing route ${routeId}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[SCREENSHOT_BASELINE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log(
  "[SCREENSHOT_BASELINE_OK] authority=NOT_AUTHORITY before_manifest=present after2_manifest=present route_count=9 capture_status=BASELINE_PRESENT"
);
