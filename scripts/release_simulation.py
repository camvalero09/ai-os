#!/usr/bin/env python3
"""Exercise a release against disposable vaults only.

The simulation installs the tagged baseline, adds synthetic personal state,
updates the installed System checkout to a candidate commit, and rolls back.
It proves that generated adapters change with System while personal files do
not. No network remote, live vault, or real credential is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PERSONAL_FIXTURES = (
    "Maps & Manuals/Me.md",
    "Maps & Manuals/Active Context.md",
    "Maps & Manuals/Writing Style.md",
    "Ideaverse/Atlas/Synthetic Personal Note.md",
    "vault.config.json",
    "credentials/simulation-placeholder.txt",
)


class SimulationError(RuntimeError):
    pass


def isolated_environment(cwd: Path) -> dict[str, str]:
    """Keep local tools usable without inheriting caller secrets or Git policy."""
    keep = ("PATH", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "COMSPEC", "PATHEXT")
    env = {name: os.environ[name] for name in keep if name in os.environ}
    env.update(
        {
            "HOME": str(cwd),
            "VAULT_ROOT": str(cwd),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ALLOW_PROTOCOL": "file",
        }
    )
    return env


def run(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=isolated_environment(cwd),
    )
    if result.returncode:
        output = (result.stdout + result.stderr).strip()
        raise SimulationError(f"{' '.join(args)} failed ({result.returncode}):\n{output}")
    return (result.stdout + result.stderr).strip()


def fingerprint(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def generated_entries(vault: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((vault / name).read_bytes()).hexdigest()
        for name in ("CLAUDE.md", "AGENTS.md")
    }


def generated_skill_loaders(vault: Path, target: str = ".claude/skills") -> dict[str, str]:
    root = vault / target
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("SKILL.md")
    }


def system_is_clean(system: Path) -> bool:
    return not run(["git", "status", "--porcelain"], cwd=system)


def settings_synced(vault: Path) -> bool:
    return (vault / ".claude/settings.json").read_bytes() == (
        vault / "System/claude-settings.json"
    ).read_bytes()


def neutral_entry(text: str) -> str:
    return text.replace("CLAUDE.md", "ENTRY").replace("AGENTS.md", "ENTRY")


def verify_adapters(vault: Path) -> bool:
    claude = (vault / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (vault / "AGENTS.md").read_text(encoding="utf-8")
    if neutral_entry(claude) != neutral_entry(agents):
        return False
    rules = (vault / "System/Agent Rules.md").read_text(encoding="utf-8")
    card_match = re.search(r"<!-- BEGIN CARD -->\n(.*?)<!-- END CARD -->", rules, re.DOTALL)
    if not card_match:
        return False
    shared_headings = re.findall(r"^## .+$", card_match.group(1), re.MULTILINE)
    if not shared_headings or not all(heading in claude for heading in shared_headings):
        return False

    trees: list[dict[str, bytes]] = []
    for root in (vault / ".claude/skills", vault / ".agents/skills"):
        trees.append({str(path.relative_to(root)): path.read_bytes() for path in root.rglob("SKILL.md")})
    if not trees[0] or trees[0] != trees[1]:
        return False
    for content in trees[0].values():
        text = content.decode("utf-8")
        description = next((line for line in text.splitlines() if line.startswith("description:")), "")
        if "Use when:" not in description[:60]:
            return False
    return True


def validate_vault(vault: Path) -> None:
    python = sys.executable
    system = vault / "System"
    run([python, str(system / "scripts/build_views.py")], cwd=vault)
    run([python, str(system / "scripts/vault_lint.py")], cwd=vault)
    run([python, str(system / "scripts/acceptance_test.py")], cwd=vault)


def add_synthetic_personal_state(vault: Path) -> list[Path]:
    me = vault / "Maps & Manuals/Me.md"
    text = me.read_text(encoding="utf-8")
    if "TO FILL IN" not in text:
        raise SimulationError("baseline Me.md has no onboarding slot for the synthetic owner")
    me.write_text(
        text.replace("TO FILL IN", "Alex Rivera, a synthetic release-simulation owner", 1),
        encoding="utf-8",
    )

    active = vault / "Maps & Manuals/Active Context.md"
    active.write_text(
        active.read_text(encoding="utf-8") + "\nSynthetic simulation priority: preserve this line.\n",
        encoding="utf-8",
    )
    style = vault / "Maps & Manuals/Writing Style.md"
    style.write_text(
        style.read_text(encoding="utf-8") + "\nSynthetic simulation voice marker.\n",
        encoding="utf-8",
    )

    atlas_note = vault / "Ideaverse/Atlas/Synthetic Personal Note.md"
    atlas_note.write_text(
        "---\n"
        "id: synthetic-personal-note\n"
        "type: atlas\n"
        "status: stable\n"
        "domain: simulation\n"
        "updated: 2026-09-04\n"
        'summary: "Synthetic personal note used only by the disposable release gate."\n'
        "---\n\n"
        "# Synthetic Personal Note\n\n"
        "This represents adopter-owned knowledge and must survive System updates.\n",
        encoding="utf-8",
    )

    config = {
        "google_account": "",
        "onboarding_stage": 1,
        "owner_name": "Alex Rivera",
        "primary_language": "en",
        "remote_agent": "claude",
        "remote_models": {},
        "telegram_allowed_ids": [],
        "timezone": "UTC",
        "vault_name": "Synthetic Release Simulation",
    }
    (vault / "vault.config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    credential = vault / "credentials/simulation-placeholder.txt"
    credential.write_text("synthetic fixture; not a credential\n", encoding="utf-8")
    credential.chmod(0o600)
    return [vault / rel for rel in PERSONAL_FIXTURES]


def simulate(repo: Path, baseline: str, candidate: str, workspace: Path) -> dict[str, object]:
    repo = repo.resolve()
    candidate_sha = run(["git", "rev-parse", candidate], cwd=repo)
    run(["git", "rev-parse", "--verify", baseline], cwd=repo)

    candidate_vault = workspace / "clean-install-vault"
    candidate_vault.mkdir(parents=True)
    candidate_system = candidate_vault / "System"
    run(["git", "clone", "--no-hardlinks", str(repo), str(candidate_system)], cwd=workspace)
    run(["git", "checkout", candidate_sha], cwd=candidate_system)
    candidate_install_output = run(
        [sys.executable, str(candidate_system / "scripts/install_vault.py")],
        cwd=candidate_vault,
    )
    # Inspect the installer's own result before any follow-up generator could
    # repair it and hide an installation defect.
    candidate_adapters_valid = verify_adapters(candidate_vault)
    candidate_settings_synced = settings_synced(candidate_vault)
    candidate_system_clean = system_is_clean(candidate_system)
    validate_vault(candidate_vault)
    clean_install = {
        "passed": (
            "Done." in candidate_install_output
            and candidate_adapters_valid
            and candidate_settings_synced
            and candidate_system_clean
        ),
        "system_commit": run(["git", "rev-parse", "HEAD"], cwd=candidate_system),
        "candidate_adapters_valid": candidate_adapters_valid,
        "settings_synced": candidate_settings_synced,
        "system_clean": candidate_system_clean,
        "install_completed": "Done." in candidate_install_output,
    }

    vault = workspace / "upgrade-vault"
    vault.mkdir(parents=True)
    system = vault / "System"
    run(["git", "clone", "--no-hardlinks", str(repo), str(system)], cwd=workspace)
    run(["git", "checkout", baseline], cwd=system)

    run([sys.executable, str(system / "scripts/install_vault.py")], cwd=vault)
    validate_vault(vault)

    personal_paths = add_synthetic_personal_state(vault)
    validate_vault(vault)
    personal_before = fingerprint(personal_paths)
    credential_mode_before = personal_paths[-1].stat().st_mode & 0o777
    baseline_entries = generated_entries(vault)
    baseline_skill_loaders = generated_skill_loaders(vault)
    baseline_portable_skill_loaders = generated_skill_loaders(vault, ".agents/skills")

    if run(["git", "status", "--porcelain"], cwd=system):
        raise SimulationError("installed System checkout was dirty before upgrade")
    run(["git", "checkout", candidate_sha], cwd=system)
    shutil.copy2(system / "claude-settings.json", vault / ".claude/settings.json")
    validate_vault(vault)
    personal_after_upgrade = fingerprint(personal_paths)
    candidate_entries = generated_entries(vault)
    candidate_skill_loaders = generated_skill_loaders(vault)
    candidate_portable_skill_loaders = generated_skill_loaders(vault, ".agents/skills")
    credential_permissions_after_upgrade = (personal_paths[-1].stat().st_mode & 0o777) == credential_mode_before
    skill_loaders_rebuilt = candidate_skill_loaders != baseline_skill_loaders
    portable_skill_loaders_rebuilt = candidate_portable_skill_loaders != baseline_portable_skill_loaders
    candidate_settings_synced = settings_synced(vault)
    candidate_system_clean = system_is_clean(system)
    adapters_rebuilt = candidate_entries != baseline_entries and verify_adapters(vault)
    upgrade = {
        "passed": (
            personal_after_upgrade == personal_before
            and credential_permissions_after_upgrade
            and adapters_rebuilt
            and skill_loaders_rebuilt
            and portable_skill_loaders_rebuilt
            and candidate_settings_synced
            and candidate_system_clean
        ),
        "personal_state_preserved": personal_after_upgrade == personal_before,
        "credential_permissions_preserved": credential_permissions_after_upgrade,
        "adapters_rebuilt": adapters_rebuilt,
        "skill_loaders_rebuilt": skill_loaders_rebuilt,
        "portable_skill_loaders_rebuilt": portable_skill_loaders_rebuilt,
        "settings_synced": candidate_settings_synced,
        "system_clean": candidate_system_clean,
        "candidate_commit": candidate_sha,
    }

    run(["git", "checkout", baseline], cwd=system)
    shutil.copy2(system / "claude-settings.json", vault / ".claude/settings.json")
    validate_vault(vault)
    personal_after_rollback = fingerprint(personal_paths)
    restored_entries = generated_entries(vault)
    restored_skill_loaders = generated_skill_loaders(vault)
    restored_portable_skill_loaders = generated_skill_loaders(vault, ".agents/skills")
    credential_permissions_after_rollback = (personal_paths[-1].stat().st_mode & 0o777) == credential_mode_before
    baseline_restored = run(["git", "describe", "--tags", "--exact-match"], cwd=system) == baseline
    skill_loaders_restored = restored_skill_loaders == baseline_skill_loaders
    portable_skill_loaders_restored = restored_portable_skill_loaders == baseline_portable_skill_loaders
    baseline_settings_synced = settings_synced(vault)
    baseline_system_clean = system_is_clean(system)
    rollback = {
        "passed": (
            personal_after_rollback == personal_before
            and credential_permissions_after_rollback
            and baseline_restored
            and restored_entries == baseline_entries
            and skill_loaders_restored
            and portable_skill_loaders_restored
            and baseline_settings_synced
            and baseline_system_clean
        ),
        "personal_state_preserved": personal_after_rollback == personal_before,
        "credential_permissions_preserved": credential_permissions_after_rollback,
        "baseline_restored": baseline_restored,
        "adapters_restored": restored_entries == baseline_entries,
        "skill_loaders_restored": skill_loaders_restored,
        "portable_skill_loaders_restored": portable_skill_loaders_restored,
        "settings_synced": baseline_settings_synced,
        "system_clean": baseline_system_clean,
    }

    report: dict[str, object] = {
        "clean_install": clean_install,
        "upgrade": upgrade,
        "rollback": rollback,
    }
    if not all(section["passed"] for section in (clean_install, upgrade, rollback)):
        raise SimulationError(f"release simulation assertions failed: {json.dumps(report, sort_keys=True)}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--baseline", default="v2.28")
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    temporary = None
    workspace = args.workspace
    if workspace is None:
        if args.keep:
            workspace = Path(tempfile.mkdtemp(prefix="aios-release-simulation-"))
        else:
            temporary = tempfile.TemporaryDirectory(prefix="aios-release-simulation-")
            workspace = Path(temporary.name)
    else:
        workspace.mkdir(parents=True, exist_ok=True)

    try:
        report = simulate(args.repo, args.baseline, args.candidate, workspace)
        if args.keep:
            report["workspace"] = str(workspace)
        print(json.dumps(report, indent=2) if args.json else "Release simulation: PASS")
        return 0
    except (OSError, SimulationError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}))
        else:
            print(f"Release simulation: FAIL\n{error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
