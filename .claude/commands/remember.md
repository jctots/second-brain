Save context from the current conversation to persistent storage. Execute in order:

1. **Scan for memory events** — look back through this conversation for 🧠 `[memory event]` markers. If none found, skip to step 3. For each event, identify the target file and write using Edit (never Write):
   - Project state change or open question → `_memory.md`
   - Key decision → `decisions.md` (prepend); if missing, add to "Key decisions" in `_memory.md`
   - Profile fact or behavioral observation → `_self/about.md`
   - Behavioral correction or feedback → `_self/rules.md`

   Only add if not already captured. If a target `_memory.md` doesn't exist, create it from template.

   **Memory filter:** `_memory.md` captures current state, open questions, and active constraints — not implementation documentation. If a candidate describes *how something works* rather than *what has changed or what is still open*, skip it.

2. **Scan for task events** — look back through this conversation for ✅ `[task event]` markers. If none found, skip to step 3. Route each task to the relevant project's `roadmap.md` (if it exists) or the "Next actions" section of `_memory.md`.

3. **Emit processed markers** — output on separate lines:
   - `🔁 [remember processed]` always
   - `📋 [task processed]` only if ✅ task events were found and processed

4. Briefly confirm what was written and what was skipped.
