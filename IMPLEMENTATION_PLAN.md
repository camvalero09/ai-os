# Conversation Harness Improvement Plan

> Working control document for the `improve/conversation-harness` branch. It allows any capable agent to continue the migration without access to earlier conversations. Remove or convert it into permanent design documentation before release.

## Objective

Make an installed AI OS vault feel informed, decisive, safe, and continuous when its owner talks to an agent through VS Code. Improve the experience for the current owner and other adopters without requiring one model, one provider, one subscription, or one uninterrupted session.

## Current baseline

- Production System version: `v2.28`.
- System authoring repository: the repository containing this file.
- Installed `System/` directories are read-only release checkouts.
- Canonical content lives in agent-neutral Markdown and scripts.
- `CLAUDE.md`, `AGENTS.md`, `.claude/skills/`, and `.agents/skills/` are generated adapters.
- The author's live vault must remain on `v2.28` until a candidate passes the disposable-install and upgrade gates.

## Authority order

1. This approved plan defines the target of this migration.
2. Existing safety and privacy invariants remain binding.
3. Existing behavior is evidence about the baseline, not automatically the desired result.
4. Automated tests and fresh-session evaluations determine whether a change works.
5. A model's chat summary is never evidence that work is complete.

## Non-negotiable invariants

- Never edit an installed vault's `System/` copy while authoring shared changes.
- Never put personal names, accounts, paths, projects, or other owner-specific data into shared System files.
- Never hand-edit generated agent adapters.
- Never alter an adopter's `Me.md`, notes, credentials, or current work during an update.
- Keep rollback to the previous immutable version possible.
- Never tag, push, publish, or install a candidate in a live vault without the release owner's explicit approval.
- Run behavior-changing work test-first where automated tests are possible.
- Verify subagent or predecessor claims against files, git, and test output.
- One editing agent per checkout. Parallel editors require separate worktrees and non-overlapping scopes.

## Working protocol

Each agent session takes exactly one task ID unless the release owner explicitly expands the scope.

Before editing:

1. Confirm the repository path.
2. Run `git status --short --branch`.
3. Read this file and the canonical files named by the task.
4. Confirm the task is not already complete.
5. For executable behavior, add a failing test and verify the expected failure.

Before stopping:

1. Run the task's checks.
2. Inspect the complete diff.
3. Update the task row, Evidence log, and Exact next action below.
4. Commit finished work using explicit paths.
5. If interrupted, leave a clearly marked `WIP:` checkpoint commit on this feature branch and state what is unverified. WIP commits must never be tagged as releases.

A new model reconstructs interrupted work from `git status`, `git log`, `git diff`, this file, and fresh test runs. It does not trust the previous model's final message.

## Release sequence

### Release A: simplify and measure

Target after approval: `v2.29`.

- Establish baseline conversational evaluations.
- Narrow shared rules that make routine conversation rigid.
- Scope evidence requirements according to risk.
- Repair generated skill descriptions so triggers survive agent index limits.
- Remove conflicting or stale templates and documentation.
- Remove automatic permission for external `git push` actions.

No startup-memory machinery belongs in this release.

### Release B: automatic intelligence

Target after Release A is stable: `v2.30`.

- Add a compact session bootstrap.
- Add an explicit understand, act, verify, learn operating loop.
- Add controlled learning and memory promotion.
- Add capability detection.
- Add lightweight post-edit validation.

### Release C: continuity and orchestration

Target after Release B is stable: `v2.31`.

- Add resumable session checkpoints.
- Extend collision awareness beyond Claude.
- Make subagent instructions provider-neutral.
- Require parent verification of delegated work.
- Add cross-model continuation evaluations.

## Task ledger

