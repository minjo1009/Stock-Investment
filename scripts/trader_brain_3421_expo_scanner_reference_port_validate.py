from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "ios-trader-brain"
SRC = APP / "src"
TABS_DIR = SRC / "app" / "(tabs)"
REPORT = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "task_3421_expo_scanner_reference_port.md"
GPT_PROMPT = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop11_gpt_uiux_prompt.md"
TOBE_SPEC = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop12_gpt_tobe_layer_spec.md"
BACKEND_LAYER_SPEC = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop13_gpt_backend_layer_blueprint.md"
LOOP14_GPT_APP_SPEC = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop14_gpt_brain_uiux_app_program.md"
LOOP15_VISUAL_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop15_visual_density_qa.md"
LOOP16_LIVE_DB_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop16_live_db_runtime_qa.md"
LOOP17_DB_TABS_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop17_db_evidence_tabs_qa.md"
LOOP18_CHART_UX_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop18_chart_marker_pnl_ux_qa.md"
LOOP19_EXTERNAL_DESIGN_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop19_external_design_typography_qa.md"
LOOP20_SCAN_DENSITY_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop20_scan_density_qa.md"
LOOP21_SCAN_ALIGNMENT_QA = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop21_scan_header_chart_alignment_qa.md"
LOOP22_GPT_SUBAGENT_P0_UIUX = ROOT / "docs" / "reports" / "task_3421_expo_scanner_reference_port" / "loop22_gpt_subagent_p0_uiux_implementation.md"
SCREENSHOT = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "expo_dom_3052_db_bound_loop4_430x932_dsf2.png"
LOOP16_LIVE_HOME = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop16_live_db_home_css426_dsf2.png"
LOOP16_LIVE_SETTINGS = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop16_live_db_settings_css426_dsf2.png"
LOOP17_DB_ANALYSIS = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop17_db_evidence_analysis_css426_dsf2.png"
LOOP17_DB_MARKET = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop17_db_evidence_market_css426_dsf2.png"
LOOP17_DB_RISK = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop17_db_evidence_risk_css426_dsf2.png"
LOOP18_CHART_ANALYSIS = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop18_chart_ux_analysis_css426_dsf2.png"
LOOP18_CHART_DETAIL = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop18_chart_ux_detail_css426_dsf2.png"
LOOP19_EXTERNAL_HOME = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop19_external_design_typography_home_css426_dsf2.png"
LOOP19_EXTERNAL_SCAN = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop19_external_design_typography_scan_css426_dsf2.png"
LOOP19_EXTERNAL_DETAIL = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop19_external_design_typography_detail_css426_dsf2.png"
LOOP19_EXTERNAL_ANALYSIS = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop19_external_design_typography_analysis_css426_dsf2.png"
LOOP20_SCAN_DENSITY_SCAN = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop20_scan_density_scan_css426_dsf2.png"
LOOP20_SCAN_DENSITY_DETAIL = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop20_scan_density_detail_css426_dsf2.png"
LOOP21_SCAN_ALIGNMENT_SCAN = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop21_scan_alignment_scan_css426_dsf2.png"
LOOP21_SCAN_ALIGNMENT_DETAIL = ROOT / "data" / "artifacts" / "task_3421_expo_scanner_reference_port" / "loop21_scan_alignment_detail_css426_dsf2.png"
CATALOG_LOOP = ROOT / "scripts" / "start_ios_runtime_catalog_loop.ps1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_tokens(name: str, text: str, tokens: list[str]) -> None:
    absent = [token for token in tokens if token not in text]
    if absent:
        raise AssertionError(f"{name} missing tokens: {absent}")


