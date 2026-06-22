import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const routePatterns = [
  {
    file: "app/(tabs)/index.tsx",
    sourceFiles: ["app/(tabs)/index.tsx", "src/read-models/homeFixture.ts"],
    routes: ["/system"],
  },
  {
    file: "app/(tabs)/brain.tsx",
    sourceFiles: ["app/(tabs)/brain.tsx", "src/read-models/brainFixture.ts"],
    routes: [
      "/brain/candidate/fixture-candidate-review",
      "/brain/candidate/fixture-candidate-blocked",
    ],
  },
  {
    file: "app/(tabs)/portfolio.tsx",
    sourceFiles: ["app/(tabs)/portfolio.tsx", "src/read-models/portfolioFixture.ts"],
    routes: ["/portfolio/position/fixture-position-unknown"],
  },
  {
    file: "app/(tabs)/orders.tsx",
    sourceFiles: ["app/(tabs)/orders.tsx", "src/read-models/ordersFixture.ts"],
    routes: ["/orders/fixture-order-blocked"],
  },
  {
    file: "app/brain/candidate/[candidateId].tsx",
    sourceFiles: ["app/brain/candidate/[candidateId].tsx"],
    routes: ["/brain/chain/fixture-chain"],
  },
];
const routeFileByPrefix = new Map([
  ["/", "app/(tabs)/index.tsx"],
  ["/brain", "app/(tabs)/brain.tsx"],
  ["/portfolio", "app/(tabs)/portfolio.tsx"],
  ["/orders", "app/(tabs)/orders.tsx"],
  ["/system", "app/(tabs)/system.tsx"],
  ["/brain/candidate/", "app/brain/candidate/[candidateId].tsx"],
  ["/brain/chain/", "app/brain/chain/[chainId].tsx"],
  ["/portfolio/position/", "app/portfolio/position/[positionId].tsx"],
  ["/orders/", "app/orders/[orderId].tsx"],
]);
const findings = [];

function routeFileFor(route) {
  const matches = [...routeFileByPrefix.entries()]
    .filter(([prefix]) => route === prefix || route.startsWith(prefix))
    .sort((a, b) => b[0].length - a[0].length);
  return matches[0]?.[1] ?? null;
}

for (const { file, routes, sourceFiles } of routePatterns) {
  const path = join(process.cwd(), file);
  if (!existsSync(path)) {
    findings.push(`${file}: missing route source`);
    continue;
  }
  const sourceContents = sourceFiles
    .filter((sourceFile) => existsSync(join(process.cwd(), sourceFile)))
    .map((sourceFile) => readFileSync(join(process.cwd(), sourceFile), "utf8"));
  for (const route of routes) {
    if (!sourceContents.some((content) => content.includes(route))) {
      findings.push(`${file}: missing route reference ${route}`);
    }
    const targetFile = routeFileFor(route);
    if (!targetFile || !existsSync(join(process.cwd(), targetFile))) {
      findings.push(`${route}: missing target route file`);
    }
  }
}

if (findings.length > 0) {
  console.error("[ROUTE_LINK_FAIL]");
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log("[ROUTE_LINK_OK] scaffold route links resolve to local route files");
