from __future__ import annotations

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_views.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_views_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def description_from(loader: str) -> str:
    match = re.search(r"^description: (.+)$", loader, re.MULTILINE)
    if not match:
        raise AssertionError("loader has no quoted description")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise AssertionError("loader description is not a valid quoted YAML/JSON scalar") from error


class SkillLoaderTests(unittest.TestCase):
    def test_trigger_precedes_summary_inside_index_window(self):
        module = load_module()
        loader = module.render_loader(
            {
                "id": "example-skill",
                "summary": "Produces a detailed reusable output for the owner",
                "triggers": "the owner asks to compare options",
                "_title": "Example Skill",
                "_rel_md": "System/Skills/Workflows/Example Skill.md",
            }
        )
        description = description_from(loader)

        self.assertTrue(description.startswith("Use when: "))
        self.assertIn("compare options", description[:60])
        self.assertGreater(description.index("Produces"), description.index("compare options"))

    def test_description_escapes_backslashes_and_quotes(self):
        module = load_module()
        loader = module.render_loader(
            {
                "id": "portable-skill",
                "summary": r'Handles C:\temp and "quoted" values',
                "triggers": r"a path such as C:\new\queue",
                "_title": "Portable Skill",
                "_rel_md": "System/Skills/Tools/Portable Skill.md",
            }
        )

        self.assertEqual(
            r'Use when: a path such as C:\new\queue. Handles C:\temp and "quoted" values.',
            description_from(loader),
        )

    def test_loader_rejects_missing_triggers(self):
        module = load_module()
        with self.assertRaisesRegex(ValueError, "triggers"):
            module.render_loader(
                {
                    "id": "unroutable-skill",
                    "summary": "Has no usable routing phrase",
                    "_title": "Unroutable Skill",
                    "_rel_md": "System/Skills/Tools/Unroutable Skill.md",
                }
            )

    def test_both_host_adapter_trees_are_reproducible_and_trigger_first(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault = Path(tmp_dir)
            system = vault / "System"
            shutil.copytree(ROOT / "Skills", system / "Skills")
            setattr(module, "VAULT", vault)
            setattr(module, "SYSTEM", system)
            changed = module.generate_loaders(check=False)
            self.assertTrue(changed)
            self.assertEqual([], module.generate_loaders(check=True))

            claude = sorted((module.VAULT / ".claude/skills").glob("*/SKILL.md"))
            agents = sorted((module.VAULT / ".agents/skills").glob("*/SKILL.md"))
            exposed = [
                skill
                for skill in module.collect_skills("Skills/Workflows") + module.collect_skills("Skills/Tools")
                if module.is_exposed(skill) and skill.get("id")
            ]
            exposed_by_id = {skill["id"]: skill for skill in exposed}
            self.assertEqual(len(exposed), len(claude))
            self.assertEqual([p.parent.name for p in claude], [p.parent.name for p in agents])

            for claude_path, agents_path in zip(claude, agents):
                claude_text = claude_path.read_text(encoding="utf-8")
                self.assertEqual(claude_text, agents_path.read_text(encoding="utf-8"))
                description = description_from(claude_text)
                first_trigger = exposed_by_id[claude_path.parent.name]["triggers"].split(",", 1)[0].strip()
                self.assertTrue(first_trigger)
                self.assertTrue(description.startswith("Use when: "))
                self.assertIn(first_trigger, description[:60])


if __name__ == "__main__":
    unittest.main()
