from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
MODULE_PATH = ROOT / "scripts" / "build_views.py"

# Names a capable coding agent auto-loads as live instructions out of whatever
# folder it is working in. A copy of one sitting in template/ as seed content
# is indistinguishable from a real one to that agent.
RESERVED_ENTRY_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}


def load_build_views():
    spec = importlib.util.spec_from_file_location("build_views_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TemplateEntryFileTests(unittest.TestCase):
    def test_template_carries_no_reserved_entry_filenames(self):
        reserved = [p for p in TEMPLATE.rglob("*") if p.is_file() and p.name in RESERVED_ENTRY_NAMES]

        self.assertEqual(
            [], reserved,
            "template/ must not seed a live reserved entry filename; a harness "
            "starting inside template/ would load it as real instructions",
        )

    def test_install_still_produces_valid_generated_root_entry_files(self):
        module = load_build_views()
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            for src in TEMPLATE.rglob("*"):
                rel = src.relative_to(TEMPLATE)
                dst = vault / rel
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            module.VAULT = vault
            module.SYSTEM = ROOT
            changed = module.generate_entry_files(check=False)

            self.assertEqual({"CLAUDE.md", "AGENTS.md"}, set(changed))
            claude = (vault / "CLAUDE.md").read_text(encoding="utf-8")
            agents = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("generated", claude.lower())

            def neutral(text: str) -> str:
                return text.replace("CLAUDE.md", "ENTRY").replace("AGENTS.md", "ENTRY")

            self.assertEqual(neutral(claude), neutral(agents))


if __name__ == "__main__":
    unittest.main()
