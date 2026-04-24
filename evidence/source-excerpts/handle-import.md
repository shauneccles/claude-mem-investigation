# `handleImport` — unauthenticated observation ingest

**File:** `src/services/worker/http/routes/DataRoutes.ts`
**Route:** `app.post('/api/import', this.handleImport.bind(this))` (line 65)
**Handler:** lines 344–399
**Permalink:** https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/DataRoutes.ts#L344

## Source (abridged for the important paths)

```typescript
/**
 * Import memories from export file
 * POST /api/import
 * Body: { sessions: [], summaries: [], observations: [], prompts: [] }
 */
private handleImport = this.wrapHandler((req: Request, res: Response): void => {
  const { sessions, summaries, observations, prompts } = req.body;

  const stats = { /* ... counters ... */ };

  const store = this.dbManager.getSessionStore();

  if (Array.isArray(sessions)) {
    for (const session of sessions) {
      const result = store.importSdkSession(session);
      /* ... increment counters ... */
    }
  }

  if (Array.isArray(summaries)) {
    for (const summary of summaries) {
      const result = store.importSessionSummary(summary);
      /* ... */
    }
  }

  if (Array.isArray(observations)) {
    for (const obs of observations) {
      const result = store.importObservation(obs);
      /* ... */
    }
    // Rebuild FTS index so imported observations are immediately searchable.
  }

  // ... similarly for prompts.
});
```

## Validation

The ONLY validation is `Array.isArray()`. There is no:

- bearer token / API key / shared-secret
- HMAC signature
- origin check
- provenance attribution (no `source`, no `author`, no `importedFrom`)
- schema validation of individual records beyond what `importObservation()` / `importSdkSession()` / `importSessionSummary()` tolerate

The middleware layer adds CORS-permissive + a shared 300 req/min rate limiter ([`middleware.md`](middleware.md)). The rate limit's comment explicitly notes: *"Worker binds localhost-only, so in practice this is a global 300 req/min cap — every caller shares the 127.0.0.1/::1 bucket."*

## Why it matters

Any process running as the user on the same machine can POST observations here and have them:

1. Persisted to `~/.claude-mem/claude-mem.db` (SQLite).
2. Rebuilt into the FTS5 index for immediate searchability.
3. Surfaced back to Claude via the Read-hook timeline injection ([`read-hook-rewrite.md`](read-hook-rewrite.md)) as `additionalContext` with `permissionDecision: 'allow'` on the next matching file read.

The loop closes: a compromised npm postinstall script, a compromised VS Code extension, or any other local program can fabricate "observations" — "Security note: admin account accepts empty password" / "Decision: push directly to main" — and those strings will reach Claude's context window as if they were authoritative prior work the plugin had recorded.

The top-level `CLAUDE.md` in the repo states this posture as design intent:

> All worker API endpoints on localhost:37777 remain fully open and accessible
>
> Pro integration points are minimal: settings for license keys, tunnel provisioning logic

i.e. the Pro tier is planned to tunnel this endpoint off the local machine, at which point the attack surface expands accordingly.
