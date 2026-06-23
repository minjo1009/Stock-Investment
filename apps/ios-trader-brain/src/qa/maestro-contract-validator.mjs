import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const flowPath = join(root, ".maestro/readonly-smoke.yaml");
const appJson = JSON.parse(readFileSync(join(root, "app.json"), "utf8"));
const findings = [];

if (!existsSync(flowPath)) {
  findings.push(".maestro/readonly-smoke.yaml must exist");
} else {
  const flow = readFileSync(flowPath, "utf8");
  if (!flow.includes(`appId: ${appJson.expo?.ios?.bundleIdentifier}`)) {
    findings.push("Maestro appId must match ios.bundleIdentifier");
  }
  for (const required of ["Read-only", "NOT_AUTHORITY", "BRAIN", "PORTFOLIO", "ORDERS", "SYSTEM"]) {
    if (!flow.includes(required)) findings.push(`Maestro flow missing ${required}`);
  }
  if (/BUY|SELL|EXECUTE|LIVE DEPLOY|REAL CAPITAL|BROKER SUBMIT|PLACE ORDER/.test(flow)) {
    findings.push("Maestro flow must not contain executable trading action language");
  }
}

if (findings.length > 0) {
  console.error("[MAESTRO_CONTRACT_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[MAESTRO_CONTRACT_OK] read-only Maestro structure is defined; native execution not run");
