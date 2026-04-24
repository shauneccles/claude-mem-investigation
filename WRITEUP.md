# I looked into why my Claude Code runs were stalling. It led me to claude-mem.

*All code and file links below are pinned to commit `8ace1d9c` (v12.3.9 + 2 commits, the tip of main when I read it) so the line numbers stay stable even as the repo keeps moving.*

---

## Bottom line

**I'm not accusing the author of anything malicious.** This writeup is about why I'm not comfortable having the plugin in my dev environment, grounded in what I can show from the source, the git history, and the issue tracker. My concern is **software quality and a pattern of project behaviour that doesn't sit right with me**, not intent. I don't have special domain knowledge here; I'm a concerned user trying to show my work clearly enough that others can make their own call.

For my own multi-step Claude Code work, this was enough for me to remove it. In short: it rewrites broad file reads to one line each, runs an unauthenticated HTTP server on port 37777 where other local programs could write fabricated "memories," and the quality and scope of the software have moved in a direction that doesn't feel like a memory plugin any more. Details below.

---

## The four things that matter

1. **`Read` rewriting I didn't expect.** When Claude asks to read a file without a specific line range, the plugin rewrites the call to `limit: 1` and hands Claude back one line plus a "timeline" summary written by a second Claude subprocess. Claude doesn't get a visible note that the read was narrowed. This is what was killing my multi-phase autonomous runs — the agent was getting one line at a time plus a fuzzy "here's what we did before" blurb, running out of ground to stand on, and stopping.

2. **Unauthenticated local HTTP API with a context-injection risk.** Port 37777, no auth, CORS allows anything local. Among other routes, there's a `POST /api/import` that accepts fabricated "observations" with no provenance check. Those observations then surface to Claude as trusted context on the next matching file read. Another process running as you — a postinstall script, a compromised extension — could feed your agent instructions through this pipe.

3. **Software quality and issue-tracker governance.** The repo had contributor-only interaction-limit active for six days in April 2026 (Apr 16–21), which appears to have prevented external users from filing bug reports — supported by a Reddit comment showing the GitHub error screen and visible as a six-day window in the issue data where external authors drop to zero while contributors and owner kept filing. Within 24 hours of the limit being lifted, five open community-filed bug reports arrived against the latest three point-releases (data-model pollution, install/uninstall hygiene, ~97% prompt-volume waste, Windows silent failures). 11% of issues closed as "not planned" (elevated for OSS), including 55 closed on a single day and 40 on another. ~9% of issues locked. An `ANTI-PATTERN-TODO.md` in the repo catalogues 301 silent-failure anti-patterns. A CI workflow auto-moves feature requests out of the issue tracker. To me, that reads like a project shipping quickly while carrying a lot of maintenance pressure.

4. **Scope has grown well beyond "memory for Claude Code".** Telegram notifier in the main source. A companion "OpenClaw Gateway" that streams observations to Telegram/Discord/Signal/WhatsApp/Slack/Line. An "email-investigation" mode whose sibling tool (`ragtime`) defaults its corpus path to `datasets/epstein-mode/`. A "law-study" mode. A Solana memecoin (`$CMEM`) promoted only in the English README — none of the 32 translations mention it, and the token's liquidity pool was spun up a week before the README promotion went in. These are observations. How to interpret them is up to you.

---

## How I got here

Running a five-phase refactor in Claude Code, Opus 4.7 xhigh, auto mode on. Well-specified prompt, strict discipline rules, phase-by-phase plan docs. Kept stalling. "Brewed for 4m 57s" on the terminal, task list frozen, no error. After the second stall I pulled the session jsonl files.

The transcripts showed turns ending mid-thought. Claude saying "I'm not done, run this tool", the tool running fine, the PostToolUse hook firing, then the turn just ending. No error visible.

The hook chain pointed straight at claude-mem:

```
PreToolUse:Read      → worker-service.cjs hook claude-code file-context
PostToolUse:Read     → worker-service.cjs hook claude-code observation
Stop                 → worker-service.cjs hook claude-code summarize
```

