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
const contract = readText("../../docs/frontend_app_ssot/25_BACKTEST_SNAPSHOT_READ_PATH.md");
const pkg = JSON.parse(readText("package.json"));

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
]) {
  expectIncludes(fixture, required, "backtestSnapshotFixture.ts");
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
  "Task3905 installs the frontend-side contract fixture and validator only",
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
