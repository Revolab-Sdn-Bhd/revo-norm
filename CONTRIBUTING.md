# Contributing to Revo Norm

Thanks for helping improve text normalization for TTS.

## Project layout

Two implementations of the same engine, locked to identical output:

| Directory | What it is |
|---|---|
| `revonorm-core/python/revonorm/` | Pure Python — the reference implementation |
| `revonorm-core/` | Compiled engine, shipped as the `revonorm` (PyPI) and `@revolab/revonorm` (npm) packages |

Behavior changes go in Python first — it is the source of truth. CI
regenerates test fixtures from Python and runs them against the compiled
engine, so any rule change without a matching port **fails CI** until both
agree byte-for-byte.

## Setup

```bash
git clone https://github.com/Revolab-Sdn-Bhd/revo-norm.git
cd revo-norm
uv sync --all-extras
```

## Development loop

```bash
# Python: lint + tests
uv run ruff check revonorm-core/python/revonorm/
uv run pytest ../revo-norm-tests/ -q        # private test repo (CI runs it for you)

# Compiled engine: parity + lint
cargo test --manifest-path revonorm-core/Cargo.toml
cargo clippy --manifest-path revonorm-core/Cargo.toml -- -D warnings
```

The test suite lives in a separate private repository (`revo-norm-tests`).
You cannot run it locally without access; CI runs it on every PR — a green
CI is the test gate for external contributors.

### Changing normalization rules

1. Edit the rule in `revonorm-core/python/revonorm/` (and its language pack entry if vocabulary changed).
2. Regenerate parity fixtures:
   ```bash
   uv run python revonorm-core/tests/gen_fixtures.py
   ```
3. Port the same change to `revonorm-core/src/` until `cargo test` passes.
4. Both outputs must match byte-for-byte — quirks included. If the change is
   intentional, update fixtures; never special-case the compiled side.

## Pull requests

- Branch from `main`; one logical change per PR.
- Conventional commit subjects: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:` — max 50 chars.
- CI must be green: Python tests, rust parity, clippy.
- Never self-merge — a maintainer reviews and merges.

### Releases (maintainers)

- Version lives in `revonorm-core/Cargo.toml` — the single source; PyPI and
  npm inherit it. Bump it in the release PR.
- Tag as `vX.Y.Z` **equal to** the Cargo version — CI fails the tag otherwise.
- Pushing the tag builds and publishes PyPI (trusted publishing) and npm
  automatically. Tag with a `-no-publish` suffix for a dry run.
- Lock-and-wrap the release: a separate `chore(release): bump to vX.Y.Z`
  commit that bumps the version and updates `docs/changelog.md`, nothing else.

## Adding a language

Each language is one pack of vocabulary plus one normalizer module — no core
pipeline edits:

- Python: an entry in `revonorm-core/python/revonorm/langpack.py` + a `normalizer_<code>.py`.
- Compiled: `revonorm-core/src/lang/<code>.rs` + registry entry, mirroring
  the Python module exactly.

## Questions

Open an issue with the input text, the language, and what you expected vs.
got.
