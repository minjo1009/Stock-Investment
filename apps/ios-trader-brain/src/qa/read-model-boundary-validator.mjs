import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const path = join(process.cwd(), "src/services/read-model-boundary.ts");
const findings = [];

if (!existsSync(path)) {
  findings.push("read-model-boundary.ts must exist");
} else {
  const source = readFileSync(path, "utf8");
  for (const required of [
    "authority: \"NOT_AUTHORITY\"",
    "source: \"static_fixture_snapshot\"",
    "runtimeConnectionPermitted: false",
    "directDbAccessPermitted: false",
    "brokerMutationPermitted: false",
  ]) {
    if (!source.includes(required)) findings.push(`missing boundary clause ${required}`);
  }
  if (/fetch\(|axios|sqlite|trading\.db|KIS|Alpaca|submit|placeOrder/.test(source)) {
    findings.push("boundary service must not import or call runtime, DB, or broker paths");
  }
}

if (findings.length > 0) {
  console.error("[READ_MODEL_BOUNDARY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[READ_MODEL_BOUNDARY_OK] read-model boundary remains static fixture only");
