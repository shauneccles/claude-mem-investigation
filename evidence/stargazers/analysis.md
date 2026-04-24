# Stargazer analysis — full-corpus results

Dataset: `stars-graphql.jsonl.gz` (66,433 records). Source: `gh api graphql` on 2026-04-24, paginated over the `stargazers` connection with `orderBy: {field: STARRED_AT, direction: ASC}`.

## Top 20 star days

| rank | day | stars |
|---|---|---|
| 1 | 2026-04-13 | 3,280 |
| 2 | 2026-04-14 | 2,537 |
| 3 | 2026-02-04 | 2,181 |
| 4 | 2026-04-15 | 2,088 |
| 5 | 2026-02-03 | 2,083 |
| 6 | 2026-04-16 | 1,913 |
| 7 | 2026-04-17 | 1,814 |
| 8 | 2026-04-12 | 1,735 |
| 9 | 2026-02-02 | 1,721 |
| 10 | 2026-02-05 | 1,221 |
| 11 | 2026-03-16 | 1,166 |
| 12 | 2025-12-10 | 1,143 |
| 13 | 2025-12-11 | 1,071 |
| 14 | 2026-04-18 | 1,040 |
| 15 | 2026-04-20 | 1,029 |
| 16 | 2025-12-15 | 1,015 |
| 17 | 2026-03-30 | 1,013 |
| 18 | 2026-03-17 | 903 |
| 19 | 2026-04-21 | 880 |
| 20 | 2026-04-19 | 874 |

11 of the top 20 are in April 2026. The single biggest week (Mon 2026-04-13 → Sun 2026-04-20) carried 14,575 stars — 22% of the entire all-time star count.

## Weekly rollup

| week (Monday) | stars | throwaway % | <30d % | <1d % |
|---|---|---|---|---|
| 2025-09-08 | 2 | 0 | 0 | 0 |
| 2025-09-22 | 8 | 0 | 0 | 0 |
| 2025-09-29 | 3 | 0 | 0 | 0 |
| 2025-10-06 | 1 | 0 | 0 | 0 |
| 2025-10-13 | 4 | 0 | 0 | 0 |
| 2025-10-20 | 216 | 2.8 | 0.5 | 0 |
| 2025-10-27 | 65 | 7.7 | 0 | 0 |
| 2025-11-03 | 62 | 1.6 | 3.2 | 0 |
| 2025-11-10 | 52 | 1.9 | 1.9 | 0 |
| 2025-11-17 | 25 | 4.0 | 0 | 0 |
| 2025-11-24 | 16 | 6.2 | 0 | 0 |
| 2025-12-01 | 215 | 2.8 | 0.5 | 0 |
| 2025-12-08 | 4,824 | 5.5 | 2.2 | 1.1 |
| 2025-12-15 | 2,769 | 3.9 | 1.7 | 0.8 |
| 2025-12-22 | 680 | 3.8 | 0.4 | 0 |
| 2025-12-29 | 898 | 5.6 | 0.8 | 0 |
| 2026-01-05 | 2,947 | 5.4 | 2.5 | 1.2 |
| 2026-01-12 | 1,197 | 5.1 | 1.5 | 0.3 |
| 2026-01-19 | 658 | 5.5 | 2.3 | 0.5 |
| 2026-01-26 | 1,198 | 6.3 | 3.3 | 1.2 |
| 2026-02-02 | 8,979 | 9.1 | 3.9 | 1.7 |
| 2026-02-09 | 2,968 | 6.1 | 2.1 | 0.4 |
| 2026-02-16 | 1,825 | 6.8 | 3.0 | 0.7 |
| 2026-02-23 | 1,854 | 7.0 | 2.9 | 0.8 |
| 2026-03-02 | 1,490 | 8.1 | 3.4 | 0.7 |
| 2026-03-09 | 2,133 | 10.0 | 5.3 | 1.1 |
| 2026-03-16 | 3,924 | 9.5 | 5.1 | 1.2 |
| 2026-03-23 | 3,131 | 10.9 | 5.2 | 1.1 |
| 2026-03-30 | 3,075 | 11.5 | 5.1 | 1.3 |
| 2026-04-06 | 4,419 | 11.7 | 4.6 | — |
| **2026-04-13** | **13,546** | **13.1** | **5.1** | **1.2** |
| 2026-04-20 | 3,249 | — | — | — |

Reading the throwaway column: 3.3% in the organic baseline period (pre-December 2025), rising materially over time to 13.1% in the peak week. The week-to-week path is uneven, but the baseline-to-peak move is not noise.

## Account-age distribution (full corpus)

| age bucket when starring | stars | % |
|---|---|---|
| <1 week | 1,225 | 1.8% |
| 1–4 weeks | 1,352 | 2.0% |
| 1–3 months | 2,290 | 3.4% |
| 3–12 months | 5,604 | 8.4% |
| 1–2 years | 4,609 | 6.9% |
| 2–5 years | 12,653 | 19.0% |
| 5–10 years | 20,588 | 31.0% |
| >10 years | 18,112 | 27.3% |

77% of stargazers have accounts >2 years old. The base is organic; the amplification sits on top.

## Same-hour star clusters

Only 1 hour in the entire dataset had ≥5 accounts all created within the same hour starring in the same hour: `2026-04-16T05Z` with 5 accounts (`dwala1983zuma-pixel`, `lawnthings`, `yashdeeparya939-cyber`, `GoykD`, `reddameronasiempresiempre-web`). The amplification pattern is spread out rather than burst-clustered.

## Insider logins

Three logins in the dataset match obvious insiders:

| login | account age | starred |
|---|---|---|
| `thedotmack` | 2011 account | 2025-11-24 (author starring own repo) |
| `bigph00t` (committer, 5 commits as Alexander Knigge) | 2024 account | 2025-12-17 |
| `ousamabenyounes` (top contributor, 20 commits) | 2012 account | 2026-03-13 |

No `claude-memory`, `openclaw`, `jarvis`, `rajivsinclair` stars observed. No obvious sock-puppet activity.

## Bot-pattern logins (overall 3,447 / 5.2%)

Regex categories:

| pattern | count |
|---|---|
| `^[a-z]+\d{4,}$` (e.g. `john1234`) | 3,414 |
| `^[a-zA-Z]+-[a-zA-Z]+-\d{3,}$` | 32 |
| `^user[0-9]+$` | 1 |

5.2% is elevated above the pre-amplification baseline (2.9%) but within noise — legitimate humans do pick names with numbers. The stronger signal is the **suffix** pattern in the April 13 cohort (see [`april-cohort-sample.md`](april-cohort-sample.md)), which isn't captured by these regexes but is visible by eye.

## Reproduction

```bash
cd scripts
python analyze_stars.py --input ../evidence/stargazers/stars-graphql.jsonl.gz
```

See [`../../scripts/analyze_stars.py`](../../scripts/analyze_stars.py) for the full analysis pipeline.
