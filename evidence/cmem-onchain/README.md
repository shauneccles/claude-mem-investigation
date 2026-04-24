# `$CMEM` on-chain — timing and liquidity

Backs [`../../REPORT.md`](../../REPORT.md) §2 Priority 6.

**Contract:** `2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS` (Solana)
**CoinGecko ID:** `claude-memory`
**Symbol:** CMEM
**Decimals:** 9
**Total supply:** 998,477,515.21 (~1B — standard memecoin supply)

## Sources

- DexScreener: `https://api.dexscreener.com/latest/dex/tokens/2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS`
- GeckoTerminal: `https://api.geckoterminal.com/api/v2/networks/solana/tokens/2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS/pools`

Public Solana RPCs were either rate-limited or required API keys at the time of review. The deployer wallet and pre-graduation mint transaction were therefore **not** determinable from this machine. Those remain open questions.

## What GeckoTerminal confirms

The token launched on a **pump.fun-style bonding-curve launchpad**, graduated to Meteora on **2026-01-06 07:59:49 UTC** with `graduation_percentage: 100.0`. Graduation migrated the LP to main pool `6MzFAkWnac6GSK1EdFX93dZeukGfzrFq4UHWarhGSQyd`.

## All pools

Market snapshot captured **2026-04-24 UTC**; FDV, liquidity, and price values are volatile.

| pool | created UTC | FDV USD | liquidity USD | price USD |
|---|---|---|---|---|
| `6MzFAkWn…GSQyd` (main, Meteora) | 2026-01-06 07:59:49 | 53,441 | 16,855 | 0.0000535 |
| `DUNUS2Wk…jFbj` | 2026-01-11 10:41:05 | 178,445 | 2,099 | 0.000179 |
| `GK8bG8FY…cGfKX` | 2026-01-12 04:14:00 | 170,442 | 1,884 | 0.000171 |
| `FYbqC9f…iJ39j` | 2026-01-14 11:01:05 | 1,482,731 | 2,869 | 0.00148 |
| `GT1PcoMT…B1aSx` | 2026-01-16 08:21:09 | 3,092,404 | 10,800 | 0.00309 |

At review time (**2026-04-24 UTC**), combined liquidity across all pools was under $35,000 USD. Main-pool FDV was **below the pump.fun graduation threshold** (~$69k) — the token had lost value since graduation.

## Timeline

| UTC | event |
|---|---|
| pre-2026-01-06 | Token deployed on pump.fun bonding curve (exact date requires RPC access) |
| **2026-01-06 07:59:49** | Bonding curve graduates to 100%; main Meteora LP (`6MzFAkWn…`) created |
| 2026-01-10 02:46:21 | `cmem.ai` domain registered at Cloudflare (see [`../live-probes/README.md`](../live-probes/README.md)) |
| 2026-01-11–16 | Four additional Meteora LPs created at wildly different prices |
| **2026-01-13 02:23:09** | `$CMEM` section added to English `README.md` (commit `8990a788`) |

Three infrastructure actions in seven days, in an order consistent with preparation rather than with passive "3rd-party embrace."

## What the README says

From [`README.md` line 420–422](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/README.md#L420-L422):

> $CMEM is a solana token created by a 3rd party without Claude-Mem's prior consent, but officially embraced by the creator of Claude-Mem (Alex Newman, @thedotmack). The token acts as a community catalyst for growth and a vehicle for bringing real-time agent data to the developers and knowledge workers that need it most. $CMEM: 2TsmuYUrsctE57VLckZBYEEzdokUF8j8e1GavekWBAGS

No wallet code, no contract SDK, and no product integration with the token exists anywhere in the source tree. Of 32 translated READMEs in `docs/i18n/`, **zero mention `$CMEM`**.

## What's unresolved

- Deployer wallet identity.
- Whether the deployer's SOL was funded from any address correlatable with `thedotmack` or `claude-memory` identities.
- Pre-graduation holder distribution.
- Sniper / insider-buyer patterns at graduation.

All four require a paid Solana RPC (Helius, QuickNode, Shyft, or Solscan Pro). Cloudflare-backed WHOIS for `cmem.ai` is privacy-protected, so registrant identity cannot be correlated with the on-chain deployer from this machine.
