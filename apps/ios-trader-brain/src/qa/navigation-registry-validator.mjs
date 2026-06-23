import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const registryPath = join(process.cwd(), "src/qa/navigation-registry.json");
const findings = [];

if (!existsSync(registryPath)) {
  findings.push("navigation-registry.json must exist");
} else {
  const registry = JSON.parse(readFileSync(registryPath, "utf8"));
  if (registry.contractVersion !== "navigation-registry-v1") findings.push("contractVersion must be navigation-registry-v1");
  if (registry.authority !== "NOT_AUTHORITY") findings.push("authority must remain NOT_AUTHORITY");
  const ids = new Set();
  for (const route of registry.routes ?? []) {
    if (ids.has(route.id)) findings.push(`duplicate route id ${route.id}`);
    ids.add(route.id);
    if (!route.path?.startsWith("/")) findings.push(`${route.id}: path must start with /`);
    if (!["tab", "detail"].includes(route.surface)) findings.push(`${route.id}: surface must be tab or detail`);
    if (!existsSync(join(process.cwd(), route.file))) findings.push(`${route.id}: file missing ${route.file}`);
  }
  for (const required of ["home", "brain", "portfolio", "orders", "system", "candidate-detail", "chain-detail", "position-detail", "order-detail"]) {
    if (!ids.has(required)) findings.push(`missing route id ${required}`);
  }
}

if (findings.length > 0) {
  console.error("[NAVIGATION_REGISTRY_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[NAVIGATION_REGISTRY_OK] route registry matches scaffold surfaces");
