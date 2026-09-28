# Contributing

Thanks for your interest in KeyzBoard!

## The golden rule

**Never edit `layout/keyzboard.vil` or `docs/*.md` by hand.** They are
generated output. The single source of truth is `tools/generate_layout.py`:

- Layer maps live in the `LAYERS` structure.
- Macros live in the `MACROS` catalog.

## Workflow

1. Edit `tools/generate_layout.py`.
2. Validate (no files are written):

   ```sh
   python3 tools/generate_layout.py --check
   ```

3. Regenerate `layout/` and `docs/`:

   ```sh
   python3 tools/generate_layout.py
   ```

4. Commit the generator change **together with** its regenerated output.
   CI runs `--check` on every push and PR, so an out-of-sync tree fails
   the build.

## Testing on hardware

Load `layout/keyzboard.vil` into [Vial](https://get.vial.today/) (desktop
app or Chrome; note that WSL2 cannot see HID devices). Changes apply live,
no flashing. Keep `currentLayout.vil` untouched — it is the factory
recovery snapshot.

## Pull requests

- Keep PRs small and focused (one layer or one macro group per PR is a
  good size).
- Make sure `--check` passes locally before pushing.
- Explain *what* the layout change does and *why* (ergonomics, encoding
  fix, etc.).
