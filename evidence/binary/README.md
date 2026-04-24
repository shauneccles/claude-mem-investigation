# Binary review — Mach-O `plugin/scripts/claude-mem`

Backs [`../../REPORT.md`](../../REPORT.md) §2 Priority 2.

**File:** `plugin/scripts/claude-mem` in the upstream repo at commit `8ace1d9c`.
**Type:** Mach-O 64-bit arm64 executable, 63,412,576 bytes.
**Compiled:** 2026-02-23 (commit `c2c3e306`, "chore: bump version to 10.3.2"). Not rebuilt since.
**Hashes:** see [`../sha256sums.txt`](../sha256sums.txt).

## Verdict

The extracted JavaScript bundle is **clean** of:

- Exfil domains (no references beyond the whitelist in the TypeScript source).
- Hardcoded bearer tokens, API keys, or credentials.
- `crypto.subtle`, `createCipheriv`, `createSign` — no cryptographic operations.
- `process.env.USER` / `os.hostname()` / literal-string gating — no user or hostname-targeted logic.
- Date-gated code paths.
- Obfuscated binary blobs beyond the expected Bun runtime bytecode.

`eval(` in the bundle resolves to `$EvalError = require_eval()` (an error class). `new Function(` is Ajv's JSON-schema validator compilation. `dub.sh/security-redirect` is Express's upstream warning URL. `0.0.0.0` appears twice — both in a validation error message listing it as a valid example, not a default.

## Mach-O segment layout

| segment | file offset | file size | notes |
|---|---|---|---|
| `__PAGEZERO` | 0 | 0 | |
| `__TEXT` | 0 | 58,195,968 | Includes `__text` 49 MB JSC bytecode, `__cstring` 3.3 MB |
| `__DATA_CONST` | 58,195,968 | 1,196,032 | |
| `__DATA` | 59,392,000 | 180,224 | |
| `__DATA_DIRTY` | 59,572,224 | 16,384 | |
| **`__BUN`** | **59,588,608** | **3,112,960** | Single section `__BUN.__bun`, 3,098,213 bytes — the embedded JS bundle |
| `__LINKEDIT` | 62,701,568 | 711,008 | |

## Rebuild policy and runtime path

See [`rebuild-policy.md`](rebuild-policy.md) for the CI/release-path check.

Short version: the committed Mach-O is stale and not rebuilt by GitHub Actions, but the normal hook and CLI paths appear to run `worker-service.cjs` through `bun-runner.js`, not this native binary. The published npm package also excludes `plugin/scripts/claude-mem`. This makes the stale Mach-O a distribution-hygiene issue rather than evidence that macOS users normally receive a different runtime.

## Bun bundle extraction

```bash
# Reproduce the extraction:
python3 -c '
import sys
with open("plugin/scripts/claude-mem","rb") as f: data = f.read()
bundle = data[59588608:59588608+3098213]
open("bun-section.bin","wb").write(bundle)
import hashlib
print(hashlib.sha256(bundle).hexdigest())
'
# → fd189159fc07898ec428524721702ec2712dcb0c92471fd0f09c1c69aa367829
```

The section starts with Bun's trailer header: `]F/\0\0\0\0\0\0/$bunfs/root/claude-mem\0// @bun\n var __create = Object.create;…` — standard single-file executable format, virtual-FS root `/$bunfs/root/claude-mem`.

## External URLs in the extracted bundle

See [`bun-urls.txt`](bun-urls.txt) for the full list (27 URLs). Categories:

- **Localhost / worker API** (4): `http://localhost:37777/api/{context/recent,context/timeline,search/by-type,search/observations}` — documentation strings embedded in source.
- **Approved external APIs** (2): `https://generativelanguage.googleapis.com/v1/models`, `https://openrouter.ai/api/v1/chat/completions`.
- **Project surface** (3): GitHub repo, Discord invite, docs site.
- **JSON-schema drafts + npm-package reference URLs** (rest): Express's `connect`, `iconv-lite`, `ajv-validator`, `feross.org/opensource`, `git.io/debug_fd`.

Note: `api.telegram.org`, `ANTHROPIC_BASE_URL`, and `docs.claude-mem.ai/usage/gemini-provider` are present in the current `worker-service.cjs` (HEAD) but **not** in the Mach-O binary — those features were added after the binary was compiled.

## Binary-vs-source staleness

Features present in HEAD TypeScript source but **not** in the committed Mach-O binary (which dates from 2026-02-23):

| feature | source file | introduced |
|---|---|---|
| Read-hook timeline injection | `src/cli/handlers/file-context.ts` | 2026-03-18 |
| `ANTHROPIC_BASE_URL` override | `src/shared/EnvManager.ts` | 2026-04-09 |
| `TelegramNotifier` | `src/services/integrations/TelegramNotifier.ts` | 2026-04-22 |

No `.github/workflows/*.yml` rebuilds the binary. The normal hook and CLI paths appear to run `worker-service.cjs`, not this stale Mach-O; see [`rebuild-policy.md`](rebuild-policy.md).
