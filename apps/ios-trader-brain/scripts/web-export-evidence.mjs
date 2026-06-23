import { execFileSync, execSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";

const root = process.cwd();
const distDir = join(root, "dist");

if (process.platform === "win32") {
  execSync("npx expo export --platform web --output-dir dist", {
    cwd: root,
    stdio: "inherit",
  });
} else {
  execFileSync("npx", ["expo", "export", "--platform", "web", "--output-dir", "dist"], {
    cwd: root,
    stdio: "inherit",
  });
}

if (!existsSync(distDir)) {
  console.error("[WEB_EXPORT_EVIDENCE_FAIL] dist directory missing");
  process.exit(1);
}

const files = [];
function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      walk(path);
    } else {
      files.push(relative(distDir, path).replaceAll("\\", "/"));
    }
  }
}
walk(distDir);

const manifest = {
  authority: "NOT_AUTHORITY",
  brokerMutationPermitted: false,
  captureStatus: "LOCAL_EXPORT_EVIDENCE_ONLY",
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
  exportDirectory: "dist",
  fileCount: files.length,
  htmlCount: files.filter((file) => file.endsWith(".html")).length,
  indexHtmlPresent: files.includes("index.html"),
  jsCount: files.filter((file) => file.endsWith(".js")).length,
  realCapital: "FORBIDDEN",
  strategyAcceptance: "NOT_ACCEPTED",
};

mkdirSync(distDir, { recursive: true });
writeFileSync(join(distDir, "web-export-artifact-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log("[WEB_EXPORT_EVIDENCE_OK] local static export evidence generated");
