---
id: working-from-a-clone
type: tool
status: stable
domain: ai_os
updated: 2026-08-28
summary: "What is different when the vault is a clone rather than the machine it lives on, so absent tools are not reported as broken."
triggers: "System folder missing, skills all dead links, credentials missing, working from phone or browser, cloned repo, personal-google unavailable"
expose: true
---

# Working From a Clone

You are reading a clone of the vault repository, not the machine the vault lives on. This happens when Camilo works from his phone or a browser. **Read this before concluding anything is broken.**

## Fetch the skills first

`System/` is not tracked by the vault repository, so a clone has every note and zero workflows. Skill Map lists them and every link is dead.

```
git clone --depth 1 https://github.com/camvalero09/ai-os System
```

If that fails because the repository is private and this environment has no access, say so plainly and stop. A guessed version of a tested workflow is worse than none.

## What is absent by design

**The local Google server cannot exist here.** `credentials/` is gitignored, so `personal-google` and `personal-outlook` are unavailable whatever their notes say. Use the host platform's own Gmail, Calendar and Drive connectors instead, and tell Camilo that is what you did, because the permissions differ from his own server. Do not report the tool as broken.

**The commit check is not installed.** Git hooks live outside the repository. Run the checks by hand before every commit:

```
python3 System/scripts/vault_lint.py
python3 System/scripts/build_views.py
```

**`vault.config.json` is absent**, so take identity from `Maps & Manuals/Me.md`, not from config.

## Your work only reaches Camilo by being pushed

There is no shared filesystem between here and his laptop. An edit that is never committed and pushed did not happen. Close with [[System/Skills/Workflows/Session Handover|Session Handover]] and push, or say clearly that you did not.

## One drift to expect

His laptop runs a pinned version tag while a clone takes the newest. If a skill behaves differently from how he describes it, that gap is the likely reason. Name it rather than working around it.
