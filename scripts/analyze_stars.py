"""
Stargazer account-quality signal analysis for thedotmack/claude-mem.

Consumes stars-graphql.jsonl (or .jsonl.gz) produced by fetch_stars.py and
produces:

  - per-day.csv           (day, stars, throwaway%, <30d%, <7d%, <1d%, <1h%, bot%)
  - stdout headline tables

Standard library only. Python 3.9+.

Usage:
  python analyze_stars.py                                     # default input: ./stars-graphql.jsonl
  python analyze_stars.py --input PATH                        # explicit input (.jsonl or .jsonl.gz)
  python analyze_stars.py --output-csv PATH                   # override output CSV path
  python analyze_stars.py --sample-cohort START END [--age-max-days N]
                                                              # print sample of accounts in START..END
                                                              # whose account age at starring is <N days
"""

from __future__ import annotations
import argparse
import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


BOT_PATTERNS = [
    re.compile(r"^[a-z]+\d{4,}$"),
    re.compile(r"^user\d+$"),
    re.compile(r"^[a-zA-Z]+-[a-zA-Z]+-\d{3,}$"),
]


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def age_days(edge: dict) -> float:
    return (parse_dt(edge["starredAt"]) - parse_dt(edge["node"]["createdAt"])).total_seconds() / 86400.0


def is_throwaway(edge: dict) -> bool:
    node = edge["node"]
    return node["repositories"]["totalCount"] == 0 and node["followers"]["totalCount"] == 0


def is_bot_pattern(edge: dict) -> bool:
    login = edge["node"]["login"]
    return any(p.match(login) for p in BOT_PATTERNS)


