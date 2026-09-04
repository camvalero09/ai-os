from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / "scripts" / "release_simulation.py"


class ReleaseSimulationTests(unittest.TestCase):
    def test_update_system_documents_repeatable_release_gate(self):
        update_skill = (ROOT / "Skills/Tools/Update System.md").read_text(encoding="utf-8")
        self.assertIn("scripts/release_simulation.py", update_skill)
        self.assertIn("--baseline v2.28", update_skill)

    def test_clean_install_upgrade_and_rollback_preserve_personal_state(self):
        with tempfile.TemporaryDirectory() as unrelated_vault:
            hostile_git_config = Path(unrelated_vault) / "hostile-gitconfig"
            hostile_git_config.write_text(
                '[protocol "file"]\n\tallow = never\n', encoding="utf-8"
            )
            env = os.environ.copy()
            env["VAULT_ROOT"] = unrelated_vault
            env["GIT_CONFIG_GLOBAL"] = str(hostile_git_config)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SIMULATOR),
                    "--repo",
                    str(ROOT),
                    "--baseline",
                    "v2.28",
                    "--candidate",
                    "HEAD",
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)

        self.assertTrue(report["clean_install"]["passed"])
        self.assertTrue(report["clean_install"].get("candidate_adapters_valid", False))
        self.assertTrue(report["clean_install"].get("settings_synced", False))
        self.assertTrue(report["clean_install"].get("system_clean", False))
        self.assertEqual(
            report["upgrade"]["candidate_commit"],
            report["clean_install"].get("system_commit"),
        )
        self.assertTrue(report["upgrade"]["passed"])
        self.assertTrue(report["upgrade"]["personal_state_preserved"])
        self.assertTrue(report["upgrade"].get("credential_permissions_preserved", False))
        self.assertTrue(report["upgrade"]["adapters_rebuilt"])
        self.assertTrue(report["upgrade"].get("skill_loaders_rebuilt", False))
        self.assertTrue(report["upgrade"].get("portable_skill_loaders_rebuilt", False))
        self.assertTrue(report["upgrade"].get("settings_synced", False))
        self.assertTrue(report["upgrade"].get("system_clean", False))
        self.assertTrue(report["rollback"]["passed"])
        self.assertTrue(report["rollback"]["personal_state_preserved"])
        self.assertTrue(report["rollback"].get("credential_permissions_preserved", False))
        self.assertTrue(report["rollback"]["baseline_restored"])
        self.assertTrue(report["rollback"]["adapters_restored"])
        self.assertTrue(report["rollback"].get("skill_loaders_restored", False))
        self.assertTrue(report["rollback"].get("portable_skill_loaders_restored", False))
        self.assertTrue(report["rollback"].get("settings_synced", False))
        self.assertTrue(report["rollback"].get("system_clean", False))


if __name__ == "__main__":
    unittest.main()
