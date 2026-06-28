const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const PROVIDER = "public_headline_browser_watch";
const EXTRACTOR_VERSION = "public_headline_browser_crawler.v0.1.0";
const SELECTOR_VERSION = "public_headline_browser_crawler.selectors.v0.1.0";

const SOURCES = {
  prnewswire: {
    sourceId: "prnewswire_all_news_releases",
    url: "https://www.prnewswire.com/news-releases/",
    evidenceSelector: "a[href*='/news-releases/']",
    hrefIncludes: ["/news-releases/"],
    hrefExcludes: ["/rss/", "/resources/", "/account/", "#"],
    requireArticleUrl: true,
  },
  globenewswire: {
    sourceId: "globenewswire_newsroom_latest",
    url: "https://www.globenewswire.com/newsroom",
    evidenceSelector: "a[href*='/news-release/']",
    hrefIncludes: ["/news-release/"],
    hrefExcludes: ["#"],
  },
};

function parseArgs(argv) {
  const out = {
    sources: "prnewswire,globenewswire",
    rawDir: "data/raw/l0_public_headline_browser_smoke",
    eventPath: "data/artifacts/l0_public_headline_browser_smoke/collector_events.jsonl",
    summaryPath: "data/artifacts/l0_public_headline_browser_smoke/smoke_summary.json",
    maxHeadlines: "25",
    headless: "true",
    chromePath: process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe",
  };
  for (let index = 2; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) continue;
    const name = key.slice(2).replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
    const next = argv[index + 1];
    if (next && !next.startsWith("--")) {
      out[name] = next;
      index += 1;
    } else {
      out[name] = "true";
    }
  }
  return out;
}

function ensureDir(fileOrDir, isDir = false) {
  const dir = isDir ? fileOrDir : path.dirname(fileOrDir);
  fs.mkdirSync(dir, { recursive: true });
}

function nowZ() {
  return new Date().toISOString().replace(".000Z", "Z");
}

function safePart(value) {
  return String(value || "unknown").replace(/[^A-Za-z0-9_.=-]+/g, "_").slice(0, 120) || "unknown";
}

function sha256Buffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function sha256Text(text) {
  return sha256Buffer(Buffer.from(text, "utf8"));
}

function canonicalHeadlineHash(row) {
  const input = JSON.stringify({
    provider: PROVIDER,
    title: row.title,
    url: row.url,
    source_page_url: row.source_page_url,
  });
  return sha256Text(input);
}

function writeJson(filePath, payload) {
  ensureDir(filePath);
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function appendJsonl(filePath, payload) {
  ensureDir(filePath);
  fs.appendFileSync(filePath, `${JSON.stringify(payload)}\n`, "utf8");
}

async function extractHeadlines(page, source, capturedAt, maxHeadlines) {
  return page.evaluate(
    ({ source, capturedAt, maxHeadlines, provider, selectorVersion }) => {
      function norm(text) {
        return String(text || "").replace(/\s+/g, " ").trim();
      }
      function parentText(anchor) {
        const box = anchor.closest("article, li, .row, .card, div") || anchor.parentElement || anchor;
        return norm(box.innerText || box.textContent || "");
      }
      function allowedHref(href) {
        if (!href) return false;
        if (!source.hrefIncludes.every((part) => href.includes(part))) return false;
        if (source.hrefExcludes.some((part) => href.includes(part))) return false;
        if (source.requireArticleUrl && !/\.html(?:[?#].*)?$/i.test(href)) return false;
        return true;
      }
      function timeCandidate(text) {
        const patterns = [
          /\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)\s+\d{1,2},\s+\d{4},?\s+\d{1,2}:\d{2}\s+(?:ET|EST|EDT|UTC)\b/i,
          /\b[A-Z][a-z]+ \d{1,2}, \d{4} \d{1,2}:\d{2} (?:ET|EST|EDT|UTC)\b/,
          /\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?\b/,
          /\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)\s+\d{1,2},\s+\d{4}\b/i,
          /\b[A-Z][a-z]+ \d{1,2}, \d{4}\b/,
        ];
        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match) return match[0];
        }
        return "";
      }
      const rows = [];
      const seen = new Set();
      for (const anchor of Array.from(document.querySelectorAll("a[href]"))) {
        const href = anchor.href;
        const title = norm(anchor.innerText || anchor.textContent || "");
        if (!allowedHref(href)) continue;
        if (title.length < 20) continue;
        if (/^(news|products|contact|resources|client login|send a release|read more)$/i.test(title)) continue;
        const key = `${title} ${href}`.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        const evidenceText = parentText(anchor);
        rows.push({
          provider,
          source_id: source.sourceId,
          title,
          url: href,
          canonical_url: href.split("#")[0],
          source_page_url: source.url,
          detected_at: capturedAt,
          event_time: capturedAt,
          published_at: "",
          published_at_text: timeCandidate(evidenceText),
          title_text_span: title,
          evidence_selector: source.evidenceSelector,
          evidence_text_span: evidenceText.slice(0, 500),
          selector_version: selectorVersion,
          symbols: [],
          entities: [],
        });
        if (rows.length >= maxHeadlines) break;
      }
      return rows;
    },
    {
      source,
      capturedAt,
      maxHeadlines,
      provider: PROVIDER,
      selectorVersion: SELECTOR_VERSION,
    },
  );
}