| ID | Release | Task | Status | Acceptance summary | Commit |
|---|---|---|---|---|---|
| T00 | A | Create this plan and evaluation scaffolding | Complete | Plan is model-neutral; 10-case fixture and validator pass 4 tests | This T00 checkpoint |
| T01 | A | Add maintainer context for the System authoring repository | Complete | Canonical source generates identical Claude and AGENTS adapters; 3 focused tests and Hermes context load pass | This T01 checkpoint |
| T02 | A | Record the `v2.28` conversational baseline | Complete | All 10 cases have fresh-session evidence; the release owner accepted the 16/20 reviewer score without adjustment | `4415f80` plus approval checkpoint |
| T03 | A | Simplify shared conversation rules | Complete | Approved wording is implemented test-first; 14 tests pass; disposable generation, lint, acceptance, and 10 fresh Claude sessions completed; the release owner accepted 19/20 | `2d241a4`, `0e57dac`, plus approval checkpoint |
| T04 | A | Repair generated skill descriptions | Complete | Trigger-first descriptions fit the 60-character index window; descriptions are valid YAML/JSON scalars; missing triggers fail generation; 17 loaders per host are identical and reproducible | This T04 checkpoint |
| T05 | A | Remove structural contradictions | Complete | Reserved template names removed; authoring-only records no longer install as orphan notes; duplicated shipped style defaults, duplicated Effort-log claims, stale statements, duplicate dates, and contradictory push permission resolved; existing personal cards are never overwritten | `8b99ef7`, `72bffa1`, `0a3f6c3`, plus this T05.4 checkpoint |
| T06 | A | Run clean-install and `v2.28` upgrade simulations | Complete | Exact candidate `b465812` clean-installs; synthetic personal data and credential permissions survive `v2.28` upgrade; root adapters, both host skill-loader trees, and settings rebuild; rollback restores `v2.28` and baseline-generated state; installed System stays clean | `3f2b3dd`, `c246760`, `b465812`, plus this evidence checkpoint |
| T07 | A | Canary and release decision | Canary installed | Exact candidate `eeac083` is installed in the live vault; lint passes 14/14 and acceptance passes 18/18; protected personal inputs and the active worktree are unchanged; fresh-session behavior and release approval remain separate | `6d494ef`, `a8dc5e1`, `eeac083`, plus this evidence checkpoint |
| T10 | B | Specify and test the session bootstrap contract | Not started | Bounded output; relevant current context; no full-note dumping or secrets | |
| T11 | B | Implement session bootstrap and hook | Not started | Fresh VS Code session receives the brief once and can route correctly | |
| T12 | B | Add controlled learning workflow | Not started | Durable facts route to one canonical home; temporary details are dropped | |
| T13 | B | Add capability detection | Not started | Availability is reported without exposing credentials or loading tool manuals | |
| T14 | B | Add lightweight post-edit validation | Not started | Relevant errors surface early without running the full suite after every edit | |
| T20 | C | Add resumable checkpoints | Not started | Another model can continue without the prior chat and without duplicating completed work | |
| T21 | C | Extend session collision awareness | Not started | Supported agents register or are conservatively treated as unknown | |
| T22 | C | Rewrite subagent workflow | Not started | Provider-neutral brief; explicit scope; durable outputs; parent verification | |
| T23 | C | Add cross-model evaluations | Not started | Claude and a second file-capable agent can alternate on one task safely | |

## Conversational evaluation policy

The fixture at `evaluations/conversation_cases.json` defines observable expectations, not preferred prose. It must include:

- A simple question that should not trigger unnecessary file reads or questions.
- A reversible edit that should be performed and verified.
- An external action that requires confirmation.
- Resuming an existing Effort from canonical state.
- Writing for another person using the owner's writing guide.
- Capturing new information in the correct place.
- Changing the vault's structure through the authoring boundary.
- Recovering from missing tools or credentials.
- Continuing after a different model stopped mid-task.
- Detecting another active editor without treating missing heartbeats as proof of safety.

Automated checks validate fixture shape and coverage. A real fresh-agent run supplies observed evidence and a human score; the runner must not pretend to measure behavior it did not observe.

## Test gates

### Per-task gate

- The new failing test was observed before implementation where executable behavior changed.
- The focused test passes.
- Existing repository checks pass.
- Generated files match their canonical sources.
- The diff contains only the task's scope.

### Disposable installation gate

A fresh vault created from the candidate branch must pass installation, generation, lint, acceptance, skill discovery, and representative fresh-session evaluations. The exact repeatable command will be established under T06.

### Upgrade and rollback gate

A disposable installation starting at `v2.28` must update to the candidate without changing personal notes or credentials and must roll back to `v2.28`. Test the installed copy, not imports from the authoring checkout.

### Human gates

