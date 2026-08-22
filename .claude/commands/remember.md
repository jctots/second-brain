Save context from the current conversation to persistent storage.

This command is deliberately cheap: one pass over the conversation, a few in-place
edits, nothing else. Two things it does **not** do — task sync (`/maintain` option 2)
and memory consolidation (`/maintain` option 5). Both are periodic, not per-save.

1. **Judgment pass** — one read of the conversation; decide what is worth persisting.
   Read the active project's `_memory.md` only if it was not injected this session.
   `_self/about.md` and `_self/corrections.md` are injected on turn one — never re-read
   them; read `_self/reflection.md` only if this conversation contains user-side
   self-observations.

   Route by target:
   - project state, decisions with rationale, open questions, next actions → `_memory.md`
   - profile facts → `_self/about.md`
   - behavioural corrections, feedback rules, repeated failure modes → `_self/corrections.md`
   - user-side self-awareness with no Claude action → `_self/reflection.md`
   - generalizable beyond this project → emit the missed `🗂️ [distill event]:` marker
     now; `/distill` writes it, not this command

   🧠/👤/🗂️ markers are signals, not the authoritative source. Unmarked content that
   meets the bar still gets saved; a marker for something already recorded does not.

2. **Write** — Edit each target in place. Skip any file with nothing new.

   `_memory.md` sections:
   - `## Snapshot` — overwrite with one current-state line.
   - `## Working Context` — **replace** with one paragraph on this session. Prior
     sessions live in git history, not here.
   - `## Next Actions` — merge. Preserve any `[#N]` suffix verbatim; never invent one.
     For items completed this session: delete the item if it has no `[#N]`; prefix it
     with `✅ ` if it does, leaving it for `/maintain` option 2 to close in Vikunja
     and remove.
   - `## Open questions` — merge; delete resolved.
   - `## Key decisions` — if `decisions/` exists, add the decision as a row in
     `decisions/index.md` (newest-first, D# incremented from the top row) and keep
     `## Key decisions` as a pointer line only. If not, append inline; once past
     ~8 bullets, say so once and stop — `/maintain` option 5 does the split.

   `_self/` files: merge into existing bullets, supersede in place, add only what has
   no existing home.

3. **Report** — one line per file written or skipped, then, only for what was written:
   - `🔁 [remember processed]` if `_memory.md` was written
   - `🪪 [profile processed]` if any `_self/` file was written
   - `📋 [task processed]` if task content was captured

   Then run `wc -c` on the `_memory.md` just written. Stay silent below 9,700 bytes.
   At or above it, emit one line: `⚠️ {path} at {n} bytes — near the 10,000 hook cap,
   run /maintain option 5`. This is the only budget check here, and it fires only when
   the file is about to stop injecting entirely. The advisory 9,000-char target and its
   WARN threshold belong to `/maintain` option 5 and CI — do not run
   `test_hook_budget.py` from this command.

   No handover block — `inject-context-memory.py` loads `_memory.md`, including
   `## Next Actions`, on the next session's first turn.
