#!/usr/bin/env python3
"""Generate the KeyzBoard Vial layout (.vil) and documentation.

Source of truth for the custom layout. Reads the factory snapshot
(``currentLayout.vil``) only to preserve hardware-bound fields (uid,
protocols, encoder layout), then replaces layers and macros.

Usage:
    python3 tools/generate_layout.py            # write layout/ + docs/
    python3 tools/generate_layout.py --check    # validate only, write nothing

Everything is expressed in QMK keycodes (legacy names, exactly the style the
factory Vial export uses). The host OS layout is Latin American Spanish
(es-419 / es-MX); the ASCII maps show the characters that layout produces.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FACTORY = REPO / "currentLayout.vil"
OUT_VIL = REPO / "layout" / "keyzboard.vil"
OUT_LAYOUT_MD = REPO / "docs" / "layout.md"
OUT_MACROS_MD = REPO / "docs" / "macros.md"

# ---------------------------------------------------------------------------
# HID usage IDs used by the macro encoder (internal, numeric).
# ---------------------------------------------------------------------------

KC = {
    "A": 0x04, "B": 0x05, "C": 0x06, "D": 0x07, "E": 0x08, "F": 0x09,
    "G": 0x0A, "H": 0x0B, "I": 0x0C, "J": 0x0D, "K": 0x0E, "L": 0x0F,
    "M": 0x10, "N": 0x11, "O": 0x12, "P": 0x13, "Q": 0x14, "R": 0x15,
    "S": 0x16, "T": 0x17, "U": 0x18, "V": 0x19, "W": 0x1A, "X": 0x1B,
    "Y": 0x1C, "Z": 0x1D,
    "1": 0x1E, "2": 0x1F, "3": 0x20, "4": 0x21, "5": 0x22,
    "6": 0x23, "7": 0x24, "8": 0x25, "9": 0x26, "0": 0x27,
    "ENTER": 0x58, "SPACE": 0x2C,
    "MINUS": 0x2D, "LBRACKET": 0x2F, "RBRACKET": 0x30,
    "COMMA": 0x36, "SLASH": 0x38,
    "LEFT": 0x50, "UP": 0x52,
    "LSFT": 0xE1,
}

SS_PREFIX = 0x01
SS_TAP, SS_DOWN, SS_UP, SS_DELAY = 0x01, 0x02, 0x03, 0x04

# Accented vowels: dead acute (US '[' scancode) + vowel, with a small delay
# so the OS composition engine does not miss the vowel.
DEAD_ACUTE = "LBRACKET"
ACCENTS = {"á": "A", "é": "E", "í": "I", "ó": "O", "ú": "U",
           "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}


def _tap(kc: int) -> bytes:
    return bytes([SS_PREFIX, SS_TAP, 0x00, kc])


def _down(kc: int) -> bytes:
    return bytes([SS_PREFIX, SS_DOWN, 0x00, kc])


def _up(kc: int) -> bytes:
    return bytes([SS_PREFIX, SS_UP, 0x00, kc])


def _delay(ms: int) -> bytes:
    return bytes([SS_PREFIX, SS_DELAY, ms])


def encode_macro(text: str) -> str:
    """Encode macro text into Vial's byte-string format, LatAm-aware.

    Layout-stable characters (letters, digits, space, comma, dot) are stored
    as plain text. Everything else is encoded as explicit tap sequences so
    the characters survive the es-419 host layout.
    """
    out = bytearray()
    for ch in text:
        if ch.isalnum() and ch.isascii() or ch in " ,.":
            out.extend(ch.encode("latin-1"))
        elif ch == ";":
            out.extend(_down(KC["LSFT"]))
            out.extend(_tap(KC["COMMA"]))
            out.extend(_up(KC["LSFT"]))
        elif ch == '"':
            out.extend(_down(KC["LSFT"]))
            out.extend(_tap(KC["2"]))
            out.extend(_up(KC["LSFT"]))
        elif ch in ACCENTS:
            out.extend(_tap(KC[DEAD_ACUTE]))
            out.extend(_delay(20))
            out.extend(_tap(KC[ACCENTS[ch]]))
        elif ch == "-":
            out.extend(_tap(KC["SLASH"]))
        elif ch == "'":
            out.extend(_tap(KC["MINUS"]))
        elif ch == "(":
            out.extend(_down(KC["LSFT"]))
            out.extend(_tap(KC["8"]))
            out.extend(_up(KC["LSFT"]))
        elif ch == ")":
            out.extend(_down(KC["LSFT"]))
            out.extend(_tap(KC["9"]))
            out.extend(_up(KC["LSFT"]))
        elif ch == ":":
            out.extend(_down(KC["LSFT"]))
            out.extend(_tap(0x37))  # KC_DOT
            out.extend(_up(KC["LSFT"]))
        else:
            raise ValueError(
                f"Character {ch!r} cannot be typed reliably on an ANSI "
                f"es-419 layout; rewrite the macro without it."
            )
    return out.decode("latin-1")


ENTER = _tap(KC["ENTER"])
LEFT = _tap(KC["LEFT"])

# Bracket sequences for es-419 (explicit AltGr / shift scancode taps — these
# characters are not representable as plain macro text).
RALT_DOWN, RALT_UP = _down(0xE6), _up(0xE6)
LSFT_DOWN, LSFT_UP = _down(0xE1), _up(0xE1)
LBRACK = RALT_DOWN + _tap(0x25) + RALT_UP          # AltGr+8 = [
RBRACK = RALT_DOWN + _tap(0x26) + RALT_UP          # AltGr+9 = ]
LBRACE = _tap(0x34)                                # US ' scancode base = {
RBRACE = LSFT_DOWN + _tap(0x31) + LSFT_UP          # Shift+US \ = }

# ---------------------------------------------------------------------------
# Macro catalog. Slot numbers match the .vil `macro` array.
# ---------------------------------------------------------------------------


def m(*parts: bytes | str) -> str:
    """Concatenate macro parts, encoding every string through encode_macro."""
    out = bytearray()
    for p in parts:
        if isinstance(p, str):
            out.extend(encode_macro(p).encode("latin-1"))
        else:
            out.extend(p)
    return out.decode("latin-1")


MACROS: dict[int, tuple[str, str]] = {
    0: ("git status", m("git status", ENTER)),
    1: ("git diff", m("git diff", ENTER)),
    2: ("git log --oneline -10", m("git log ", "-", "-", "oneline ", "-", "10", ENTER)),
    3: ("git pull --rebase", m("git pull ", "-", "-", "rebase", ENTER)),
    4: ("git push", m("git push", ENTER)),
    5: ("git add -A", m("git add ", "-", "A", ENTER)),
    6: ('git commit -m "" (cursor inside)', m("git commit ", "-", "m ", '"', LEFT)),
    7: ("git push -u origin HEAD", m("git push ", "-", "u origin HEAD", ENTER)),
    8: ("git reflog", m("git reflog", ENTER)),
    9: ("git stash", m("git stash", ENTER)),
    10: ("AI: explain this code", m("Explica este c", "ó", "digo: ")),
    11: ("AI: refactor", m("Refactoriza: ")),
    12: ("AI: write tests", m("Escribe tests para: ")),
    13: ("AI: TL;DR", m("TL;", "DR: ")),
    14: ("snippet ()", m("(", ")", LEFT)),
    15: ("snippet []", m(LBRACK, RBRACK, LEFT)),
    16: ("snippet {}", m(LBRACE, RBRACE, LEFT)),
    17: ('snippet ""', m('"', LEFT)),
    18: ("snippet ''", m("'", LEFT)),
}

# ---------------------------------------------------------------------------
# Layer maps: 9 layers, each 4 rows x 12 keys, legacy Vial keycode names.
# ---------------------------------------------------------------------------

TR = "KC_TRNS"
NO = "KC_NO"

L0 = [
    ["KC_Q", "KC_W", "KC_E", "KC_R", "KC_T", "KC_ESCAPE", "KC_TAB", "KC_Y", "KC_U", "KC_I", "KC_O", "KC_P"],
    ["LGUI_T(KC_A)", "LALT_T(KC_S)", "LCTL_T(KC_D)", "LSFT_T(KC_F)", "KC_G",
     "KC_LBRACKET", "KC_SCOLON", "KC_H", "RSFT_T(KC_J)", "RCTL_T(KC_K)", "RALT_T(KC_L)", "LT2(KC_ENTER)"],
    ["KC_Z", "KC_X", "KC_C", "KC_V", "KC_B", "KC_COMMA", "KC_DOT",
     "KC_N", "KC_M", "KC_SLASH", "KC_MINUS", "KC_GRAVE"],
    ["MO(3)", "KC_LSFT", "KC_LCTL", "KC_LALT", "LT1(KC_SPACE)", "KC_ENTER", "KC_BSPACE",
     "KC_DELETE", "MO(2)", "MO(4)", "KC_CAPSLOCK", "KC_RALT"],
]

L1 = [
    ["LSFT(KC_1)", "LSFT(KC_2)", "LSFT(KC_3)", "LSFT(KC_4)", "LSFT(KC_5)",
     "RALT(KC_4)", "RALT(KC_BSLASH)", "KC_7", "KC_8", "KC_9", "KC_RBRACKET", "LSFT(KC_RBRACKET)"],
    ["LSFT(KC_7)", "LSFT(KC_8)", "LSFT(KC_9)", "LSFT(KC_0)", "RALT(KC_2)",
     "KC_GRAVE", TR, "KC_4", "KC_5", "KC_6", "KC_SLASH", "LSFT(KC_SLASH)"],
    ["LSFT(KC_QUOTE)", "LSFT(KC_BSLASH)", "RALT(KC_8)", "RALT(KC_9)", "RALT(KC_MINUS)",
     "KC_EQUAL", "LSFT(KC_EQUAL)", "KC_1", "KC_2", "KC_3", "KC_0", "KC_DOT"],
    [TR, TR, TR, TR, TR, "LSFT(KC_COMMA)", "LSFT(KC_DOT)", TR, TR, TR, TR, TR],
]

L2 = [
    ["M0", "M1", "M2", "M3", "M4", TR, TR, "M5", "M6", "M7", "M8", "M9"],
    ["M10", "M11", "M12", "M13", NO, TR, TR, "M14", "M15", "M16", "M17", "M18"],
    ["KC_PSCREEN", "LGUI(KC_R)", "KC_VOLD", "KC_VOLU", "KC_BRID",
     "KC_BRIU", "LGUI(KC_LEFT)", "LGUI(KC_RIGHT)", "LGUI(KC_UP)", "LGUI(KC_DOWN)", NO, NO],
    [TR, TR, TR, TR, TR, TR, TR, TR, "TO(0)", TR, TR, TR],
]

L3 = [
    ["KC_F1", "KC_F2", "KC_F3", "KC_F4", "KC_F5", "KC_F6",
     "KC_F7", "KC_F8", "KC_F9", "KC_F10", "KC_F11", "KC_F12"],
    ["LCTL(KC_Z)", "LCTL(KC_X)", "LCTL(KC_C)", "LCTL(KC_V)", "LCTL(KC_A)",
     "KC_BTN1", "KC_MS_U", "KC_BTN2", "KC_WH_U", "KC_DELETE", NO, NO],
    ["KC_HOME", "KC_INSERT", "KC_END", "KC_PGUP", "KC_PSCREEN",
     "KC_MS_L", "KC_MS_D", "KC_MS_R", "KC_WH_D", NO, NO, NO],
    [TR, TR, TR, TR, TR, "KC_LEFT", "KC_DOWN", "KC_UP", "KC_RIGHT", "KC_PGDOWN", TR, TR],
]

L4 = [
    ["KC_MUTE", "KC_VOLD", "KC_VOLU", "KC_MPRV", "KC_MPLY", "KC_MNXT",
     "KC_BRID", "KC_BRIU", "KC_PSCREEN", "KC_SCROLLLOCK", "KC_PAUSE", NO],
    ["TO(0)", "TO(1)", "TO(2)", "TO(3)", "TO(4)", NO, NO, NO, NO, NO, NO, NO],
    ["RGB_TOG", "RGB_MOD", "RGB_HUI", "RGB_SAI", "RGB_VAI",
     "RGB_HUD", "RGB_SAD", "RGB_VAD", NO, NO, NO, NO],
    [NO, NO, NO, NO, NO, NO, NO, NO, NO, NO, NO, "QK_BOOT"],
]

LAYERS = [L0, L1, L2, L3, L4] + [
    [[NO] * 12 for _ in range(4)] for _ in range(4)  # layers 5-8 unused
]

MACRO_REFS = {f"M{i}": i for i in range(19)}

# ---------------------------------------------------------------------------
# Docs: ASCII maps showing es-419 output characters.
# ---------------------------------------------------------------------------

L0_ASCII = """\
 Q      W      E      R      T   │ Esc    Tab  │ Y      U      I      O      P
