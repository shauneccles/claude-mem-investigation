# claude-mem review notes — technical report

**Review SHA pin:** `8ace1d9c84e5ce455356cf852c370ea625e3b1d1` (v12.3.9 + 2 commits, HEAD of `main` at time of analysis, 2026-04-23).
**Permalink prefix:** `https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/`
**Repo total commits at pin:** 1,797.
**Author:** Alex Newman (GitHub `thedotmack`, Twitter `@Claude_Memory`, GitHub account since 2011-03-22, 1,381 followers).

---

## 1. Executive summary

1. **The "memory plugin" framing is a real account of the first ~6 weeks, but the last ~60 days look broader to me.** The root commit (2025-09-06) had no `package.json`, no Express server, no HTTP API, no modes, no `ragtime`, and no token — it is a minimal memory plugin with session-start/session-end/pre-compact hooks. The HTTP worker on `localhost:37777` lands week 6 (2025-10-17/19). Modes + `ragtime` + `email-investigation` appear week 16 (2025-12-22/23). **The Read-hook rewrite** (`src/cli/handlers/file-context.ts`) is only **2026-03-18** — five weeks before pin. **ANTHROPIC_BASE_URL override** is **2026-04-09**. **TelegramNotifier** is **2026-04-22 — the day before this review pin.** The project *did* start as a memory plugin; it *has* accumulated a full observation-and-notification pipeline, and the broader capabilities are recent and still moving.

2. **`$CMEM` is a pump.fun-style memecoin launch that appears closely timed with the repo's distribution.** The token graduated its bonding curve (100% completion → Meteora LP) on **2026-01-06 07:59 UTC**. `cmem.ai` was registered four days later (**2026-01-10**). The `$CMEM` README section was added **2026-01-13 21:23 UTC**. At review time (**2026-04-24 UTC**), the main pool FDV was about **$53k** (below the ~$69k graduation threshold — the token had lost value since graduation) with about **$16.9k** liquidity. The `cmem.ai` homepage is a token marketing page linking to Jupiter/Raydium/Dexscreener swaps — not a product landing page. The "3rd-party created, officially embraced" framing is not falsified by available evidence, but the **timing of LP creation, domain purchase, and README promotion** (three distinct infrastructure actions across seven days) does not read to me like passive adoption.

3. **The committed Mach-O binary is clean and stale, but the normal runtime path appears to use `worker-service.cjs`.** The 63 MB arm64 binary (`dfd8597…`) was compiled **2026-02-23** and pre-dates the Read-hook rewrite, ANTHROPIC_BASE_URL override, and TelegramNotifier. Its `__BUN.__bun` section (3.1 MB) extracts cleanly and contains no unexpected outbound domains, no hardcoded credentials, no unexpected endpoints. The 1.98 MB `worker-service.cjs` (`f641bd1…`) at HEAD **does** contain all three of those features plus `api.telegram.org/bot$`. Follow-up release-path review shows the hooks and CLI alias call `worker-service.cjs`, and npm excludes `plugin/scripts/claude-mem`, so the stale Mach-O is better treated as a stale repo artifact rather than evidence that macOS users normally get a different runtime.

4. **Zero secrets redaction in the observation pipeline, and the architecture explicitly contemplates exposing `localhost:37777` beyond the local machine.** No `redact`/`scrub`/secret-pattern code exists in `src/`. The top-level `CLAUDE.md` "Pro Features Architecture" section states as design principles: *"All worker API endpoints on localhost:37777 remain fully open and accessible"* and *"Pro integration points are minimal: settings for license keys, tunnel provisioning logic."* Combined with the `POST /api/import` unauthenticated ingest endpoint on the worker and the absent redaction, this is a pipeline capable of carrying any plaintext credential Claude happens to read into the local DB — and a Pro tier will tunnel that DB off-box.

5. **The live installer matches the repo exactly; no unadvertised install.cmem.ai endpoints exist; the binary has no telemetry/beacon.** `install.cmem.ai/openclaw.sh` is byte-identical to `openclaw/install.sh` (sha256 `78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4`). `install.cmem.ai/install.sh` is a 703-byte redirect shim deprecating curl-pipe-bash in favor of `npx claude-mem install`. All of `beacon`, `telemetry`, `update.sh`, `uninstall.sh`, `api/health`, `metrics` return 404. The infrastructure the project advertises is the infrastructure it operates; there is no evidence of out-of-band deployment or hidden endpoints.

6. **The full stargazer graph shows a measurable amplification layer on top of real popularity.** A GraphQL v4 fetch captured all **66,433** stargazer records at the review pin, resolving the earlier REST pagination cap. The pre-December-2025 baseline was **3.3%** throwaway-shaped accounts; the April 13 calendar week reached **13.1%** across **13,546** stars, the largest Monday-Sunday week in the repo's history. The base remains real — 77% of stargazers have accounts older than two years — but the full graph shows an additive amplification layer.

7. **Software quality and issue-tracker governance are part of the concern.** The repo had GitHub's contributor-only interaction-limit active for approximately six days in April 2026, with external issue creation dropping to zero while contributor/owner activity continued. Within 24 hours of the limit lifting, five independent community bug reports arrived against v12.1.2 -> v12.3.9. Across the issue corpus, 121 issues (10.9%) were closed as "not planned" and 104 (9.3%) were locked. This is separate from intent; it describes the maintenance pressure around a tool that sits inside developer agent loops.

---

## 2. Per-priority findings

### Priority 1 — Timeline archaeology

**Commands run** (ran via `git log`, `git show`, `git rev-list`, etc. on the cloned repo):

- `git log --reverse --format='%h %ai %s'` to enumerate oldest commits.
- `git show $(git rev-list --max-parents=0 HEAD):{README.md,package.json,install.sh}` to reconstruct day-1 state.
- `git log --follow --diff-filter=A` per path of interest to date introduction.
- `git log --all -p -S '$CMEM' -- README.md`, likewise for `ANTHROPIC_BASE_URL`, `37777`, `epstein-mode`, `Solana`.
- `git shortlog -sne --all` to count commits per author.

**What I found**

