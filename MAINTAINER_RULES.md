# System Maintainer Rules

These instructions apply when developing the shared AI OS System repository. They do not authorize changes to an installed user's vault.

## Boundaries

- Never edit an installed vault's `System/` copy. Make shared changes in this authoring repository.
- Never put personal names, accounts, home paths, private projects, credentials, or other owner-specific material in shared files.
- Never read a user's `Private/` directory as part of System development or testing.
- Treat installed vault notes, `Me.md`, `Active Context.md`, credentials, and local configuration as user-owned data that an update must preserve.

## Sources and adapters

- Edit canonical, agent-neutral Markdown and scripts, not generated adapters.
- Root `AGENTS.md` and `CLAUDE.md` are generated from this file and must remain identical.
- Template entry files and project skill loaders are generated compatibility surfaces. A change is incomplete until regeneration and drift checks pass.
- Existing behavior is a baseline under revision, not automatically the desired result. An approved implementation specification defines the target for its branch.

## Working method

- Read `IMPLEMENTATION_PLAN.md` when it exists. Take one task ID at a time and obey its scope, invariants, tests, and human gates.
- Check repository path, branch, status, and relevant history before editing.
- Use test-driven development for executable behavior: observe the focused test fail, implement the smallest passing change, then run the wider checks.
- Keep changes model-independent. A different capable agent must be able to continue from files, git history, tests, and the recorded handover without the previous chat.
- Do not trust a subagent or predecessor's completion claim without checking the files and rerunning the relevant tests.

## Verification

- Test an installed disposable vault, not only imports from the authoring checkout.
- Test clean installation, upgrade from the supported prior version, generated adapters, personal-data preservation, and rollback when the task can affect them.
- Do not claim conversational behavior was tested unless a fresh agent session was actually run and its evidence recorded.
- Inspect the complete diff before committing. A passing plan is not proof that the requested behavior works.

## Release control

- Do not tag, push, publish, announce, or install a candidate in a live vault without the maintainer's explicit approval.
- Versions are immutable after publication. Fix a released problem with a new version, never by moving a tag.
- Update `CHANGELOG.md` in plain language before release.
- Work-in-progress commits are allowed only on an unreleased feature branch and must be clearly marked. They are continuity checkpoints, not release evidence.
