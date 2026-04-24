# Live probes — `install.cmem.ai`, `cmem.ai`, `openclaw.ai`, `publicdata.works`

Backs [`../../REPORT.md`](../../REPORT.md) §2 Priority 3 and Addendum §6.G-H.

## `install.cmem.ai/openclaw.sh` — live matches repo exactly

```
$ curl -sSL https://install.cmem.ai/openclaw.sh | sha256sum
78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4

$ sha256sum claude-mem/openclaw/install.sh
78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4
```

Same 66,214 bytes. The `.github/workflows/deploy-install-scripts.yml` workflow copies `openclaw/install.sh → install/public/openclaw.sh` on pushes to `main` and deploys to Vercel via `amondnet/vercel-action@v25` with `VERCEL_TOKEN`/`VERCEL_ORG_ID`/`VERCEL_PROJECT_ID` secrets. No hidden side channel.

## `install.cmem.ai` endpoint probe

All probed paths except `openclaw.sh` and `install.sh` (both are served) return 404. No unadvertised endpoints.

| path | status | content-type | size |
|---|---|---|---|
| `/` | 200 | `application/x-sh` | 703 (deprecation shim → `npx claude-mem install`) |
| `/install.sh` | 200 | `text/plain` | 703 (same shim) |
| `/openclaw.sh` | 200 | `text/plain` | 66,214 (matches repo) |
| `/robots.txt` `/uninstall.sh` `/update.sh` `/beacon` `/beacon.json` `/telemetry` `/api/health` `/api` `/status` `/metrics` `/.well-known/security.txt` `/sitemap.xml` `/claude-mem.sh` `/cmem.sh` `/openclaw.ps1` `/claude-mem.ps1` `/bootstrap.sh` `/config.json` | 404 | | |

## Domain registrations (RDAP)

| domain | registered | registrar | nameservers | status |
|---|---|---|---|---|
| `claude-mem.ai` | 2025-08-31 | Cloudflare | kate.ns + ivan.ns.cloudflare.com | Active. 5 days before first repo commit. |
| `cmem.ai` | **2026-01-10** | Cloudflare | kate.ns + ivan.ns.cloudflare.com | Active. **3 days before `$CMEM` README promotion (Jan 13).** |
| `claude-mem.com` | 2026-04-15 | NameCheap | LAUNCH1/LAUNCH2.SPACESHIP.NET + NS1/NS2.SEDOPARKING.COM + NS3/NS4.AFTERNIC.COM | Parked / for-sale. HTML is `window.location.href="/lander"`. Not project-operated. |
| `openclaw.ai` | *(RDAP not retrievable for `.ai`; HEAD 200)* | — | — | Live. Vercel-hosted. Title: **"OpenClaw — Personal AI Assistant"**, 222,992 bytes of landing page. |
| `openclaw.dev` | — | — | — | **DNS does not resolve.** The URL `https://openclaw.dev/docs/installation` appears as a string literal in the repo source; at pin it is a dead link. |
| `publicdata.works` | *(multiple TLD)* | — | — | HTTP 200, Cloudflare, title "Public Data Works". Real engineering studio. Explains the three `Claude <rajiv@publicdata.works>` co-authored commits as contractor contributions. Cleared. |

## `cmem.ai` homepage

Title: **"$CMEM — The Currency of the Agentic Economy"**. External links on the landing page:

- `https://jup.ag/swap/SOL-2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS` — Jupiter swap
- `https://dexscreener.com/solana/2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS`
- `https://raydium.io/swap/?inputMint=sol&outputMint=2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS`
- `https://github.com/thedotmack/crab-mem` — a separate, archived side-project ("🦀 Continuous cognition for OpenClaw agents")
- `https://crab-mem.sh/bounties`, `https://moltbook.com/u/Crab-Mem`

This is a token-promotion site, not a software-product site.

## OpenClaw subdomain probe

| host | status |
|---|---|
| `openclaw.ai` | 200 OK, Vercel, "Personal AI Assistant" landing |
| `www.openclaw.ai` | 307 → `openclaw.ai` |
| `docs.openclaw.ai` | 200 OK, Cloudflare |
| `api.openclaw.ai` | DNS fail |
| `install.openclaw.ai` | DNS fail |
| `openclaw.dev` | DNS fail |
| `docs.openclaw.dev` | DNS fail |
