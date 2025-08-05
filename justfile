_default:
    @just --list

# --- Testing ---

alias t := test-all

test-all *args:
    @uv run --group=test --group=sftp pytest --backend-tests --sftp-tests {{args}}

test *args:
    @uv run --group=test pytest {{args}}

# --- Formatting ---

alias f := format

# Format files
format *files: (format-python files)

# Format Python files
format-python *files:
    @uv run --group=format ruff format {{files}}

# Format Markdown files
format-md *files='.':
    @uv run --group=format mdformat {{files}}

# --- Linting ---

alias l := lint

# Lint the codebase
lint *files: (lint-python files) (spell files)

# Lint Python files
lint-python *files:
    @uv run --group=lint ruff check --fix --exit-non-zero-on-fix {{files}}

# Check spelling
spell *files:
    @uv run --group=lint codespell {{files}}

# Type-check with Mypy
mypy *args='.':
    @uv run --group=dev mypy {{args}}

# --- Other ---

# Remove the output from a Jupyter notebook
strip-output *notebooks:
    @uv run --group=format nbstripout \
      --drop-empty-cells \
      --extra-keys 'metadata.language_info.version cell.metadata.jp-MarkdownHeadingCollapsed cell.metadata.pycharm' \
      {{notebooks}}
