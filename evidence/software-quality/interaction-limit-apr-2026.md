# Interaction-limit window, 2026-04-16 to 2026-04-21

## What happened

Between 2026-04-16 and 2026-04-21, the `thedotmack/claude-mem` repository had GitHub's **contributor-only interaction limit** turned on. This is different from disabling the issue tracker entirely: when interaction-limit-to-contributors is active, external users (who have never had a PR merged, never been added as a collaborator, and never been assigned an issue) cannot file new issues. Users who have contributed before can still file. The repo owner can still file.

The exact GitHub error surface is documented: [GitHub Docs — Limiting interactions in your repository](https://docs.github.com/en/communities/moderating-comments-and-conversations/limiting-interactions-in-your-repository). This feature can be set for 24 hours, 3 days, 1 week, 1 month, 6 months, or indefinitely.

## Direct evidence

On **2026-04-21 at approximately 14:27 UTC**, Reddit user [`xii`](https://old.reddit.com/user/xii) posted a [comment in `r/ClaudeCode`](https://www.reddit.com/r/ClaudeCode/comments/1scz5kk/comment/ohe4en3/) on a thread started by `thedotmack`, describing having hit the interaction-limit error while trying to file a bug report. Reproduced from that comment:

> @/u/thedotmack: As a long time `claude-mem` user, I'm really disheartened and frustrated.
>
> The plugin was working spectacularly for quite a long time on my Win11 machine with CC, but very recently with one of your updates the plugin went completely ass up.
>
> Enabling the plugin causes Claude Code startup to spawn ~8–9 bash processes and makes the UI unresponsive for ~1 minute. Typed commands are ignored or severely delayed even after startup.
>
> **I tried submitting a bug report, but you've blocked everyone but contributors access to creating any kind of issue. Why?**
>
> I then tried using your bug-report tool via `npm run bug-report`:
>
> ```
> cd ~/.claude/plugins/marketplaces/thedotmack
> npm run bug-report
> ```
>
> I filled out all of the prompts in the console, and at the end when it was time to submit, I was once again greeted with:
>
> > *"An owner of this repository has limited the ability to create an issue to users that have contributed to this repository in the past."*
>
> If you happen to see this post, I've put together a detailed bug report here: https://gist.github.com/futuremotiondev/a337c35230ac3e0fcc5e7dfad3b785f8
>
> […]

The quoted error text *"An owner of this repository has limited the ability to create an issue to users that have contributed to this repository in the past"* is the exact message GitHub renders when contributor-only interaction-limit is active and an external user tries to file. It is a direct visual confirmation that the feature was engaged.

## Corroborating evidence from the issue-tracker data

The `issues-graphql.jsonl.gz` dataset supports the Reddit account. Per-day activity around the event, from the full corpus:

The first four count columns are issue counts. The `unique external authors` column is separate, because a single reporter can file more than one issue on the same day.

| date | total issues | external issues | contributor issues | owner issues | unique external authors | signature |
|---|---:|---:|---:|---:|---:|---|
| 2026-04-11 | 17 | 16 | 1 | 0 | 12 | normal |
| 2026-04-12 | 12 | 12 | 0 | 0 | 12 | normal |
| 2026-04-13 | 15 | 13 | 2 | 0 | 12 | normal |
| 2026-04-14 | 21 | 19 | 2 | 0 | 12 | normal |
| **2026-04-15** | **164** | **27** | **0** | **137** | **22** | **surge — likely the trigger** |
| **2026-04-16** | **2** | **0** | **2** | **0** | **0** | **interaction-limit signature** |
| **2026-04-17** | **2** | **0** | **1** | **1** | **0** | **interaction-limit signature** |
| **2026-04-18** | 0 | 0 | 0 | 0 | 0 | silent |
| **2026-04-19** | **1** | **0** | **0** | **1** | **0** | **interaction-limit signature** |
| **2026-04-20** | 0 | 0 | 0 | 0 | 0 | silent |
| **2026-04-21** | 0 | 0 | 0 | 0 | 0 | silent (Reddit post goes up 14:27 UTC) |
| 2026-04-22 | 3 | 2 | 0 | 1 | 2 | first external filer after gap |
| **2026-04-23** | **22** | **22** | **0** | **0** | **17** | pent-up flood |

The pattern in isolation:

- The 31-day window from 2026-03-15 → 2026-04-14 has external-author filings on **every single active day** (31 of 31). That's the baseline.
- 2026-04-15 spikes to 164 issues filed: 27 external issues from 22 unique external authors, plus 137 owner-filed issues.
- For the following six days, **no external user files an issue**. On the active days in that window, contributors and the owner continue filing a handful. This matches the contributor-only interaction-limit signature: external users absent, pre-existing contributors still allowed through.
- Then on 2026-04-22 (one day after the Reddit post made the restriction visible publicly), a community filer appears. On 2026-04-23, seventeen unique external reporters file — the pent-up demand pouring through as soon as the gate reopened. The five bug tickets reproduced in [`issue-snapshot-2026-04-23.md`](issue-snapshot-2026-04-23.md) are from that cohort.

The date range matches: the Reddit post lands on 2026-04-21, and community filings resume on 2026-04-22. Whether the owner saw the Reddit post and lifted the restriction in response, or the restriction was always scheduled to expire around that point, cannot be determined from the data alone — but the timing is tight.

## Candidate earlier events

Using the same interaction-limit signature against the full corpus also flags four days in November 2025:

| date | total issues | external | contributor | owner |
|---|---|---|---|---|
| 2025-11-12 | 1 | 0 | 0 | 1 |
| 2025-11-13 | 3 | 0 | 0 | 3 |
| 2025-11-19 | 2 | 0 | 0 | 2 |
| 2025-11-22 | 1 | 0 | 0 | 1 |

These are much weaker signals: all four days are low-volume (1–3 issues each), no contributors filed, only the owner was active. The repository was still in its pre-adoption period in November 2025 with low overall activity, so "external authors = 0" on a given day could plausibly mean "no external users were filing anything that day" rather than "external users were prevented from filing." However, the clustering of four signature-matching days within 10 days is worth flagging as a candidate earlier event. Without a direct observation like the Reddit comment, this one is **candidate, not confirmed**.

## What this means

The repository owner turned on an interaction limit that appears to have prevented external users from filing bug reports for approximately six days (2026-04-16 through 2026-04-21), immediately after an acute issue-volume spike on 2026-04-15. When the limit lifted, 22 external issues from 17 unique external authors arrived on 2026-04-23 — evidence that real users had reports to file.

This is a factual observation about the project's moderation behaviour, not an imputation of motive. Legitimate reasons to enable interaction-limit include responding to a spam wave, a single angry user filing many duplicates, or a CI/spam attack. I'm not privy to whichever was the case. The observable fact is: **external-user reporting appears to have been unavailable for six days in the middle of a period when external users had a lot of new breakage to report against the latest release.**
