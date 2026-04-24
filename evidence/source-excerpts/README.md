# Source excerpts — verbatim source behind the load-bearing claims

Each file in this directory is a permalinked snippet from the upstream repo at `8ace1d9c84e5ce455356cf852c370ea625e3b1d1`. Backs [`../../REPORT.md`](../../REPORT.md) §2 Priority 4 and Addendum §6.C–D.

| excerpt | claim it supports |
|---|---|
| [`read-hook-rewrite.md`](read-hook-rewrite.md) | "Silently rewrites `Read` tool calls to `limit: 1` and injects a timeline as `additionalContext`." |
| [`handle-import.md`](handle-import.md) | "`POST /api/import` accepts arbitrary observations with no provenance check." |
| [`middleware.md`](middleware.md) | "No auth of any kind — only a shared 300 req/min rate limit." |
| [`env-manager-override.md`](env-manager-override.md) | "`ANTHROPIC_BASE_URL` override allows the secondary subprocess API endpoint to be redirected." |

Each file contains:
- The verbatim source snippet.
- A pinned permalink to the line in the upstream repo.
- A one-paragraph explanation of what the code does and why it matters.