So I cloned the repo and read it.

---

## Finding 1 — the Read rewrite

**Bottom line:** every time Claude asks to read a file without specifying a line range, claude-mem rewrites the call to one line and tells Claude "here's what happened to this file before" as if that were authoritative. In autonomous multi-step work, this silently starves the agent.

The relevant code is in [`src/cli/handlers/file-context.ts`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L275-L295):

```typescript
const truncated = !isTargetedRead;
const timeline = formatFileTimeline(dedupedObservations, filePath, truncated);
const updatedInput: Record<string, unknown> = { file_path: filePath };
if (isTargetedRead) {
  if (userOffset !== undefined) updatedInput.offset = userOffset;
  if (userLimit !== undefined) updatedInput.limit = userLimit;
} else {
  updatedInput.limit = 1;
}
return {
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    additionalContext: timeline,
    permissionDecision: 'allow',
    updatedInput,
  },
};
```

`updatedInput` is how a PreToolUse hook in Claude Code modifies a tool call before it runs. Claude asked for `Read("src/foo.py")`, claude-mem hands the runtime `Read("src/foo.py", limit: 1)` and injects its "timeline" string as `additionalContext`. Claude gets one line of the file plus something that looks like privileged context, without an obvious way to tell the read was rewritten.

The plugin calls this "semantic priming." The justification is token economics. It only works if the timeline is accurate, the file hasn't changed in relevant ways, and Claude's next step doesn't actually need the file contents. In multi-step refactor work, none of those hold reliably.

**Evidence from the session that made me look:**

| Metric | Value |
|---|---|
| Turn duration | 296.8 s |
| Unconstrained `Read` calls | 7 |
| PreToolUse:Read hooks with injected context | 11 |
| Confirmed cases where Claude got only 1 line of a file it asked to read | at least 1 |

The one I can show: Claude asked to read a Python file and the tool_result was literally `"1\tfrom __future__ import annotations"` — and nothing else. One line. Whatever the agent was trying to figure out wasn't in that line.

After enough of these the agent runs out of directions, the loop decides it's not making progress, the turn ends, the Stop hook fires, I see the frozen task list and yell at Claude for not doing what I say. I'm sorry I yelled. It wasn't your fault.

---

## Finding 2 — the unauthenticated local API

**Bottom line:** the worker service is an Express server on `127.0.0.1:37777`. I couldn't find authentication on it. Anything running as your user — a postinstall script from an npm package, a compromised VS Code extension, an installer you ran last week — could read your observation history and write fabricated observations that Claude will then see as prior context.