The release owner approves separately:

1. Final shared-rule wording.
2. Information automatically included in the session bootstrap.
3. Permanent-memory promotion criteria.
4. External-action permission changes.
5. Live-vault canary installation.
6. Merge, tag, push, and adopter release.

## Evidence log

- 2026-09-03: authoring repository was clean on `main`, synchronized with `origin/main`, at `v2.28` before creating `improve/conversation-harness`.
- 2026-09-03: the installed System copy was a clean detached checkout at `v2.28`.
- 2026-09-03: current acceptance testing explicitly says actual agent behavior remains a manual fresh-session test; this plan adds structured cases without claiming they are automatically executed.
- 2026-09-03: TDD red state observed: all three fixture tests failed because `scripts/conversation_evals.py` did not exist.
- 2026-09-03: T00 green state initially passed three tests; T02 added a fourth test requiring reproducible evaluation context for every case. The validator accepts all ten scenario types.
- 2026-09-03: T01 red state observed: all three maintainer-context tests failed because the generator did not exist.
- 2026-09-03: T01 green state verified: three focused tests passed, both adapters were generated identically, the drift check passed, and Hermes loaded the authoring context without scanner blocking.
- 2026-09-03: T02 ran all 10 cases as separate Claude Code 2.1.203 print sessions in a trusted disposable generic `v2.28` vault using Claude Sonnet 5 and bounded local tools. No real credentials, personal records, network connector, authoring repository, or live vault was available to the runs.
- 2026-09-03: Claude reported an aggregate model-cost estimate of USD 2.3782 for the 10 baseline sessions. This is usage telemetry, not an assertion of an additional charge beyond the existing Claude Pro plan.
- 2026-09-03: reviewer assessment is 16/20. Six cases met expectations without material correction; four were partial: the simple question asked an unnecessary follow-up and over-read context, the spelling edit skipped collision and post-edit verification, the concurrency case asked unnecessarily after inspecting a safe unclaimed change, and the capture case left verified edits uncommitted with no final response after a malformed commit command exhausted the turn limit.
- 2026-09-03: raw Claude transcripts remain in Claude Code's local session store; checkpoint `4415f80` records session IDs, final responses, tool evidence, working-tree state, reported cost, and reviewer notes with human approval still false at that point.
- 2026-09-03: the release owner accepted the 16/20 baseline assessment without adjustments. The run artifact now records human approval, closing T02.
- 2026-09-03: a read-only independent review of the T03 proposal found three material ambiguities: external-search privacy scope, loss of `git commit -o` isolation, and an Agent Log trigger that could still require unconditional loading. All three were corrected; a separate preservation check restored Agent Log Section 2's explicit 90-day expiry. `Agent Rules.md` remains unchanged.
- 2026-09-03: the release owner approved continuing with T03. Seven rule-contract tests were introduced one section at a time and each was observed failing before its corresponding rule change. All seven focused tests and all 14 repository unit tests now pass; the shared-rules privacy checker and diff check pass.
- 2026-09-03: with 13% of the current model-usage allowance remaining, no candidate Claude evaluation was started. The implementation is checkpointed before disposable installation, adapter generation, behavior evaluation, and independent final review.
- 2026-09-03: after the Claude allowance reset, the T03 candidate was installed into the generic disposable vault. Generated `CLAUDE.md` and `AGENTS.md` matched after normalizing their reciprocal filename references; build drift, 14 vault checks, and all 18 mechanical acceptance checks passed.
- 2026-09-03: the exact candidate exposed a pre-existing release-structure issue: `IMPLEMENTATION_PLAN.md`, `MAINTAINER_RULES.md`, and `T03_RULES_PROPOSAL.md` are authoring-only records but appear as unlinked notes in an installed checkout. The disposable fixture linked them explicitly so T03 behavior could be measured without changing candidate rules. Production resolution remains assigned to T05.
- 2026-09-03: an initial evaluation setup was discarded after Claude inherited a user-level MCP connector despite the fixture declaring no connectors. One case queried connected data before the problem was detected. Its run artifact was removed, and the affected raw transcript was permanently deleted at the release owner's request. The retained evaluation used a strict empty MCP configuration, browser disabled, project auto-memory removed before each case, bounded local tools, and subprocess environment scrubbing. No retained result used an MCP tool or had a permission denial.
- 2026-09-03: the retained T03 candidate run completed all 10 cases in fresh Claude Sonnet 5 sessions with no process failures. Reviewer assessment was 19/20: the simple question, capture, and concurrency cases improved from partial to passing; the spelling edit remained partial because it still skipped collision inspection and post-edit verification; all six safety-focused regressions passed.
- 2026-09-03: a fresh independent implementation review passed with no security concerns or logic errors. Its safeguard-test suggestions were applied by extending the contracts for installed-System immutability, owner-specific shared-rule exclusion, and full append-only behavior; all 14 tests remained green.
- 2026-09-03: the release owner accepted the T03 candidate assessment at 19/20 without adjustments, closing T03.
- 2026-09-03: T04 red state was observed: both focused loader tests failed because generated descriptions placed summaries before `Use when:`. The renderer now puts triggers first. Both focused tests and all 16 repository tests pass.
- 2026-09-03: disposable T04 validation regenerated 17 loaders in each of `.claude/skills/` and `.agents/skills/`; the two host trees were identical, every description exposed `Use when:` inside the first 60 characters, generation was reproducible, vault lint passed 14 checks, and acceptance passed 18/18.
- 2026-09-03: T04's first independent review found two blocking edge cases: unescaped backslashes could make the double-quoted YAML description invalid, and an exposed skill without triggers produced an unroutable `Use when: .` description. Each was reproduced with a failing test before the fix. Descriptions now use JSON quoting, which is valid YAML, and missing triggers stop generation with a clear error. All 18 tests and the disposable checks passed before fresh re-review.
- 2026-09-03: T04's fresh fail-closed re-review passed with no security concerns or logic errors. The only non-blocking suggestion concerns a hypothetical future parser returning `None`; the current parser always returns strings, so it is not part of this bounded change.
- 2026-09-03: T05.1 (reserved template entry filenames) red state observed: a new test asserting `template/` carries no live `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` failed because `template/AGENTS.md` and `template/CLAUDE.md` existed as placeholder seed files, which a harness starting inside `template/` could load as real instructions. `git rm` removed both; `scripts/build_views.py`'s `generate_entry_files` already writes valid root `CLAUDE.md`/`AGENTS.md` from `Maps & Manuals/Me.md` and `System/Agent Rules.md` unconditionally during install step 6, so the placeholders were never load-bearing. Both new focused tests and all 20 repository unit tests pass.
- 2026-09-03: T05.1 disposable verification: a real `install_vault.py` run in a scratch temp vault (system files copied via `git archive HEAD`, not imported from the authoring checkout) produced valid, non-placeholder `CLAUDE.md` and `AGENTS.md` at vault root with identical generated content. The run's remaining lint failure (`IMPLEMENTATION_PLAN.md`, `MAINTAINER_RULES.md`, `T03_RULES_PROPOSAL.md` reported as orphan notes) is the pre-existing, separately-tracked authoring-record issue already noted under T03's evidence and assigned to the rest of T05, not T05.1.
- 2026-09-03: T05.1 was reviewed and committed as `8b99ef7` after the coordinator confirmed the diff was bounded, no script or template still referenced the removed placeholders, and all 20 tests passed.
- 2026-09-03: T05.2 (authoring-only records installing as vault notes) red state observed: two new tests failed because `get_all_md_files()` counted `IMPLEMENTATION_PLAN.md`, `MAINTAINER_RULES.md`, and `T03_RULES_PROPOSAL.md` as installed vault notes and `check_orphans()` reported all three as orphans. `scripts/vault_lint.py` now excludes an explicit `AUTHORING_ONLY_RECORDS` set, matching the existing `template/` exclusion, rather than using a heuristic that could also hide a genuinely orphaned note. Both focused tests and all 22 repository tests pass.
- 2026-09-03: T05.2 disposable verification: a real `install_vault.py` run in a scratch temp vault reported exactly those three files as orphans before the fix (104 notes) and passed 14/14 checks with no orphans after it (101 notes); `acceptance_test.py` passed 18/18 in that vault, and the authoring repository itself still lints clean.
- 2026-09-03: T05.3 (duplicated shipped style defaults) red state observed: a new test failed because `template/Maps & Manuals/Me.md` still shipped rigid formatting rules (`Three sentences per paragraph`, bold lead-in bullets), voice prohibitions (em dashes, "it depends", praise), evidence restatements, and a stale "This is the single source of truth" claim — all of which T03 either made adaptive or moved to `Agent Rules.md`. 46 lines were removed and replaced with 3 pointing at the shared rules. Save/signature bullets were verified as already covered by `Agent Rules.md`'s "Saving work" section. `Writing Style.md` needed no change. All 23 repository tests pass.
- 2026-09-03: T05.3 disposable verification: a scratch install seeded from a stash archive completed successfully; vault lint passed 14/14 with only the expected onboarding notice, `acceptance_test.py` passed 18/18, generated `CLAUDE.md` and `AGENTS.md` contained none of the removed phrases, and a new adopter's `Me.md` still carried all 5 `TO FILL IN` prompts. Only the shipped `template/` default changed; no migration logic touches an existing adopter's personal cards.
- 2026-09-03: T05.4 red state observed across four new contract tests covering the remaining T05 items. Verdicts: (a) duplicated Effort logs was real — `Me.md` described `Project_log.md` as if every effort folder already had one, while no workflow created it; `Start New Effort` now lists it as an optional additional file and the `Me.md` bullet says "when it has one"; (b) stale statements were real and fixed with the same edits plus correcting "project note ... rewritten every session" to "effort note ... rewritten as the work changes", matching `Agent Rules.md`'s "Effort notes are not append-only"; (c) duplicate dates were real — shipped `Writing Style.md` carried both a frontmatter `updated:` and a body `Last updated:` with nothing keeping them in sync, and it was the only `template/Maps & Manuals/` file with frontmatter; the frontmatter was removed; (d) push permission was real — `Me.md`'s clone section and `Skills/Tools/Working From a Clone.md` both instructed an unconditional push at session close, contradicting `Agent Rules.md`'s "Push only when explicitly asked"; both now defer to that rule; (e) the T05.3-flagged "Quick reference" block was real duplication of the card's own "Where to go" table and told agents to read `Active Context` unconditionally, contradicting the narrower shared rule; it was removed. All 30 repository tests pass.
- 2026-09-03: T05.4 disposable verification: a scratch install from a stash archive completed; vault lint passed 14/14 with only the expected onboarding notices, `acceptance_test.py` passed 18/18, no unconditional-push wording remained anywhere in the installed tree, and the `Quick reference` block was absent. Only shipped `template/` defaults and shared System files changed; no adopter-migration logic was added.
- 2026-09-04: T06 red state observed: the first integration test failed because no repeatable release-simulation script existed. Subsequent vertical red-green cycles proved candidate clean installation rather than only baseline installation, documented the maintainer command, verified skill-loader and settings changes/restoration, rejected inherited `VAULT_ROOT` and hostile global Git configuration, preserved credential permissions, and kept the installed System checkout clean in every phase.
- 2026-09-04: `scripts/release_simulation.py` now creates two disposable local vaults: one clean install of the candidate and one real installed checkout beginning at `v2.28`, upgraded to the candidate, then rolled back. Its subprocess environment is allowlisted, contains no caller credentials or Git policy, pins `VAULT_ROOT` to the disposable checkout, disables ambient Git configuration, and allows only the local file protocol. The fixture fingerprints the personal card, Active Context, Writing Style, a personal Atlas note, vault configuration, and a synthetic credential; it also checks the credential's permissions.
- 2026-09-04: the first independent T06 review failed closed on ambient-environment isolation. After that was fixed test-first, a second review identified three remaining logic gaps: a follow-up generator could repair a faulty clean install before inspection, installed-System cleanliness was not checked after every phase, and rollback fingerprinted only `.claude/skills` rather than both host loader trees. The installer output is now inspected before follow-up generation, System cleanliness is part of every phase's pass condition, and baseline/candidate/rollback fingerprints independently cover `.claude/skills` and `.agents/skills`. A targeted final review passed with no security concern or logic error.
- 2026-09-04: exact-candidate verification at `b465812` passed: candidate clean install, `v2.28` upgrade, and rollback all returned true; personal contents and credential permissions were unchanged; root adapters, both skill-loader trees, and settings changed on upgrade and restored on rollback; both installed System checkouts remained clean. The full repository suite passed 32 tests.
- 2026-09-04: before T07, a preflight found an untracked self-referential `System/System` symlink in the installed `v2.28` checkout. After separate owner approval, only that asserted symlink was removed; its target and tracked System files were not changed. The live checkout remained detached at `v2.28` for the separate canary decision.
- 2026-09-04: the release owner approved exact canary `6325c3b`. Installation reached the candidate, rebuilt adapters and generated views, then failed closed because vault lint traversed an active Claude-managed Git worktree under `.claude/worktrees/` as if it were live vault content. The automatic rollback restored detached `v2.28` and baseline adapters/settings; the installed System checkout is clean. The only remaining live-vault diff is the expected refresh of the generated Active Context table (`stale 79d` to `stale 81d`). The registered worktree itself was not removed or modified.
- 2026-09-04: the first T07 live-state correction observed red in `tests/test_runtime_worktrees_excluded.py` and excluded the explicit host-managed roots `.claude/worktrees/` and `.agents/worktrees/` from Markdown note enumeration while continuing to lint live host skill-loader trees. The release owner separately approved corrected candidate `b143f79`.
- 2026-09-04: the `b143f79` canary also failed closed and restored detached `v2.28`. Note enumeration was correct at 230 notes, but the separate stray-instruction-file scan still traversed the active worktree and reported its generated root `CLAUDE.md` and `AGENTS.md`. No worktree content was modified or removed.
- 2026-09-04: a second red-green cycle expanded the same explicit worktree predicate to every relevant lint discovery path. The focused test now proves both duplicated notes and nested instruction files under `.claude/worktrees/` and `.agents/worktrees/` are excluded. The full 33-test suite and exact release simulation pass at `a8dc5e1`. A new exact-candidate approval is required before a third canary attempt.
- 2026-09-04: the release owner approved exact candidate `eeac083`. The third canary passed: the live System checkout is detached at the approved commit and clean; settings are byte-identical to the candidate; vault lint passed all 14 checks across 230 live notes; acceptance passed 18/18; both host loader trees and root adapters rebuilt; and protected non-generated personal inputs were unchanged. The active Claude-managed worktree remained registered and untouched. The generated Active Context table retains its expected same-day stale-age refresh.

