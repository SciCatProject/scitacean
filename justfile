# Lint the codebase.
lint:
    @uv run --group=lint ruff check

# Remove the output from a Jupyter notebook.
strip-output *notebooks:
    @uv run --group=format nbstripout \
      --drop-empty-cells \
      --extra-keys 'metadata.language_info.version cell.metadata.jp-MarkdownHeadingCollapsed cell.metadata.pycharm' \
      {{notebooks}}
