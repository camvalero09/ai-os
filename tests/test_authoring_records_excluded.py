from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "vault_lint.py"

# Records that describe the authoring repository itself, not an installed
# vault. An installed checkout carries them under System/ but they have no
# vault-note home to link them from, so they must never be treated as notes.
AUTHORING_ONLY_RECORDS = ("IMPLEMENTATION_PLAN.md", "MAINTAINER_RULES.md", "T03_RULES_PROPOSAL.md")


def load_vault_lint():
    spec = importlib.util.spec_from_file_location("vault_lint_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuthoringOnlyRecordTests(unittest.TestCase):
    def _installed_checkout(self, directory: Path):
        vault = Path(directory)
        system = vault / "System"
        (vault / "Maps & Manuals").mkdir(parents=True)
        (vault / "Ideaverse").mkdir(parents=True)
        (system / "template").mkdir(parents=True)
        for name in AUTHORING_ONLY_RECORDS:
            (system / name).write_text(f"# {name}\n\nAuthoring-only record.\n", encoding="utf-8")
        return vault, system

    def test_authoring_records_are_not_counted_as_vault_notes(self):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault, system = self._installed_checkout(Path(directory))
            module.VAULT = vault
            module.SYSTEM = system

            files = module.get_all_md_files()
            rels = {str(f.relative_to(vault)) for f in files}
            for name in AUTHORING_ONLY_RECORDS:
                self.assertNotIn(
                    f"System/{name}", rels,
                    f"{name} is an authoring-repository record and must not be "
                    "treated as an installed vault note",
                )

    def test_fresh_install_reports_no_orphans_for_authoring_records(self):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault, system = self._installed_checkout(Path(directory))
            module.VAULT = vault
            module.SYSTEM = system

            files = module.get_all_md_files()
            orphans = module.check_orphans(files)
            self.assertEqual(
                [], orphans,
                "a fresh install must not report authoring-only records as orphan notes",
            )


if __name__ == "__main__":
    unittest.main()
