#!/usr/bin/env bash
set -eu -o pipefail

./scripts/build-lean.sh

(cd tbps-be && \
uv add -r requirements.txt && \
uv run python -m search_app.main_new)
