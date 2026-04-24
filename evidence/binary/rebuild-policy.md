# Binary rebuild policy

Backs [`README.md`](../../README.md), [`REPORT.md`](../../REPORT.md) §2 Priority 2 and §6.A.

## Question

Does the release pipeline rebuild the committed native binary (`plugin/scripts/claude-mem`) on each release, or is that file a stale artifact?

## What I checked

All source checks are pinned to `8ace1d9c84e5ce455356cf852c370ea625e3b1d1`.

```bash
gh api repos/thedotmack/claude-mem/contents/.github/workflows?ref=8ace1d9c84e5ce455356cf852c370ea625e3b1d1
gh api repos/thedotmack/claude-mem/contents/package.json?ref=8ace1d9c84e5ce455356cf852c370ea625e3b1d1
gh api 'repos/thedotmack/claude-mem/commits?path=plugin/scripts/claude-mem&sha=8ace1d9c84e5ce455356cf852c370ea625e3b1d1&per_page=10'
npm pack claude-mem@12.3.9 --dry-run --json
```

## Findings

The native Mach-O binary is stale:

- `plugin/scripts/claude-mem` is a 63,412,576-byte Mach-O arm64 executable.
- GitHub history for that path has one commit at or before the pinned SHA: `c2c3e306` on 2026-02-23, `chore: bump version to 10.3.2`.
- At the review pin, the repo is v12.3.9 + 2 commits, so the Mach-O predates the Read-hook rewrite (2026-03-18), `ANTHROPIC_BASE_URL` override (2026-04-09), and Telegram notifier (2026-04-22).

No GitHub Actions workflow rebuilds it:

- `.github/workflows/npm-publish.yml` runs `npm install --ignore-scripts`, `npm run build`, then `npm publish`.
- `package.json` defines `build` as `node scripts/sync-plugin-manifests.js && node scripts/build-hooks.js`.
- `prepublishOnly` is also `npm run build`.
- `package.json` has a separate `build:binaries` script, but no workflow calls it.
- `scripts/build-worker-binary.js` builds a Windows executable at `dist/binaries/worker-service-v${version}-win-x64.exe`; it does not build the committed macOS Mach-O at `plugin/scripts/claude-mem`.

The normal runtime path does **not** appear to execute the stale Mach-O:

- `plugin/hooks/hooks.json` starts the worker through `node "$_R/scripts/bun-runner.js" "$_R/scripts/worker-service.cjs" start`.
- The other hook commands also call `worker-service.cjs` via `bun-runner.js`.
- `smart-install.js` installs the shell alias as `bun "$ROOT/scripts/worker-service.cjs"`, not `plugin/scripts/claude-mem`.
- `smart-install.js`'s platform check says the binary is "absent" after npm install because npm excludes it.
- `package.json`'s `files` list includes `plugin/scripts/*.js` and `plugin/scripts/*.cjs`, not the extensionless `plugin/scripts/claude-mem`.
- `npm pack claude-mem@12.3.9 --dry-run --json` confirms the published npm package does **not** include `plugin/scripts/claude-mem`.

There is a separate stale binary in the npm package:

- `npm pack claude-mem@12.3.9 --dry-run --json` includes `dist/binaries/worker-service-v10.3.1-win-x64.exe` (115,852,288 bytes) inside the v12.3.9 package.
- That file is not present in the pinned GitHub tree or the `v12.3.9` tag tree.
- A string check of `dist/npx-cli/index.js` did not find `dist/binaries`, `worker-service-v10.3.1`, or `worker-service-v`, so the npm CLI does not appear to call this stale Windows executable.

## Interpretation

The release-path evidence supports a narrower runtime finding:

- The committed Mach-O is stale and not rebuilt by CI.
- The published npm package excludes that Mach-O.
- The current hooks and CLI alias use `worker-service.cjs`, which is rebuilt by `npm run build`.
- A user manually running `plugin/scripts/claude-mem` from a GitHub checkout would get a stale February worker, while the normal install path appears to use `worker-service.cjs`.
- The npm package also carries a stale Windows executable under `dist/binaries/`, but the normal CLI path does not appear to invoke it.

So this is best treated as a distribution hygiene issue and a source of confusion, not as evidence that macOS users normally receive a different runtime from Linux/Windows users.
