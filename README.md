# claude-mem notes
A careful read-through of [`github.com/thedotmack/claude-mem`](https://github.com/thedotmack/claude-mem) — a Claude Code plugin with ~66k GitHub stars that pitches itself as persistent memory for Claude Code, and whose actual product surface looked meaningfully broader than I expected.

All observations are pinned to commit **`8ace1d9c84e5ce455356cf852c370ea625e3b1d1`** (v12.3.9 + 2 commits, tip of `main` when I read it on 2026-04-23).

## Bottom line

I'm not accusing the author of anything malicious. This write-up is about **software quality and a pattern of project behaviour that doesn't sit right with me** — not about intent. My goal is to make enough visible that readers can form their own view from the evidence below.

I do not have special domain knowledge here; I'm a concerned user who read the code after my Claude Code runs kept stalling. I uninstalled it after this, and this repo is my attempt to show what I found and why it concerned me.

1. **The plugin rewrites broad `Read` tool calls to `limit: 1`** and injects a "timeline" string as trusted context on unconstrained reads. [`src/cli/handlers/file-context.ts` L282-291](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L282-L291). This explained the stalls I was seeing in autonomous multi-step work: the agent was often getting one line plus a summary instead of the file it had asked for.

2. **It runs an unauthenticated HTTP server on `127.0.0.1:37777`** with a `POST /api/import` endpoint that accepts arbitrary "observations" with no provenance check. Those observations can surface to Claude as prior-work context on the next file read. My concern is that any local process running as the same user can feed strings into the agent's context window. Handler verified at [`src/services/worker/http/routes/DataRoutes.ts:344`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/DataRoutes.ts#L344); the only validation is `Array.isArray()`.

3. **Software quality and issue-tracker governance are what gave me pause.** The repository had GitHub's contributor-only interaction-limit active for approximately six days (2026-04-16 -> 2026-04-21), which appears to have prevented external users from filing issues during that window. This is supported by a [Reddit comment](https://www.reddit.com/r/ClaudeCode/comments/1scz5kk/comment/ohe4en3/) posted 2026-04-21 with a screenshot of GitHub's exact error message, and by the issue-creation data showing external authors = 0 while contributor/owner activity continued. Details at [`evidence/software-quality/interaction-limit-apr-2026.md`](evidence/software-quality/interaction-limit-apr-2026.md). Separately: five independent community bug reports were filed on 2026-04-23 against the current three point-releases, covering data-model pollution, install/uninstall hygiene, process lifecycle, ~97% prompt-volume waste, and platform failures that were silent to the user. 121 issues (10.9%) have been closed as "not planned", including two high-volume closure days (55 on 2026-02-08, 40 on 2026-04-10). 104 issues (9.3%) are locked. The repo's own `ANTI-PATTERN-TODO.md` catalogued 301 silent-failure anti-patterns fixed over 8 months. The `.github/workflows/convert-feature-requests.yml` workflow auto-moves feature requests out of the issue tracker into discussions. Details in [`evidence/software-quality/`](evidence/software-quality/).

4. **The project's scope has grown well beyond "memory for Claude Code".** Telegram notifier in the main source, an "OpenClaw Gateway" companion that streams observations to Telegram/Discord/Signal/WhatsApp/Slack/Line, a separately-licensed email-investigation tool (`ragtime`) whose default corpus path is `datasets/epstein-mode/`, `law-study` and `email-investigation` modes, and a Solana memecoin (`$CMEM`) promoted in the English README only — 0 of 32 translated READMEs mention it. `openclaw.ai` publicly markets as "Personal AI Assistant." I'm presenting these as observations — how to interpret them is up to you.

5. **The star count has a measurable amplification layer (~15–20% of 66k).** Full 66,433-stargazer dataset pulled via GraphQL shows throwaway-shape accounts rising from a 3.3% baseline to 13.1% in the 2026-04-13 peak week. That week alone had 14,575 stars (22% of all stars ever) with 0.78% of accounts created within one hour of when they starred. I can't tell you who's doing this or why. ~77% of stars remain from established accounts. Details in [`evidence/stargazers/`](evidence/stargazers/).

## What's in this repo

| file | what it is |
|---|---|
| [`REPORT.md`](REPORT.md) | Detailed technical notes, per-priority observations, confidence ratings, and pinned permalinks. ~65 KB. |
| [`WRITEUP.md`](WRITEUP.md) | Narrative writeup in plain English. ~20 KB. |
| [`evidence/`](evidence/) | Supporting artifacts: SHA-256 sums, source excerpts, domain probes, stargazer data, issue-tracker snapshots, software-quality metrics, rendered charts. |
| [`scripts/`](scripts/) | Reproducible data collection + analysis. `fetch_stars.py` / `analyze_stars.py` regenerate the star-amplification analysis. `fetch_issues.py` / `analyze_issues.py` regenerate the issue-tracker and software-quality analysis. `plot_charts.py` regenerates the six evidence charts (needs `uv`). All work against any public GitHub repo. |

## Methodology

Everything in this repo was produced from:

1. A fresh clone of `github.com/thedotmack/claude-mem` at commit `8ace1d9c`, checked out locally and read.
2. Git log and git blame against that checkout.
3. Live `curl`/`gh api` probes against `install.cmem.ai`, `cmem.ai`, `openclaw.ai`, `publicdata.works`, DexScreener, GeckoTerminal, Cloudflare/Verisign RDAP.
4. Mach-O parsing of the committed 63 MB binary using a Node.js header-walker (no llvm or otool required); the `__BUN.__bun` section was extracted and scanned for URLs and unexpected patterns.
5. GitHub GraphQL v4 full pagination of all 66,433 stargazers with account metadata (no REST-endpoint 40k cap).

All permalinks in the report are pinned to the review SHA. If the repo changes after publication, the evidence still resolves to what was true at the time of writing.

## What I found in this pass

- Mach-O binary's embedded Bun bundle extracted and checked — clean of unexpected outbound domains, hardcoded creds, and date/hostname-gated logic. Also two months stale vs HEAD source, though the normal hook/CLI path appears to run `worker-service.cjs`, not that native binary.
- Live `install.cmem.ai/openclaw.sh` verified byte-identical to the repo's `openclaw/install.sh` (sha256 `78c39b15…`).
- Full stargazer stream paginated via GraphQL (past REST's 40k cap), analyzed for account-quality signals — shows measurable amplification.
- `$CMEM` tracked on-chain to a pump.fun bonding-curve graduation (2026-01-06 07:59 UTC), followed by `cmem.ai` domain registration (Jan 10) and the README promotion (Jan 13). Three infrastructure actions in seven days.
- `0 of 32` i18n README translations mention `$CMEM`.
- No CI workflow rebuilds the committed Mach-O binary (`.github/workflows/`), and the published npm package excludes it. The npm package does include a separate stale Windows executable under `dist/binaries/`, but the normal CLI path does not appear to invoke it.

## What's not in this repo (and why)

- The full upstream repo clone (216 MB). Reproduce with `git clone github.com/thedotmack/claude-mem && cd claude-mem && git checkout 8ace1d9c`.
- The extracted Mach-O `__BUN.__bun` section (3 MB). It's a derivative of the upstream binary and re-hosting is unhelpful. Its SHA-256 is in `evidence/sha256sums.txt` and the 27 URLs it contains are in `evidence/binary/bun-urls.txt`. Reproduce via `scripts/extract_bun_section.py` (or walk the Mach-O with any LC_SEGMENT_64 parser).
- The live `openclaw.sh` downloaded copy (66 KB). SHA matches the repo copy. Reproduce with `curl -sSL https://install.cmem.ai/openclaw.sh | sha256sum` and compare to the sha256 in `evidence/sha256sums.txt`.

## Disclaimer

This is a one-off read of a single piece of open-source software as published. It is not an accusation of malice or deception. The author, Alex Newman (`@thedotmack`), is a real person with a 14-year GitHub account building in public. These notes describe what I saw in the code, where the project's product surface appears to be heading based on its own commits and stated design principles, and what the observable amplification layer on top of its star count looks like. I am leaving the conclusion open.

## Reproducing the observations

Every major observation has a pinned permalink or a reproducible script:

- **Read-hook rewrite** → open [`src/cli/handlers/file-context.ts#L282-L291`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L282-L291).
- **handleImport unauthenticated** → open [`src/services/worker/http/routes/DataRoutes.ts#L344`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/DataRoutes.ts#L344).
- **openclaw.sh live-vs-repo match** → expected output from `curl -sSL https://install.cmem.ai/openclaw.sh | sha256sum`: `78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4`.
- **Star amplification analysis** → `python scripts/fetch_stars.py` (takes ~30 min; `gh auth login` required) then `python scripts/analyze_stars.py`.
- **Issue-tracker governance analysis** → `python scripts/fetch_issues.py` (takes ~30 s) then `python scripts/analyze_issues.py --mass-close-threshold 20`.
- **Everything else** → cross-references at the bottom of the relevant REPORT.md section.

Both data-fetch scripts work against **any public GitHub repo** — pass `--owner OWNER --repo REPO` to point them somewhere else. The analysis scripts just consume the jsonl output, so you can adapt this methodology to any project you're considering installing.

## Licence

Text and findings: Creative Commons Attribution 4.0 International (CC BY 4.0). Use freely with attribution back to this repo.
Scripts: MIT.
