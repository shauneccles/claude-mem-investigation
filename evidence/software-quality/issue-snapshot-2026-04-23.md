# Issue snapshot — 2026-04-23

Five independent community-filed bug reports against `thedotmack/claude-mem`, all opened on a single day. All five were still open at review time (2026-04-24). None of the authors have `author_association: OWNER | COLLABORATOR | CONTRIBUTOR` — every one is an outside user.

The five cover: data-model pollution, install/uninstall hygiene, process lifecycle, prompt-volume waste, and platform-specific silent failures. Point-releases affected span v12.1.2 → v12.3.9 (the three most recent minor versions).

Links are to the upstream repo, not to this review's pinned SHA, because these are live tickets whose state may change after publication. The captured snapshot as of 2026-04-24 is in `issues-graphql.jsonl.gz` in this directory.

---

## #2109 — SessionStart context injection silently fails on Windows + Git Bash

**Author:** `vdruts` (author_association: NONE)
**Filed:** 2026-04-23 22:24 UTC
**Labels:** (none yet — not triaged)
**Link:** https://github.com/thedotmack/claude-mem/issues/2109

**Summary** (from body):

> Severity: high | Component: windows / hooks | Version: 12.3.8 (likely all 12.x)
>
> SessionStart context injection (the prior-session summary that should appear at session start) silently never fires on Windows + Git Bash. Worker is healthy and PostToolUse / Stop events show up in ~/.claude-mem/logs/ (because the transcript watcher catches them out-of-band), but the recent-context dump never gets injected into the model. Users see this as "claude-mem stopped showing CLI/session info."
>
> The hook computes the worker health URL with a port/POSIX-path mismatch that only manifests under Git Bash's path translation, and fails quietly.

---

## #2108 — observer-sessions restart/compaction churn can consume ~97% of prompt volume

**Author:** `ahmed-hassan19` (author_association: NONE)
**Filed:** 2026-04-23 20:45 UTC
**Link:** https://github.com/thedotmack/claude-mem/issues/2108

**Summary** (from body):

> On my install, 581 of 892 rows in user_prompts are observer-session churn — distinct `memory_session_id`s for the same `contentSessionId` re-entered because of worker restart/compaction. That's 65% of rows on the churn side; measured prompt-character volume across the recent month is ~97% observer-session content.
>
> Expected invariants that appear to be violated:
> - observer-sessions should not dominate prompt-character volume during ordinary use
> - a single observed primary session should not trigger repeated `handleSessionInitByClaudeId` calls for the same `contentSessionId`
> - worker restart should not cause repeated stale `memory_session_id` churn on the same observer flow
> - startup backfill should not materially amplify token usage after repeated worker restarts
> - compaction should not cause observer prompts to ingest already-expanded session material or recursively re-observe prior observer content

Reported on v12.3.7, v12.3.8, and v12.3.9 — the current three point-releases.

---

## #2107 — worker-cli.js start/restart can self-trigger duplicate-worker detection

**Author:** `songjianping-cloud` (author_association: NONE)
**Filed:** 2026-04-23 17:04 UTC
**Link:** https://github.com/thedotmack/claude-mem/issues/2107

**Summary:** worker start/restart sequence can race against its own duplicate-detection logic and leave claude-mem in a broken reconnect state where the worker is alive but the CLI can't talk to it.

---

## #2106 — Multiple errors across install, uninstall, reinstall

**Author:** `ogrotten` (author_association: NONE)
**Filed:** 2026-04-23 14:19 UTC
**Link:** https://github.com/thedotmack/claude-mem/issues/2106

**Summary** (from body):

> I had an adventure with install and reinstall. ... Uninstall took A WHILE. Multiple files in multiple places was a small surprise. The remaining and automatically restarting daemons likely caused initial reinstall failures.
>
> - Reinstall prompted to overwrite existing installation (and failed a couple of times), suspected leftover files from the broken install were part of the problem
> - Decided on full uninstall/reinstall, no data to save
> - First cleanup: npm uninstall, kill processes, remove ~/.claude-mem
> - Found stale references in ~/.claude/settings.json
> - ~/.claude-mem kept getting recreated by active session hooks
> - Multiple rounds of find-and-delete across 6+ directories
> - Found detached daemon processes surviving window restarts
> - Killed daemons and nuked all remaining directories to achieve clean state
> - Processes to kill:
>   - worker-service.cjs (bun, detached --daemon)
>   - mcp-server.cjs (bun)
>   ...

---

## #2104 — Observer agent's own system prompt and tool event XML are persisted as rows in `user_prompts` table

**Author:** `marcelopossa` (author_association: NONE)
**Filed:** 2026-04-23 12:43 UTC
**Link:** https://github.com/thedotmack/claude-mem/issues/2104

**Summary:** The observer-agent subprocess's own system prompt and tool event XML are written into the `user_prompts` table as if they were user input. Reproduces on v12.1.2 through v12.3.9. The data-model invariant "`user_prompts` contains rows originating from the user" does not hold.

---

## Why this snapshot matters

Bug-report volume on a single day isn't by itself a quality indicator — a popular project will have bad days. What this snapshot is evidence of, taken together with the other findings in [`README.md`](README.md), is:

- Concrete invariant violations in current releases — data-model pollution (#2104), prompt-volume waste (#2108), process-lifecycle incorrectness (#2107), install/uninstall-hygiene failures (#2106), platform-silent-failure (#2109).
- Reports spanning the three most recent point-releases — not a single bad version, a sustained defect surface.
- All from outside contributors — the author's internal testing isn't catching them.

These are shown verbatim with links so readers can judge the reports themselves, and revisit them later to see how they were resolved.
