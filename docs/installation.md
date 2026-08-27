# Installation

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.9 |
| Dependencies | `nltk >= 3.8`, `inflect >= 6.0` |

Dependencies are installed automatically with revo-norm.

## Install via uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager.

```bash
# Add to your project
uv add revo-norm
```

## Install via pip

```bash
pip install revo-norm
```

## Install from Source

Use this method if you need to modify revo-norm or want the latest development version.

```bash
# Clone the repository
git clone https://github.com/Revolab-Sdn-Bhd/revo-norm.git
cd revo-norm

# Install in development mode
uv sync
```

!!! note
    Install [uv](https://docs.astral.sh/uv/) first if you don't have it:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Verify Installation

Run this quick test to confirm revo-norm is installed correctly:

```bash
python -c "from revonorm import normalize_text; print(normalize_text('Hello 123', language='en'))"
```

You should see output like:

```
Hello one hundred and twenty three
```

## Development Dependencies

If you are contributing to revo-norm, install the development toolchain:

```bash
# Clone and enter the repo
git clone https://github.com/Revolab-Sdn-Bhd/revo-norm.git
cd revo-norm

# Install with dev dependencies
uv sync --group dev

# Install with docs dependencies
uv sync --group docs

# Install everything
uv sync --all-groups
```

### Dev Tools Included

| Tool | Purpose |
|------|---------|
| `pytest >= 8.4.2` | Test runner |
| `pytest-cov >= 7.0.0` | Coverage reporting |
| `ruff >= 0.8.0` | Linting and formatting |

### Common Dev Commands

```bash
# Run linter
uv run ruff check revonorm-core/python/revonorm/

# Auto-fix lint issues
uv run ruff check revonorm-core/python/revonorm/ --fix

# Format code
uv run ruff format revonorm-core/python/revonorm/

# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov --cov-report=term-missing
```

!!! tip
    Run `uv run ruff check revonorm-core/python/revonorm/` and `uv run pytest -q` before every commit to catch issues early.
