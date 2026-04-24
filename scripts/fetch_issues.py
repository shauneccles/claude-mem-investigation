"""
Resumable issue-tracker fetcher for any public GitHub repo.

Paginates every issue via GitHub GraphQL v4 with the metadata most useful for
governance / software-quality reviews:

  - createdAt, closedAt
  - state, stateReason (COMPLETED / NOT_PLANNED / DUPLICATE / REOPENED)
  - locked, author.login, authorAssociation (OWNER / COLLABORATOR / CONTRIBUTOR / NONE)
  - labels (names)
  - comments count
  - title
  - optional body text (opt-in with --with-body to reduce bandwidth)

Writes one JSON edge per line to `issues-graphql.jsonl` alongside the script.
Checkpointed; safe to Ctrl-C and restart.

Auth: uses `gh` CLI (`gh auth login`). Required scope: `repo` (default). No
elevated scopes required.

Usage:
  python fetch_issues.py                                    # defaults to thedotmack/claude-mem
  python fetch_issues.py --owner OWNER --repo REPO          # any public repo
  python fetch_issues.py --owner nodejs --repo node         # for example
  python fetch_issues.py --with-body                        # also fetch body text (bigger file)
  python fetch_issues.py --restart                          # wipe data + checkpoint
  python fetch_issues.py --status                           # progress summary only
  python fetch_issues.py --resume-from-last                 # anchor-mode resume (no checkpoint needed)
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
RETRYABLE = ("HTTP 5", "timeout", "Bad gateway", "ETIMEDOUT",
             "ECONNRESET", "Resource limits", "abuse detection")


def build_query(owner: str, repo: str, with_body: bool) -> str:
    body_field = "body" if with_body else ""
    return f"""