- **Repo day 1: 2025-09-06.** Root commit `598369e8` is titled *"Initial release v3.3.8"* (unusual starting version — suggests prior private history). Files present: `.gitignore`, `LICENSE`, `README.md`, `RELEASE.md`, `docs/`, `hooks/` (only `pre-compact.js`, `session-end.js`, `session-start.js`, two shared helpers), `install.sh`. **No `package.json`**, no `src/`, no `plugin/`, no Express server. `install.sh` is a 56-line shell script that downloads a platform-specific binary from GitHub releases. The day-1 README describes a memory plugin with install-via-npm and hook-based compression — and nothing else. `package.json` first appears at `aae7de8e` on **2025-09-09** (three days later).
- **First 32 commits (Sep 6 → Oct 6)** are almost entirely version bumps (3.5.x, 3.6.x, 3.7.x, 3.9.x). Normal release cadence.
- **Worker service introduced 2025-10-17** (`37285494`, *"feat: Implement Worker Service with session management and SDK integration"*). This is the first appearance of `src/services/worker-service.ts` and `plugin/scripts/worker-service.cjs`.
- **Port 37777 first referenced 2025-10-19** (`7ff611fe`).
- **HTTP middleware + route architecture 2025-12-05** (`3aaee6f1`, *"refactor: Organize worker into clean route-based HTTP architecture"*) — `src/services/worker/http/middleware.ts` first appearance.
- **Mode system + email-investigation + ragtime 2025-12-22/23** (`3ea0b60b` — *"Mode system with inheritance and multilingual support"*, then `e32f2d7b` adding the `ragtime` script for processing markdown files through a Claude agent).
- **`epstein-mode` path references** first at `8bca13a9` 2025-12-23 and expanded at `2eaef1f5` 2026-01-30 (*"feat: implement ragtime email investigation with self-iteration and cleanup"*).
- **$CMEM README section 2026-01-13** (`8990a788` *"Update README with $CMEM token details"*, followed by four more commits the same evening).
- **EnvManager centralization 2026-01-17** (`006ff401` *"fix: use centralized credentials from ~/.claude-mem/.env to prevent API key hijacking"*). This is framed as a *defensive* change — interesting given what came later.
- **OpenClaw-related scaffold 2026-02-07** (`89333434`). The claude-mem repo adds OpenClaw plugin/installer code; a separate `Jarvis <jarvis@openclaw.ai>` committer identity appears in Apr 2026. This shows OpenClaw-related integration in the repo. OpenClaw itself is separate.
- **Mach-O binary 2026-02-23** (`c2c3e306` *"chore: bump version to 10.3.2"*) — the committed macOS binary is a snapshot of code state at this date.
- **law-study mode 2026-03-08** (`97ea9e45` *"feat: add law-study mode for law students"*).
- **Read-hook timeline injection 2026-03-18** (`fb9d917f` *"feat: inject file observation timeline on PreToolUse Read hook"*, by Alex Newman with Claude Opus 4.6 as co-author). 430 insertions, 194 deletions across 9 files, including +142 lines in the new `src/cli/handlers/file-context.ts`.
- **ANTHROPIC_BASE_URL override 2026-04-09** (`07be61cf`, author `WuTao <taobaorun@gmail.com>`, PR #1627, commit messages tagged *"Generated with AI — Co-Authored-By: AI Partner"*). Not author-originated; community PR.
- **TelegramNotifier 2026-04-22** (`f2d361b9` *"feat: security observation types + Telegram notifier"*) — 23 hours before this review pin.
- **Renames:** no repo-level renames; only file-level moves.
- **Top authors:** `Alex Newman <thedotmack@gmail.com>` 2394 commits; `copilot-swe-agent[bot]` 188; `Ousama Ben Younes` 20; `Claude <noreply@anthropic.com>` 18; `Copilot` 18; `Rod Boev` 15; `claude[bot]` 12. Additional notable committers: `Claude <rajiv@publicdata.works>` (3 commits 2026-01-21 — an unusual co-author-style identity using someone else's domain), `Jarvis <jarvis@openclaw.ai>` (3 commits 2026-04-02). **284 commits have the prefix `MAESTRO:`** — an AI automation signature.

**Interpretation.** Pattern = **organic memory plugin → accretion → acceleration**. Days 1–40 are a thin plugin. Day 41–120 add the worker + HTTP API + modes. Days 120+ add the broader observation features (ragtime/email-investigation, then file-context Read rewrite, then env override, then Telegram). The features most useful for an observation-pipeline product are the ones most recently added; the features most useful to a memory plugin were added first. The project *could* have been redesigned around an observation pipeline from the start and been gradually framed toward it, but the git record I read does not show that. It supports the simpler story: the author started with a memory plugin, found it worked, and has been building out the observation/intelligence layer on top of distribution they already had. That is less alarming than "it was always this," but still more scope than I expected from a memory plugin — especially because the Read-rewrite with timeline injection was added five weeks ago and ships today.

- README.md pinned permalink: [README.md#L2](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/README.md)
- file-context.ts (Read rewrite): [src/cli/handlers/file-context.ts#L282-L291](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L282-L291)
- EnvManager override: [src/shared/EnvManager.ts](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/shared/EnvManager.ts)
- CLAUDE.md Pro Features Architecture: [CLAUDE.md](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/CLAUDE.md)

**Confidence: high.** Commit SHAs and dates are deterministic facts from the git object store.

---

### Priority 2 — Mach-O binary disassembly

**Commands run**

- `file plugin/scripts/claude-mem` → `Mach-O 64-bit arm64 executable, flags:<NOUNDEFS|DYLDLINK|TWOLEVEL|BINDS_TO_WEAK|PIE|HAS_TLV_DESCRIPTORS>`.
- `sha256sum` → `dfd8597261d2c57f76e483783fbd20a2aa97e657b2a6117a9327d830f987f2a0`.
- Custom Node.js parser reading Mach-O 64-bit headers + LC_SEGMENT_64 load commands to produce the segment/section table below.
- Slice the `__BUN.__bun` section out and hash it: `fd189159fc07898ec428524721702ec2712dcb0c92471fd0f09c1c69aa367829` (3,098,213 bytes).
- Printable-run scan (≥8 ASCII chars) → extract URLs and keyword contexts.

(`llvm-objdump` / `otool` / `strings` were not available on this Windows review host; the Node.js parser was written to substitute for them.)

**Binary layout** (63,412,576 bytes total):

| segment | file offset | file size | sections |
|---|---|---|---|
| `__PAGEZERO` | 0 | 0 | 0 |
| `__TEXT` | 0 | 58,195,968 | 8 (incl. `__text` 49 MB JSC, `__cstring` 3.3 MB, `__const` 5.2 MB) |
| `__DATA_CONST` | 58,195,968 | 1,196,032 | 2 |
| `__DATA` | 59,392,000 | 180,224 | 8 |
| `__DATA_DIRTY` | 59,572,224 | 16,384 | 1 |
| **`__BUN`** | **59,588,608** | **3,112,960** | **1 (`__BUN.__bun` — 3,098,213 bytes)** |
| `__LINKEDIT` | 62,701,568 | 711,008 | 0 |

The `__BUN.__bun` section begins with a Bun-standard header `]F/\0\0\0\0\0\0/$bunfs/root/claude-mem\0// @bun\n` and then `var __create = Object.create;…` — i.e. the JS bundle in plaintext, using Bun's virtual filesystem (`/$bunfs/root/claude-mem`) as the module root.

**External URLs in the extracted bundle** (27 unique, de-duplicated, filtered from 63,850 printable runs):

- Localhost/worker: `http://127.0.0.1:`, `http://localhost:`, `http://localhost:37777/api/{context/recent,context/timeline,search/by-type,search/observations}` (four example URLs used in documentation strings).
- Approved external APIs: `https://generativelanguage.googleapis.com/v1/models`, `https://openrouter.ai/api/v1/chat/completions`.
- Project surface: `https://github.com/thedotmack/claude-mem`, `https://docs.claude-mem.ai/cursor`, `https://discord.gg/J4wttp9vDu`.
- JSON-schema drafts, Connect/Express middleware help URLs, `feross.org/opensource`, `git.io/debug_fd`, `raw.githubusercontent.com/ajv-validator/ajv/master/lib/refs/data.json`, `github.com/ashtuchkin/iconv-lite/wiki/...` — **all upstream npm package license/docs/schema URLs, not runtime destinations.**
- One flagged-then-cleared URL: `https://dub.sh/security-redirect` appears in an Express warning message (`res.location` best-practice link). Benign, upstream Express.

The binary does **not** contain:
- `ANTHROPIC_BASE_URL` string (feature post-dates the binary).
- `api.telegram.org` (feature post-dates the binary).
- Any unexpected-outbound-domain patterns (`ngrok`, `pastebin`, `webhook.site`, etc.).
- `crypto.subtle`, `createCipheriv`, `createDecipheriv`, `createSign`, `createVerify` in non-Express/non-Ajv contexts (only `createSignalHandler` in ProcessManager, which is OS signal handling — unrelated to cryptographic signing).
- `process.env.USER` / `process.env.USERNAME` / `os.hostname()` comparisons against literals.
- Hardcoded credentials, bearer tokens, or API keys.

The only `eval(` reference is `$EvalError = require_eval()` (an error class). All `new Function(` calls are Ajv's JSON-schema validator compilation. `0.0.0.0` appears twice, both in a validation error message listing it as a valid example (`EM_WORKER_HOST must be a valid IP address (e.g., 127.0.0.1, 0.0.0.0)`); `workerHost` is case-preserved in binary strings but the default in source defaults to `127.0.0.1` (`HealthMonitor.ts:79` hardcodes it, `Server.ts:97` takes it from config which defaults to localhost).

**Interpretation.** The binary does not contain anything that is not also in the TypeScript source. It does contain *less* than the current source, because it was compiled **2026-02-23** — before the Read-hook timeline injection (Mar 18), the ANTHROPIC_BASE_URL override (Apr 9), and the TelegramNotifier (Apr 22). Follow-up release-path review shows no CI rebuild for this Mach-O, but also shows the normal hooks and CLI alias call `worker-service.cjs`, and the published npm package excludes `plugin/scripts/claude-mem`. The practical implication is narrow: the Mach-O is a stale repo artifact and would be stale if executed manually from a checkout, while normal installs appear to use the CJS worker.

- Binary permalink: [plugin/scripts/claude-mem](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/plugin/scripts/claude-mem)
- Binary introduction commit: `c2c3e306` 2026-02-23

**Confidence: high** on what the binary contains and on the release-path finding; see [`evidence/binary/rebuild-policy.md`](evidence/binary/rebuild-policy.md).

---

### Priority 3 — Live installer verification

**Commands run**

- `curl -sI https://install.cmem.ai/openclaw.sh` and `curl -sSL ... -o live-openclaw.sh`; `sha256sum` compare.
- `curl -sI` against 22 candidate paths under `install.cmem.ai`.
- `curl -sI -X {GET,POST,PUT,OPTIONS}` against `claude-mem.com`.
- `nslookup` + RDAP (`https://rdap.verisign.com/com/v1/domain/...`, `https://rdap.identitydigital.services/rdap/domain/...`) for each domain.
- `curl -sSL` against `cmem.ai/`, `claude-mem.com/`, `crab-mem.sh/` for homepage content.

**Key findings**

- **`install.cmem.ai/openclaw.sh`**: live 66,214 bytes, sha256 `78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4`, **byte-identical to `openclaw/install.sh` in the repo**. Vercel-served, `Last-Modified: Wed, 22 Apr 2026 21:51:52 GMT`.
- **`install.cmem.ai/install.sh`** *and* **`install.cmem.ai/`**: 703 bytes, both serve the same deprecation shim — a colored-output script that tells users *"The curl-pipe-bash installer has been replaced. Install claude-mem with a single command: `npx claude-mem install`"*. This is a **defensive change**; the curl|bash attack surface has been intentionally retired.
- **All other paths 404**: `/robots.txt`, `/beacon`, `/beacon.json`, `/telemetry`, `/update.sh`, `/uninstall.sh`, `/api/health`, `/.well-known/security.txt`, `/sitemap.xml`, `/claude-mem.sh`, `/cmem.sh`, `/status`, `/metrics`, `/openclaw.ps1`, `/claude-mem.ps1`, `/bootstrap.sh`, `/config.json`, `/api`, `/index.html`. No hidden plumbing.
- **Domain registration facts** (RDAP):
  - `cmem.ai`: registered **2026-01-10T02:46:21Z**, expires 2028-01-10, Cloudflare registrar, NS `kate.ns.cloudflare.com` + `ivan.ns.cloudflare.com`. **Active.**
  - `claude-mem.ai`: registered **2025-08-31T06:50:40Z** (5 days before repo commit 1), expires 2027-08-31, Cloudflare registrar, same Cloudflare NS as cmem.ai. **This is the project's actual docs/install-CNAME origin.**
  - `claude-mem.com`: registered **2026-04-15** (8 days ago at pin), NameCheap registrar, NS mix of Spaceship + Sedo + Afternic — **parked / parked-for-sale domain, not project-operated.** HTML is `window.onload=function(){window.location.href="/lander"}`. Likely squatter.
- **`cmem.ai` homepage is a token-marketing page**, not a product landing page. Title: `$CMEM — The Currency of the Agentic Economy`. External links include Jupiter swap, Raydium swap, DexScreener, and crucially a **separate author project `crab-mem` (`github.com/thedotmack/crab-mem`, `crab-mem.sh`, `moltbook.com/u/Crab-Mem`)** and Twitter `@Claude_Memory`.

**Interpretation.** The installer the repo advertises is the installer that serves. There is no out-of-band deployment, no secondary payload, no telemetry beacon at the install host. The domain layout is consistent with an individual operator who bought `claude-mem.ai` pre-launch (Aug 31) and `cmem.ai` a week before launching the token (Jan 10), both through Cloudflare; `claude-mem.com` is a squatter. This priority is **cleared**: the distribution plumbing is as advertised.

**Confidence: high.**

---

### Priority 4 — Unminify and diff `worker-service.cjs`

**Commands run**

- Size/type/hash: 1,984,234 bytes, ASCII with very long lines (35,957 chars/line), sha256 `f641bd11e7ef5184877592a1d5dc704064c79d5f62abc06019d1c1328f15080b`.
- Node.js regex scan over the raw text for URL literals and 35 patterns of concern.
- Cross-reference against `src/` TypeScript sources (specifically `EnvManager.ts`, `file-context.ts`, `Server.ts`, `HealthMonitor.ts`, `TelegramNotifier.ts`).

**External URLs in the bundle (31 unique):** superset of the Mach-O binary's set; adds:

- `https://api.telegram.org/bot$` (TelegramNotifier — added 2026-04-22).
- `https://bun.sh` (runtime installer redirect).
- `https://docs.astral.sh/uv/getting-started/installation/` (uv installer help URL).
- `https://docs.claude-mem.ai/usage/gemini-provider` (docs).

Nothing that isn't either (a) an approved API, (b) a docs URL, (c) an npm-upstream license/help URL, or (d) the installer for the SessionStart-auto-installed runtimes.

**Suspicious pattern counts** (hand-selected interpretation):

| pattern | count | interpretation |
|---|---|---|
| `ANTHROPIC_BASE_URL` | 6 | present (matches source EnvManager) |
| `app.post("/api/import"` | 1 | matches `src/services/worker/http/routes/DataRoutes.ts`, unauthenticated — confirms the local API concern |
| `new Function(` | 3 | Ajv validator; benign |
| `:37777` | 4 | default worker port |
| `127.0.0.1` | 11 | worker binding |
| `0.0.0.0` | 2 | validation error message example only |
| `telegram` | 14 | TelegramNotifier present |
| `additionalContext` | 7 | Read-hook timeline injection present |
| `PreToolUse` | 1 | hook wiring |
| `limit: 1` | 3 | Chroma health checks + session-store queries (**not** the Read-rewrite; the Read-rewrite sets `updatedInput.limit = 1` via `file-context.ts`, which is compiled into the bundle but expressed in different minified form — the TypeScript source is the clearer artifact to cite) |
| `eval(` | 1 | `$EvalError = require_eval()`, benign |
| `dub.sh/security-redirect` | 1 | Express upstream; benign |
| `process.env.USER/USERNAME` | 0 | no user-gating |
| `os.hostname()` | 0 | no hostname-gating |
| `createCipheriv` / `crypto.subtle` | 0 | no cryptographic operations |
| `ngrok` / `pastebin` / `webhook.site` | 0 | no unexpected outbound domains |

**Read-hook injection site in source** (line-accurate):

```
src/cli/handlers/file-context.ts:282:    if (userLimit !== undefined) updatedInput.limit = userLimit;
src/cli/handlers/file-context.ts:284:    updatedInput.limit = 1;
src/cli/handlers/file-context.ts:289:      hookEventName: 'PreToolUse',
src/cli/handlers/file-context.ts:290:      additionalContext: timeline,
src/cli/handlers/file-context.ts:291:      permissionDecision: 'allow',
```

The source-level behavior is this: the hook respects a user-supplied `limit` if present, otherwise defaults it to 1 and injects `timeline` as `additionalContext` with `permissionDecision: 'allow'`. Claude's subsequent read of the injected timeline is indistinguishable — from the model's view — from file content it just read. My concern is that anything reaching the observation database can become context Claude later treats as prior work.

**Interpretation.** `worker-service.cjs` at HEAD is a faithful bundle of the current TypeScript. It contains the concerning features already described — no more, no less. I did not find novel surface area hidden in the bundle. The `handleImport` endpoint at `app.post("/api/import", this.handleImport.bind(this))` is the ingest path; it is unauthenticated, and the observation data it accepts is what the Read-hook injects into Claude's context as "timeline." The loop closes: write anything to `POST /api/import` → Claude reads a file in that project → hook injects your payload as `additionalContext`. That is a context-injection path I would not want inside my own agent loop.

- `/api/import` handler permalink: [src/services/worker/http/routes/DataRoutes.ts](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/DataRoutes.ts)
- Read-hook site: [src/cli/handlers/file-context.ts#L282-L291](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L282-L291)

**Confidence: high.**

---

### Priority 5 — Author's public repos and adjacent integrations

**Commands run**

- `gh repo list thedotmack --limit 100 --json name,description,createdAt,pushedAt,stargazerCount,forkCount,isFork,isArchived`.
- `gh api users/thedotmack` (profile).
- `gh api users/thedotmack/orgs` (empty).
- `gh api search/code?q=user:thedotmack+...` (refused by GitHub — repeatedly rate-limited/errored).

**Profile.** GitHub `thedotmack` (Alex Newman), account created **2011-03-22**, Twitter `@Claude_Memory`, 1,381 followers, 113 following, 98 public repos, 14 gists. No org affiliation, no email, no location, no bio, no blog. The Twitter handle is *project-branded* not *personal-branded*.

**Top repos by stars (non-fork)** — 53 non-fork repos total; only one is over 100 stars:

```
 66,433  2025-08-31  claude-mem                (the subject; stargazer dataset at review pin)
     43  2025-10-01  mcp-client-cli            Command-line interface for any MCP server
     19  2026-02-06  aims                      ⚡ AI Messenger Service — watch AI bots communicate in real time
     18  2026-02-01  crab-mem  (ARCHIVED)      🦀 Continuous cognition for OpenClaw agents
     12  2026-02-23  sequential-thinking-skill Claude Code skill replicating Sequential Thinking MCP
     12  2025-09-16  claude-mem-docs           docs.claude-mem.ai
      9  2025-09-08  claude-commands           Custom Claude Code commands
      8  2026-02-02  crabspace-app             🦀 CrabSpace — MySpace for AI Agents
      8  2025-11-27  rad-mem                   Domain-flexible temporal intelligence
      7  2026-02-24  mackeroni-skills          Specialized agent skills for Claude Code and Gemini CLI
      6  2025-10-14  HIPAApotamus              (no description public)
      5  2026-04-11  redplanet-cleaning-station
      5  2026-02-27  notch                     Schema-less CLI state machine for LLM agents
```

**Repos created in 2026** (13 of the 53):

```
2026-02-01  crab-mem                ARCHIVED  Continuous cognition for OpenClaw agents
2026-02-01  cmem-ai                           (empty)
2026-02-02  crabspace-skill                   CrabSpace skill — MySpace-style social network for AI
2026-02-02  crabspace-app                     🦀 CrabSpace — MySpace for AI Agents
2026-02-06  aims                              AI Messenger Service
2026-02-19  antipattern-czar                  Error-handling anti-pattern detector for TypeScript
2026-02-23  sequential-thinking-skill         Sequential-Thinking MCP replica
2026-02-24  aims-v2                           AIMS v2 — Live workspace sync dashboard for OpenClaw
2026-02-24  mackeroni-skills                  Skills collection
2026-02-27  notch                             CLI state machine for LLM agents
2026-03-03  optimal-openclaw                  (empty)
2026-04-10  MemeDeck                          Next.js 15 reference implementation of a card-game-style Solana memecoin trading [...]
2026-04-11  redplanet-cleaning-station        (empty)
2026-04-12  MovieBot                          (truncated)
```

**Pattern observations.**

1. There is a recognizable **ecosystem** around the author's LLM/agent tooling: `claude-mem`, `claude-mem-docs`, `claude-commands`, `mackeroni-skills`, `sequential-thinking-skill`, `mcp-client-cli`, `rad-mem` (*"domain-flexible temporal intelligence — apply to any document corpus"* — this framing is notable: it's the same observation pipeline with a generic-corpus label), `crab-mem` (*"continuous cognition for OpenClaw agents"* — ties an author-owned memory repo to OpenClaw), `crabspace-app`/`crabspace-skill`, `aims`/`aims-v2` (*"AI Messenger Service — watch AI bots communicate"* and *"live workspace sync dashboard for OpenClaw AI agents"*).
2. **OpenClaw is a separate adjacent product surface; this evidence is about integrations.** `openclaw.ai` and `docs.openclaw.ai` are live, `openclaw.dev` is referenced in source but dead, and the claude-mem repo contains OpenClaw plugin/installer code. Several author-owned repos describe themselves as for OpenClaw agents. The finding is that the author built OpenClaw-related adapters/integrations.
3. **`MemeDeck` (2026-04-10): *"Next.js 15 reference implementation of a card-game-style Solana memecoin trading…"*** — the author has a second, separate interest in Solana memecoin mechanics, created two weeks before this review pin.
4. No memecoin-launch-then-abandon pattern in the author's prior work is visible; `$CMEM` appears to be the first.
5. Commit-activity signature: ~63% of commits are Alex Newman personally, ~10% are Copilot, another ~16% is `MAESTRO:` (an AI tool, probably an automated PR triager) — so ~26% of commits are explicitly AI-tooling-authored. That's high but not atypical for 2026.

**Interpretation.** This is a solo operator running a broad LLM-adjacent toolchain. The repo set does **not** show a prior history of "build product → launch token → abandon." It shows that the author has a demonstrated interest in both the agent-memory space *and* the Solana memecoin space, and that several author-owned repos integrate with or reference OpenClaw. The narrower story is: claude-mem started as the adoption vehicle, `$CMEM` is the monetization experiment, and the author's public repos include observation/messaging tools that can sit alongside OpenClaw.

**Confidence: medium.** The raw `gh` data is high-confidence; the operator-intent narrative is inferential.

---

### Priority 6 — `$CMEM` on-chain

**Commands run**

- `curl` to `https://api.mainnet-beta.solana.com`, `https://solana-rpc.publicnode.com`, `https://rpc.ankr.com/solana` for `getTokenSupply`, `getTokenLargestAccounts`, `getSignaturesForAddress`, `getAccountInfo`, `getTransaction`.
- Solscan `token/meta` public and pro endpoints.
- `https://api.dexscreener.com/latest/dex/tokens/${mint}`.
- `https://api.geckoterminal.com/api/v2/networks/solana/tokens/${mint}` and `.../pools`.
- `https://public-api.birdeye.so/defi/token_overview` (requires key — denied).
- Solscan web scrape.

**What the public endpoints returned.**

- Public Solana RPCs: all three refused — `publicnode` returned `-32700 Parse error`, `mainnet-beta` returned `503 Service unavailable`, `ankr` requires a key. The oldest-signature walk / deployer-wallet trace is **not possible from this environment without a paid RPC key or a Helius/QuickNode key**.
- **GeckoTerminal** (authoritative): token name **"Claude Memory"**, symbol **CMEM**, decimals 9, total supply **998,477,515.21** tokens (~1B — standard memecoin supply), CoinGecko ID `claude-memory`. `launchpad_details`: **`graduation_percentage: 100.0, completed: true, completed_at: "2026-01-06T07:59:49.000Z"`**, `migrated_destination_pool_address: 6MzFAkWnac6GSK1EdFX93dZeukGfzrFq4UHWarhGSQyd`. This is a **pump.fun-style bonding-curve graduation** — the token launched on a launchpad bonding curve (pump.fun or similar), hit the graduation threshold (~$69k market cap), and migrated liquidity to Meteora.
- **Five Meteora pools** exist for this token, created over a 10-day window:

Market snapshot captured **2026-04-24 UTC**; these values are volatile.

| pool | created (UTC) | FDV USD | liquidity USD | price |
|---|---|---|---|---|
| `6MzFAkWn…GSQyd` (main) | 2026-01-06 07:59:49 | 53,440 | 16,855 | $0.0000535 |
| `DUNUS2Wk…jFbj` | 2026-01-11 10:41:05 | 178,445 | 2,099 | $0.000179 |
| `GK8bG8FY…cGfKX` | 2026-01-12 04:14:00 | 170,442 | 1,884 | $0.000171 |
| `FYbqC9f…iJ39j` | 2026-01-14 11:01:05 | 1,482,731 | 2,869 | $0.00148 |
| `GT1PcoMT…B1aSx` | 2026-01-16 08:21:09 | 3,092,404 | 10,800 | $0.00309 |

- **DexScreener** (corroborating, captured 2026-04-24 UTC): 1 Meteora pair visible, FDV $53,565, liq $16,916, price $0.00005364.
- **Solscan public endpoint** returned `{"error_message":"Token is missing or invalid"}` for the pro-api endpoint (needs a key for that token); the web page yielded 5 addresses but no identified deployer/mint-authority metadata in the initial HTML (SPA — needs JS execution to populate).

**Timeline of coordinated infrastructure actions (reconstruction):**

| UTC | event |
|---|---|
| pre-2026-01-06 | Token deployed on pump.fun-style bonding curve (exact date not determinable without RPC) |
| 2026-01-06 07:59:49 | Bonding curve graduates; main Meteora LP (`6MzFAk…`) is created |
| 2026-01-10 02:46:21 | `cmem.ai` domain registered at Cloudflare |
| 2026-01-11–16 | Four additional Meteora LPs spun up at wildly different prices |
| 2026-01-13 02:23:09 (21:23 ET) | `$CMEM` section added to `README.md` (commit `8990a788`) |

**Interpretation.** The "3rd-party created without our prior consent, officially embraced" framing is **not falsified** by any evidence I could obtain without RPC access, but the **timing does not read to me like passive embrace.** Between the graduation (Jan 6) and the README promotion (Jan 13), someone registered `cmem.ai` (Jan 10) and built out a token marketing site at that domain. The `cmem.ai` site is hosted on the same Cloudflare nameservers as `claude-mem.ai` — the project's pre-existing docs domain. That is the kind of infrastructure overlap I would expect from the same operator, though it does not establish identity by itself. Either the author moved quickly to formalize a community-launched token, or the "3rd party" is close enough to the operator that I cannot separate them from the public evidence alone. At review time, the main-pool market cap (~$53k) was **below the graduation threshold**, i.e. the token had lost value post-graduation and the LPs had a combined <$35k of liquidity — not a large-scale monetization outcome as captured.

**What would close this priority:** a working Solana RPC (paid tier) to run `getSignaturesForAddress` back to the deploy TX, identify the deployer wallet, and trace its SOL funding source. If the deployer address can be correlated with a wallet known to be `thedotmack`'s (e.g. via a wallet-address commit in any of the author's repos, or a tweet), the "3rd party" framing would need to be revised.

**Confidence: medium.** Timing and liquidity facts are high-confidence. Deployer identity and pre-graduation activity are **not determined**.

---

### Priority 7 — Star curve

**Commands run**

- `python scripts/fetch_stars.py` — paginated GitHub GraphQL v4's `repository.stargazers` connection with `orderBy: {field: STARRED_AT, direction: ASC}`.
- `python scripts/analyze_stars.py` — regenerated the per-day CSV, weekly rollup, account-age buckets, and chart inputs.

**What changed from the initial REST pass.** GitHub's REST `/stargazers` endpoint capped out at page 400 (40,000 results), so the first pass only covered the oldest slice of the graph. The GraphQL fetch resolves that limitation: it captured all **66,433** stargazer records at the review pin, from `vlasky @ 2025-09-09T06:44:10Z` through `ajankuv @ 2026-04-23T23:33:17Z`.

**Full-corpus findings.**

- 77% of stargazers have accounts older than two years. The repo's base popularity is real.
- Pre-December-2025 baseline: **3.3%** throwaway-shaped accounts, **0%** accounts created less than one day before starring.
- Full corpus: **9.3%** throwaway-shaped accounts, **1.1%** accounts created less than one day before starring.
- April 13 calendar week: **13,546** stars, **13.1%** throwaway-shaped accounts, **1.2%** accounts created less than one day before starring, and **0.78%** created within one hour of starring.
- The strongest April cohort includes repeated dictionary-plus-suffix account names, mostly 0 followers and 0-1 repos, created hours before starring.

**Interpretation.** The full graph shows measurable star-count amplification that rises materially over time and peaks in the April 13 calendar week. That does not mean the repo's popularity is artificial; it means the advertised star count appears to include an additive amplification layer on top of a large organic base.

**Confidence: high.** The GraphQL dataset covers the full stargazer connection at the review pin and is reproducible from the scripts in this repo. See §8 and [`evidence/stargazers/`](evidence/stargazers/) for the detailed tables and artifacts.

---

## 3. Unanticipated findings

**UF-1 — OpenCode (Goose) MCP config reach.** `src/services/integrations/OpenCodeInstaller.ts:180` shows the plugin fetches `http://127.0.0.1:${workerPort}/api/readiness` during installation, and `McpIntegrations.ts:274` (pulled in the review) writes/merges MCP config into `~/.config/goose/config.yaml`. The plugin installs itself as an MCP server for **other agents besides Claude Code** (Goose is a separate agentic tool). The reach of the plugin is greater than the repo name implies.

**UF-2 — Windows installer uses `irm | iex` pattern.** `src/utils/bun-path.ts:66-67` and `plugin/scripts/smart-install.js:222` issue `powershell -c "irm bun.sh/install.ps1 | iex"` as the Bun-install command on Windows. The earlier curl-pipe-bash concern has a Windows equivalent. On Linux, `plugin/scripts/smart-install.js:229` uses `curl -fsSL https://bun.sh/install | bash`. Both auto-execute on SessionStart if Bun isn't present.

**UF-3 — HealthMonitor hard-codes 127.0.0.1 but Server takes host from config.** `src/services/infrastructure/HealthMonitor.ts:79` has `server.listen(port, '127.0.0.1')` (fixed). `src/services/server/Server.ts:97` has `this.app.listen(port, host, ...)` with `host` from config. The default of `host` in config is `127.0.0.1`, but it is user-settable — meaning a user can bind the worker to `0.0.0.0` by setting `EM_WORKER_HOST`. This by itself is not a bug, but combined with the "tunnel provisioning logic" design principle, it is the mechanism by which the Pro tier can expose the observation DB remotely. The validation error string that was the source of both `0.0.0.0` hits in the binary reads: *"EM_WORKER_HOST must be a valid IP address (e.g., 127.0.0.1, 0.0.0.0)"* — so `0.0.0.0` is accepted as a valid configuration.

**UF-4 — Co-author identity `Claude <rajiv@publicdata.works>`.** Three commits on 2026-01-21 are attributed to this address (`rajiv@publicdata.works`). The `publicdata.works` domain is unrelated to the project. This is an AI-authoring attribution, but using someone else's domain as the email — unusual. Probably a Rajiv Sinclair contributed code via an AI-assisted workflow and used the `Claude <rajiv@publicdata.works>` convention for git co-author attribution. Not diagnostic of anything malicious; worth noting because it deviates from the project's otherwise-uniform `Claude <noreply@anthropic.com>` co-author format.

**UF-5 — `MAESTRO:` commit prefix (284 commits).** An internal AI automation the author runs against the repo. Signals that a significant fraction of the codebase is not hand-written by Alex Newman — it is generated by an LLM tool under his supervision. This is not hidden (commits are clearly marked), but worth noting for any code-review interpretation of "the author wrote this."

**UF-6 — Binary files review** (for completeness): the only files over 500 KB are the Mach-O binary (63 MB), the marketing GIF `docs/public/cm-preview.gif` (2.16 MB), `worker-service.cjs` (1.98 MB), and two copies of the Monaspace-Radon variable-width font at 563 KB. No hidden blobs.

**UF-7 — No cryptographic operations in the product code.** Zero hits for `crypto.subtle`, `createCipheriv`, `createDecipheriv`, `createSign`, `createVerify`, `createHmac` in `src/`. The `createSignalHandler` in `ProcessManager.ts` is OS signals, not crypto. The observation DB is plain SQLite with no encryption, and the HTTP API has no HMAC/JWT — confirming the "no auth on localhost:37777" concern from a different angle (there is no crypto primitive available in the codebase to enforce auth even if someone wanted to bolt it on).

**UF-8 — `crab-mem` is explicitly labeled as "for OpenClaw agents."** That is an ecosystem signal: an author-owned memory repo was positioned as an OpenClaw-agent integration, not just a Claude-Code-layer tool. The crab-mem repo is archived (2026-02-10), possibly rolled back into claude-mem. This is an integration signal only.

**UF-9 — `MemeDeck` and the author's interest in memecoin mechanics.** Created 2026-04-10, described as *"Next.js 15 reference implementation of a card-game-style Solana memecoin trading..."* The author is actively building infrastructure around Solana memecoin trading alongside the LLM tooling. This does not establish anything about `$CMEM` specifically but corrects any impression that the token was a one-off detour.

---

## 4. What remains unresolved

Only two questions remain outside the evidence I could collect from this host:

1. **$CMEM deployer wallet and funding source.** Requires a paid Solana RPC (Helius / QuickNode / Shyft / Solscan pro). I made best-effort attempts against three public endpoints; all refused. The decisive question — whether the deployer wallet is funded from an address tied to `thedotmack` — cannot be answered from this host as configured. If/when access exists: run `getSignaturesForAddress` walked backwards until empty, identify the oldest signature, `getTransaction` on it, extract fee-payer pubkey, then walk that pubkey's own funding history.
2. **Whether `$CMEM` deployer is same operator as `cmem.ai` registrant.** Only paid RPC access plus non-public Cloudflare registrant data would close this. Cloudflare WHOIS is privacy-protected, and the public RDAP response does not surface a registrant.

The earlier open questions around stargazer coverage, binary rebuild policy, and translated README staleness are now resolved in §§6-8.

---

## 5. Recommendation

**I'm not making a claim about intent. I'm describing the state of the software, the project's own stated design principles, and the observable governance and amplification patterns.** I do not have special domain knowledge here; this is a concerned user's technical read-through. The pieces below are consistent with a project whose published direction extends beyond a local memory plugin. Whether that is concerning enough to uninstall or avoid is a judgment call each reader can make from the evidence.

- What the code says about itself: the top-level `CLAUDE.md` names "tunnel provisioning" as a Pro integration point and states that "all worker API endpoints on localhost:37777 remain fully open and accessible" as a design principle. That is the author's own stated roadmap, in writing.
- What the source shows: zero secrets-redaction anywhere in `src/`; unauthenticated `POST /api/import`; the Read-hook injecting timeline observations as `additionalContext` with `permissionDecision: allow`. Those three together create a context-injection loop in the code. I'm not claiming the loop was put there to be exploited — I'm pointing out it exists.
- What the ecosystem shows: `openclaw.ai` publicly describes itself as "Personal AI Assistant" with a config schema for streaming observations to six messaging channels. `crab-mem` (archived), `aims`/`aims-v2`, `crabspace-*`, and the in-repo OpenClaw plugin/installer code indicate the author has built OpenClaw-related adapters and observation tooling. The point is integration.
- What the commit history shows: feature-addition acceleration over the last 60 days. The Read-hook rewrite (2026-03-18), the `ANTHROPIC_BASE_URL` override (2026-04-09), and the Telegram notifier (2026-04-22) are all post-March 2026. The project's trajectory is not static.
- What I cleared: no unexpected outbound data paths, no hidden install endpoints, no hardcoded bearer tokens, no hostname / user / date-gated logic, no cryptographic primitives in the source. The committed Mach-O binary is a strict subset of the TypeScript source, not a superset. These are **not** findings against the project.
- What I could not determine from this environment: the `$CMEM` deployer wallet identity (requires a paid Solana RPC). Without that I cannot falsify the README's "3rd-party embrace" framing; I've documented the observable on-chain timing and left the interpretation open.

My read is: a memory plugin that has accumulated a substantial observation-and-notification surface over eight months, whose own design principles explicitly contemplate remote access to its local database via a Pro tier, whose quality-of-delivery is under measurable pressure (see §9), whose public star count has a measurable inorganic amplification layer, and whose author has built OpenClaw-related adapters and observation tooling alongside it. The question isn't whether any of that is malicious today — I'm not claiming it is. The question is whether the trajectory and the software quality are a place a given user wants their agent's credentials to live.

---

*Review pinned at SHA `8ace1d9c84e5ce455356cf852c370ea625e3b1d1`. Evidence artefacts live under `evidence/` in this repository: source excerpts, SHA-256 sums, live-probe records, stargazer dataset (gzipped), issue-tracker dataset (gzipped), on-chain timeline, rendered charts. Large / derivative artefacts (the 216 MB upstream repo clone, the 3 MB extracted Bun bundle, the 66 KB live `openclaw.sh`) are not re-hosted — SHAs are recorded in `evidence/sha256sums.txt` and reproducer commands are in the relevant evidence README.*

---

## 6. Addendum — follow-up findings after initial report

### A. `.github/workflows/` review — binary-rebuild policy resolved

Six workflow files total:

| file | purpose |
|---|---|
| `deploy-install-scripts.yml` (726 B) | On push to `main` touching `openclaw/install.sh` or `install/**`: copies `openclaw/install.sh` → `install/public/openclaw.sh`, deploys to Vercel via `amondnet/vercel-action@v25` using `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` secrets. **This is the only deploy automation.** |
| `npm-publish.yml` (438 B) | npm publish. |
| `claude-code-review.yml`, `claude.yml`, `convert-feature-requests.yml`, `summary.yml` | All use `anthropics/claude-code-action@v1` with `CLAUDE_CODE_OAUTH_TOKEN` to run Claude Code in CI for PR reviews, issue triage, and the `MAESTRO:` commit stream. |

**Crucial:** there is **no Mach-O rebuild workflow**. `plugin/scripts/claude-mem` (the 63 MB Mach-O) is *not* rebuilt in CI. The `scripts/build-worker-binary.js` script is present, but no workflow invokes it, and the script builds a Windows executable under `dist/binaries/`, not the committed macOS Mach-O. The binary has not been updated since `c2c3e306` on 2026-02-23.

The install-path evidence narrows the runtime claim: `plugin/hooks/hooks.json` starts the worker through `node "$_R/scripts/bun-runner.js" "$_R/scripts/worker-service.cjs" start`, the other hooks use the same `worker-service.cjs` path, and `smart-install.js` installs the shell alias as `bun "$ROOT/scripts/worker-service.cjs"`. `package.json`'s `files` list includes `plugin/scripts/*.js` and `plugin/scripts/*.cjs`, not the extensionless `plugin/scripts/claude-mem`, and `npm pack claude-mem@12.3.9 --dry-run --json` confirms the published npm package excludes the Mach-O.

One extra distribution-hygiene note: the v12.3.9 npm tarball does include `dist/binaries/worker-service-v10.3.1-win-x64.exe` (115,852,288 bytes), which is not present in the pinned GitHub tree or the `v12.3.9` tag tree. A string check of `dist/npx-cli/index.js` did not find `dist/binaries`, `worker-service-v10.3.1`, or `worker-service-v`, so the normal CLI path does not appear to invoke this stale Windows executable either. Full notes: [`evidence/binary/rebuild-policy.md`](evidence/binary/rebuild-policy.md).

### B. `openclaw/install.sh` — 66 KB of installer, cleared

Only 12 distinct URLs appear anywhere in the 1,800-line installer:

```
http://127.0.0.1:37777/api/admin/shutdown
http://127.0.0.1:37777/api/health
http://127.0.0.1:37777/api/readiness
https://ai.google.dev                       (user-facing help URL)
https://astral.sh/uv/install.sh             (uv runtime installer, curl-pipe-sh)
https://bun.sh/install                      (bun runtime installer, curl-pipe-bash)
https://github.com/thedotmack/claude-mem.git (clone)
https://install.cmem.ai/openclaw.sh         (self-reference in usage comment)
https://openclaw.dev/docs/installation      (docs URL — DNS doesn't resolve)
https://openrouter.ai                        (user-facing help URL)
https://t.me/userinfobot                    (user-facing help URL for Telegram chat-ID setup)
```

No `curl … -X POST` to any external endpoint. The only POSTs are `http://127.0.0.1:37777/api/admin/shutdown` (local worker control). The installer:

- Accepts `--api-key=KEY`, `--provider=claude|gemini|openrouter`, `--non-interactive`, `--upgrade` flags.
- Falls back to `read_tty -rs AI_PROVIDER_API_KEY` for interactive key entry.
- Exports the key into child processes via `INSTALLER_AI_API_KEY=… node -e …`.
- Never uploads the key anywhere.

**The installer does not make unexpected outbound POSTs.** The 66 KB is explained by: TTY detection, interactive prompts, provider selection, version-parsing helpers, health polling with retries, upgrade mode, shutdown handling, colored output, and error recovery. Benign.

### C. `handleImport` handler body — confirmed unauthenticated, no provenance

`src/services/worker/http/routes/DataRoutes.ts:344-399` is the full handler. Verbatim shape:

```ts
private handleImport = this.wrapHandler((req, res) => {
  const { sessions, summaries, observations, prompts } = req.body;
  const stats = { ... };
  const store = this.dbManager.getSessionStore();
  if (Array.isArray(sessions))    for (const s of sessions)      store.importSdkSession(s);
  if (Array.isArray(summaries))   for (const s of summaries)     store.importSessionSummary(s);
  if (Array.isArray(observations)) for (const o of observations) store.importObservation(o);
  // ... rebuild FTS index so imported observations are immediately searchable
});
```

Validation is solely `Array.isArray()`. There is **no auth header, no origin check, no signature, no source attribution, no per-field validation beyond shape.** Anything able to POST to `127.0.0.1:37777/api/import` — which includes every process running on the user's machine and every iframe / `fetch()` / DNS-rebound origin able to reach the port — can inject arbitrary observations that are then:

1. Persisted to `~/.claude-mem/claude-mem.db`.
2. Rebuilt into the FTS5 index for immediate searchability.
3. Surfaced back to Claude via the Read-hook timeline injection (`file-context.ts:282-291`) as `additionalContext` with `permissionDecision: 'allow'`.

This is a **documented context-injection path**. The `/api/import` endpoint is intended to import backups; the absent auth makes it reachable by other local processes. The middleware layer (next point) adds only a shared rate limit, not authentication.

### D. Middleware — rate limit only, no auth

`src/services/worker/http/middleware.ts` contains this comment verbatim:

```
// Simple in-memory rate limiter (#1935).
// Worker binds localhost-only, so in practice this is a global 300 req/min
// cap — every caller shares the 127.0.0.1/::1 bucket.
```

The only access control is localhost-binding + 300 req/min shared across all callers. No API key, no HMAC, no token. This matches the project's stated design (CLAUDE.md Pro Features: *"All worker API endpoints on localhost:37777 remain fully open and accessible"*).

### E. `docs/i18n/` staleness — validated across all translations

- **32 translated README files**.
- **32/32** carry the `version-6.5.0` shields.io badge (project is at 12.3.9+2).
- **0/32** mention `$CMEM`.
- **32/32** are therefore stale by that joint test.

The English `README.md` at HEAD also carries the `version-6.5.0` badge (that piece is just a not-auto-updated shields link — not the translations' fault) but **English additionally contains the `$CMEM` section that none of the 32 translations do.** Users reading the Chinese, Spanish, German, Japanese, etc. README get the project described without its current token promotion. This is not necessarily malicious (translations drift); it is worth noting that the English version promotes a token the translations don't mention.

### F. Daemonization / persistence review

- `src/services/worker-service.ts:1212`: *"needs to relaunch as a detached daemon. The MCP server (a separate Node ..."*
- `src/services/worker-service.ts:1346`: *"Ensure worker is running as a detached daemon (#1249)"*
- **No launchd `.plist`**, no systemd `.service` unit, no PM2 config, no Windows Task Scheduler registration, no `~/.config/autostart/`, no cron entry, no login-hook shim in any of the source files or plugin scripts.

**Conclusion:** the worker is a **detached user-mode daemon** that the plugin spawns when Claude Code (or Goose, via `OpenCodeInstaller`) starts a session. It persists *across Claude Code session closes within the same OS login session* (i.e. after you close Claude Code, the worker keeps running and still listens on 37777 and still has the SQLite DB open). It does **not** survive a reboot or logout — no system-level autostart hook gets the worker back up. Uninstalling the plugin + killing the running `bun`/`node` worker process is sufficient to fully stop it. **Persistence concern: moderate, not severe.**

### G. `publicdata.works` — cleared

HTTP 200 from `https://publicdata.works/`, served by Cloudflare. Title: **"Public Data Works"**. Description from the page: *"Public Data Works is an engineering and design studio. We build tools that help make data useful to the public. We work with mission-aligned organizations..."* This is a real engineering studio. The three commits attributed to `Claude <rajiv@publicdata.works>` on 2026-01-21 are AI-assisted contributions from Rajiv Sinclair (the studio's principal, per his other public footprint) using an unusual-but-not-malicious co-author attribution pattern. **Cleared.**

### H. OpenClaw domains — separate product surface

- `openclaw.ai` → HTTP 200, Vercel. Title: **"OpenClaw — Personal AI Assistant"**. 222,992 bytes of landing page.
- `www.openclaw.ai` → 307 → `openclaw.ai`.
- `docs.openclaw.ai` → HTTP 200, Cloudflare.
- `api.openclaw.ai`, `openclaw.dev`, `docs.openclaw.dev`, `install.openclaw.ai` → **DNS does not resolve**. The `openclaw.dev/docs/installation` URL that appears in `claude-mem`'s source is **a dead link at pin.** This means (a) either the project was planning to use a `.dev` domain and abandoned it, or (b) a `.dev` domain is planned for future cut-over. Either way the installer (`openclaw/install.sh`) and in-tree source point users at a URL that currently does not resolve.

OpenClaw publicly describes itself as a **"Personal AI Assistant"** — i.e. a consumer-facing agent product. OpenClaw itself is separate from Alex Newman's author-owned repo set. The claude-mem repo contains OpenClaw plugin/installer code, and several author-owned repos describe themselves as OpenClaw-agent tools. That supports an integration/ecosystem finding.

### I. CLAUDE.md observations surfaced during the follow-up

Reading the in-tree `CLAUDE.md` (the AI-development-instructions file shipped with the repo) confirms several design facts:

1. **Only privacy primitive is an opt-in tag.** *"`<private>content</private>` — User-level privacy control (manual, prevents storage). Implementation: Tag stripping happens at hook layer (edge processing) before data reaches worker/database. See `src/utils/tag-stripping.ts` for shared utilities."* Everything not explicitly wrapped in `<private>` is stored. The tag only helps when the user already knows to apply it. There is no automatic secrets detection / PII detection / credential-pattern stripping.
2. **Viewer UI runs in a browser on the worker port.** *"Viewer UI (`src/ui/viewer/`) — React interface at http://localhost:37777"* — the same port as the JSON API, co-located. This means a browser tab on any site that can bypass SOP (DNS rebinding, CSRF to same-origin calls with CORS permissive enough — and the middleware is `Access-Control-Allow-Origin: *`) can interact with the observation DB.
3. **Bun and uv are auto-installed as plugin prerequisites** — *"Bun (all platforms - auto-installed if missing), uv (all platforms - auto-installed if missing, provides Python for Chroma)"*. Confirmed, explicit.
4. **Plugin marketplace:** *"Installed Plugin: `~/.claude/plugins/marketplaces/thedotmack/`"*. The author runs their own Claude Code plugin marketplace under their GitHub handle, shipping this plugin from it.
5. **Docs auto-deploy via Mintlify** from `docs/public/` on push to main.

---

## 7. Addendum summary

The follow-up work resolved several open questions and added two later evidence sections:

- The binary-staleness finding is **narrowed**: the committed Mach-O is stale and not rebuilt by CI, but the normal hook/CLI path appears to use `worker-service.cjs`, so this is not evidence of a normal macOS-vs-Linux runtime split.
- The `/api/import` unauthenticated-ingest claim is **confirmed verbatim** in the handler source: `Array.isArray()` is the only validation.
- The i18n staleness claim is **confirmed with precision**: **0/32** translated READMEs mention `$CMEM` while English does.
- The GraphQL stargazer pass resolves the REST page-400 cap and updates Priority 7 to a full-corpus finding: real organic popularity plus a measurable amplification layer.
- The issue-tracker pass adds software-quality and governance evidence: current-version bug reports, not-planned/locked closure rates, and the confirmed April interaction-limit window.

The `openclaw/install.sh`, the workflow deploy path, and the `publicdata.works` contributor are cleared in the narrower sense checked here. The OpenClaw ecosystem (`openclaw.ai` live, `openclaw.dev` dead, OpenClaw code in-tree) confirms an adjacent integration surface.

*Follow-up artifacts: workflow YAMLs read in place at `.github/workflows/`; middleware and DataRoutes TypeScript read in place at `src/services/worker/{http/middleware.ts,worker/http/routes/DataRoutes.ts}`; saved artifacts under [`evidence/stargazers/`](evidence/stargazers/) and [`evidence/software-quality/`](evidence/software-quality/).*

---

## 8. Priority 7 detail — GraphQL full-corpus stargazer review

The initial REST-API pass in Priority 7 hit GitHub's 40k pagination cap and only covered the oldest slice of the graph. The GraphQL API resolves that cap. With the `gh` CLI already authenticated (scopes: `gist, read:org, repo, workflow`) and a lean query (omitting `email` and `contributionsCollection` which require extra scope or exceed resource budgets), I paginated all **66,433 stars** into [`evidence/stargazers/stars-graphql.jsonl.gz`](evidence/stargazers/stars-graphql.jsonl.gz). The first star is `vlasky @ 2025-09-09T06:44:10Z`; the last is `ajankuv @ 2026-04-23T23:33:17Z` — i.e. the full graph at pin. Per-day CSV saved at [`evidence/stargazers/per-day.csv`](evidence/stargazers/per-day.csv).

**The full-corpus signal updates the Priority 7 conclusion: there is a measurable amplification layer, rising over time and peaking in the April 13 calendar week (the largest Monday-Sunday week in the repo's history at 13,546 stars).** The repo remains majority-organic — 77% of stars come from accounts over 2 years old — but the amplification layer on top is visible in the data.

### Account-age distribution (full corpus)

| age at starring | stars | % |
|---|---|---|
| <1 week | 1,225 | 1.8% |
| 1–4 weeks | 1,352 | 2.0% |
| 1–3 months | 2,290 | 3.4% |
| 3–12 months | 5,604 | 8.4% |
| 1–2 years | 4,609 | 6.9% |
| 2–5 years | 12,653 | 19.0% |
| 5–10 years | 20,588 | 31.0% |
| >10 years | 18,112 | 27.3% |

77% of stargazers have accounts >2 years old. This is a healthy organic distribution for a trendy dev tool.

### Amplification signals — overall and baseline

| metric | baseline (pre-2025-12, n=454) | full corpus (n=66,433) |
|---|---|---|
| throwaway (0 repos + 0 followers) | 3.3% | 9.3% (6,209) |
| account <30d old when starring | 0.9% | 3.9% (2,577) |
| account <7d old when starring | 0 | 1.8% (1,225) |
| account <1d old when starring | 0 | 1.1% (713) |
| bot-pattern login (`name+4+digits` etc.) | 2.9% | 5.2% (3,447) |

Pre-December 2025 (when the repo was essentially unknown), throwaway rate was 3.3%, <1d accounts were zero. At full corpus, throwaway is 9.3% and <1d is 1.1%. I use that baseline as "what organic stars from this audience looked like" before the larger visibility spikes; the delta is the amplification layer.

### Weekly trend — amplification rises over time

| week (Monday) | stars | throwaway% | <30d% | <1d% |
|---|---|---|---|---|
| 2025-12-08 | 4,824 | 5.5 | 2.2 | 1.1 |
| 2026-01-05 | 2,947 | 5.4 | 2.5 | 1.2 |
| 2026-02-02 | 8,979 | 9.1 | 3.9 | 1.7 |
| 2026-02-23 | 1,854 | 7.0 | 2.9 | 0.8 |
| 2026-03-09 | 2,133 | 10.0 | 5.3 | 1.1 |
| 2026-03-16 | 3,924 | 9.5 | 5.1 | 1.2 |
| 2026-03-30 | 3,075 | 11.5 | 5.1 | 1.3 |
| 2026-04-06 | 4,419 | 11.7 | 4.6 | — |
| **2026-04-13** | **13,546** | **13.1** | **5.1** | **1.2** |
| 2026-04-20 | 3,249 | — | — | — |

The throwaway rate rises materially from the 3.3% pre-amplification baseline to 13.1% in the April 13 calendar week. That is a 4× increase, concurrent with the largest single star-week in the repo's life.

### The April 13 cohort

The April 13 calendar week (13,546 stars, ~20% of the full corpus) has the heaviest account-quality signals in the whole dataset:
- **throwaway: 13.1%** (vs 3.3% baseline — a 4× signal)
- **<30d: 5.1%** (vs 0.9% baseline — a 5.7× signal)
- **<1d: 1.2%** (vs 0% baseline — pure signal)
- **<1h: 0.78%** (113 accounts created and starred within the same hour)
- **bot-pattern login: 5.9%**

### Sample April-13 stargazer accounts (<1d old, randomly sampled)

| login | created | starred | gap | followers | repos |
|---|---|---|---|---|---|
| `odyssey-work` | 2026-04-13 01:12:00 | 2026-04-13 01:30:51 | 0.3 h | 0 | 1 |
| `kauaesyt20-prog` | 2026-04-12 21:12:22 | 2026-04-13 01:40:58 | 4.5 h | 0 | 0 |
| `brendawong-max` | 2026-04-13 03:46:38 | 2026-04-13 04:17:55 | 0.5 h | 1 | 0 |
| `leonardobernardo199824-jpg` | 2026-04-13 01:29:04 | 2026-04-13 05:09:12 | 3.7 h | 0 | 1 |
| `blockbirdbot-hub` | 2026-04-13 01:37:42 | 2026-04-13 05:57:24 | 4.3 h | 0 | 0 |
| `NoahC963-jpg` | 2026-04-12 18:58:44 | 2026-04-13 06:47:16 | 11.8 h | 0 | 1 |
| `qq1834639311-cloud` | 2026-04-13 01:35:31 | 2026-04-13 07:14:55 | 5.7 h | 0 | 0 |
| `gogmad-Ghub` | 2026-04-12 19:11:41 | 2026-04-13 09:14:44 | 14.1 h | 2 | 0 |
| `kaingaji-cyber` | 2026-04-12 19:23:35 | 2026-04-13 09:45:27 | 14.4 h | 1 | 1 |

Login suffix inventory across the cohort: `-work`, `-prog`, `-max`, `-jpg`, `-hub`, `-cyber`, `-cloud`, `-web`, `-pixel`, `-Ghub`. The suffix pattern looks consistent with dictionary-plus-suffix account generation. Almost every sampled account has 0 followers, 0-1 repo, was created the same day it starred, and never stars anything else visible in its profile.

### What the pattern is not

The 77% >2-year-old cohort is real. `thedotmack` (account from 2011) starred his own repo on 2025-11-24, `bigph00t` (committer, 2024 account) on 2025-12-17, and `ousamabenyounes` (top contributor, 2012 account) on 2026-03-13 — these are the only insider logins the dataset shows, and all three are expected. The first 454 stars pre-December-2025 have nearly-clean signals (3.3% throwaway, 0% <1d) — the repo's early adoption is legitimate. What's been added on top is amplification; I am not saying the repo's popularity is artificial.

### Updated Priority 7 assessment

**High confidence: measurable star-count amplification is present, rises materially over time, and peaks in the final week before this review pin.** The growth from roughly 34k to 66k stars observed during review overlaps heavily with the April 13 calendar week: that week alone accounts for 13,546 stars, far above ordinary organic growth in this repo's history. The baseline rate (pre-amplification) was ~3% throwaway / 0% <1d; the peak rate is 13% throwaway / 1.2% <1d / 0.78% <1h. That is a sustained elevated signal across weekly cohorts, not an isolated outlier.

This does not mean the repo is fake. It means the advertised star count (66k+) **over-represents organic developer interest by roughly the amplification delta** — call it 9,000 to 13,000 stars of inorganic amplification above the baseline, concentrated in the last three months.

*Artifacts: `evidence/stargazers/stars-graphql.jsonl.gz` (66,433 records, 2 MB gzipped), `evidence/stargazers/per-day.csv` (per-day account-quality signal table), `scripts/fetch_stars.py` (resumable GraphQL fetcher with `--resume-from-last` mode), `scripts/analyze_stars.py` (regenerates the per-day CSV and headline tables).*

---

## 9. Software quality and issue-tracker governance

This section was added after the primary review. It addresses the concern that the notes above describe a broad architecture but not the quality of the software as shipped or the pattern of moderation around user reports. Those are separate questions that may matter to someone deciding whether to install it.

All numbers below come from `gh api graphql` paginated over every issue ever opened on `thedotmack/claude-mem` (1,114 issues as of 2026-04-24). Reproducible via `scripts/fetch_issues.py` + `scripts/analyze_issues.py`. Supporting artifacts in `evidence/software-quality/`.

### 9.1 Bug-report surface on current versions

On a single day (2026-04-23), five independent community members with no prior contributor relationship filed separate bug tickets against v12.1.2 through v12.3.9 (the current three point-releases). Full snapshot at `evidence/software-quality/issue-snapshot-2026-04-23.md`.

| # | author | what | affects |
|---|---|---|---|
| [#2104](https://github.com/thedotmack/claude-mem/issues/2104) | marcelopossa | Observer agent's own system prompt + tool-event XML persisted as rows in `user_prompts` table | v12.1.2 – v12.3.9 |
| [#2106](https://github.com/thedotmack/claude-mem/issues/2106) | ogrotten | Install/uninstall/reinstall leaves detached daemons; `~/.claude-mem/` recreated by active session hooks; multiple rounds of find-and-delete across 6+ directories | current |
| [#2107](https://github.com/thedotmack/claude-mem/issues/2107) | songjianping-cloud | `worker-cli.js` restart can self-trigger duplicate-worker detection and leave claude-mem in a broken reconnect state | current |
| [#2108](https://github.com/thedotmack/claude-mem/issues/2108) | ahmed-hassan19 | `observer-sessions` restart/compaction churn consumes ~97% of prompt volume (581 / 892 rows churn) | v12.3.7 – v12.3.9 |
| [#2109](https://github.com/thedotmack/claude-mem/issues/2109) | vdruts | SessionStart context injection silently fails on Windows + Git Bash (port + POSIX path bugs) | 12.3.8, likely all 12.x |

Five distinct failure domains (data-model pollution, install hygiene, process lifecycle, prompt-volume waste, platform silent failure), five different reporters, all against the latest three point-releases. Thicker defect surface than expected for a released product.

Supporting context: the repo ships [`ANTI-PATTERN-TODO.md`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/ANTI-PATTERN-TODO.md) with header `Total: 301 issues | Fixed: 289 | Approved Overrides: 12 | Remaining: 0`. The categories catalogued (`GENERIC_CATCH`, `CATCH_AND_CONTINUE_CRITICAL_PATH`, `LARGE_TRY_BLOCK`, `NO_LOGGING_IN_CATCH`, `ERROR_MESSAGE_GUESSING`) are precisely the patterns that produce silent failures. 301 in 8 months is substantial. A recent changelog entry: *"Stop hook: fire-and-forget summarize. Eliminated the ~110s terminal block when a session ended."*

### 9.2 Issue-tracker moderation patterns

Totals at pin:

| metric | value |
|---|---|
| Total issues opened | 1,114 |
| Closed as completed | 847 (76.0%) |
| Closed as not-planned | 121 (10.9%) |
| Closed as duplicate | 6 (0.5%) |
| Currently open (incl. reopened) | 140 |
| Locked issues | 104 (9.3%) |
| Labelled `bug` | 308 (27.6%) |
| Labelled `consolidated` | 137 |
| Labelled `severity:high` or `severity:critical` | 68 |
| Filed by OWNER | 162 (14.5%) |
| Filed by NONE (outside user) | 869 (78.0%) |

**Not-planned rate 10.9%, heavily concentrated.** Healthy OSS norms are under 5%. Two days account for 78 of the 121:

| day | NOT_PLANNED closures on that day |
|---|---|
| 2026-02-08 | 55 |
| 2026-04-10 | 40 |
| all other days combined | 26 |

**Locked issues: 104 (9.3%).** Locking prevents further community comment. 62 are closed+locked. Top closed+lock day: 2025-12-13 with 10 issues sealed at once.

**Auto-conversion of feature requests to discussions.** [`.github/workflows/convert-feature-requests.yml`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/.github/workflows/convert-feature-requests.yml) is triggered on `issues:` events and auto-converts anything labelled `feature-request` into a GitHub discussion. 105 issues carry that label. Effect: the open-issue count visible at the top of the GitHub page understates the volume of community-requested work.

**Reopened-issue skew.** 80 of 81 currently-reopened issues (99%) are reopened versions of owner-authored tickets. Only 1 community-authored reopened issue exists. The "reopened" state on this tracker is almost exclusively an owner-side mechanism rather than the community-facing "this wasn't actually fixed" signal it typically represents.

### 9.3 Confirmed interaction-limit window: 2026-04-16 → 2026-04-21

The repository had GitHub's **contributor-only interaction-limit** active for approximately six days in April 2026, which appears to have prevented external (NONE-association) users from filing bug reports while continuing to let contributors, collaborators, and the owner file. This is a different feature from disabling the tracker entirely — the `has_issues` flag stays `true` but GitHub's public-facing error on an external user's failed submission reads *"An owner of this repository has limited the ability to create an issue to users that have contributed to this repository in the past."*

Full writeup with direct Reddit evidence at [`evidence/software-quality/interaction-limit-apr-2026.md`](evidence/software-quality/interaction-limit-apr-2026.md). Headline table:

| date | total | external authors | contrib | owner |
|---|---|---|---|---|
| 2026-04-11 → 2026-04-14 | 65 total | every day had external filings | — | — |
| **2026-04-15** | **164** | 22 unique (surge — likely trigger) | 0 | 1 |
| **2026-04-16** | **2** | **0** | **2** | 0 |
| **2026-04-17** | **2** | **0** | **1** | **1** |
| 2026-04-18 | 0 | silent | — | — |
| **2026-04-19** | **1** | **0** | 0 | **1** |
| 2026-04-20 / 2026-04-21 | 0 / 0 | silent (Reddit post goes up Apr 21 14:27 UTC) | — | — |
| 2026-04-22 | 3 | 2 (first external filer after gap) | 0 | 1 |
| 2026-04-23 | 22 | 17 unique (pent-up flood — including the five tickets in §9.1) | 0 | 0 |

31 of 31 prior days (2026-03-15 → 2026-04-14) had external authors filing. Apr 16–19 is the only multi-day run in the repo's active history where every active day had zero external authors. The first external filer appears on Apr 22, one day after Reddit user `xii` posted a comment with a screenshot of the GitHub interaction-limit error message.

The five bug tickets documented in §9.1 were filed by five independent external users within 24 hours of the limit being lifted. That burst is corroborating evidence that real users had been trying to file and had been unable to do so.

This is a factual observation about project moderation behaviour, not an imputation of motive. Legitimate reasons to enable interaction-limit include responding to a spam wave, a single abusive user filing duplicates, or a CI/spam attack. I'm not privy to which was the case. The observable fact is: **external-user bug reporting appears to have been unavailable for six days immediately following a 164-issue bug-report surge against the current releases.**

### 9.4 Candidate earlier signature cluster (low confidence)

Running the same interaction-limit detector over the full corpus also flags four days in November 2025:

| date | total | external | owner |
|---|---|---|---|
| 2025-11-12 | 1 | 0 | 1 |
| 2025-11-13 | 3 | 0 | 3 |
| 2025-11-19 | 2 | 0 | 2 |
| 2025-11-22 | 1 | 0 | 1 |

All four are low-volume; the repo was still pre-adoption in November 2025 with low overall activity, so "external authors = 0" could plausibly mean "no external users were filing anything" rather than "external users were prevented from filing." The clustering within a 10-day window is worth flagging as a candidate earlier event but there's no external corroboration. **Candidate, not confirmed.**

### 9.5 Broader creation-gap runs (for completeness)

Days with zero new issues filed from any author, grouped into consecutive runs of ≥3 days:

| period | days with zero new issues |
|---|---|
| 2025-09-10 – 2025-10-13 | 34 |
| 2025-10-15 – 2025-10-22 | 8 |
| 2025-11-23 – 2025-11-30 | 8 |

These are all pre-adoption and would only detect a full tracker-disable (`has_issues: false`), not interaction-limit. Included for completeness.

### 9.6 Interpretation

Individually no signal is disqualifying:

- Bug-report volume is partly a function of scale (66k stars → more users filing).
- `ANTI-PATTERN-TODO.md` existing is a sign the maintainer knows about anti-patterns.
- 11% not-planned isn't enormous absolute.
- Auto-converting feature requests is a legitimate workflow choice.
- Owner filing their own tickets is normal for an active maintainer.

Taken together the picture is of a project **shipping fast while carrying a lot of maintenance pressure**, with quality defects reaching current releases in bulk, an elevated rate of not-planned closures, and active shaping of the visible issue surface. That is separate from any question about intent or architecture — it's a question about the maintenance model. Whether that maintenance model is acceptable for a tool that lives inside a developer's agent loop with their credentials is a judgment call for each installer.

**Confidence: high** on all numbers (they are deterministic output of queries against the public GitHub API); **medium** on the interpretive framing — reasonable people could read the same numbers as "active maintenance" rather than "heavy moderation."

*Artifacts: `evidence/software-quality/issues-graphql.jsonl.gz` (1,114 issues, 69 KB gzipped), `evidence/software-quality/issues-per-day.csv`, `evidence/software-quality/issue-snapshot-2026-04-23.md`. Reproduce with `scripts/fetch_issues.py` (works against any public GitHub repo — pass `--owner OWNER --repo REPO`) and `scripts/analyze_issues.py`.*