async function collectSource(browser, sourceKey, options) {
  const source = SOURCES[sourceKey];
  if (!source) {
    throw new Error(`unknown source: ${sourceKey}`);
  }
  const capturedAt = nowZ();
  const stamp = capturedAt.replace(/[:.]/g, "").replace(/-/g, "");
  const captureDir = path.join(options.rawDir, `provider=${PROVIDER}`, `source=${safePart(sourceKey)}`, `captured_at=${stamp}`);
  ensureDir(captureDir, true);

  const page = await browser.newPage({ viewport: { width: 1365, height: 1200 } });
  let status = "EXPORTED";
  let errorCategory = "";
  let errorMessage = "";
  let headlines = [];
  let pageTitle = "";
  let html = "";
  try {
    await page.goto(source.url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3000);
    pageTitle = await page.title();
    html = await page.content();
    headlines = await extractHeadlines(page, source, capturedAt, Number(options.maxHeadlines));
    headlines = headlines.map((row) => ({ ...row, headline_hash: canonicalHeadlineHash(row) }));
    if (headlines.length === 0) {
      status = "EMPTY_PROVIDER_RESPONSE";
    }
  } catch (error) {
    status = "FAILED_RETRYABLE";
    errorCategory = error && error.name ? error.name : "Error";
    errorMessage = String(error && error.message ? error.message : error);
    html = await page.content().catch(() => "");
  }

  const htmlPath = path.join(captureDir, "page.html");
  fs.writeFileSync(htmlPath, html, "utf8");
  const screenshotPath = path.join(captureDir, "screenshot.png");
  await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => undefined);
  await page.close();

  const htmlSha256 = sha256Text(html);
  const payload = {
    schema_version: 1,
    provider: PROVIDER,
    source_key: sourceKey,
    source_id: source.sourceId,
    source_url: source.url,
    source_period: "latest_listing",
    captured_at: capturedAt,
    page_title: pageTitle,
    extractor_version: EXTRACTOR_VERSION,
    selector_version: SELECTOR_VERSION,
    terms_posture: "public_headline_only_no_login_no_paywall_no_bypass",
    raw_html_path: htmlPath,
    raw_html_sha256: htmlSha256,
    screenshot_path: fs.existsSync(screenshotPath) ? screenshotPath : "",
    headlines,
  };
  const rawPath = path.join(captureDir, "headlines.json");
  writeJson(rawPath, payload);
  const rawSha256 = sha256Buffer(fs.readFileSync(rawPath));
  const event = {
    provider: PROVIDER,
    source_family: PROVIDER,
    source_id: `${source.sourceId}::latest_listing`,
    status,
    row_count: headlines.length,
    raw_path: rawPath,
    raw_sha256: rawSha256,
    updated_at: capturedAt,
    error_category: errorCategory,
    error_message_redacted: errorMessage ? errorMessage.slice(0, 500) : "",
    secret_logged_flag: 0,
    diagnostic_only_flag: 1,
    trade_authority_flag: 0,
    broker_mutation_permitted_flag: 0,
    real_capital_permitted_flag: 0,
    notes: `source_key=${sourceKey};source_url=${source.url};html_path=${htmlPath};screenshot_path=${payload.screenshot_path};terms_posture=${payload.terms_posture}`,
  };
  appendJsonl(options.eventPath, event);
  return { source_key: sourceKey, status, row_count: headlines.length, raw_path: rawPath, raw_sha256: rawSha256 };
}

async function main() {
  const options = parseArgs(process.argv);
  const selected = options.sources.split(",").map((item) => item.trim()).filter(Boolean);
  ensureDir(options.eventPath);
  ensureDir(options.summaryPath);
  const browser = await chromium.launch({
    headless: options.headless !== "false",
    executablePath: options.chromePath,
    args: ["--disable-dev-shm-usage"],
  });
  const results = [];
  try {
    for (const sourceKey of selected) {
      results.push(await collectSource(browser, sourceKey, options));
    }
  } finally {
    await browser.close();
  }
  const summary = {
    schema_version: 1,
    provider: PROVIDER,
    extractor_version: EXTRACTOR_VERSION,
    updated_at: nowZ(),
    sources: results,
    total_rows: results.reduce((acc, item) => acc + Number(item.row_count || 0), 0),
    event_path: options.eventPath,
    diagnostic_only_flag: 1,
    trade_authority_flag: 0,
    broker_mutation_permitted_flag: 0,
    real_capital_permitted_flag: 0,
  };
  writeJson(options.summaryPath, summary);
  console.log(`[PUBLIC_HEADLINE_BROWSER_CRAWLER] sources=${results.length} rows=${summary.total_rows} event_path=${options.eventPath} summary_path=${options.summaryPath}`);
}

main().catch((error) => {
  console.error(`[PUBLIC_HEADLINE_BROWSER_CRAWLER_ERROR] ${error && error.stack ? error.stack : error}`);
  process.exit(1);
});
