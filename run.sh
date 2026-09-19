#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v uv >/dev/null 2>&1; then
    echo 'Please install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
uv sync --locked
exec uv run --frozen navigation-lab "$@"
