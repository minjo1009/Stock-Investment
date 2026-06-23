import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const runbookPath = join(root, "../../docs/frontend_ios/ios_dev_client_operator_runbook.md");
const findings = [];

if (!existsSync(runbookPath)) {
  findings.push("docs/frontend_ios/ios_dev_client_operator_runbook.md must exist");
} else {
  const runbook = readFileSync(runbookPath, "utf8");
  const requiredTerms = [
    "com.minjo.stockinvestment.iostraderbrain.dev",
    "development",
    "development-simulator",
    "preview-internal",
    "BLOCKED_UNTIL_USER_OPERATOR",
    "NOT_ACCEPTED",
    "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "FORBIDDEN",
    "No broker mutation",
    "No live order",
    "No paper promotion",
  ];
  for (const term of requiredTerms) {
    if (!runbook.includes(term)) findings.push(`runbook missing ${term}`);
  }
  if (/APPROVED|REAL_CAPITAL_ALLOWED|DEPLOYMENT_READY\s*=\s*true/.test(runbook)) {
    findings.push("runbook must not contain approval or readiness uplift language");
  }
}

if (findings.length > 0) {
  console.error("[IOS_OPERATOR_RUNBOOK_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[IOS_OPERATOR_RUNBOOK_OK] iOS dev-client operator runbook exists and remains blocked until operator evidence");