def open_input(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load_records(path: Path):
    with open_input(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def percent(num: int, denom: int) -> float:
    return round(num / denom * 100, 2) if denom else 0.0


def monday_key(dt_iso: str) -> str:
    dt = datetime.fromisoformat(dt_iso[:10])
    monday_ord = dt.toordinal() - dt.weekday()
    return datetime.fromordinal(monday_ord).date().isoformat()


def write_per_day_csv(records: list, out_path: Path) -> None:
    by_day = defaultdict(list)
    for r in records:
        by_day[r["starredAt"][:10]].append(r)
    with out_path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(["day", "stars", "throwaway_pct", "fresh_30d_pct",
                    "fresh_7d_pct", "fresh_1d_pct", "fresh_1h_pct", "bot_pattern_pct"])
        for d in sorted(by_day):
            rs = by_day[d]
            n = len(rs)
            w.writerow([
                d, n,
                percent(sum(1 for r in rs if is_throwaway(r)), n),
                percent(sum(1 for r in rs if age_days(r) < 30), n),
                percent(sum(1 for r in rs if age_days(r) < 7), n),
                percent(sum(1 for r in rs if age_days(r) < 1), n),
                percent(sum(1 for r in rs if age_days(r) < 1 / 24), n),
                percent(sum(1 for r in rs if is_bot_pattern(r)), n),
            ])
    print(f"wrote {out_path}  ({sum(len(v) for v in by_day.values()):,} records over {len(by_day)} days)")


def print_top_days(records: list, k: int = 20) -> None:
    by_day = Counter(r["starredAt"][:10] for r in records)
    print(f"\n=== top {k} star days ===")
    for d, c in by_day.most_common(k):
        print(f"  {d}  {c:>6}")


def print_weekly_rollup(records: list) -> None:
    by_week = defaultdict(list)
    for r in records:
        by_week[monday_key(r["starredAt"])].append(r)
    print("\n=== weekly rollup (week of Monday | stars | throwaway% | <30d% | <1d%) ===")
    for w in sorted(by_week):
        rs = by_week[w]
        n = len(rs)
        thr = percent(sum(1 for r in rs if is_throwaway(r)), n)
        f30 = percent(sum(1 for r in rs if age_days(r) < 30), n)
        f1 = percent(sum(1 for r in rs if age_days(r) < 1), n)
        print(f"  {w}  {n:>6}  {thr:>6}  {f30:>6}  {f1:>6}")


def print_account_age_buckets(records: list) -> None:
    ages = [age_days(r) for r in records]
    buckets = [
        (0, 7, "<1w"), (7, 30, "1-4w"), (30, 90, "1-3m"),
        (90, 365, "3-12m"), (365, 730, "1-2y"), (730, 1825, "2-5y"),
        (1825, 3650, "5-10y"), (3650, 1e9, ">10y"),
    ]
    print("\n=== account age at starring (full corpus) ===")
    for lo, hi, label in buckets:
        n = sum(1 for a in ages if lo <= a < hi)
        print(f"  {label:<7}  {n:>6}  {n/len(ages)*100:>5.1f}%")


def print_baseline_vs_recent(records: list) -> None:
    baseline = [r for r in records if r["starredAt"] < "2025-12-01"]
    # April 13-20 peak week
    peak = [r for r in records if "2026-04-13" <= r["starredAt"][:10] <= "2026-04-20"]
    print("\n=== baseline vs peak ===")
    print(f"  baseline (pre-2025-12, n={len(baseline)})")
    _emit_signal_row(baseline)
    print(f"  full corpus (n={len(records)})")
    _emit_signal_row(records)
    print(f"  April 13-20 peak week (n={len(peak)})")
    _emit_signal_row(peak)


def _emit_signal_row(rs: list) -> None:
    n = len(rs)
    if not n:
        return
    print(f"    throwaway%: {percent(sum(1 for r in rs if is_throwaway(r)), n):>5}")
    print(f"    <30d%:      {percent(sum(1 for r in rs if age_days(r) < 30), n):>5}")
    print(f"    <7d%:       {percent(sum(1 for r in rs if age_days(r) < 7), n):>5}")
    print(f"    <1d%:       {percent(sum(1 for r in rs if age_days(r) < 1), n):>5}")
    print(f"    <1h%:       {percent(sum(1 for r in rs if age_days(r) < 1/24), n):>5}")
    print(f"    bot-pat%:   {percent(sum(1 for r in rs if is_bot_pattern(r)), n):>5}")


def print_insider_matches(records: list) -> None:
    insiders = {
        "thedotmack", "alex-newman", "AlexNewman", "claude-memory",
        "openclaw", "jarvis", "rajivsinclair", "publicdata-works",
        "bigphoot", "bigph00t", "Ousama", "ousamabenyounes",
    }
    hits = [r for r in records if r["node"]["login"] in insiders]
    print(f"\n=== insider-login matches: {len(hits)} ===")
    for h in hits:
        print(f"  {h['starredAt']}  {h['node']['login']}  (account created {h['node']['createdAt'][:10]})")


def sample_cohort(records: list, start: str, end: str, age_max_days: float) -> None:
    cohort = [
        r for r in records
        if start <= r["starredAt"][:10] <= end and age_days(r) < age_max_days
    ]
    print(f"\n=== cohort sample: {start}..{end}, age < {age_max_days}d ({len(cohort)} records) ===")
    for r in cohort[:30]:
        created = r["node"]["createdAt"]
        starred = r["starredAt"]
        gap_h = (parse_dt(starred) - parse_dt(created)).total_seconds() / 3600
        print(f"  {r['node']['login']:<35}  created={created}  starred={starred}  "
              f"gap={gap_h:5.1f}h  f={r['node']['followers']['totalCount']}  "
              f"r={r['node']['repositories']['totalCount']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="stars-graphql.jsonl",
                    help="Path to stars-graphql.jsonl or .jsonl.gz")
    ap.add_argument("--output-csv", default="per-day.csv",
                    help="Path to write per-day CSV")
    ap.add_argument("--sample-cohort", nargs=2, metavar=("START", "END"),
                    help="Print sample of stargazers from this YYYY-MM-DD range")
    ap.add_argument("--age-max-days", type=float, default=1.0,
                    help="For --sample-cohort: only include accounts younger than this at starring")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"input not found: {inp}", file=sys.stderr)
        return 1

    print(f"loading {inp}…")
    records = list(load_records(inp))
    if not records:
        print("no records parsed", file=sys.stderr)
        return 1
    print(f"records: {len(records):,}")
    print(f"first: {records[0]['starredAt']} by {records[0]['node']['login']}")
    print(f"last:  {records[-1]['starredAt']} by {records[-1]['node']['login']}")

    write_per_day_csv(records, Path(args.output_csv))
    print_top_days(records, k=20)
    print_weekly_rollup(records)
    print_account_age_buckets(records)
    print_baseline_vs_recent(records)
    print_insider_matches(records)

    if args.sample_cohort:
        sample_cohort(records, args.sample_cohort[0], args.sample_cohort[1], args.age_max_days)

    return 0


if __name__ == "__main__":
    sys.exit(main())
