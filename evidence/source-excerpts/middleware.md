# Worker middleware — no auth, rate limit only

**File:** `src/services/worker/http/middleware.ts`
**Permalink:** https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/middleware.ts

## The explicit comment

```typescript
// Simple in-memory rate limiter (#1935).
// Worker binds localhost-only, so in practice this is a global 300 req/min
// cap — every caller shares the 127.0.0.1/::1 bucket.
const requestCounts = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 300;
```

## What else the middleware does

- Request / response logging.
- CORS (permissive — allows requests with no Origin header, i.e. anything local).
- JSON body parsing.
- Static file serving (the in-browser viewer at `http://localhost:37777`).

## What the middleware does NOT do

- No bearer-token check.
- No API-key header check.
- No cookie / session validation.
- No HMAC signature.
- No origin whitelist.
- No per-caller identity — the rate-limit bucket is shared across the loopback address.

## Why it matters

The design posture is stated verbatim in the repo's top-level `CLAUDE.md`: *"All worker API endpoints on localhost:37777 remain fully open and accessible."* That's not an oversight. It's the architecture. The rate limit's comment acknowledges the consequence: the 300 req/min cap is global across all callers sharing the loopback address, so a misbehaving local process can either consume the budget or — by staying under it — inject freely.

The `CLAUDE_MEM_WORKER_HOST` setting is user-configurable and [the validator explicitly accepts `0.0.0.0`](https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/services/worker/http/routes/SettingsRoutes.ts#L286-L292) with no warning, so a user can turn this into a LAN-exposed unauthenticated API by flipping one setting. Combined with the "tunnel provisioning logic" mentioned in the Pro Features design, the progression from localhost-only to remote-accessible is a planned one.
