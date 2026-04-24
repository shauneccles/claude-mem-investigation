# Evidence

Every file in here backs a specific finding in [`../REPORT.md`](../REPORT.md). This directory is the raw material — the report is the argument.

| subdir | covers | report section |
|---|---|---|
| [`timeline/`](timeline/) | When each concerning component landed in the repo | §2 Priority 1 |
| [`binary/`](binary/) | Mach-O layout, extracted Bun bundle URLs, rebuild-policy check, sha256 sums | §2 Priority 2 + §6.A |
| [`live-probes/`](live-probes/) | `install.cmem.ai` live-vs-repo, domain WHOIS, OpenClaw landing | §2 Priority 3 |
| [`source-excerpts/`](source-excerpts/) | Verbatim source of the four load-bearing claims | §2 Priority 4 + Addendum §6.C/D |
| [`cmem-onchain/`](cmem-onchain/) | `$CMEM` pool graduation timeline from DexScreener/GeckoTerminal | §2 Priority 6 |
| [`stargazers/`](stargazers/) | Full 66,433-stargazer dataset, per-day signal table, amplification analysis | §8 Priority 7 revisited |
| [`software-quality/`](software-quality/) | 1,114-issue dataset, per-day rollup, issue-tracker governance metrics, snapshot of five bugs filed on one day | §9 Software quality |

## Reproducibility

Anything in here derived from a live external source can be reproduced:

```bash
# Binary hashes
curl -sLO https://raw.githubusercontent.com/thedotmack/claude-mem/8ace1d9c/plugin/scripts/claude-mem
sha256sum claude-mem  # should match evidence/sha256sums.txt

# Live installer matches the repo
curl -sSL https://install.cmem.ai/openclaw.sh | sha256sum
# → 78c39b15d15c265af2543cf422ad57e03d9a91494ef4c0a6038fe426085343d4

# Stargazer amplification analysis
cd ../scripts && python fetch_stars.py && python analyze_stars.py

# Issue-tracker governance analysis
cd ../scripts && python fetch_issues.py && python analyze_issues.py --mass-close-threshold 20
```

Both data-fetch scripts accept `--owner OWNER --repo REPO` so you can point this methodology at any public GitHub repo you're considering installing.

## Global sha256 sums

See [`sha256sums.txt`](sha256sums.txt) — covers the Mach-O binary, the minified worker bundle, the extracted Bun section, the stale Windows executable in the npm tarball, and both copies of `openclaw.sh` (live and in-repo — they match).
