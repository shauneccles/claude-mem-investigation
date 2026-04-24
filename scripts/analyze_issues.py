"""
Issue-tracker governance / software-quality analysis.

Consumes the `issues-graphql.jsonl` (or .jsonl.gz) produced by fetch_issues.py
and produces:

  - per-day CSV: issues opened, closed-completed, closed-not-planned, closed-duplicate
  - headline governance metrics:
      * total issues
      * not-planned rate (%)
      * duplicate rate (%)
      * reopened count
      * largest creation gaps (candidate "tracker disabled" signatures)
      * high-volume not-planned closure days (>= N issues closed as not-planned on the same day)
      * author-association distribution
      * label frequency
  - optional --sample-issues START END to print issue titles filed in that date range

These are the same metrics used in `../evidence/software-quality/` for the
claude-mem review, generalised so anyone can point them at any repo.

Standard library only. Python 3.9+.

Usage:
  python analyze_issues.py
  python analyze_issues.py --input ../evidence/software-quality/issues-graphql.jsonl.gz
  python analyze_issues.py --mass-close-threshold 20
  python analyze_issues.py --sample-issues 2026-04-20 2026-04-25
"""

from __future__ import annotations
import argparse
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def open_input(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load(path: Path):
    with open_input(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def monday_of(iso_date: str) -> str:
    dt = datetime.fromisoformat(iso_date[:10])
    monday_ord = dt.toordinal() - dt.weekday()
    return datetime.fromordinal(monday_ord).date().isoformat()


def percent(num: int, denom: int) -> float:
    return round(num / denom * 100, 2) if denom else 0.0


def find_creation_gaps(records: list, min_days: int = 3) -> list:
    if not records:
        return []
    bydate = defaultdict(int)
    for r in records:
        bydate[r["createdAt"][:10]] += 1
    days = sorted(bydate)
    first = datetime.fromisoformat(days[0]).date()
    last = datetime.fromisoformat(days[-1]).date()
    all_days = [(first + timedelta(days=i)).isoformat()
                for i in range((last - first).days + 1)]
    zero_days = [d for d in all_days if d not in bydate]
    runs: list[list[str]] = []
    if zero_days:
        cur = [zero_days[0]]
        for d in zero_days[1:]:
            prev = datetime.fromisoformat(cur[-1]).date()
            this = datetime.fromisoformat(d).date()
            if (this - prev).days == 1:
                cur.append(d)
            else:
                runs.append(cur)
                cur = [d]
        runs.append(cur)
    return sorted([r for r in runs if len(r) >= min_days],
                  key=lambda x: -len(x))


def find_mass_dismissals(records: list, threshold: int = 10) -> list[tuple[str, int]]:
    day_counts = Counter()
    for r in records:
        if r.get("stateReason") == "NOT_PLANNED" and r.get("closedAt"):
            day_counts[r["closedAt"][:10]] += 1
    return sorted(
        [(d, c) for d, c in day_counts.items() if c >= threshold],
        key=lambda x: -x[1],
    )


def write_daily_csv(records: list, out_path: Path) -> None:
    daily = defaultdict(lambda: Counter())
    for r in records:
        day = r["createdAt"][:10]
        daily[day]["opened"] += 1
        assoc = r.get("authorAssociation")
        if assoc == "NONE":
            daily[day]["opened_external"] += 1
            if r.get("author"):
                daily[day]["_ext_authors"] = daily[day].get("_ext_authors", set()) | {r["author"]}
        elif assoc == "OWNER":
            daily[day]["opened_owner"] += 1
        elif assoc == "CONTRIBUTOR":
            daily[day]["opened_contributor"] += 1
        if r.get("closedAt"):
            close_day = r["closedAt"][:10]
            reason = r.get("stateReason") or "OPEN"
            daily[close_day][f"closed_{reason.lower()}"] += 1
    with out_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(["day", "opened", "opened_external", "opened_owner",
                    "opened_contributor", "unique_external_authors",
                    "closed_completed", "closed_not_planned",
                    "closed_duplicate", "closed_reopened"])
        for d in sorted(daily):
            row = daily[d]
            ext_authors = row.get("_ext_authors") or set()
            w.writerow([d, row["opened"],
                        row["opened_external"], row["opened_owner"], row["opened_contributor"],
                        len(ext_authors),
                        row["closed_completed"], row["closed_not_planned"],
                        row["closed_duplicate"], row["closed_reopened"]])
    print(f"wrote {out_path}")


# Kept as an alias so existing callers don't break.
def write_weekly_csv(records: list, out_path: Path) -> None:
    write_daily_csv(records, out_path)


def print_summary(records: list, mass_threshold: int) -> None:
    n = len(records)
    states = Counter((r["state"], r.get("stateReason")) for r in records)
    print(f"\n=== totals ===")
    print(f"records: {n}")
    for k, v in states.most_common():
        print(f"  {k!r}: {v}")

    nr = sum(1 for r in records if r.get("stateReason") == "NOT_PLANNED")
    dup = sum(1 for r in records if r.get("stateReason") == "DUPLICATE")
    reopened = sum(1 for r in records if r.get("stateReason") == "REOPENED")
    locked = sum(1 for r in records if r.get("locked"))
    print(f"\n=== governance metrics ===")
    print(f"not-planned rate:  {percent(nr, n):>5}% ({nr}/{n})")
    print(f"duplicate rate:    {percent(dup, n):>5}% ({dup}/{n})")
    print(f"currently reopened:{reopened}")
    print(f"locked issues:     {locked}")

    print(f"\n=== author-association (for opened issues) ===")
    assoc = Counter(r.get("authorAssociation") or "UNKNOWN" for r in records)
    for a, c in assoc.most_common():
        print(f"  {a}: {c}  ({percent(c, n)}%)")

    # Interaction-limit detection.
    #
    # GitHub's contributor-only interaction-limit blocks NONE-association users from
    # filing issues, but pre-existing contributors, collaborators, and the owner can
    # still file. The signature is therefore "days with issue activity where zero
    # external authors appear, but contributor/owner/collaborator are present" - not
    # "days with zero issues filed." The latter misses the feature entirely.
    #
    # Reference: https://docs.github.com/en/communities/moderating-comments-and-conversations/limiting-interactions-in-your-repository
    print(f"\n=== interaction-limit detection (DAILY - checks contributor-only signature) ===")
    from collections import defaultdict
    daily_ext_authors = defaultdict(set)
    daily_own_authors = defaultdict(set)
    daily_contrib_authors = defaultdict(set)
    daily_coll_authors = defaultdict(set)
    daily_counts = defaultdict(int)
    for r in records:
        d = r["createdAt"][:10]
        daily_counts[d] += 1
        assoc = r.get("authorAssociation")
        author = r.get("author")
        if not author:
            continue
        if assoc == "NONE":
            daily_ext_authors[d].add(author)
        elif assoc == "OWNER":
            daily_own_authors[d].add(author)
        elif assoc == "CONTRIBUTOR":
            daily_contrib_authors[d].add(author)
        elif assoc in ("COLLABORATOR", "MEMBER"):
            daily_coll_authors[d].add(author)

    all_days = sorted(set(daily_counts))
    active_days = [d for d in all_days if daily_counts[d] >= 3]
    if active_days:
        ext_counts = sorted(len(daily_ext_authors[d]) for d in active_days)
        median_ext = ext_counts[len(ext_counts) // 2]
        mean_ext = sum(ext_counts) / len(ext_counts)
        print(f"median unique external reporters per active day (>=3 issues filed): {median_ext}")
        print(f"mean unique external reporters per active day:                     {mean_ext:.1f}")
        print(f"active days (>=3 issues): {len(active_days)}")
    else:
        print("(not enough active days to compute a baseline)")

    # Interaction-limit signature: day has ANY activity, external=0, at least one
    # non-external author filed. Weighted by run length.
    signature_days = [
        d for d in all_days
        if daily_counts[d] >= 1
        and len(daily_ext_authors[d]) == 0
        and (len(daily_contrib_authors[d]) + len(daily_own_authors[d]) + len(daily_coll_authors[d])) >= 1
    ]
    print(f"\ndays matching interaction-limit signature (any activity, 0 external, >=1 contrib/owner/collab):")
    for d in signature_days:
        assocs_present = []
        if daily_own_authors[d]:     assocs_present.append(f"owner={len(daily_own_authors[d])}")
        if daily_contrib_authors[d]: assocs_present.append(f"contrib={len(daily_contrib_authors[d])}")
        if daily_coll_authors[d]:    assocs_present.append(f"collab={len(daily_coll_authors[d])}")
        print(f"  {d}  total={daily_counts[d]}  ext=0  {' '.join(assocs_present)}")
    print(f"\ntotal signature days: {len(signature_days)}")

    # Group consecutive signature days into runs (allowing up to 1 silent day between)
    if signature_days:
        from datetime import datetime as _dt
        runs = []
        cur = [signature_days[0]]
        for d in signature_days[1:]:
            prev = _dt.fromisoformat(cur[-1]).date()
            this = _dt.fromisoformat(d).date()
            if (this - prev).days <= 2:
                cur.append(d)
            else:
                runs.append(cur); cur = [d]
        runs.append(cur)
        print(f"\nsignature-day runs (<=1-day gap tolerated, suggesting sustained restriction):")
        for r in runs:
            total_issues = sum(daily_counts[d] for d in r)
            print(f"  {r[0]} .. {r[-1]}  ({len(r)} signature day(s), {total_issues} total issues during run)")

    print("\nNote: runs of >=2 signature days during an otherwise-active period are the")
    print("strongest interaction-limit candidates. Single-day signatures in an otherwise")
    print("quiet window may simply indicate low overall activity that day.")

    gaps = find_creation_gaps(records, min_days=3)
    print(f"\n=== creation-gap runs >=3 days (top 15) ===")
    print(f"(long gaps early in a repo's life are expected; gaps mid-life are candidate 'tracker disabled' signatures)")
    for run in gaps[:15]:
        print(f"  {run[0]} .. {run[-1]}  ({len(run)} days)")

    mass = find_mass_dismissals(records, threshold=mass_threshold)
    print(f"\n=== high-volume not-planned closure days (>={mass_threshold} issues closed as NOT_PLANNED in one day) ===")
    if not mass:
        print(f"  (none at threshold {mass_threshold})")
    for d, c in mass:
        print(f"  {d}  {c} issues")


def print_sample(records: list, start: str, end: str) -> None:
    sample = [r for r in records if start <= r["createdAt"][:10] <= end]
    sample.sort(key=lambda r: r["createdAt"])
    print(f"\n=== issues opened {start}..{end} ({len(sample)}) ===")
    for r in sample:
        state = r["state"]
        reason = r.get("stateReason") or ""
        title = (r.get("title") or "")[:90]
        print(f"  #{r['number']}  {r['createdAt'][:10]}  {state}/{reason}  {r['author']}  {title}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="issues-graphql.jsonl",
                    help="path to issues-graphql.jsonl or .gz")
    ap.add_argument("--output-csv", default="issues-per-day.csv")
    ap.add_argument("--mass-close-threshold", type=int, default=10,
                    help="minimum NOT_PLANNED closures on a single day to flag as high-volume closure")
    ap.add_argument("--sample-issues", nargs=2, metavar=("START", "END"),
                    help="print issues opened in this YYYY-MM-DD range")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"input not found: {inp}", file=sys.stderr)
        return 1
    print(f"loading {inp}...")
    records = list(load(inp))
    if not records:
        print("no records parsed", file=sys.stderr)
        return 1

    write_daily_csv(records, Path(args.output_csv))
    print_summary(records, args.mass_close_threshold)

    if args.sample_issues:
        print_sample(records, args.sample_issues[0], args.sample_issues[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