A/Gui  S/Alt  D/Ctl  F/Sft   G   │  ´      ñ   │  H    J/Sft  K/Ctl  L/Alt Ent/L2
 Z      X      C      V      B   │  ,      .   │  N      M      -      '      |
L3     Sft    Ctl    Alt   Spc/L1│ Enter  Bksp │ Del    L2     L4    Caps  AltGr"""

L1_ASCII = """\
 !      "      #      $      %   │  ~      `   │  7      8      9      +      *
 /      (      )      =      @   │  |          │  4      5      6      -      _
 {      }      [      ]      \\   │  ¿      ¡   │  1      2      3      0      .
                             │  ;      :   │"""

L2_ASCII = """\
gst    gdp    glo    gpl    gps  │             │ gaa    gcm    gpu    grl    gsh
exp    ref    tst    tldr        │             │ ( )    [ ]    { }    ""     ''
PrtSc  rofi   vol-   vol+   br-  │ br+   snapL │ snapR  snapUp snapDn
                                          │      │       TO(0)"""

L3_ASCII = """\
 F1     F2     F3     F4     F5   │  F6     F7   │  F8     F9    F10    F11    F12
undo   cut    copy   paste  selall│ Lclk  ms↑   │ Rclk   whl↑   Del
Home   Ins    End    PgUp   PrtSc │ ms←   ms↓   │ ms→    whl↓
                             │  ←      ↓    │  ↑      →    PgDn"""

L4_ASCII = """\
mute   vol-   vol+   prev   play │ next   br-   │ br+    PrtSc  Scrlk Pause
TO(0)  TO(1)  TO(2)  TO(3)  TO(4)│
rgbT   rgbM   rgbH+  rgbS+  rgbV+│ rgbH-  rgbS-  rgbV-
                                                          QK_BOOT (corner)"""


def build(data: dict) -> dict:
    """Fill the custom layout into a copy of the factory snapshot."""
    out = dict(data)
    out["layout"] = LAYERS
    macro_array = [""] * len(data["macro"])
    for slot, (_label, encoded) in MACROS.items():
        macro_array[slot] = encoded
    out["macro"] = macro_array
    return out


def validate(out: dict, factory: dict) -> tuple[list[str], int]:
    errors: list[str] = []
    if out["uid"] != factory["uid"]:
        errors.append("uid changed — Vial would reject the file")
    for key in ("vial_protocol", "via_protocol", "version", "layout_options"):
        if out.get(key) != factory.get(key):
            errors.append(f"{key} changed")
    for i, layer in enumerate(out["layout"]):
        if len(layer) != 4 or any(len(row) != 12 for row in layer):
            errors.append(f"layer {i} is not 4x12")
    if len(out["macro"]) != len(factory["macro"]):
        errors.append("macro slot count changed")

    resolved = set()
    for layer in out["layout"]:
        for row in layer:
            for key in row:
                if key in MACRO_REFS:
                    slot = MACRO_REFS[key]
                    resolved.add(slot)
                    if slot not in MACROS:
                        errors.append(f"macro slot {slot} referenced but not defined")
    for slot in MACROS:
        if slot not in resolved:
            errors.append(f"macro slot {slot} defined but never placed on a layer")

    total = sum(len(e.encode("latin-1")) for _, e in MACROS.values())
    return errors, total


def write_docs() -> None:
    layout_md = f"""# KeyzBoard — Layer Maps

