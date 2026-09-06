# KeyzBoard

Custom layout for a 40% (4x12 ortholinear) Vial keyboard, designed for a
bilingual developer (Spanish es-419 host layout, code-heavy work, Linux
Arch/Qtile + Windows).

## Structure

- `layout/keyzboard.vil` — the generated layout. **Load this into Vial.**
- `currentLayout.vil` — untouched factory snapshot (your safety net).
- `tools/generate_layout.py` — source of truth. Layer maps and the macro
  catalog live here; the `.vil` and docs are generated output.
- `docs/layout.md` — visual layer maps (characters shown = es-419 output).
- `docs/macros.md` — macro catalog, encoding rules, known limitations.

## Workflow

1. Edit `tools/generate_layout.py` (layers and/or `MACROS`).
2. Regenerate and validate:
   ```
   python3 tools/generate_layout.py --check   # validate only
   python3 tools/generate_layout.py           # write layout/ + docs/
   ```
3. Open [Vial](https://get.vial.today/) (desktop app or Chrome, on Windows —
   WSL2 cannot see HID devices).
4. `File > Load saved layout` → `layout/keyzboard.vil`. Changes apply live,
   no flashing.
5. Test, iterate. Keep the factory file untouched as recovery.

## Layer system

| Layer | Trigger | Purpose |
|------:|---------|---------|
| 0 | — | QWERTY + home-row mods; `´`/`ñ` on thumb columns |
| 1 | hold Space | Numpad digits + full code symbols (es-419 encoded) |
| 2 | hold bottom key / Enter tap-hold | git + AI macros, snippets, OS keys |
| 3 | hold bottom-left | F-keys, nav, clipboard, mouse |
| 4 | hold bottom key | media, brightness, RGB, `TO(n)`, `QK_BOOT` corner |

Macros are encoded scancode-by-scancode for the es-419 host layout: Vial
macro text otherwise assumes US and would type wrong punctuation. See
`docs/macros.md` for the details and the `<`/`>` ANSI limitation.
