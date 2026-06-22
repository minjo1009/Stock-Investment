from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/ios-trader-brain"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    package = json.loads((APP / "package.json").read_text(encoding="utf-8"))
    app_json = json.loads((APP / "app.json").read_text(encoding="utf-8"))
    _assert(package.get("main") == "expo-router/entry", "Expo Router entry missing")
    _assert(package.get("dependencies", {}).get("expo"), "expo dependency missing")
    _assert(package.get("dependencies", {}).get("expo-router"), "expo-router dependency missing")
    _assert(package.get("dependencies", {}).get("react-native-svg"), "react-native-svg dependency missing")
    _assert(app_json.get("expo", {}).get("name") == "Trader Brain", "native app name mismatch")

    required_files = [
        APP / "src/app/_layout.tsx",
        APP / "src/app/(tabs)/_layout.tsx",
        APP / "src/app/(tabs)/index.tsx",
        APP / "src/app/(tabs)/trades.tsx",
        APP / "src/app/(tabs)/risk.tsx",
        APP / "src/app/(tabs)/settings.tsx",
        APP / "src/app/trade/[id].tsx",
        APP / "src/lib/cockpit-data.ts",
        APP / "src/fixtures/cockpit-fixture.json",
        APP / "script/build_and_run.sh",
        APP / "script/build_and_run.ps1",
        APP / ".codex/environments/environment.toml",
    ]
    for path in required_files:
        _assert(path.exists(), f"required iOS app file missing: {path}")

    app_source = "\n".join(path.read_text(encoding="utf-8") for path in (APP / "src").rglob("*.tsx"))
    data_source = (APP / "src/lib/cockpit-data.ts").read_text(encoding="utf-8")
    _assert("NativeTabs" in app_source, "native tabs route not wired")
    _assert("mobile_cockpit_catalog" in (APP / "README.md").read_text(encoding="utf-8"), "rejected PWA catalog warning missing")
    _assert("mobile_cockpit_catalog" not in data_source, "app data loader must not read rejected mobile cockpit catalog")
    _assert("realOrdersAllowed: false" in data_source, "real order guard missing")
    _assert("liveOrderButtonsAllowed: false" in data_source, "live order button guard missing")
    environment = (APP / ".codex/environments/environment.toml").read_text(encoding="utf-8")
    _assert("build_and_run.ps1" in environment, "Windows Codex run action not wired")

    pwa_source = (ROOT / "frontend/trader-terminal/src/App.jsx").read_text(encoding="utf-8")
    catalog_script = (ROOT / "scripts/build_trader_terminal_catalog.py").read_text(encoding="utf-8")
    _assert("function MobileCockpitPage" not in pwa_source, "rejected PWA MobileCockpitPage still present")
    _assert("/catalog/mobile_cockpit_catalog.json" not in pwa_source, "rejected PWA mobile catalog fetch still present")
    _assert("_mobile_cockpit_payload" not in catalog_script, "rejected mobile cockpit generator still present")
    _assert(not (ROOT / "frontend/trader-terminal/public/catalog/mobile_cockpit_catalog.json").exists(), "public mobile cockpit catalog still exists")

    print("[TASK2681_2700_NATIVE_IOS_COCKPIT_VALIDATE_OK]")


if __name__ == "__main__":
    main()