Generated by `tools/generate_layout.py`. Do not edit by hand: edit the script
and regenerate. Load `layout/keyzboard.vil` with Vial (`File > Load saved
layout`).

Host OS layout assumed: **Latin American Spanish (es-419)**. Characters shown
are what the OS layout produces from each scancode. `X/Mod` = tap for `X`,
hold for `Mod`. Blank cells are transparent (fall through to the layer
below). Center columns (5-6) are the thumb zone.

## Layer 0 — BASE

QWERTY with home-row mods. Thumb left = space (hold → L1 numbers), thumb
right = enter (hold → L2 macros). The Spanish cluster (`´` dead accent +
`ñ`) lives on the center columns.

```text
{L0_ASCII}
```

- `A S D F` / `J K L` are home-row mods: tap = letter, hold = Gui/Alt/Ctrl/Shift.
- Bottom row right: `-` (dash), `'` (apostrophe), `|` (pipe) — es-419 native
  positions.
- Bottom row triggers: `L3` nav (left), `L2` macros, `L4` system (right).

## Layer 1 — NUMBERS & SYMBOLS

Hold Space. Numpad-style digits under the right hand; code symbols on the
left, all encoded through the real es-419 scancode map (Shift/AltGr), never
guessed.

```text
{L1_ASCII}
```

