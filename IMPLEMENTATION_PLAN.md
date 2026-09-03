# Conversation Harness Improvement Plan

> Working control document for the `improve/conversation-harness` branch. It allows any capable agent to continue the migration without access to earlier conversations. Remove or convert it into permanent design documentation before release.

## Objective

Make an installed AI OS vault feel informed, decisive, safe, and continuous when its owner talks to an agent through VS Code. Improve the experience for Camilo and other adopters without requiring one model, one provider, one subscription, or one uninterrupted session.

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
- Never tag, push, publish, or install a candidate in a live vault without Camilo's explicit approval.
- Run behavior-changing work test-first where automated tests are possible.
- Verify subagent or predecessor claims against files, git, and test output.
- One editing agent per checkout. Parallel editors require separate worktrees and non-overlapping scopes.

## Working protocol

Each agent session takes exactly one task ID unless Camilo explicitly expands the scope.

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
| T00 | A | Create this plan and evaluation scaffolding | Complete | Plan is model-neutral; 10-case fixture and validator pass 3 tests | This T00 checkpoint |
| T01 | A | Add maintainer context for the System authoring repository | Complete | Canonical source generates identical Claude and AGENTS adapters; 3 focused tests and Hermes context load pass | This T01 checkpoint |
| T02 | A | Record the `v2.28` conversational baseline | Not started | Every evaluation case has observed evidence and a human score; no invented passes | |
| T03 | A | Simplify shared conversation rules | Not started | Routine answers are natural; high-risk safeguards and adopter customization remain | |
| T04 | A | Repair generated skill descriptions | Not started | Trigger-first descriptions fit the supported index budget and generated adapters remain reproducible | |
| T05 | A | Remove structural contradictions | Not started | Reserved template names, duplicate Effort logs, stale statements, duplicate dates, and push permission are resolved with migration tests | |
| T06 | A | Run clean-install and `v2.28` upgrade simulations | Not started | Personal data survives; adapters rebuild; rollback works | |
| T07 | A | Canary and release decision | Not started | Camilo approves live canary and release separately; no agent self-publishes | |
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

Camilo approves separately:

1. Final shared-rule wording.
2. Information automatically included in the session bootstrap.
3. Permanent-memory promotion criteria.
4. External-action permission changes.
5. Live-vault canary installation.
6. Merge, tag, push, and adopter release.

## Evidence log

- 2026-09-02: authoring repository was clean on `main`, synchronized with `origin/main`, at `v2.28` before creating `improve/conversation-harness`.
- 2026-09-02: the installed System copy was a clean detached checkout at `v2.28`.
- 2026-09-02: current acceptance testing explicitly says actual agent behavior remains a manual fresh-session test; this plan adds structured cases without claiming they are automatically executed.
- 2026-09-02: TDD red state observed: all three fixture tests failed because `scripts/conversation_evals.py` did not exist.
- 2026-09-02: T00 green state verified: three unit tests passed and the validator accepted all ten required scenario types. No agent behavior has been run or scored.
- 2026-09-02: T01 red state observed: all three maintainer-context tests failed because the generator did not exist.
- 2026-09-02: T01 green state verified: three focused tests passed, both adapters were generated identically, the drift check passed, and Hermes loaded the authoring context without scanner blocking.

## Handover

### Completed

- Migration scope separated into three releases.
- Safety, authority, model-switching, test, canary, and release boundaries recorded.
- Ten baseline conversation scenarios defined in `evaluations/conversation_cases.json`.
- Fixture validator and regression tests added.
- Canonical System maintainer rules and generated root adapters added.

### Unverified

- No candidate vault conversation behavior has been implemented.
- No conversational baseline has been run.
- No disposable-install command has been established for this branch.

### Exact next action

Start T02: create a disposable generic vault at `v2.28`, run each evaluation case in a fresh Claude Code session with bounded tools, preserve raw outputs separately from expectations, and record evidence without changing the live vault.