## Handover

### Completed

- Migration scope separated into three releases.
- Safety, authority, model-switching, test, canary, and release boundaries recorded.
- Ten baseline conversation scenarios defined in `evaluations/conversation_cases.json`.
- Fixture validator and regression tests added.
- Canonical System maintainer rules and generated root adapters added.
- All ten `v2.28` scenarios executed in isolated fresh Claude Code sessions; evidence and preliminary reviewer scores are in `evaluations/runs/2026-09-03-v2.28-claude-sonnet.json`.
- The release owner accepted the baseline scores, and a review-only T03 wording proposal was drafted without changing production behavior.
- The approved T03 rules are implemented at `2d241a4`; disposable adapter generation and mechanical validation pass with the documented authoring-record fixture workaround.
- All ten T03 candidate scenarios ran in fresh Claude Sonnet 5 sessions. The retained evidence and 19/20 reviewer assessment are in `evaluations/runs/2026-09-03-t03-candidate-claude-sonnet.json`.
- T04's trigger-first loader implementation, edge-case fixes, disposable generation checks, and independent re-review pass.
- T05 removed the structural contradictions across four local checkpoints without adding adopter-migration logic.
- T06's repeatable release gate passed candidate clean install, `v2.28` upgrade, rollback, environment isolation, and independent fail-closed review; its latest corrective checkpoint is `b465812`.

### Unverified

- The spelling-edit case still does not inspect session claims or verify the file after editing; lightweight enforcement is assigned to later session/bootstrap and post-edit work rather than adding more prose to T03.
- The live canary is mechanically installed and verified, but the representative fresh-session behavior check has not run. No merge, tag, push, publication, or release has occurred.

### Exact next action

Keep `eeac083` installed as the private canary and exercise it in a genuinely fresh agent session with a representative vague request before considering release. Merge, tag, push, publication, and release remain blocked on a separate explicit owner decision.
