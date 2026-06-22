from __future__ import annotations

import json
import unittest
from pathlib import Path


class MobileRemoteOpsContractTest(unittest.TestCase):
    def test_trader_terminal_has_mobile_pwa_contract(self) -> None:
        root = Path("frontend/trader-terminal")
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "public/manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertIn("dev:lan", package["scripts"])
        self.assertIn("preview:lan", package["scripts"])
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/")
        self.assertTrue((root / "public/service-worker.js").exists())
        self.assertTrue((root / "public/icon.svg").exists())

    def test_mobile_ops_scripts_use_private_tunnel_and_stable_port(self) -> None:
        start_script = Path("scripts/start_trader_terminal_lan.ps1").read_text(encoding="utf-8")
        task_script = Path("scripts/install_trader_terminal_mobile_task.ps1").read_text(encoding="utf-8")
        tailscale_script = Path("scripts/configure_tailscale_trader_terminal_serve.ps1").read_text(encoding="utf-8")
        self.assertIn("vite.cmd preview", start_script)
        self.assertIn("--strictPort", start_script)
        self.assertIn("-WakeToRun", task_script)
        self.assertIn("22:20", task_script)
        self.assertIn("23:20", task_script)
        self.assertIn("tailscale.exe", tailscale_script)
        self.assertIn("tailscale serve", tailscale_script)


if __name__ == "__main__":
    unittest.main()