## Layer 2 — COMMANDS (git / AI / snippets / OS)

Hold `L2` (bottom row) or Enter tap-hold. Transparent elsewhere, so the
layer never interrupts typing. Full catalog in [macros.md](macros.md).

```text
{L2_ASCII}
```

- Git macros type into the focused terminal (alacritty + zsh) and press Enter.
- `rofi` = `Super+R` (Qtile `spawncmd`). Snap keys are Windows `Win+←→↑↓`
  (no-ops on Qtile, which owns window management through your home-row Gui).
- `gcm` = `git commit -m ""` with the cursor between the quotes.

## Layer 3 — NAV & MOUSE

Hold `L3` (bottom-left). F-row, clipboard classics, arrows on the bottom
center, and mouse keys (your firmware ships with mouse keys enabled).

```text
{L3_ASCII}
```

## Layer 4 — SYSTEM

Hold `L4` (bottom row). Media/brightness on the top row (Qtile listens to
the XF86 keys), `TO(n)` layer switchers, RGB, and `QK_BOOT` hidden at the
far bottom-right corner.

```text
{L4_ASCII}
```

## Layers 5-8

Unused (`KC_NO` everywhere). Nothing in the layout reaches them.
"""
    OUT_LAYOUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_LAYOUT_MD.write_text(layout_md, encoding="utf-8")

    rows = "\n".join(
        f"| {slot} | `{label}` |" for slot, (label, _) in sorted(MACROS.items())
    )
    macros_md = f"""# KeyzBoard — Macro Catalog

