# KeyzBoard — Macro Catalog

Defined in `tools/generate_layout.py` (`MACROS`). Slot numbers match the
`macro` array in the `.vil`. Encoded for a **Latin American (es-419) host
layout**: punctuation is emitted as explicit scancode taps, never as raw
ASCII — Vial macros otherwise assume a US layout and would type wrong
characters on your host.

| Slot | Macro |
|-----:|-------|
| 0 | `git status` |
| 1 | `git diff` |
| 2 | `git log --oneline -10` |
| 3 | `git pull --rebase` |
| 4 | `git push` |
| 5 | `git add -A` |
| 6 | `git commit -m "" (cursor inside)` |
| 7 | `git push -u origin HEAD` |
| 8 | `git reflog` |
| 9 | `git stash` |
| 10 | `AI: explain this code` |
| 11 | `AI: refactor` |
| 12 | `AI: write tests` |
| 13 | `AI: TL;DR` |
| 14 | `snippet ()` |
| 15 | `snippet []` |
| 16 | `snippet {}` |
| 17 | `snippet ""` |
| 18 | `snippet ''` |

## Encoding rules

- Letters, digits, space, `,`, `.` → plain text (identical on US and es-419).
- `-` → tap of the US `/` scancode; `'` → tap of the US `-` scancode (es-419
  positions).
- `"`, `;`, `(`, `)` → shifted taps per es-419.
- Accented vowels (`ó` in *código*) → dead acute + vowel with a 20 ms delay
  so the OS composition engine catches the vowel.

## Known limitations (documented, not bugs)

- `<` and `>` **do not exist** on an ANSI es-419 layout (they live on the ISO
  key next to left Shift). No macro can type them. Workarounds: editor
  snippets, or an XKB tweak on Linux later.
- Code fences (triple backtick) are intentionally absent: the backtick is a
  dead-key composition whose position differs between XKB `latam` and Windows
  `KBDLA`. Add a per-OS variant once confirmed on both hosts.
- Terminal macros (`git ...` + Enter) fire wherever focus is. Assume your
  alacritty window, or you will type `git status` into your editor.
- `}` and `[` `]` use AltGr/shifted scancodes verified against XKB `latam`;
  if any symbol lands wrong on Windows es-MX, tell me which — it is a
  one-line fix and regenerate.
