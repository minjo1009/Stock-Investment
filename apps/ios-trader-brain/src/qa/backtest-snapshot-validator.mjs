import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const findings = [];

function readText(path) {
  const absolute = join(root, path);
  if (!existsSync(absolute)) {
    findings.push(`${path}: missing`);
    return "";
  }
  return readFileSync(absolute, "utf8");
}

function expectIncludes(source, needle, label) {
  if (!source.includes(needle)) findings.push(`${label}: missing ${needle}`);
}

const fixture = readText("src/read-models/backtestSnapshotFixture.ts");
const currentSnapshot = readText("../../data/frontend_snapshots/current_backtest_snapshot.json");
const contract = readText("../../docs/frontend_app_ssot/25_BACKTEST_SNAPSHOT_READ_PATH.md");
const pkg = JSON.parse(readText("package.json"));
let snapshot = null;

try {
  snapshot = currentSnapshot ? JSON.parse(currentSnapshot) : null;
} catch (error) {
  findings.push(`current_backtest_snapshot.json: invalid JSON ${error.message}`);
}

for (const required of [
  "frontend-backtest-snapshot-v1",
  "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT",
  "NOT_AUTHORITY",
  "DIAGNOSTIC_ONLY",
  "Task3903",
  "exit_chain_repaired_soft_boost_cap_top2_v1",
  "SOURCE_NOT_ATTACHED",
  "NOT_ACCEPTED",
  "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  "FORBIDDEN",
  "brokerMutationPermitted: false",
  "paperPermission: false",
  "livePermission: false",
  "current_backtest_snapshot.json",
  "equityCurve",
]) {
  expectIncludes(fixture, required, "backtestSnapshotFixture.ts");
}

if (snapshot) {
  const expected = {
    contractVersion: "frontend-backtest-snapshot-v1",
    snapshotType: "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT",
    authority: "NOT_AUTHORITY",
    displayState: "DIAGNOSTIC_ONLY",
    selectedTaskId: "Task3903",
  };
  for (const [key, value] of Object.entries(expected)) {
    if (snapshot[key] !== value) findings.push(`current_backtest_snapshot.json: ${key} must be ${value}`);
  }
  const governance = snapshot.governance ?? {};
  if (governance.strategyAcceptance !== "NOT_ACCEPTED") findings.push("snapshot governance strategyAcceptance changed");
  if (governance.deploymentReadiness !== "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY") {
    findings.push("snapshot governance deploymentReadiness changed");
  }
  if (governance.realCapital !== "FORBIDDEN") findings.push("snapshot governance realCapital changed");
  if (governance.brokerMutationPermitted !== false) findings.push("snapshot brokerMutationPermitted must be false");
  if (governance.paperPermission !== false) findings.push("snapshot paperPermission must be false");
  if (governance.livePermission !== false) findings.push("snapshot livePermission must be false");
  if (!Array.isArray(snapshot.equityCurve) || snapshot.equityCurve.length === 0) {
    findings.push("snapshot equityCurve must include selected diagnostic equity points");
  }
  if (snapshot.chartSource?.status !== "READY") {
    findings.push("snapshot chartSource.status must be READY once equityCurve is attached");
  }
  if (!fixture.includes(`generatedAt": "${snapshot.generatedAt}"`)) {
    findings.push("backtestSnapshotFixture.ts must be generated from current_backtest_snapshot.json");
  }
}

for (const forbiddenPattern of [
  /\bfetch\s*\(/,
  /axios/,
  /react-query/,
  /swr/,
  /graphql-request/,
  /expo-sqlite/,
  /sqlite3/,
  /trading\.db/,
  /brokerSubmit/,
  /submitOrder/,
  /placeOrder/,
  /sendLiveOrder/,
  /KIS/,
  /Alpaca/,
]) {
  if (forbiddenPattern.test(fixture)) {
    findings.push(`backtestSnapshotFixture.ts: forbidden pattern ${forbiddenPattern}`);
  }
}

for (const required of [
  "must not read `trading.db` directly",
  "must not choose the newest file by timestamp",
  "must not treat a passing backtest as strategy acceptance",
  "Automatic update is allowed only for the selected snapshot pointer",
]) {
  expectIncludes(contract, required, "25_BACKTEST_SNAPSHOT_READ_PATH.md");
}

if (pkg.scripts?.["validate:backtest-snapshot"] !== "node src/qa/backtest-snapshot-validator.mjs") {
  findings.push("package.json: validate:backtest-snapshot script missing or unexpected");
}

if (!pkg.scripts?.test?.includes("npm run validate:backtest-snapshot")) {
  findings.push("package.json: test script must include validate:backtest-snapshot");
}

if (findings.length > 0) {
  console.error("[BACKTEST_SNAPSHOT_VALIDATOR_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[BACKTEST_SNAPSHOT_VALIDATOR_OK] read-only selected backtest snapshot boundary is enforced");
