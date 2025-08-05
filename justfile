_default:
    @just --list

# --- Testing ---

alias t := test-all

# Run all tests
test-all *args:
    @uv run --group=test --group=sftp pytest --backend-tests --sftp-tests {{args}}

# Run basic tests
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

# --- Docs ---

# Build and test the documentation
docs: docs-build
    @uv run --group=docs python -m sphinx -v -j2 -b doctest -d build/.doctrees docs html
    @uv run --group=docs python -m sphinx -v -j2 -b linkcheck -d build/.doctrees docs html
    @find html -type f -name "*.ipynb" -not -path "html/_sources/*" -delete

# Build the documentation
docs-build:
    @uv run --group=docs python -m sphinx -v -j2 -b html -d build/.doctrees docs html
    @touch html/.nojekyll
    @find html -type f -name "*.ipynb" -not -path "html/_sources/*" -delete

# Remove all documentation artifacts (intermediate and final)
clean-docs:
    rm -rf docs/generated
    rm -rf build/.doctrees
    rm -rf html

# --- Other ---

build:
    @uv run --group=build python -m build

# Remove the output from a Jupyter notebook
strip-output *notebooks:
    @uv run --group=format nbstripout \
      --drop-empty-cells \
      --extra-keys 'metadata.language_info.version cell.metadata.jp-MarkdownHeadingCollapsed cell.metadata.pycharm' \
      {{notebooks}}

# Lock dependencies
lock:
    @uv lock
