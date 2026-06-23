import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function readJson(relativePath) {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    findings.push(`${relativePath} must exist`);
    return null;
  }
  return JSON.parse(readFileSync(path, "utf8"));
}

function expect(condition, message) {
  if (!condition) findings.push(message);
}

const packageJson = readJson("package.json");
const appJson = readJson("app.json");
const easJson = readJson("eas.json");

const bundleIdentifier = appJson?.expo?.ios?.bundleIdentifier;
expect(bundleIdentifier === "com.minjo.stockinvestment.iostraderbrain.dev", "ios.bundleIdentifier must be the governed dev bundle id");
expect(packageJson?.dependencies?.["expo-dev-client"], "expo-dev-client dependency must be installed");
expect(packageJson?.scripts?.["ios:dev"]?.includes("required-post-scaffold-hardening"), "ios:dev must remain blocked and must not run an EAS build");
expect(packageJson?.scripts?.["ios:dev:preflight"] === "node src/qa/dev-build-readiness-validator.mjs", "ios:dev:preflight must run dev-build readiness validator");

const build = easJson?.build ?? {};
expect(easJson?.cli?.appVersionSource === "local", "EAS appVersionSource must remain local");
expect(build.development?.developmentClient === true, "development profile must enable developmentClient");
expect(build.development?.distribution === "internal", "development profile must use internal distribution");
expect(build["development-simulator"]?.developmentClient === true, "development-simulator profile must enable developmentClient");
expect(build["development-simulator"]?.ios?.simulator === true, "development-simulator profile must set ios.simulator true");
expect(build["development-simulator"]?.distribution === "internal", "development-simulator profile must use internal distribution");
expect(build["preview-internal"]?.distribution === "internal", "preview-internal profile must use internal distribution");
expect(!build.production, "production build profile must not be configured in this diagnostic dev-client task");

for (const [scriptName, script] of Object.entries(packageJson?.scripts ?? {})) {
  if (/eas\s+build|eas-cli\s+build/.test(script)) {
    findings.push(`${scriptName} must not silently run eas build; operator runbook owns build execution`);
  }
}

if (findings.length > 0) {
  console.error("[EAS_BUILD_CONTRACT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[EAS_BUILD_CONTRACT_OK] dev-client EAS profiles are configured; native build execution remains operator-gated");
