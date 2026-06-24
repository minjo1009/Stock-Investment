import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const requiredFiles = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/brain.tsx",
  "app/(tabs)/portfolio.tsx",
  "app/(tabs)/orders.tsx",
  "app/(tabs)/system.tsx",
  "app/brain/candidate/[candidateId].tsx",
  "app/brain/chain/[chainId].tsx",
  "app/portfolio/position/[positionId].tsx",
  "app/orders/[orderId].tsx",
];
const findings = [];

function hasReadOnlyBoundary(source) {
  return (
    source.includes("Read-only") ||
    source.includes("read-only") ||
    source.includes("읽기 전용") ||
    source.includes("읽기전용") ||
    source.includes("?쎄린?꾩슜")
  );
}

for (const file of requiredFiles) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing`);
    continue;
  }
  const source = readFileSync(path, "utf8");
  if (!hasReadOnlyBoundary(source)) {
    findings.push(`${file}: missing Read-only boundary`);
  }
  if (!source.includes("NOT_AUTHORITY")) findings.push(`${file}: missing NOT_AUTHORITY boundary`);
  if (/onSubmit=\{|onExecute=\{|placeOrder|submitOrder|brokerSubmit|sendLiveOrder|approveOrder|cancelOrder/.test(source)) {
    findings.push(`${file}: must not expose order or broker mutation handlers`);
  }
  if (/\bfetch\s*\(|axios|react-query|swr|graphql-request|expo-sqlite|sqlite3/.test(source)) {
    findings.push(`${file}: must not connect frontend directly to API or DB clients`);
  }
}

for (const file of [
  "src/read-models/homeFixture.ts",
  "src/read-models/brainFixture.ts",
  "src/read-models/portfolioFixture.ts",
  "src/read-models/ordersFixture.ts",
  "src/read-models/systemHealthFixture.ts",
  "src/read-models/candidateDetailFixture.ts",
  "src/read-models/chainDetailFixture.ts",
  "src/read-models/positionDetailFixture.ts",
  "src/read-models/orderDetailFixture.ts",
]) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing`);
    continue;
  }
  const source = readFileSync(path, "utf8");
  if (!source.includes("brokerMutationPermitted: false")) findings.push(`${file}: missing brokerMutationPermitted false`);
  if (!source.includes("paperPermission: false")) findings.push(`${file}: missing paperPermission false`);
  if (!source.includes("livePermission: false")) findings.push(`${file}: missing livePermission false`);
  if (!source.includes('realCapital: "FORBIDDEN"')) findings.push(`${file}: missing realCapital FORBIDDEN`);
}

if (findings.length > 0) {
  console.error("[FRONTEND_GOVERNANCE_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[FRONTEND_GOVERNANCE_OK] all surfaces preserve read-only NOT_AUTHORITY governance boundaries with local UI-only interaction allowed");
