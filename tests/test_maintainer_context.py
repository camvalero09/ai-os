from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_maintainer_context.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_maintainer_context", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MaintainerContextTests(unittest.TestCase):
    def test_rendered_context_contains_authoring_boundaries(self):
        module = load_module()
        source = """# System Maintainer Rules

Never edit an installed vault's System copy.
Never put personal data in shared files.
Do not tag, push, publish, or release without owner approval.
Edit canonical sources, not generated adapters.
Existing behavior is a baseline under revision, not automatically the target.
"""

        rendered = module.render_context(source)

        self.assertIn("generated from `MAINTAINER_RULES.md`", rendered)
        self.assertIn("Never edit an installed vault's System copy", rendered)
        self.assertIn("Existing behavior is a baseline under revision", rendered)

    def test_write_and_check_keep_both_adapters_identical(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "MAINTAINER_RULES.md").write_text("# Rules\n\nShared only.\n", encoding="utf-8")

            changed = module.build(root=root, check=False)

            self.assertEqual(["AGENTS.md", "CLAUDE.md"], changed)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(agents, claude)
            self.assertEqual([], module.build(root=root, check=True))

    def test_check_reports_outdated_adapter_without_writing(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "MAINTAINER_RULES.md").write_text("# Rules\n\nCurrent.\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("stale\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("stale\n", encoding="utf-8")

            changed = module.build(root=root, check=True)

            self.assertEqual(["AGENTS.md", "CLAUDE.md"], changed)
            self.assertEqual("stale\n", (root / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
