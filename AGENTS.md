# AGENTS.md

## Project Overview

**Revo Norm** is a Python library for text normalization designed for Text-to-Speech (TTS) applications. It converts written text (numbers, currency, dates, abbreviations, etc.) into spoken form for **English** and **Malay** (Bahasa Melayu).

## Setup Commands

- Install from source: `uv sync`
- Install with dev deps: `uv sync --group dev`
- Run linter: `uv run ruff check revo_norm/`
- Auto-fix lint issues: `uv run ruff check revo_norm/ --fix`
- Format code: `uv run ruff format revo_norm/`
- Check formatting: `uv run ruff format --check revo_norm/`

## Testing Instructions

Tests are maintained in a separate repository.

- Run all tests: `uv run pytest ../revo-norm-tests/ -v --tb=short`
- Run with coverage: `uv run pytest ../revo-norm-tests/ --cov --cov-report=term-missing`
- Run a single test class: `uv run pytest ../revo-norm-tests/<test_file>.py::TestClass -v`
- Run a single test: `uv run pytest ../revo-norm-tests/<test_file>.py::TestClass::test_method -v`
- Always run `uv run ruff check revo_norm/` and `uv run pytest ../revo-norm-tests/ -q` before committing.

## Code Architecture

### Module Map

| Module | Purpose |
|--------|---------|
| `text_normalizer.py` | Main orchestrator — `normalize_text()` entry point and pipeline |
| `entity_extractor.py` | Entity extraction system — extract → placeholder → process → restore |
| `pronunciation_mappings.py` | Explicit pronunciation overrides (JSON→"jay son", GUI→"gooey") |
| `normalizer_en.py` | English normalization (contractions, abbreviations, numbers) |
| `normalizer_ms.py` | Malay normalization (grammar, vocabulary, number-to-words) |
| `normalizer_zh.py` | Chinese normalization (numbers, percentages, decimals, measurement helpers) |
| `normalizer_zh_my.py` | Malaysian Chinese normalization (code-mixing, colloquial currency) |
| `shared_features.py` | Shared feature normalizers (temperature, measurements, fractions, hijri, etc.) |
| `currency_utils.py` | Currency K/M/B/T suffix expansion (RM50K → RM50000) |
| `num2word_ms.py` | Malay number-to-words conversion (zero through decillions) |
| `num2word_zh.py` | Chinese number-to-words conversion (零 through 兆) |
| `tts_utils.py` | TTS post-processing (sound words, chunking, random commas) |
| `config.py` | Configuration profiles (minimal/basic/standard/aggressive) and feature groups |

### Single Pipeline Architecture

The library uses a **single unified pipeline** with entity extraction always enabled. Entity extraction protects patterns (dates, currency, URLs, emails, etc.) from being mangled by downstream transformations.

### Feature Organization

**Entity-Specific Features** (have dedicated regex patterns, safe to disable):
- URLs, Emails, IC Numbers, Dates, Times, Temperature, Fractions, X-Kali, Measurements, Hari Bulan, Hijri Years

**Global Features** (operate on entire text):
- Language-specific normalization, number normalization, elongated words, abbreviations, acronyms, spacing

### Critical Pipeline Dependencies

These ordering constraints MUST be preserved:
1. **Currency K-suffix before URLs**: `RM30K` → `RM30000` must happen before URL processing
2. **Pronunciation mappings before acronym expansion**: Prevents `JSON` → `J S O N`
3. **Dates before Fractions**: Entity extraction prevents date/fraction pattern conflict

### Pipeline Flow Diagram

The full text normalization flow is documented in `REPO_ANALYSIS/full_text_flow.md`.
This file is auto-generated. **When you modify the pipeline** (add/remove steps, change ordering, add entity types), regenerate it:
```bash
uv run python scripts/generate_flow.py
```
Always regenerate the flow after changing `text_normalizer.py`, `entity_extractor.py`, `normalizer_en.py`, `normalizer_ms.py`, or `shared_features.py`.

## Code Style

- Python 3.12+, use `uv` for package management
- Linter: `ruff` — treat lint failures as blocking
- Use `logging` not `print` for runtime output
- Prefer functional patterns where practical
- Pre-compiled regex at module level (not inside functions)
- Sort regex alternatives by length (longest first) for overlapping patterns
- Use `\b` word boundaries carefully — avoid partial matches

### Ruff Configuration

