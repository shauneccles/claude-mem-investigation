"""
Resumable stargazer GraphQL fetcher for thedotmack/claude-mem.

Writes output alongside the script (or alongside --output-dir, if set), not in
absolute paths — so `git clone && cd scripts && python fetch_stars.py` works
on any machine.

Checkpoint:
  ./stars-graphql.jsonl       append-only data
  ./checkpoint.json           cursor + page count (fsync'd every 10 pages)

Safe to Ctrl-C and restart. `--resume-from-last` is a fallback when checkpoint
is missing or stale: it walks the stream from the start, skipping edges until
it finds the last (login, starredAt) pair in the data file, then appends.

Auth: uses `gh` (GitHub CLI, already authenticated via `gh auth login`).
Required scope: `repo` (default). `read:user` is NOT required for this query.

Usage:
  python fetch_stars.py                      # resume (default)
  python fetch_stars.py --restart            # wipe data + checkpoint, fresh start
  python fetch_stars.py --status             # print progress without fetching
  python fetch_stars.py --resume-from-last   # anchor-mode resume (no checkpoint needed)
  python fetch_stars.py --owner OWNER --repo REPO   # review a different repo
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR

QUERY_TEMPLATE = """
query($cursor: String) {
  rateLimit { cost remaining resetAt }
  repository(owner: "%(owner)s", name: "%(repo)s") {
    stargazers(first: 100, after: $cursor, orderBy: {field: STARRED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      totalCount
      edges {
        starredAt
        node {
          login
          createdAt
          followers { totalCount }
          following { totalCount }
          repositories(first: 0) { totalCount }
        }
      }
    }
  }
}
"""

RETRYABLE = ("HTTP 5", "timeout", "Bad gateway", "ETIMEDOUT",
             "ECONNRESET", "Resource limits", "abuse detection")


def load_checkpoint(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"cursor": None, "pages": 0, "total": 0,
            "started_at": time.time(), "last_update": None}


def save_checkpoint(path: Path, ck: dict) -> None:
    ck = dict(ck)
    ck["last_update"] = time.time()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ck, indent=2))
    tmp.replace(path)


def fetch_page(query_file: Path, cursor: str | None, attempt: int = 0) -> dict:
    args = ["gh", "api", "graphql", "-F", f"query=@{query_file}"]
    if cursor:
        args += ["-F", f"cursor={cursor}"]
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=60, check=False)
    except subprocess.TimeoutExpired:
        if attempt < 6:
            wait = 5 * (attempt + 1)
            print(f"  timeout, retry in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
            return fetch_page(query_file, cursor, attempt + 1)
        raise
    if r.returncode != 0:
        err = (r.stderr or "") + (r.stdout or "")
        if any(sig in err for sig in RETRYABLE) and attempt < 6:
            wait = 5 * (attempt + 1)
            first_line = err.splitlines()[0][:150] if err.splitlines() else "err"
            print(f"  retry in {wait}s (attempt {attempt + 1}): {first_line}")
            time.sleep(wait)
            return fetch_page(query_file, cursor, attempt + 1)
        raise RuntimeError(f"gh exited {r.returncode}: {err[:400]}")
    return json.loads(r.stdout)


def read_last_record(data_path: Path) -> tuple[str | None, str | None]:
    if not data_path.exists() or data_path.stat().st_size == 0:
        return None, None
    with data_path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        read_back = min(size, 8192)
        f.seek(size - read_back)
        tail = f.read()
    lines = [ln for ln in tail.splitlines() if ln.strip()]
    if not lines:
        return None, None
    last = json.loads(lines[-1])
    return last["node"]["login"], last["starredAt"]


def run_normal(query_file: Path, data_path: Path, ck_path: Path) -> None:
    ck = load_checkpoint(ck_path)
    print(f"resuming: pages={ck['pages']} total={ck['total']} "
          f"cursor={'SET' if ck['cursor'] else 'NULL'}")
    cursor = ck["cursor"]
    pages = ck["pages"]
    total = ck["total"]
    has_next = True
    last_save = time.time()
    t0 = time.time()
    with data_path.open("a", encoding="utf-8") as fout:
        while has_next:
            try:
                resp = fetch_page(query_file, cursor)
            except Exception as exc:
                print(f"fatal at page {pages}: {exc}")
                save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                          "total": total,
                                          "started_at": ck.get("started_at", t0)})
                return
            if "errors" in resp:
                print(f"graphql errors: {json.dumps(resp['errors'])[:400]}")
                save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                          "total": total,
                                          "started_at": ck.get("started_at", t0)})
                return
            sg = resp["data"]["repository"]["stargazers"]
            for edge in sg["edges"]:
                fout.write(json.dumps(edge) + "\n")
            total += len(sg["edges"])
            cursor = sg["pageInfo"]["endCursor"]
            has_next = sg["pageInfo"]["hasNextPage"]
            pages += 1
            if pages == 1:
                print(f"totalCount={sg['totalCount']}")
            now = time.time()
            if pages % 10 == 0 or now - last_save > 30:
                fout.flush()
                os.fsync(fout.fileno())
                save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                          "total": total,
                                          "started_at": ck.get("started_at", t0)})
                last_save = now
            if pages % 50 == 0:
                rl = resp["data"]["rateLimit"]
                elapsed = now - t0
                rate = total / max(1, elapsed)
                eta = (sg["totalCount"] - total) / max(1, rate)
                print(f"pages={pages} total={total}/{sg['totalCount']} "
                      f"rl={rl['remaining']} elapsed={elapsed:.0f}s "
                      f"rate={rate:.1f}/s eta={eta:.0f}s")
            if pages > 1200:
                print("safety stop at 1200 pages")
                break
    save_checkpoint(ck_path, {"cursor": cursor, "pages": pages, "total": total,
                              "started_at": ck.get("started_at", t0)})
    print(f"DONE pages={pages} total={total} elapsed={time.time() - t0:.0f}s")


def run_resume_from_last(query_file: Path, data_path: Path, ck_path: Path) -> None:
    last_login, last_ts = read_last_record(data_path)
    if not last_login:
        print("data file empty or missing — use default resume or --restart")
        return
    print(f"resume-from-last: seeking past ({last_login!r}, {last_ts}) in the stream")
    cursor = None
    has_next = True
    pages = 0
    existing = sum(1 for _ in data_path.open("r", encoding="utf-8"))
    print(f"existing data lines: {existing}")
    writing = False
    new_written = 0
    total_count = 0
    t0 = time.time()
    with data_path.open("a", encoding="utf-8") as fout:
        while has_next:
            try:
                resp = fetch_page(query_file, cursor)
            except Exception as exc:
                print(f"fatal at page {pages}: {exc}")
                return
            if "errors" in resp:
                print(f"graphql errors: {json.dumps(resp['errors'])[:400]}")
                return
            sg = resp["data"]["repository"]["stargazers"]
            total_count = sg["totalCount"]
            for edge in sg["edges"]:
                if writing:
                    fout.write(json.dumps(edge) + "\n")
                    new_written += 1
                else:
                    if (edge["node"]["login"] == last_login
                            and edge["starredAt"] == last_ts):
                        writing = True
                        print("found anchor at this page; writing from next edge")
            cursor = sg["pageInfo"]["endCursor"]
            has_next = sg["pageInfo"]["hasNextPage"]
            pages += 1
            if pages % 10 == 0:
                fout.flush()
                os.fsync(fout.fileno())
            if pages % 50 == 0:
                rl = resp["data"]["rateLimit"]
                state = "WRITING" if writing else "seeking"
                print(f"pages={pages} state={state} new_written={new_written} "
                      f"rl={rl['remaining']} elapsed={time.time() - t0:.0f}s")
            if pages > 1200:
                print("safety stop at 1200 pages")
                break
    if not writing:
        print(f"WARNING: walked {pages} pages, never found anchor. "
              f"Nothing appended. Data file may be from a different repo.")
    else:
        final_total = existing + new_written
        print(f"DONE resume-from-last: new_written={new_written} "
              f"elapsed={time.time() - t0:.0f}s final_total={final_total}/{total_count}")
        save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                  "total": final_total,
                                  "started_at": time.time()})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="thedotmack")
    ap.add_argument("--repo", default="claude-mem")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--restart", action="store_true",
                    help="wipe data + checkpoint and start fresh")
    ap.add_argument("--resume-from-last", action="store_true",
                    help="ignore checkpoint; anchor-resume off last record in the data file")
    ap.add_argument("--status", action="store_true",
                    help="print progress without fetching")
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.output_dir / "stars-graphql.jsonl"
    ck_path = args.output_dir / "checkpoint.json"

    query_body = QUERY_TEMPLATE % {"owner": args.owner, "repo": args.repo}
    tmp_dir = Path(tempfile.gettempdir())
    query_file = tmp_dir / f"stargazers_{args.owner}_{args.repo}.graphql"
    query_file.write_text(query_body)

    if args.restart:
        print("wiping data + checkpoint")
        if data_path.exists():
            data_path.unlink()
        if ck_path.exists():
            ck_path.unlink()

    if args.status:
        ck = load_checkpoint(ck_path)
        lines = sum(1 for _ in data_path.open("r", encoding="utf-8")) if data_path.exists() else 0
        last_login, last_ts = read_last_record(data_path)
        print(f"checkpoint: pages={ck['pages']} total={ck['total']} "
              f"cursor={'SET' if ck['cursor'] else 'NULL'}")
        print(f"data file lines: {lines}")
        if last_login:
            print(f"last record: {last_login} @ {last_ts}")
        return 0

    if args.resume_from_last:
        run_resume_from_last(query_file, data_path, ck_path)
    else:
        run_normal(query_file, data_path, ck_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