Defined in `tools/generate_layout.py` (`MACROS`). Slot numbers match the
`macro` array in the `.vil`. Encoded for a **Latin American (es-419) host
layout**: punctuation is emitted as explicit scancode taps, never as raw
ASCII — Vial macros otherwise assume a US layout and would type wrong
characters on your host.

| Slot | Macro |
|-----:|-------|
{rows}

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
- `}}` and `[` `]` use AltGr/shifted scancodes verified against XKB `latam`;
  if any symbol lands wrong on Windows es-MX, tell me which — it is a
  one-line fix and regenerate.
"""
    OUT_MACROS_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MACROS_MD.write_text(macros_md, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args()

    factory = json.loads(FACTORY.read_text(encoding="utf-8"))
    out = build(factory)
    errors, total_bytes = validate(out, factory)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"OK: 9 layers 4x12, {len(MACROS)} macros, {total_bytes} macro bytes")
    print(f"uid preserved: {out['uid']}")

    if args.check:
        return 0

    encoded = json.dumps(out, ensure_ascii=True, separators=(",", ":"))
    OUT_VIL.parent.mkdir(parents=True, exist_ok=True)
    OUT_VIL.write_text(encoded + "\n", encoding="utf-8")
    write_docs()
    print(f"wrote {OUT_VIL.relative_to(REPO)}")
    print(f"wrote {OUT_LAYOUT_MD.relative_to(REPO)}")
    print(f"wrote {OUT_MACROS_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
