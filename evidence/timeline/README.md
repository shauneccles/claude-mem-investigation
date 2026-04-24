# Timeline — component introduction dates

Backs [`../../REPORT.md`](../../REPORT.md) §2 Priority 1. Reconstructed from `git log --follow --diff-filter=A` at commit `8ace1d9c`.

The project **did** start as a memory plugin. The broader observation features are late additions.

| component | introduced | commit | author |
|---|---|---|---|
| root commit (initial release v3.3.8 — no `package.json`, no `src/`, no worker) | 2025-09-06 | `598369e8` | Alex Newman |
| `package.json` first appears | 2025-09-09 | `aae7de8e` (Release v3.5.4) | Alex Newman |
| `src/services/worker-service.ts` + `plugin/scripts/worker-service.cjs` (first Express server) | 2025-10-17 | `37285494` | Alex Newman |
| port 37777 first referenced | 2025-10-19 | `7ff611fe` | Alex Newman |
| HTTP route-based architecture (`src/services/worker/http/middleware.ts`) | 2025-12-05 | `3aaee6f1` | Alex Newman |
| build-worker-binary.js (Bun compile script) | 2025-12-11 | `807d1d61` | Alex Newman |
| Mode system + `email-investigation` mode + `ragtime/` script appear | 2025-12-22 / 2025-12-23 | `3ea0b60b` / `e32f2d7b` | Alex Newman |
| `epstein-mode` corpus path references | 2025-12-23, 2026-01-30 | `8bca13a9`, `2eaef1f5` | Alex Newman |
| **`$CMEM` Solana token section in English README** | **2026-01-13** | `8990a788` | Alex Newman |
| `src/shared/EnvManager.ts` centralized credentials | 2026-01-17 | `006ff401` | Alex Newman |
| OpenClaw plugin scaffold + SSE observation-feed consumer | 2026-02-07 | `89333434` / `f8d8de53` | Alex Newman (via MAESTRO: automation) |
| **Mach-O binary `plugin/scripts/claude-mem` committed** (then never rebuilt; normal hooks use `worker-service.cjs`) | **2026-02-23** | `c2c3e306` | Alex Newman |
| `law-study` mode | 2026-03-08 | `97ea9e45` | Alex Newman |
| **Read-hook silent rewrite `src/cli/handlers/file-context.ts`** | **2026-03-18** | `fb9d917f` | Alex Newman (+ Claude Opus 4.6) |
| **`ANTHROPIC_BASE_URL` override in EnvManager** | **2026-04-09** | `07be61cf` | WuTao (external PR #1627, AI-generated) |
| **`TelegramNotifier`** | **2026-04-22** | `f2d361b9` | Alex Newman (day before pin) |

## Pattern

- **Days 1–40:** thin memory plugin with session-start/session-end/pre-compact hooks. Honest scope.
- **Weeks 6–14:** worker service, HTTP API on localhost:37777, route architecture. Scope is still "local memory plugin."
- **Weeks 15–20:** mode system, ragtime / email-investigation / law-study, OpenClaw scaffold. Scope opens up.
- **Weeks 21+:** broader primitives — Read rewrite (Mar 18), env override (Apr 9), Telegram (Apr 22 — day before the pin). The features most concerning to me are all within the last 60 days of development.

## Authorship distribution

Top authors on the full commit log (via `git shortlog -sne --all`):

| author | commits |
|---|---|
| Alex Newman `<thedotmack@gmail.com>` | 2,394 |
| copilot-swe-agent[bot] | 188 |
| Ousama Ben Younes | 20 |
| Claude `<noreply@anthropic.com>` | 18 |
| Copilot | 18 |
| Rod Boev | 15 |
| claude[bot] | 12 |

284 commits carry the `MAESTRO:` prefix, indicating an AI-automation pipeline the author runs against the repo. The co-author identity `Claude <rajiv@publicdata.works>` (3 commits on 2026-01-21) is a contractor — Public Data Works is a real engineering studio; see [`../live-probes/README.md`](../live-probes/README.md). The `Jarvis <jarvis@openclaw.ai>` identity (3 commits 2026-04-02) confirms OpenClaw is an operating business with its own email domain.
