from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "vault_lint.py"


def load_vault_lint():
    spec = importlib.util.spec_from_file_location("vault_lint_worktree_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeWorktreeExclusionTests(unittest.TestCase):
    def test_host_managed_worktrees_are_not_counted_as_vault_notes(self):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            system = vault / "System"
            (system / "template").mkdir(parents=True)
            live_note = vault / "Ideaverse/Atlas/Live Note.md"
            live_note.parent.mkdir(parents=True)
            live_note.write_text("# Live Note\n", encoding="utf-8")

            for host_root in (".claude", ".agents"):
                duplicate = vault / host_root / "worktrees/task-copy/Ideaverse/Atlas/Duplicate.md"
                duplicate.parent.mkdir(parents=True)
                duplicate.write_text("# Duplicate\n", encoding="utf-8")

            setattr(module, "VAULT", vault)
            setattr(module, "SYSTEM", system)
            rels = {str(path.relative_to(vault)) for path in module.get_all_md_files()}

            self.assertIn("Ideaverse/Atlas/Live Note.md", rels)
            self.assertFalse(
                any("/worktrees/" in f"/{rel}/" for rel in rels),
                "host-managed worktree copies must not be linted as live vault notes",
            )


if __name__ == "__main__":
    unittest.main()