Configuration lives in `pyproject.toml`:

- **Line length**: 100 characters
- **Indent width**: 4 spaces
- **Quote style**: Double quotes
- **Python version**: 3.9+

#### Ruff Rules Enabled

- `E` - pycodestyle errors
- `W` - pycodestyle warnings
- `F` - pyflakes
- `I` - isort (import sorting)
- `N` - pep8-naming
- `UP` - pyupgrade (modernize Python syntax)
- `B` - flake8-bugbear (find common bugs)
- `C4` - flake8-comprehensions (improve comprehensions)
- `SIM` - flake8-simplify (simplify code)

#### Migration from Old Tools

| Old Tool | New Tool | Migration Guide |
|----------|----------|------------------|
| **pip** | **uv** | `pip install -e .[dev]` → `uv sync --all-extras` |
| **black** | **ruff format** | `black revo_norm/` → `uv run ruff format revo_norm/` |
| **flake8** | **ruff check** | `flake8 revo_norm/` → `uv run ruff check revo_norm/` |
| **isort** | **ruff check --select I** | Auto-handled by ruff |
| **mypy** | **ty** (optional) | Install separately: `uv add --dev ty` |

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
uv add --dev pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]
        pass_filenames: false
EOF

# Install hooks
pre-commit install
```

### IDE Configuration

#### VS Code

Install these extensions:
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

Add to `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

#### PyCharm

1. Go to Settings → Tools → External Tools
2. Add ruff format and ruff check as external tools
3. Enable "Enable ruff support" in Languages & Frameworks → Python

## Language-Specific Guidelines

- **Code-mixing** is common: English terms in Malay sentences are normal, don't strip them
- **Date formats**: DD/MM/YYYY, YYYY-MM-DD, DD Month YYYY (Malay month names too)
- **Hijri calendar**: Islamic year conversion exists, test both Arabic numerals and Malay text
- **Currency**: RM (Ringgit Malaysia) is the primary currency, also USD/EUR/GBP/JPY
- **IC numbers**: Malaysian identity card format (12 digits), specific spoken form

## When Adding New Features

### Entity-specific feature (URLs, dates, temperature, etc.)
1. Add entity type to `EntityType` enum in `entity_extractor.py`
2. Add pattern compilation method
3. Add extraction logic in `_compile_patterns()`
4. Add conversion in `_convert_entity_to_spoken()`

### Global feature (affects all text)
1. Add to `normalizer_en.py` or `normalizer_ms.py` (or both)
2. Add config support: new `FeatureGroup` in `config.py` if needed
3. Add to pipeline in `text_normalizer.py`

### Pronunciation override
1. Add mapping to `pronunciation_mappings.py` via `add_custom_mapping()` or edit `PRONUNCIATION_MAPPINGS`
2. Mappings are applied FIRST in the pipeline — they always win

## Testing Guidelines

- Test files are in a separate repository
- `conftest.py` provides shared fixtures: `normalize`, `pronunciation_state`, `assert_contains_any`, `assert_normalized`
- Use `pronunciation_state` fixture when calling `add_custom_mapping()` — it saves/restores global state
- Use `assert_contains_any(result, ["a", "b"])` instead of `assert "a" in result or "b" in result`
- Test both `language="en"` and `language="ms"` for bilingual features
- Use `normalize_text(text, language="en")` for default (all features on)
- Use `normalize_text(text, language="en", disable=["temperature"])` to disable specific features
- Use `normalize_text(text, language="en", profile="minimal")` for preset configurations

## Known Issues

- **M/B/T currency suffix expansion** fails in entity extraction path (7 tests fail, pre-existing bug)
- **Date DD/MM vs MM/DD**: Heuristic-based, ambiguous dates may parse wrong
- **Global state**: `add_custom_mapping()` mutates module-level dict — not thread-safe

## Troubleshooting

### "uv: command not found"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "ruff: command not found"

Install dependencies:
```bash
uv sync --all-extras
```

### Tests failing after formatting

Make sure to run `uv run ruff format` before committing. If tests fail, check that no logic was accidentally changed.

### Import errors

Run `uv sync` to ensure all dependencies are installed.

## Commit Guidelines

- Run `uv run ruff check revo_norm/` and fix all issues before committing
- Run `uv run pytest ../tests/revo-norm/ -q` and ensure no new failures
- Use `git mv` for file renames to preserve history
