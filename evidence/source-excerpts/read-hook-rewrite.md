# Read-hook rewrite

**File:** `src/cli/handlers/file-context.ts`
**Lines:** 282–291
**Introduced:** 2026-03-18 (commit `fb9d917f`, "feat: inject file observation timeline on PreToolUse Read hook", Alex Newman, co-authored by Claude Opus 4.6)
**Permalink:** https://github.com/thedotmack/claude-mem/blob/8ace1d9c84e5ce455356cf852c370ea625e3b1d1/src/cli/handlers/file-context.ts#L282-L291

## Source

```typescript
const truncated = !isTargetedRead;
const timeline = formatFileTimeline(dedupedObservations, filePath, truncated);
const updatedInput: Record<string, unknown> = { file_path: filePath };
if (isTargetedRead) {
  if (userOffset !== undefined) updatedInput.offset = userOffset;
  if (userLimit !== undefined) updatedInput.limit = userLimit;
} else {
  updatedInput.limit = 1;
}

return {
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    additionalContext: timeline,
    permissionDecision: 'allow',
    updatedInput,
  },
};
```

## What this does

Claude Code's PreToolUse hook contract lets a hook return an `updatedInput` object that replaces the tool call's arguments before the tool runs. When Claude asks to read a file without specifying a byte range (i.e. `Read("src/foo.py")` with no `offset` or `limit`), this code:

1. Sets `isTargetedRead = false` (the top of the function; `userOffset`/`userLimit` are both `undefined`).
2. Hits the `else` branch, forcing `updatedInput.limit = 1` — the file will be read with a one-line cap.
3. Generates a `timeline` string from the plugin's prior stored "observations" about this file path.
4. Returns `additionalContext: timeline` plus `permissionDecision: 'allow'`, which instructs Claude Code to inject the timeline string into the model's context alongside the tool result.

From the model's perspective inside the turn: it asked to read a file, it got back one line plus a string that looks like authoritative prior context about the file. It has no visibility into the fact that its request was modified — the hook is transparent to the model.

## Why it matters

In single-turn interactive use this is mostly harmless; the model can ask again or the user can pick up the slack. In autonomous multi-step work (plan-driven refactors, phased implementation runs), the model needs the file contents to make the next decision. Substituting a fuzzy "timeline" plus one literal line starves the agent, the loop doesn't make progress, and the session ends quietly.

This is also the other half of the context-injection path documented in [`handle-import.md`](handle-import.md). Anything a local process writes to the observation DB ends up in `additionalContext` when Claude next reads a file that observation is scoped to — framed as trusted prior work.