def main() -> None:
    paths = {
        "root_layout": SRC / "app" / "_layout.tsx",
        "tabs_layout": TABS_DIR / "_layout.tsx",
        "home": TABS_DIR / "index.tsx",
        "scan": TABS_DIR / "trades.tsx",
        "analysis": TABS_DIR / "analysis.tsx",
        "market": TABS_DIR / "market.tsx",
        "risk": TABS_DIR / "risk.tsx",
        "settings": TABS_DIR / "settings.tsx",
        "provider": SRC / "providers" / "cockpit-provider.tsx",
        "dom_tab": SRC / "components" / "dom-tab-screen.tsx",
        "dom_detail": SRC / "components" / "dom-detail-screen.tsx",
        "trade_detail_route": SRC / "app" / "trade" / "[id].tsx",
        "scanner_dom": SRC / "components" / "scanner-3052-dom.tsx",
        "scanner_web": SRC / "components" / "scanner-3052-web.tsx",
        "scanner_css": SRC / "components" / "scanner-3052.css",
        "cockpit_dom": SRC / "components" / "cockpit-3052-dom.tsx",
        "cockpit_web": SRC / "components" / "cockpit-3052-web.tsx",
        "cockpit_css": SRC / "components" / "cockpit-3052.css",
        "scanner_model": SRC / "lib" / "scanner-3052-model.ts",
        "cockpit_model": SRC / "lib" / "cockpit-3052-model.ts",
        "cockpit_data": SRC / "lib" / "cockpit-data.ts",
        "use_cockpit": SRC / "lib" / "use-cockpit.ts",
        "scanner_types": SRC / "types" / "scanner-3052.ts",
        "cockpit_types": SRC / "types" / "cockpit-3052.ts",
        "package": APP / "package.json",
        "package_lock": APP / "package-lock.json",
        "readme": APP / "README.md",
        "catalog_loop": CATALOG_LOOP,
        "report": REPORT,
        "gpt_prompt": GPT_PROMPT,
        "tobe_spec": TOBE_SPEC,
        "backend_layer_spec": BACKEND_LAYER_SPEC,
        "loop14_gpt_app_spec": LOOP14_GPT_APP_SPEC,
        "loop15_visual_qa": LOOP15_VISUAL_QA,
        "loop16_live_db_qa": LOOP16_LIVE_DB_QA,
        "loop17_db_tabs_qa": LOOP17_DB_TABS_QA,
        "loop18_chart_ux_qa": LOOP18_CHART_UX_QA,
        "loop19_external_design_qa": LOOP19_EXTERNAL_DESIGN_QA,
        "loop20_scan_density_qa": LOOP20_SCAN_DENSITY_QA,
        "loop21_scan_alignment_qa": LOOP21_SCAN_ALIGNMENT_QA,
        "loop22_gpt_subagent_p0_uiux": LOOP22_GPT_SUBAGENT_P0_UIUX,
        "screenshot": SCREENSHOT,
        "loop16_live_home": LOOP16_LIVE_HOME,
        "loop16_live_settings": LOOP16_LIVE_SETTINGS,
        "loop17_db_analysis": LOOP17_DB_ANALYSIS,
        "loop17_db_market": LOOP17_DB_MARKET,
        "loop17_db_risk": LOOP17_DB_RISK,
        "loop18_chart_analysis": LOOP18_CHART_ANALYSIS,
        "loop18_chart_detail": LOOP18_CHART_DETAIL,
        "loop19_external_home": LOOP19_EXTERNAL_HOME,
        "loop19_external_scan": LOOP19_EXTERNAL_SCAN,
        "loop19_external_detail": LOOP19_EXTERNAL_DETAIL,
        "loop19_external_analysis": LOOP19_EXTERNAL_ANALYSIS,
        "loop20_scan_density_scan": LOOP20_SCAN_DENSITY_SCAN,
        "loop20_scan_density_detail": LOOP20_SCAN_DENSITY_DETAIL,
        "loop21_scan_alignment_scan": LOOP21_SCAN_ALIGNMENT_SCAN,
        "loop21_scan_alignment_detail": LOOP21_SCAN_ALIGNMENT_DETAIL,
        "static_route_server": APP / "scripts" / "serve-static-routes.py",
    }
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.exists()]
    if missing:
        raise AssertionError(f"missing required files: {missing}")

    root_layout = read(paths["root_layout"])
    tabs_layout = read(paths["tabs_layout"])
    tab_sources = {name: read(paths[name]) for name in ["home", "scan", "analysis", "market", "risk", "settings"]}
    provider = read(paths["provider"])
    dom_tab = read(paths["dom_tab"])
    dom_detail = read(paths["dom_detail"])
    trade_detail_route = read(paths["trade_detail_route"])
    cockpit_dom = read(paths["cockpit_dom"])
    cockpit_web = read(paths["cockpit_web"])
    cockpit_css = read(paths["cockpit_css"])
    scanner_dom = read(paths["scanner_dom"])
    scanner_web = read(paths["scanner_web"])
    scanner_css = read(paths["scanner_css"])
    scanner_model = read(paths["scanner_model"])
    cockpit_model = read(paths["cockpit_model"])
    cockpit_data = read(paths["cockpit_data"])
    use_cockpit = read(paths["use_cockpit"])
    scanner_types = read(paths["scanner_types"])
    cockpit_types = read(paths["cockpit_types"])
    package = read(paths["package"])
    readme = read(paths["readme"])
    loop = read(paths["catalog_loop"])
    report = read(paths["report"])
    gpt_prompt = read(paths["gpt_prompt"])
    tobe_spec = read(paths["tobe_spec"])
    backend_layer_spec = read(paths["backend_layer_spec"])
    loop14_gpt_app_spec = read(paths["loop14_gpt_app_spec"])
    loop15_visual_qa = read(paths["loop15_visual_qa"])
    loop16_live_db_qa = read(paths["loop16_live_db_qa"])
    loop17_db_tabs_qa = read(paths["loop17_db_tabs_qa"])
    loop18_chart_ux_qa = read(paths["loop18_chart_ux_qa"])
    loop19_external_design_qa = read(paths["loop19_external_design_qa"])
    loop20_scan_density_qa = read(paths["loop20_scan_density_qa"])
    loop21_scan_alignment_qa = read(paths["loop21_scan_alignment_qa"])
    loop22_gpt_subagent_p0_uiux = read(paths["loop22_gpt_subagent_p0_uiux"])

    require_tokens("root layout", root_layout, ["CockpitProvider", '<Stack.Screen name="(tabs)"'])
    require_tokens("provider", provider, ["useCockpit()", "CockpitContext.Provider", "useCockpitContext"])
    if "\n  const { data } = useCockpit();" in "\n".join(tab_sources.values()):
        raise AssertionError("tab screens must not call useCockpit directly; use CockpitProvider")

    for name, source in tab_sources.items():
        require_tokens(name, source, ["DomTabScreen", "screen="])

    require_tokens("tabs layout", tabs_layout, ['name="settings"', 'name="trades"', "display", "none"])
    require_tokens(
        "dom tab",
        dom_tab,
        [
            "Cockpit3052Dom",
            "useCockpitContext",
            "buildCockpit3052Model",
            "cockpitFixture",
            "router.replace",
            'pathname: "/trade/[id]"',
            'contentInsetAdjustmentBehavior: "never"',
            "scrollEnabled: false",
        ],
    )
    require_tokens(
        "dom detail",
        dom_detail,
        [
            "Cockpit3052Dom",
            "useLocalSearchParams",
            "buildCockpit3052Model(data || cockpitFixture, selectedId)",
            'screen="detail"',
            'contentInsetAdjustmentBehavior: "never"',
            "scrollEnabled: false",
        ],
    )
    require_tokens("trade detail route", trade_detail_route, ["DomDetailScreen", "TradeDetailScreen"])
    require_tokens("cockpit DOM", cockpit_dom, ['"use dom"', "cockpit-3052.css", "scanner-3052.css", "MobileCockpitApp"])
    require_tokens(
        "cockpit web",
        cockpit_web,
        [
            "MobileCockpitApp",
            "HomeView",
            "AnalysisView",
            "MarketView",
            "RiskView",
            "SettingsView",
            "DetailView",
            "MobileScannerApp",
            "scan-bottom-nav",
            "footer-rail",
            "매매 손익 귀속",
            "onOpenTrade={onOpenTrade}",
            "compact-candle-svg",
            "compact-vwap-line",
            "Cockpit3052ChartBar",
            "Cockpit3052ChartMarker",
            "live-readout",
            "PnlMiniChart",
            "MarkerTape",
            "trade-marker",
            "marker-tape",
            "poll 30s",
            "MetricGrid columns={6}",
            'onClick={() => onNavigate?.("settings")}',
            'screen === "detail" ? "scan" : screen',
            "DbEvidenceStrip",
            "model.dbTabMetrics",
            "ChartStatusRail",
            "detail.tradeStats",
            "MarkerTape markers={model.analysis.markers}",
            'onClick={() => onNavigate?.("settings")}',
            "CHART_MISSING",
            "SOURCE_NOT_ATTACHED",
        ],
    )
    require_tokens(
        "cockpit CSS",
        cockpit_css,
        [
            ".cockpit-shell",
            ".cockpit-topbar",
            ".cockpit-content",
            ".account-panel",
            ".metric-grid",
            ".data-row",
            ".theme-row",
            ".analysis-chart",
            ".settings-list",
            ".detail-hero",
            ".footer-rail",
            ".data-row.interactive",
            ".compact-candle-svg",
            ".compact-vwap-line",
            ".home-pnl-db-panel",
            ".pnl-mini-chart",
            ".trade-marker-buy",
            ".trade-marker-sell",
            ".marker-tape",
            ".chart-status-rail",
            ".screen-analysis .marker-chip em",
            ".analysis-chart .readout-mini:not(.live-readout)",
            "--font-display",
            "--font-body",
            "--font-mono",
            'font-feature-settings: "tnum"',
            "height: 158px",
            "height: 350px",
            ".screen-settings .cockpit-content > .cockpit-panel:nth-child(4)",
            ".screen-analysis .compact-list .data-row > div:first-child small",
            ".screen-risk .compact-list .data-row",
            "width: 426.5px",
            "height: 922px",
        ],
    )

    require_tokens("scanner DOM", scanner_dom, ['"use dom"', "scanner-3052.css", "MobileScannerApp"])
    require_tokens(
        "scanner web",
        scanner_web,
        ["MobileScannerApp", "MobileTradingChart", "candidate-row", "chart-readout", "no execution", "onOpenTrade?.(candidate.tradeId)"],
    )
    require_tokens(
        "scanner CSS",
        scanner_css,
        [
            ".scan-shell",
            ".theme-strip",
            ".candidate-row",
            ".selected-chart-card",
            ".chart-readout",
            ".scan-bottom-nav",
            "--font-display",
            "--font-body",
            "--font-mono",
            "Sora",
            "Geist",
            "Roboto Mono",
            "-webkit-line-clamp: 2",
            "text-overflow: clip",
            "--scan-bg: #030406",
            "stroke-opacity: 0.72",
            "font-size: 5.25px",
            ".mini-status-row > div:has(.mini-spark) strong",
        ],
    )
    require_tokens(
        "scanner web loop20 chart density",
        scanner_web,
        ['width="3"', 'opacity="0.38"', 'strokeOpacity="0.9"', 'strokeWidth="0.72"'],
    )
    require_tokens(
        "scanner web loop21 alignment",
        scanner_web,
        [
            "bars.length + 10",
            "Array.from({ length: 6 }",
            'r="2"',
            "const selectedCandidateIndex",
            "key={candidate.tradeId || `${candidate.symbol}-${index}`}",
            "selected={index === selectedCandidateIndex}",
            "setActiveFilter",
            "setActiveSort",
            "activeCandidates.length",
        ],
    )
    require_tokens(
        "scanner CSS loop21 header alignment",
        scanner_css,
        ["grid-template-columns: 118px 55px 43px 29px 23px 35px 96px 9px"],
    )
    require_tokens(
        "static route server",
        read(paths["static_route_server"]),
        ["ExpoStaticRouteHandler", '"/trades": "trades.html"', '"/analysis": "analysis.html"', '"/trade/[id].html"'],
    )
    require_tokens(
        "scanner model",
        scanner_model,
        ["buildScanner3052Model", "CockpitData", "themeHeat", "noTradeReasons", "chartBars", "realOrdersAllowed", "tradeId: trade.id"],
    )
    require_tokens(
        "cockpit model",
        cockpit_model,
        [
            "buildCockpit3052Model",
            "selectedTradeId",
            "detail:",
            "footerMetrics",
            "tradeId: trade.id",
            "catalogFreshness",
            'sourceMode === "fixture-fallback"',
            "DB FRESH",
            "DB STALE",
            "FIXTURE",
            "liveOrders",
            "dataHealth.connectors",
            "requiredFiles",
            "buildScanner3052Model",
            "pnlTrendFromAccount",
            "realizedTrendFromAccount",
            "markersFromTrade",
            "lifecycleRowsFromTrade",
            "marketDeck",
            "themeDeck",
            "riskBlockerLabel",
            "riskStateLabel",
            "uiStatusLabel",
            "uiEvidenceLabel",
            "endpointLabel",
            "candidateReasonLabel",
            "pollCadence",
            "fileStatus",
            "sharedDbTabMetrics",
            "riskMetricLabel",
            "riskBlockerDetail",
            "detailTradeStats",
            "POLL",
            "FILES",
            "readOnlyTradeStatus",
            "NO EVENT EVIDENCE",
            "weakestFileLabel",
        ],
    )
    require_tokens(
        "types",
        scanner_types + "\n" + cockpit_types,
        ["Scanner3052Model", "Scanner3052Route", "Cockpit3052Model", "Cockpit3052Screen", "Cockpit3052Detail", "Cockpit3052ChartBar", "Cockpit3052ChartMarker", "realizedTrend", "lifecycleRows", '"detail"', "scanner: Scanner3052Model", "dbTabMetrics", "tradeStats"],
    )

    require_tokens(
        "data contract",
        cockpit_data,
        [
            "DEFAULT_TAILSCALE_CATALOG_BASE_URL",
            "http://100.90.255.9:8097/catalog",
            "CATALOG_FETCH_FAILED",
            'sourceMode: "fixture-fallback"',
            "CATALOG_STALE_WARN_SECONDS",
            "CATALOG_STALE_BLOCK_SECONDS",
            "STALE_5M",
            "STALE_30M",
            "catalogFreshness",
        ],
    )
    require_tokens("polling hook", use_cockpit, ["AUTO_REFRESH_MS = 30_000", "catalogBaseUrl", "lastRefreshAt", "refreshIntervalMs"])
    require_tokens(
        "catalog loop",
        loop,
        ["scripts/build_trader_terminal_catalog.py", "--paper-ops-only", "apps/trader-brain-web/public/catalog", "IntervalSeconds = 60"],
    )
    require_tokens("README", readme, ["http://100.90.255.9:8097/catalog", "polls the catalog every 30 seconds", "CATALOG_FETCH_FAILED"])
    require_tokens("package", package, ["lucide-react", "lightweight-charts", "react-native-webview"])

    require_tokens(
        "gpt prompt",
        gpt_prompt,
        ["Reference #2", "Expo Go", "10-Loop", "DB FRESH", "DB STALE", "FIXTURE", "FORBIDDEN"],
    )
    require_tokens(
        "tobe spec",
        tobe_spec,
        ["TOBE UIUX", "426.5 x 922", "Chart density", "Home Layout", "Detail Layout", "Analysis And Risk Layout"],
    )
    require_tokens(
        "backend layer spec",
        backend_layer_spec,
        ["Loop13 GPT Backend-Aware Layer Blueprint", "Reference #2", "backend OHLC/VWAP/volume", "Five-Loop Implementation", "NOT_ACCEPTED"],
    )
    require_tokens(
        "loop14 GPT app spec",
        loop14_gpt_app_spec,
        ["Loop14 GPT Brain UIUX App Program", "Backend brain layers", "10-Loop Implementation Sequence", "paper account", "buy/sell/current", "realized PnL", "NOT_ACCEPTED"],
    )
    require_tokens(
        "loop15 visual QA",
        loop15_visual_qa,
        ["Loop15 Visual Density QA", "poll 30s", "marketDeck", "themeDeck", "426.5 x 922", "FETCH_FAIL", "DETAIL VIEW", "NOT_ACCEPTED"],
    )
    require_tokens(
        "loop16 live DB QA",
        loop16_live_db_qa,
        [
            "Loop16 Live DB Runtime QA",
            "HTTP 200",
            "2026-06-21T01:34:33.214739+00:00",
            "paper-ops-runtime-v1",
            "paper_trade_detail_view_v1",
            "rows: `24`",
            "DB FRESH",
            "DB LINK",
            "POLL 30s",
            "FILES 3/3",
            "READ ONLY",
            "PAPER ONLY",
            "REAL ORDERS NO",
        ],
    )
    require_tokens(
        "loop17 DB evidence tabs QA",
        loop17_db_tabs_qa,
        [
            "Loop17 DB Evidence Tabs QA",
            "Analysis",
            "Market",
            "Risk",
            "dbTabMetrics",
            "DbEvidenceStrip",
            "SOURCE DB LINK",
            "POLL 30s",
            "FILES 3/3",
            "loop17_db_evidence_analysis_css426_dsf2.png",
            "loop17_db_evidence_market_css426_dsf2.png",
            "loop17_db_evidence_risk_css426_dsf2.png",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )
    require_tokens(
        "loop22 GPT/subagent P0 UIUX implementation",
        loop22_gpt_subagent_p0_uiux,
        [
            "Loop22 GPT/Subagent P0 UIUX Implementation",
            "policy_compare_audit.json",
            "DB STALE",
            "CHART_MISSING",
            "SOURCE_NOT_ATTACHED",
            "NO EVENT EVIDENCE",
            "Scan filter chips and sort chips",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )
    require_tokens(
        "loop18 chart marker PnL UX QA",
        loop18_chart_ux_qa,
        [
            "Loop18 Chart Marker PnL UX QA",
            "detail.tradeStats",
            "ChartStatusRail",
            "Analysis marker tape",
            "Entry, Current, Realized, Open, VWAP, and Vol",
            "loop18_chart_ux_analysis_css426_dsf2.png",
            "loop18_chart_ux_detail_css426_dsf2.png",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )
    require_tokens(
        "loop19 external design typography QA",
        loop19_external_design_qa,
        [
            "Loop19 External Design Typography QA",
            "Fontpair",
            "Mobbin",
            "Dribbble",
            "--font-display",
            "--font-body",
            "--font-mono",
            "Sora, Geist, Inter",
            "Geist Mono, Roboto Mono",
            "two-line",
            "serve-static-routes.py",
            "loop19_external_design_typography_home_css426_dsf2.png",
            "loop19_external_design_typography_scan_css426_dsf2.png",
            "loop19_external_design_typography_detail_css426_dsf2.png",
            "loop19_external_design_typography_analysis_css426_dsf2.png",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )
    require_tokens(
        "loop20 scan density QA",
        loop20_scan_density_qa,
        [
            "Loop20 Scan Density QA",
            "Visual QA explorer",
            "DB/routing safety explorer",
            "Candle bodies were widened",
            "Mini status",
            "loop20_scan_density_scan_css426_dsf2.png",
            "loop20_scan_density_detail_css426_dsf2.png",
            "REPORTING_HEALTH / GOVERNANCE_HEALTH",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )
    require_tokens(
        "loop21 scan header chart alignment QA",
        loop21_scan_alignment_qa,
        [
            "Loop21 Scan Header Chart Alignment QA",
            "single selected row",
            "header-row column alignment",
            "six horizontal price guides",
            "loop21_scan_alignment_scan_css426_dsf2.png",
            "loop21_scan_alignment_detail_css426_dsf2.png",
            "PACKAGE_HEALTH / REPORTING_HEALTH / GOVERNANCE_HEALTH",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ],
    )

    all_frontend = "\n".join([root_layout, tabs_layout, *tab_sources.values(), dom_tab, dom_detail, trade_detail_route, cockpit_dom, cockpit_web, scanner_dom, scanner_web, scanner_model, cockpit_model])
    forbidden = ["placeOrder", "sendOrder", "submitOrder", "liveOrder(", "chart-tooltip", "Catalog Gate", "catalog only", "Decision Sheet", "PriceChart"]
    found = [token for token in forbidden if token in all_frontend]
    if found:
        raise AssertionError(f"forbidden UI/order/catalog tokens found: {found}")

    require_tokens("report safety status", report, ["NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"])
    print("Task3421 Expo 3052 DOM cockpit validation passed")


if __name__ == "__main__":
    main()
