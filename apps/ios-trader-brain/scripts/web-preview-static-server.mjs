import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";

const root = process.cwd();
const distDir = resolve(root, "dist");
const port = Number(process.argv[2] ?? process.env.PORT ?? 8099);

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
};

function resolveRequestPath(url) {
  const pathname = decodeURIComponent(new URL(url, `http://127.0.0.1:${port}`).pathname);
  const requestedPath = normalize(pathname).replace(/^([/\\])+/, "");
  const filePath = resolve(distDir, requestedPath);

  if (filePath !== distDir && !filePath.startsWith(`${distDir}${sep}`)) {
    return null;
  }

  if (existsSync(filePath) && statSync(filePath).isFile()) {
    return filePath;
  }

  return join(distDir, "index.html");
}

if (!existsSync(join(distDir, "index.html"))) {
  console.error("[WEB_PREVIEW_SERVER_FAIL] dist/index.html missing; run npm run evidence:web-export first");
  process.exit(1);
}

const server = createServer((request, response) => {
  const filePath = resolveRequestPath(request.url ?? "/");
  if (!filePath) {
    response.writeHead(403, { "content-type": contentTypes[".txt"] });
    response.end("Forbidden");
    return;
  }

  const extension = extname(filePath);
  response.writeHead(200, {
    "cache-control": "no-store",
    "content-type": contentTypes[extension] ?? "application/octet-stream",
  });
  response.end(readFileSync(filePath));
});

server.listen(port, "127.0.0.1", () => {
  console.log(`[WEB_PREVIEW_SERVER_OK] http://127.0.0.1:${port}`);
});
