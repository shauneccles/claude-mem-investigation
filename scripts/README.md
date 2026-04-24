# Scripts

Reproducible data-collection and analysis.

| script | what it does |
|---|---|
| [`fetch_stars.py`](fetch_stars.py) | Paginate every stargazer of a public repo via GitHub GraphQL v4 with account metadata. Resumable via `checkpoint.json` and via `--resume-from-last`. Writes `stars-graphql.jsonl` alongside. Defaults to `thedotmack/claude-mem`; use `--owner OWNER --repo REPO` for any public repo. |
| [`analyze_stars.py`](analyze_stars.py) | Consume `stars-graphql.jsonl` (or `.jsonl.gz`) and produce the per-day account-quality signal CSV plus headline tables. Regenerates `evidence/stargazers/per-day.csv` and `analysis.md` numbers. |
| [`fetch_issues.py`](fetch_issues.py) | Paginate every issue of a public repo via GitHub GraphQL v4 with governance metadata (state, stateReason, locked, labels, author, authorAssociation). Resumable. Defaults to `thedotmack/claude-mem`; use `--owner OWNER --repo REPO` for any public repo. |
| [`analyze_issues.py`](analyze_issues.py) | Consume `issues-graphql.jsonl` and produce the per-day rollup CSV + governance headlines: not-planned rate, high-volume not-planned closure days, lock rate, author-association distribution, creation-gap candidates for "tracker disabled" signatures. Writes `issues-per-day.csv` by default. |
| [`extract_bun_section.py`](extract_bun_section.py) | Pure-Python Mach-O LC_SEGMENT_64 walker. Extracts the `__BUN.__bun` section from any Bun `--compile` binary. No `llvm-objdump` / `otool` required. |
| [`plot_charts.py`](plot_charts.py) | Render the six evidence charts (issue tracker + stargazer) as PNGs. Uses plotly + kaleido. Declares its own dependencies via PEP 723 inline metadata; run with `uv run plot_charts.py`. |

## Requirements

- Python 3.10+
- `gh` (GitHub CLI) authenticated — `gh auth login`. Default scopes (`repo`, `read:org`, `workflow`, `gist`) are sufficient; `read:user` is not required for the queries used here.
- `uv` (for `plot_charts.py` only — auto-installs plotly/kaleido/pandas via PEP 723 inline deps). Get it from https://docs.astral.sh/uv/getting-started/installation/.

The fetch/analyse scripts (`fetch_stars.py`, `analyze_stars.py`, `fetch_issues.py`, `analyze_issues.py`, `extract_bun_section.py`) are standard-library-only. Only `plot_charts.py` requires uv.

## Typical workflow

```bash
cd scripts

# Stargazer analysis (takes ~30 min for claude-mem; bigger repos scale roughly linearly)
python fetch_stars.py                     # writes stars-graphql.jsonl alongside
python analyze_stars.py                   # writes per-day.csv + stdout tables

# Issue-tracker governance analysis (takes ~30 s for claude-mem)
python fetch_issues.py                    # writes issues-graphql.jsonl alongside
python analyze_issues.py --mass-close-threshold 20
                                          # writes issues-per-day.csv + stdout tables

# Any public repo (both scripts accept the same flags)
python fetch_stars.py --owner nodejs --repo node
python fetch_issues.py --owner vercel --repo next.js

# If a long fetch dies (504, network, power):
python fetch_stars.py                     # resumes from checkpoint (default)
python fetch_stars.py --resume-from-last  # anchor-resume if checkpoint is missing/stale

# Status check without fetching
python fetch_stars.py --status
python fetch_issues.py --status

# Regenerate the six evidence charts (requires uv)
uv run plot_charts.py
```

## Output formats

- `stars-graphql.jsonl` — one GraphQL edge per line: `{starredAt, node: {login, createdAt, followers, following, repositories}}`
- `issues-graphql.jsonl` — one flattened issue per line: `{number, title, state, stateReason, locked, createdAt, closedAt, comments, labels, author, authorAssociation}`
- `per-day.csv` — `day, stars, throwaway_pct, fresh_30d_pct, fresh_7d_pct, fresh_1d_pct, fresh_1h_pct, bot_pattern_pct`
- `issues-per-day.csv` — `day, opened, opened_external, opened_owner, opened_contributor, unique_external_authors, closed_completed, closed_not_planned, closed_duplicate, closed_reopened`
- stdout: headline tables (top spike days, weekly rollup, cohort baselines, account-age distribution, creation-gap candidates, high-volume not-planned closure days, author-association distribution, insider-login hits)

## Reproducibility

The numbers in [`../evidence/stargazers/analysis.md`](../evidence/stargazers/analysis.md) and [`../evidence/software-quality/README.md`](../evidence/software-quality/README.md) were produced by running `analyze_stars.py` and `analyze_issues.py` against the gzipped jsonl datasets shipped in this repo (captured 2026-04-24). Re-running the fetch scripts later will pick up new activity, so totals will drift. The baseline and peak-week percentages should stay stable.

## Using this toolkit on other projects

The whole point of writing these as generic GitHub-repo queries rather than claude-mem-specific scripts is that the methodology is portable. If you're considering installing any open-source tool that touches your dev environment, these four scripts produce a first-pass review in under an hour:

- `fetch_stars.py` + `analyze_stars.py` → is the star count organic or amplified?
- `fetch_issues.py` + `analyze_issues.py` → what's the bug-report surface, dismissal rate, lock rate, feature-request handling?

Neither script is specific to claude-mem. Point them at any public repo and the same metrics come out.
