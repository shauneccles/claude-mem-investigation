# `ANTHROPIC_BASE_URL` override

**File:** `src/shared/EnvManager.ts`
**Introduced:** 2026-04-09 (commit `07be61cf`, "feat: support ANTHROPIC_BASE_URL in EnvManager (#1627)", by external contributor WuTao `<taobaorun@gmail.com>`, commit messages tagged "Generated with AI — Co-Authored-By: AI Partner")
**Permalink:** https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/shared/EnvManager.ts

## The diff that introduced it

```typescript
export interface ClaudeMemEnv {
  ANTHROPIC_API_KEY?: string;
+ ANTHROPIC_BASE_URL?: string;
  GEMINI_API_KEY?: string;
  OPENROUTER_API_KEY?: string;
}
```

```typescript
// In buildIsolatedEnv():
+ // Override ANTHROPIC_BASE_URL from .env if configured
+ // This ensures the SDK subprocess uses a stable API endpoint instead of
+ // inheriting a dynamic local proxy port that may become stale
+ if (credentials.ANTHROPIC_BASE_URL) {
+   isolatedEnv.ANTHROPIC_BASE_URL = credentials.ANTHROPIC_BASE_URL;
+ }
```

## What this does

`buildIsolatedEnv()` is the function that constructs the environment passed to the secondary Claude subprocess that claude-mem spawns via the Agent SDK for ambient observation-classification. Prior to this commit, the subprocess inherited its Anthropic credentials from the parent process env with `ANTHROPIC_API_KEY` and `CLAUDECODE` stripped, and no `ANTHROPIC_BASE_URL` handling.

After this commit, if `~/.claude-mem/.env` contains an `ANTHROPIC_BASE_URL` value, it is copied into the subprocess environment. That value overrides where the subprocess sends its Anthropic API traffic.

## Why it matters

Any local process that can write to `~/.claude-mem/.env` — any process running as the user, including the observation-import primitive at `POST /api/import` combined with the worker's `PUT /api/settings` endpoint — can redirect the subprocess's API traffic to an attacker-controlled endpoint. The subprocess's inputs include the full raw text of every file Claude reads, every tool input, every tool output, because that is exactly what the plugin feeds the subprocess to classify.

The PR author (a community contributor) framed it as a convenience: *"ensures the SDK subprocess uses a stable API endpoint instead of inheriting a dynamic local proxy port that may become stale."* The mechanism is the same either way: the plugin's secondary subprocess, which sees everything Claude sees, now has its destination URL configurable from a file any local process can modify.

Combined with the [unauthenticated `POST /api/import`](handle-import.md) and the absent secrets redaction in the observation pipeline, this creates a possible tool-chained exposure path that wasn't available in the bundle embedded in the stale Mach-O binary (compiled 2026-02-23, three weeks before this commit landed).
