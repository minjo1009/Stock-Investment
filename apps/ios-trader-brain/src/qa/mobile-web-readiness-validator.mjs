import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function readText(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath} must exist`);
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
    findings.push(`${relativePath} must be valid JSON: ${error.message}`);
    return null;
  }
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const packageJson = readJson("package.json");
const manifest = readJson("public/manifest.json");
const readiness = readJson("src/qa/mobile-web-readiness.json");
const viewports = readJson("src/qa/mobile-web-viewports.json");
const indexHtml = readText("public/index.html");
const runbook = readText("../../docs/frontend_web/mobile_web_operator_runbook.md");
const projectSsot = readText("../../docs/frontend_app_ssot/00_PROJECT_SSOT.md");
const mobileBoundary = readText("../../docs/frontend_app_ssot/23_MOBILE_WEB_PWA_BOUNDARY.md");

expect(packageJson?.scripts?.["web:mobile"] === "expo start --web --host lan --port 8098", "web:mobile must run Expo web on LAN port 8098");
expect(packageJson?.scripts?.["build:web"] === "expo export --platform web", "build:web must export the Expo web bundle");
expect(packageJson?.scripts?.["validate:mobile-web-readiness"] === "node src/qa/mobile-web-readiness-validator.mjs", "validate:mobile-web-readiness script must run this validator");
expect(packageJson?.scripts?.test?.includes("validate:mobile-web-readiness"), "npm test must include mobile web readiness");

expect(indexHtml.includes('rel="manifest" href="/manifest.json"'), "public/index.html must link /manifest.json");
expect(indexHtml.includes("viewport-fit=cover"), "public/index.html must opt into iPhone safe-area viewport fitting");
expect(indexHtml.includes("apple-mobile-web-app-capable"), "public/index.html must include iOS home-screen metadata");
expect(!indexHtml.includes("serviceWorker.register"), "service worker must remain deferred in this task");

expect(manifest?.display === "standalone", "manifest display must be standalone");
expect(manifest?.orientation === "portrait", "manifest orientation must be portrait");
expect(manifest?.start_url === "/", "manifest start_url must be /");
expect(manifest?.scope === "/", "manifest scope must be /");
expect(Array.isArray(manifest?.icons) && manifest.icons.length >= 2, "manifest must declare at least two icons");
for (const icon of manifest?.icons ?? []) {
  const iconPath = icon.src?.startsWith("/") ? icon.src.slice(1) : icon.src;
  expect(iconPath && existsSync(join(root, "public", iconPath)), `manifest icon must exist: ${icon.src}`);
}

expect(readiness?.target === "mobile_web_first_phone_optimized", "readiness target must be mobile web first");
expect(readiness?.appleDeveloperProgramRequiredNow === false, "Apple Developer Program must not be required now");
expect(readiness?.macRequiredNow === false, "Mac must not be required now");
expect(readiness?.strategyAcceptance === "NOT_ACCEPTED", "strategy acceptance must remain NOT_ACCEPTED");
expect(readiness?.deploymentReadiness === "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment readiness must remain diagnostic only");
expect(readiness?.realCapital === "FORBIDDEN", "real capital must remain FORBIDDEN");
expect(readiness?.brokerMutationPermitted === false, "broker mutation must remain forbidden");
expect(readiness?.paperPermission === false, "paper permission must remain false");
expect(readiness?.livePermission === false, "live permission must remain false");
expect(readiness?.serviceWorker === "DEFERRED_WITH_REASON_AGGRESSIVE_CACHE_RISK", "service worker must be explicitly deferred with cache-risk reason");

expect(Array.isArray(viewports?.requiredViewports) && viewports.requiredViewports.length >= 4, "mobile viewport matrix must include at least four phone sizes");
expect(viewports?.requiredRoutes?.includes("/orders"), "mobile viewport matrix must include ORDERS route");
expect(viewports?.qaStatus === "SCREENSHOT_QA_REQUIRED_NEXT", "visual screenshot QA must remain an explicit next requirement");

expect(runbook.includes("Safari Share -> Add to Home Screen"), "mobile web runbook must document iPhone home-screen install");
expect(runbook.includes("No broker mutation"), "mobile web runbook must preserve no broker mutation");
expect(runbook.includes("FORBIDDEN"), "mobile web runbook must preserve real-capital forbidden status");
expect(!/APPROVED|DEPLOYMENT_READY\s*=\s*true|REAL_CAPITAL_ALLOWED/.test(runbook), "mobile web runbook must not imply approval or deployment readiness");
expect(projectSsot.includes("mobile-web-first phone preview"), "frontend SSOT must mention the near-term mobile-web-first preview target");
expect(mobileBoundary.includes("Strategy acceptance: `NOT_ACCEPTED`"), "mobile web boundary must preserve NOT_ACCEPTED");
expect(mobileBoundary.includes("Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`"), "mobile web boundary must preserve diagnostic-only deployment status");
expect(mobileBoundary.includes("Real capital: `FORBIDDEN`"), "mobile web boundary must preserve FORBIDDEN real capital status");
expect(mobileBoundary.includes("Runtime API connection from frontend"), "mobile web boundary must forbid runtime API connection from frontend");
expect(mobileBoundary.includes("Service worker caching"), "mobile web boundary must explicitly defer service worker caching");

if (findings.length > 0) {
  console.error("[MOBILE_WEB_READINESS_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MOBILE_WEB_READINESS_OK] mobile-web-first run path is defined without native, broker, deployment, or real-capital permission");