query($cursor: String) {{
  rateLimit {{ cost remaining resetAt }}
  repository(owner: "{owner}", name: "{repo}") {{
    issues(first: 100, after: $cursor, orderBy: {{field: CREATED_AT, direction: ASC}}) {{
      pageInfo {{ hasNextPage endCursor }}
      totalCount
      nodes {{
        number
        title
        state
        stateReason
        locked
        createdAt
        closedAt
        updatedAt
        comments {{ totalCount }}
        labels(first: 20) {{ nodes {{ name }} }}
        author {{ login }}
        authorAssociation
        {body_field}
      }}
    }}
  }}
}}
"""


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
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, check=False)
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
            first = err.splitlines()[0][:150] if err.splitlines() else "err"
            print(f"  retry in {wait}s (attempt {attempt + 1}): {first}")
            time.sleep(wait)
            return fetch_page(query_file, cursor, attempt + 1)
        raise RuntimeError(f"gh exited {r.returncode}: {err[:400]}")
    return json.loads(r.stdout)


def flatten(node: dict) -> dict:
    """Flatten the GraphQL shape into a single-level JSON record we can jsonl."""
    return {
        "number": node["number"],
        "title": node.get("title"),
        "state": node.get("state"),
        "stateReason": node.get("stateReason"),
        "locked": node.get("locked"),
        "createdAt": node.get("createdAt"),
        "closedAt": node.get("closedAt"),
        "updatedAt": node.get("updatedAt"),
        "comments": node.get("comments", {}).get("totalCount", 0),
        "labels": [l["name"] for l in node.get("labels", {}).get("nodes", [])],
        "author": (node.get("author") or {}).get("login"),
        "authorAssociation": node.get("authorAssociation"),
        "body": node.get("body"),
    }


def read_last_number(data_path: Path) -> int | None:
    if not data_path.exists() or data_path.stat().st_size == 0:
        return None
    with data_path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 8192))
        tail = f.read()
    lines = [ln for ln in tail.splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])["number"]


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
            iss = resp["data"]["repository"]["issues"]
            for node in iss["nodes"]:
                fout.write(json.dumps(flatten(node)) + "\n")
            total += len(iss["nodes"])
            cursor = iss["pageInfo"]["endCursor"]
            has_next = iss["pageInfo"]["hasNextPage"]
            pages += 1
            if pages == 1:
                print(f"totalCount={iss['totalCount']}")
            now = time.time()
            if pages % 5 == 0 or now - last_save > 30:
                fout.flush()
                os.fsync(fout.fileno())
                save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                          "total": total,
                                          "started_at": ck.get("started_at", t0)})
                last_save = now
            if pages % 10 == 0:
                rl = resp["data"]["rateLimit"]
                elapsed = now - t0
                rate = total / max(1, elapsed)
                eta = (iss["totalCount"] - total) / max(1, rate)
                print(f"pages={pages} total={total}/{iss['totalCount']} "
                      f"rl={rl['remaining']} elapsed={elapsed:.0f}s eta={eta:.0f}s")
            if pages > 2000:
                print("safety stop at 2000 pages")
                break
    save_checkpoint(ck_path, {"cursor": cursor, "pages": pages, "total": total,
                              "started_at": ck.get("started_at", t0)})
    print(f"DONE pages={pages} total={total} elapsed={time.time() - t0:.0f}s")


def run_resume_from_last(query_file: Path, data_path: Path, ck_path: Path) -> None:
    last_n = read_last_number(data_path)
    if last_n is None:
        print("data file empty or missing — use default resume or --restart")
        return
    print(f"resume-from-last: seeking past issue #{last_n}")
    cursor = None
    has_next = True
    pages = 0
    existing = sum(1 for _ in data_path.open("r", encoding="utf-8"))
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
            iss = resp["data"]["repository"]["issues"]
            total_count = iss["totalCount"]
            for node in iss["nodes"]:
                if writing:
                    fout.write(json.dumps(flatten(node)) + "\n")
                    new_written += 1
                elif node["number"] == last_n:
                    writing = True
            cursor = iss["pageInfo"]["endCursor"]
            has_next = iss["pageInfo"]["hasNextPage"]
            pages += 1
            if pages % 10 == 0:
                fout.flush()
                os.fsync(fout.fileno())
            if pages > 2000:
                break
    if not writing:
        print(f"WARNING: walked {pages} pages, never saw #{last_n}. Nothing appended.")
    else:
        final = existing + new_written
        print(f"DONE new_written={new_written} elapsed={time.time() - t0:.0f}s "
              f"final={final}/{total_count}")
        save_checkpoint(ck_path, {"cursor": cursor, "pages": pages,
                                  "total": final, "started_at": time.time()})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="thedotmack")
    ap.add_argument("--repo", default="claude-mem")
    ap.add_argument("--with-body", action="store_true",
                    help="also fetch issue body text (larger output)")
    ap.add_argument("--output-dir", type=Path, default=SCRIPT_DIR)
    ap.add_argument("--restart", action="store_true")
    ap.add_argument("--resume-from-last", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.output_dir / "issues-graphql.jsonl"
    ck_path = args.output_dir / "issues-checkpoint.json"

    query_body = build_query(args.owner, args.repo, args.with_body)
    tmp = Path(tempfile.gettempdir()) / f"issues_{args.owner}_{args.repo}.graphql"
    tmp.write_text(query_body)

    if args.restart:
        print("wiping issue data + checkpoint")
        if data_path.exists(): data_path.unlink()
        if ck_path.exists(): ck_path.unlink()

    if args.status:
        ck = load_checkpoint(ck_path)
        lines = sum(1 for _ in data_path.open("r", encoding="utf-8")) if data_path.exists() else 0
        last_n = read_last_number(data_path)
        print(f"checkpoint: pages={ck['pages']} total={ck['total']} "
              f"cursor={'SET' if ck['cursor'] else 'NULL'}")
        print(f"data lines: {lines}")
        if last_n: print(f"last issue: #{last_n}")
        return 0

    if args.resume_from_last:
        run_resume_from_last(tmp, data_path, ck_path)
    else:
        run_normal(tmp, data_path, ck_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
