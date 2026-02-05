_default:
    @just --list

# --- Testing ---

alias t := test-all

# Run all tests
test-all *args:
    @uv run --group=test --group=sftp pytest --backend-tests --sftp-tests {{ args }}

# Run basic tests
test *args:
    @uv run --group=test pytest {{ args }}

# Run tests with dependencies as lowest bounds
test-lowest *args:
    @uv run --resolution=lowest-direct --group=test --group=sftp pytest --backend-tests --sftp-tests {{ args }}

# --- Formatting ---

alias f := format

# Format args
format: format-python format-md format-just

# Format Python args
format-python:
    @prek run ruff-format -a

# Format Markdown args
format-md:
    @prek run mdformat -a

# Format Justfiles
format-just:
    @prek run just-format -a

# --- Linting ---

alias l := lint

# Lint the codebase
lint: lint-python spell

# Lint Python args
lint-python:
    @prek run ruff -a

# Check spelling
spell:
    @prek run typos -a

# Type-check with Mypy
mypy *args='.':
    @uv run --group=dev mypy {{ args }}

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

# Build a wheel
build:
    @uv build

# Generate SciCat models, launches a SciCat backend
[working-directory('tools/model-generation')]
generate-models:
    @uv run python generate_models.py --launch-scicat

# Remove the output from a Jupyter notebook
strip-output *notebooks:
    @prek run nbstripout {{ notebooks }}

# Lock dependencies
lock:
    @uv lock