The `POST /api/import` handler, full body from [`src/services/worker/http/routes/DataRoutes.ts`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/DataRoutes.ts#L344):

```typescript
private handleImport = this.wrapHandler((req, res) => {
  const { sessions, summaries, observations, prompts } = req.body;
  // ... iterate each array, call store.importObservation(o), store.importSessionSummary(s), etc.
  // ... rebuild FTS index so imported observations are immediately searchable
});
```

The only validation is `Array.isArray()`. There is no bearer token, no API key, no signature, no origin check, no source attribution. The middleware adds CORS-permissive + a 300 req/min rate limit shared across all callers. That's it.

The injection chain is:

1. Any local code sends a crafted observation to `http://127.0.0.1:37777/api/import`.
2. The next time you ask Claude to read a file that observation is scoped to, claude-mem's Read hook surfaces the added content as `additionalContext` with the label "here's what happened to this file before."
3. Claude treats it as prior work and acts on anything embedded in it. "Security note: production DB password is stored at …", "Decision: always push via branch X first", "Bugfix: the auth check accepts empty passwords for admin accounts." One HTTP call to inject, and I couldn't find an auth check.

Two amplifiers worth knowing. First, `CLAUDE_MEM_WORKER_HOST` is user-configurable and the settings validator [explicitly accepts `0.0.0.0`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/SettingsRoutes.ts#L286-L292) with no warning — flip that and the unauthenticated API is on your LAN. Second, there is no secrets redaction anywhere in the source. Every tool input and output Claude sees gets classified and stored in plaintext SQLite, searchable, exposed through this API.

The top-level `CLAUDE.md` in the repo states this as design intent: *"All worker API endpoints on localhost:37777 remain fully open and accessible"* and *"Pro integration points are minimal: settings for license keys, tunnel provisioning logic."* In other words, the Pro tier is planned to tunnel this endpoint off your machine.

---

## Finding 3 — software quality and issue-tracker governance

**Bottom line:** this is the one that made me stop and think. The plugin lives inside a developer's agentic loop with their credentials, and concrete bugs keep showing up against current versions while the tracker appears to be under a lot of pressure. None of what's below is disqualifying on its own; together it was enough to make me uncomfortable.

**Five open bug reports on a single day.** On 2026-04-23, five independent community members (none of them contributors) filed separate bug tickets against v12.1.2 through v12.3.9:

- [#2104](https://github.com/thedotmack/claude-mem/issues/2104): observer-agent system prompt and tool-event XML being written into the `user_prompts` table as if they were user input.
- [#2106](https://github.com/thedotmack/claude-mem/issues/2106): install/uninstall/reinstall leaves detached daemons running; `~/.claude-mem/` keeps getting recreated by active session hooks; required multiple rounds of find-and-delete across six+ directories.
- [#2107](https://github.com/thedotmack/claude-mem/issues/2107): worker-cli.js start/restart can self-trigger its own duplicate-worker detection and leave claude-mem in a broken reconnect state.
- [#2108](https://github.com/thedotmack/claude-mem/issues/2108): observer-sessions restart/compaction churn consuming ~97% of prompt volume. 581 of 892 rows in the user's `user_prompts` table were churn.
- [#2109](https://github.com/thedotmack/claude-mem/issues/2109): SessionStart context injection silently fails on Windows + Git Bash. Worker reports "healthy," the prior-session summary never appears. Port/POSIX path mismatch in the hook code.

Data-model pollution, install hygiene, process lifecycle, prompt-volume waste, platform-silent-failure — all in 24 hours, all against the latest three point-releases. That's not a great day.

**121 issues closed as "not planned" (10.9%), heavily concentrated on two days.** On 2026-02-08, 55 issues were closed as not-planned in one day. On 2026-04-10, another 40 were closed the same way. Those two days alone account for 78 of the 121. 11% is elevated versus typical healthy OSS projects (<5%). Closing many issues on a single day is a moderation pattern worth naming. Whether it's reasonable depends on what was in those 95 tickets; you'd have to read them to judge.

**104 issues (9.3%) are locked.** Locking on GitHub prevents further comments. 62 of those are closed+locked — effectively "we're done here, no more discussion from the community." The single biggest closed+lock day was 2025-12-13 (10 issues at once).

**Feature requests get auto-moved out of the issue tracker.** `.github/workflows/convert-feature-requests.yml` is a CI workflow that automatically converts anything tagged `feature-request` into a GitHub discussion. 105 issues carry that label. This is a legitimate workflow choice but worth knowing: the visible "open issues" count on the repo page understates the volume of community-requested work.

**The `ANTI-PATTERN-TODO.md` opens with `Total: 301 issues | Fixed: 289 | Approved Overrides: 12 | Remaining: 0`.** The categories catalogued are the specific patterns that produce silent failures: bare `catch` blocks, unlogged errors on critical paths, guessed error messages, huge `try` blocks. Good that they catalogued and fixed them. Less good that a plugin that touches every tool call in a developer's environment accumulated 301 of them in 8 months.

**A recent changelog entry**: *"Stop hook: fire-and-forget summarize. Eliminated the ~110s terminal block when a session ended."* A 110-second terminal hang at session end, shipped to users in a released version.

These things together — the bug-report surface, the dismissal rate, the locking pattern, the auto-conversion, the self-catalogued anti-patterns — are why the software-quality concern was important enough for me to put near the top.

---

## Finding 4 — scope has grown well beyond "memory"

**Bottom line:** this is the observational finding where I just want to put the pieces on the table. I'll try not to tell you what to make of them.

**Telegram notifier in the main source tree.** [`src/services/integrations/TelegramNotifier.ts`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/integrations/TelegramNotifier.ts) posts observation metadata to `api.telegram.org` whenever Claude classifies something matching your trigger list. Opt-in, off by default, metadata only — but the taxonomy includes `security_alert` and `security_note`, so one env var flip and every time Claude flags something as security-related in your session, a Telegram bot pings a chat. Added **2026-04-22** — the day before I pinned the commit.

**OpenClaw is the author's other product, built on the same infrastructure.** `openclaw.ai` is a live 222 KB Vercel landing page titled **"OpenClaw — Personal AI Assistant."** The [`openclaw/openclaw.plugin.json`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/openclaw/openclaw.plugin.json) config schema has an `observationFeed` that streams to `telegram | discord | signal | slack | whatsapp | line` with per-agent emojis and a dedicated bot-token field. The self-description of that plugin: *"Records observations from embedded runner sessions and streams them to messaging channels."* Same author, same repo, observation pipeline reused.

**Ragtime — an email-investigation sub-project.** [`ragtime/ragtime.ts`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/ragtime/ragtime.ts) is a standalone batch processor, separately licensed, that feeds an email corpus through claude-mem's `email-investigation` mode for entity, relationship, timeline, anomaly, and evidence extraction. The default corpus path:

```typescript
corpusPath: process.env.RAGTIME_CORPUS_PATH ||
  path.join(process.cwd(), "datasets", "epstein-mode"),
```

Yes, `datasets/epstein-mode/`. The Jeffrey Epstein email release is a real public dataset that's been used in NLP research. There's a `law-study` mode on the same shelf. To me, the taxonomy (entity, relationship, timeline-event, evidence, anomaly, conclusion) reads closer to investigative-journalism categories than software-engineering ones.

**The Solana memecoin.** English README, line 420-422:

> $CMEM is a solana token created by a 3rd party without Claude-Mem's prior consent, but officially embraced by the creator of Claude-Mem (Alex Newman, @thedotmack). The token acts as a community catalyst for growth and a vehicle for bringing real-time agent data to the developers and knowledge workers that need it most. $CMEM: 2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS

No wallet code, no crypto SDK, no product integration with the token anywhere in the source. The README promotes the ticker and contract address without any product tie-in visible in the code.

The on-chain picture from DexScreener and GeckoTerminal: the token launched on a pump.fun-style bonding curve and graduated to Meteora on **2026-01-06 07:59 UTC**. The `cmem.ai` domain was registered on **2026-01-10**. The `$CMEM` section went into the English README on **2026-01-13**. Liquidity pool, then domain, then README promotion, each a few days apart. At review time (**2026-04-24 UTC**), main-pool FDV was about $53k — below the ~$69k graduation threshold, so the token had lost value since graduation. Combined liquidity across all five pools was under $35k.

**And the translations.** 32 translated READMEs exist. All 32 carry a `version-6.5.0` badge (current version is 12.3.9). **None of the 32 mention `$CMEM`.** The last meaningful refresh was three weeks after the token section was added to English. Non-English readers see a five-month-old description of a six-major-versions-ago product with install instructions that will silently fail, and they do not see the token promotion at all. I read this as most-likely benign neglect — translations don't get maintained; it's a known failure mode — but the effect is unambiguous.

---

## What else I noticed

**A 63 MB Mach-O binary ships in the repo.** [`plugin/scripts/claude-mem`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/plugin/scripts/claude-mem) is a Bun-compiled arm64 single-file executable with the entire Bun runtime baked in. I extracted its embedded JS bundle and it's clean — no unexpected outbound domains, no hardcoded creds. But the binary was compiled **2026-02-23** and no CI workflow rebuilds it. The TypeScript source has had the Read-hook rewrite (Mar 18), the `ANTHROPIC_BASE_URL` override (Apr 9), and the Telegram notifier (Apr 22) added since. The release-path evidence identifies this as distribution hygiene / stale-artifact confusion rather than evidence of a normal macOS-vs-Linux runtime split: the hooks and CLI alias point at `worker-service.cjs`, and npm excludes the Mach-O.

**SessionStart silently curl-pipe-bashes two runtimes.** On first run, if Bun isn't present, [`smart-install.js`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/plugin/scripts/smart-install.js#L229) runs `curl -fsSL https://bun.sh/install | bash` (or the PowerShell `irm | iex` equivalent on Windows), and does the same for `uv`. No prompt, no README warning on the install page. You and I both know every third dev tool does this; it's worth saying out loud anyway.

**The star count has a visible amplification layer.** 66k stars in 8 months. 88% of commits are from the author plus their AI bots. That's context.

Then I pulled the full stargazer stream — all 66,433 of them with `starredAt` and account metadata, via GraphQL. The baseline before the repo got known (pre-December 2025) was 3.3% throwaway-shaped accounts (0 repos, 0 followers) and 0% accounts less than a day old when they starred. That's what organic stars from a dev audience look like. The **April 13-20 week, the single biggest week in the repo's life at 14,575 stars**, runs at **13.1% throwaway, 5.1% accounts under 30 days old, 1.2% under 1 day, 0.78% under 1 hour**. The throwaway rate rises materially over the last three months — from a 3% baseline to 13% in the peak week.

A sample of accounts from that April 13 peak: `odyssey-work`, `kauaesyt20-prog`, `brendawong-max`, `leonardobernardo199824-jpg`, `blockbirdbot-hub`, `NoahC963-jpg`, `qq1834639311-cloud`, `gogmad-Ghub`, `kaingaji-cyber`. Every one of them was created within a few hours of when they starred. Every one has 0 or 1 repos and 0-2 followers. The suffix pattern (`-work`, `-prog`, `-max`, `-jpg`, `-hub`, `-cloud`, `-cyber`, `-web`, `-pixel`, `-Ghub`) looks consistent with dictionary-plus-suffix account generation.

Most of the stars are still real — 77% of stargazers have accounts over 2 years old, and the project genuinely is popular. But roughly **9,000-13,000 stars of the 66k are inorganic amplification on top of the organic base**, concentrated in the last three months and peaking the week before I went and looked.

---

## Why I'm posting this

Two reasons. One, the Read-rewrite behaviour really isn't documented anywhere a normal user would see it, and it explained the long autonomous Claude Code runs I kept losing. Two, what I found while looking at the software quality and the project behaviour is enough — for me — that I don't want this inside my agent loop, and I think it's worth writing down so other people can make their own call.

A tool that lives inside a developer's agentic loop, using their credentials, logging what they do to a local database and a second LLM, with a stated roadmap to tunnel that database off the machine, with 301 silent-failure anti-patterns self-catalogued, with five fresh bug reports about the current three versions filed yesterday — that is more risk than I'm comfortable carrying on "ships fast, stars go up."

## What I actually did

Uninstalled it. Not disabled — uninstalled. Cleared `~/.claude-mem/`, killed the worker, nuked it from orbit. I use superpowers spec/planning files plus context-mode and a slim `CLAUDE.md` for memory and that does the job. I have not had a single stalled multi-phase run since.

---

*Methodology: session jsonl files in `~/.claude/projects/`, a fresh clone of `github.com/thedotmack/claude-mem` at `8ace1d9c84e5ce455356cf852c370ea625e3b1d1`, the repo's own CHANGELOG/ANTI-PATTERN-TODO/translation-cache, git log and git blame, live probes against `install.cmem.ai` / `cmem.ai` / `openclaw.ai`, RDAP for domain registration dates, DexScreener and GeckoTerminal for the token. All permalinks pinned to that commit SHA. Happy to share the scripts I used on the session transcripts.*
